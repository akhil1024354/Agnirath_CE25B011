import numpy as np

def get_solar_power(time_seconds):
    """
    Calculates the available electrical power from the solar array at a specific time.
    
    Parameters:
    time_seconds (float): Seconds elapsed since midnight (e.g., 8:00 AM = 28800)
    
    Returns:
    float: Electrical power output in Watts
    """
    # Hardware Constants
    AREA = 6.0              # m^2
    EFFICIENCY = 0.241      # 24.1%
    
    # Gaussian Environment Constants
    PEAK_IRRADIANCE = 1073.0 # W/m^2
    MEAN_TIME = 43200.0      # 12:00 PM in seconds
    STD_DEV = 11600.0        # seconds
    
    # Calculate Irradiance at time t using the Gaussian curve
    irradiance = PEAK_IRRADIANCE * np.exp(-0.5 * ((time_seconds - MEAN_TIME) / STD_DEV)**2)
    
    # Convert Irradiance to Electrical Power
    power_out = AREA * EFFICIENCY * irradiance
    
    return power_out