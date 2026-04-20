import requests
import pandas as pd
import numpy as np
import time
from scipy.interpolate import interp1d

# ==========================================
# 1. HELPER FUNCTIONS
# ==========================================
def haversine(lat1, lon1, lat2, lon2):
    """Calculates the physical distance in meters between two GPS coordinates."""
    R = 6371000  
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

# ==========================================
# 2. FETCH OSRM ROUTE
# ==========================================
print("1. Fetching raw route from OSRM...")
# Sasolburg to Zeerust
lon1, lat1 = 27.8285, -26.8183 
lon2, lat2 = 26.0754, -25.5369 

osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
osrm_response = requests.get(osrm_url).json()

raw_coordinates = osrm_response['routes'][0]['geometry']['coordinates']
raw_lats = [coord[1] for coord in raw_coordinates]
raw_lons = [coord[0] for coord in raw_coordinates]
print(f"   -> Fetched {len(raw_coordinates)} raw coordinates.")

# ==========================================
# 3. CLEANING & CUMULATIVE DISTANCE
# ==========================================
print("\n2. Cleaning data and filtering duplicates...")
clean_lats = [raw_lats[0]]
clean_lons = [raw_lons[0]]
cumulative_distances = [0.0]

for i in range(1, len(raw_lats)):
    dist = haversine(clean_lats[-1], clean_lons[-1], raw_lats[i], raw_lons[i])
    # Drop points that have 0 distance between them to prevent math crashes later
    if dist > 0:
        clean_lats.append(raw_lats[i])
        clean_lons.append(raw_lons[i])
        cumulative_distances.append(cumulative_distances[-1] + dist)

total_route_distance = cumulative_distances[-1]
print(f"   -> Total physical route distance: {total_route_distance / 1000:.2f} km")

# ==========================================
# 4. GENERATE BASE GEOMETRIES
# ==========================================
print("\n3. Generating Base Geometries...")
API_RES = 250.0  # Safe resolution for the API
OPT_RES = 50.0   # High resolution for the Optimizer

api_distances = np.arange(0, total_route_distance, API_RES)
opt_distances = np.arange(0, total_route_distance, OPT_RES)

# Interpolate Lat/Lons based on the physical distances
lat_interpolator = interp1d(cumulative_distances, clean_lats, kind='linear')
lon_interpolator = interp1d(cumulative_distances, clean_lons, kind='linear')

api_lats = lat_interpolator(api_distances)
api_lons = lon_interpolator(api_distances)

opt_lats = lat_interpolator(opt_distances)
opt_lons = lon_interpolator(opt_distances)

print(f"   -> Required API Points: {len(api_distances)} (Rate-Limit Safe)")
print(f"   -> Final Optimizer Points: {len(opt_distances)} (High-Res)")

# ==========================================
# 5. FETCH ELEVATION (WITH STRICT PAIRING)
# ==========================================
print("\n4. Fetching API Elevation Data (POST Method w/ Strict Pairing)...")
meteo_url = "https://api.open-meteo.com/v1/elevation"

verified_distances = []
verified_elevations = []
chunk_size = 100 

for i in range(0, len(api_lats), chunk_size):
    chunk_lats = api_lats[i : i + chunk_size].tolist()
    chunk_lons = api_lons[i : i + chunk_size].tolist()
    chunk_dists = api_distances[i : i + chunk_size].tolist()
    
    payload = {"latitude": chunk_lats, "longitude": chunk_lons}
    
    max_retries = 3
    chunk_success = False
    
    for attempt in range(max_retries):
        try:
            response = requests.post(meteo_url, json=payload, timeout=10)
            if response.status_code == 200:
                elevs = response.json().get('elevation', [])
                
                # STRICT PAIRING: Only append if the API returned exactly what we asked for
                if len(elevs) == len(chunk_lats):
                    verified_elevations.extend(elevs)
                    verified_distances.extend(chunk_dists)
                    chunk_success = True
                break # Success, break out of retry loop
                
            elif response.status_code == 429:
                time.sleep(5 * (attempt + 1)) # Exponential backoff
            else:
                break # Fatal error, don't retry
                
        except requests.exceptions.RequestException:
            time.sleep(5) # Catch timeouts and silent drops
    
    if chunk_success:
        print(f"   -> Fetched chunk {i // chunk_size + 1} successfully.")
    else:
        print(f"   -> WARNING: Chunk {i // chunk_size + 1} dropped points. Skipped to protect alignment.")
        
    time.sleep(1.0) # Polite pacing

print(f"\n   -> API returned {len(verified_elevations)} perfectly aligned points out of {len(api_distances)} requested.")

# ==========================================
# 6. LOCALLY UPSAMPLE TO 50m
# ==========================================
print("\n5. Locally Upsampling Elevation to 50m Resolution...")
elev_interpolator = interp1d(
    np.array(verified_distances), 
    np.array(verified_elevations), 
    kind='linear', 
    fill_value='extrapolate'
)

# Generate the high-res 50m elevations using the safe interpolator
opt_elevations = elev_interpolator(opt_distances)

# ==========================================
# 7. PHYSICS CALCULATIONS & EXPORT
# ==========================================
print("\n6. Calculating Physics Parameters and Exporting...")
df = pd.DataFrame({
    'distance_from_start_m': opt_distances,
    'latitude': opt_lats,
    'longitude': opt_lons,
    'elevation': opt_elevations
})

# Calculate elevation change and slope
df['next_elevation'] = df['elevation'].shift(-1)
df['delta_h'] = df['next_elevation'] - df['elevation']
df['distance_m'] = OPT_RES 

# Theta = arctan(opposite / adjacent)
df['slope_rad'] = np.arctan2(df['delta_h'], df['distance_m'])
df['slope_deg'] = np.degrees(df['slope_rad'])

# Clean up dataframe
df = df.dropna()
df = df[['distance_from_start_m', 'latitude', 'longitude', 'elevation', 'distance_m', 'slope_deg']]

export_filename = "sasolburg_to_zeerust_50m_res.csv"
df.to_csv(export_filename, index=False)
print(f"   -> Pipeline complete! Map saved locally as '{export_filename}'. Total rows: {len(df)}")