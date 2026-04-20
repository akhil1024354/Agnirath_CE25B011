import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def estimate_coefficients(csv_path: str):
    # constants
    MASS_KG = 300.0       # mass
    GRAVITY = 9.81        # g
    RHO = 1.225           # density
    
    # load data
    df = pd.read_csv(csv_path)
    
    # fix cols
    df.columns = df.columns.str.strip()
    
    # rename
    if 'timestamp' in df.columns and 'timestamps' not in df.columns:
        df.rename(columns={'timestamp': 'timestamps'}, inplace=True)
        
    # check cols
    if 'timestamps' not in df.columns:
        print(f"ERROR: Could not find 'timestamps' column.")
        print(f"Your CSV actually has these columns: {list(df.columns)}")
        return
    
    # cast to numeric
    df['velocity_ms'] = pd.to_numeric(df['velocity_ms'], errors='coerce')
    df['Gradient_deg'] = pd.to_numeric(df['Gradient_deg'], errors='coerce')
    df['timestamps'] = pd.to_numeric(df['timestamps'], errors='coerce')
    
    # rm negatives
    df.loc[df['velocity_ms'] < 0, 'velocity_ms'] = np.nan
    
    # interpolate
    cols_to_interpolate = ['velocity_ms', 'Gradient_deg']
    df[cols_to_interpolate] = df[cols_to_interpolate].interpolate(method='linear')
    
    # drop nans
    df = df.dropna(subset=['timestamps', 'velocity_ms', 'Gradient_deg']).reset_index(drop=True)
    
    # smooth
    WINDOW_SIZE = 15
    df['v_smooth'] = df['velocity_ms'].rolling(window=WINDOW_SIZE, center=True).mean()
    df['grad_smooth'] = df['Gradient_deg'].rolling(window=WINDOW_SIZE, center=True).mean()
    
    df = df.dropna(subset=['v_smooth', 'grad_smooth']).reset_index(drop=True)
    
    # kinematics
    dt = df['timestamps'].diff().bfill()
    dv = df['v_smooth'].diff().bfill()
    
    # no div by 0
    dt = dt.replace(0, np.nan).bfill() 
    
    df['acceleration'] = dv / dt
    
    # to rad
    df['theta_rad'] = np.radians(df['grad_smooth'])
    
    # drop nans
    df = df.dropna(subset=['acceleration', 'theta_rad', 'v_smooth']).reset_index(drop=True)
    
    # curve fit
    term_cda = 0.5 * RHO * (df['v_smooth'] ** 2)
    term_crr = MASS_KG * GRAVITY * np.cos(df['theta_rad'])
    A = np.column_stack((term_cda, term_crr))
    
    b = -MASS_KG * df['acceleration'] - MASS_KG * GRAVITY * np.sin(df['theta_rad'])
    
    # solve
    x, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
    
    estimated_cda = x[0]
    estimated_crr = x[1]
    
    print(f"--- ESTIMATION RESULTS ---")
    print(f"Estimated CdA : {estimated_cda:.4f} m^2")
    print(f"Estimated Crr : {estimated_crr:.5f}")
    
    # plot
    fitted_b = A.dot(x)
    fitted_acceleration = (-fitted_b - MASS_KG * GRAVITY * np.sin(df['theta_rad'])) / MASS_KG
    
    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamps'], df['acceleration'], label='Actual Smoothed Acceleration', alpha=0.7)
    plt.plot(df['timestamps'], fitted_acceleration, label='Fitted Acceleration Model', color='red', linewidth=2)
    
    plt.title('Coast-Down Validation: Actual vs Fitted Acceleration')
    plt.xlabel('Timestamp (s)')
    plt.ylabel('Acceleration (m/s^2)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# run
if __name__ == "__main__":
    estimate_coefficients("telemetry_A.csv")