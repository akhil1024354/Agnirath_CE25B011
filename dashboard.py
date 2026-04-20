import pandas as pd
import matplotlib.pyplot as plt

print("Loading optimal race strategy...")
try:
    df = pd.read_csv("optimal_race_strategy.csv")
except FileNotFoundError:
    print("ERROR: Could not find 'optimal_race_strategy.csv'.")
    exit()

# Convert distance from meters to kilometers for a much cleaner X-axis
df['distance_km'] = df['distance_from_start_m'] / 1000.0

# Create a massive 3-panel presentation dashboard
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
fig.suptitle('Agnirath Race Strategy: Sasolburg to Zeerust', fontsize=20, fontweight='bold')

# --- Panel 1: Route Topography ---
# Fills the area under the elevation curve so it looks like a physical mountain range
ax1.plot(df['distance_km'], df['elevation'], color='saddlebrown', linewidth=2)
ax1.fill_between(df['distance_km'], df['elevation'], df['elevation'].min() - 50, color='sandybrown', alpha=0.3)
ax1.set_ylabel('Elevation (m)', fontsize=12, fontweight='bold')
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.set_title('Physical Terrain', fontsize=14)

# --- Panel 2: Optimal Velocity Profile ---
ax2.plot(df['distance_km'], df['optimal_velocity_kmh'], color='royalblue', linewidth=2)
ax2.set_ylabel('Speed (km/h)', fontsize=12, fontweight='bold')
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.set_title('Optimizer Velocity Commands', fontsize=14)

# --- Panel 3: Battery State of Charge (SOC) ---
ax3.plot(df['distance_km'], df['expected_soc_percentage'], color='forestgreen', linewidth=2.5)
# Draw the strict 20% survival guardrail
ax3.axhline(y=20, color='red', linestyle='--', linewidth=2, label='20% Redline (Strict Limit)') 
ax3.set_xlabel('Distance (km)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Battery SOC (%)', fontsize=12, fontweight='bold')
ax3.set_ylim(0, 105) # Keep the Y-axis fixed from 0 to 100%
ax3.grid(True, linestyle='--', alpha=0.6)
ax3.legend(loc='upper right')
ax3.set_title('Energy Storage Management', fontsize=14)

# Clean up layout, save a high-res copy, and display
plt.tight_layout(rect=[0, 0.03, 1, 0.96])
plt.savefig('agnirath_strategy_dashboard.png', dpi=300)
print("Dashboard saved as high-resolution image: 'agnirath_strategy_dashboard.png'")

plt.show()