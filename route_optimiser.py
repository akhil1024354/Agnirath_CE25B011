import numpy as np
import pandas as pd
from scipy.optimize import minimize
import time

# IMPORT YOUR EXTERNAL SOLAR MODEL HERE
from solar_model import get_solar_power

# ==========================================
# 1. HARDWARE & ENVIRONMENT CONSTANTS
# ==========================================
MASS = 350.0            
A_FRONT = 1.2           
CD = 0.15               
CRR = 0.002             
RHO = 1.15              
G = 9.81                

ETA_M = 0.90            
ETA_R = 0.70            

BATT_CAPACITY_KWH = 5.0 
MAX_JOULES = BATT_CAPACITY_KWH * 3600000.0  
MIN_JOULES = 0.20 * MAX_JOULES # 20% strict floor

START_TIME_SEC = 8 * 3600.0    # 8:00 AM
MAX_FINISH_TIME = 17 * 3600.0  # 5:00 PM
MAX_DURATION = MAX_FINISH_TIME - START_TIME_SEC 

# ==========================================
# 2. LOAD THE MAP DATA
# ==========================================
print("Loading Map Data...")
try:
    route_df = pd.read_csv("sasolburg_to_zeerust_50m_res.csv")
except FileNotFoundError:
    print("ERROR: Could not find 'sasolburg_to_zeerust_50m_res.csv'. Run the Smart Cartographer API script first.")
    exit()

slopes = np.radians(route_df['slope_deg'].values)
distances = route_df['distance_m'].values
num_segments = len(slopes)
print(f"Loaded {num_segments} physical segments.")

# ==========================================
# 3. THE PHYSICS ENGINE
# ==========================================
def calculate_physics(velocities):
    times = distances / velocities
    cumulative_time = START_TIME_SEC + np.cumsum(times)
    
    F_aero = 0.5 * RHO * CD * A_FRONT * (velocities ** 2)
    F_rr = CRR * MASS * G * np.cos(slopes)
    F_g = MASS * G * np.sin(slopes)
    
    P_mech = (F_aero + F_rr + F_g) * velocities
    P_elec = np.where(P_mech > 0, P_mech / ETA_M, P_mech * ETA_R)
    
    # Free energy from the sun
    P_solar = get_solar_power(cumulative_time)
    
    energy_used_per_segment = (P_elec - P_solar) * times
    return times, cumulative_time, energy_used_per_segment

def calculate_battery_states(energy_used_per_segment):
    """Simulates the physical charge controller with a hard 100% ceiling."""
    battery_levels = np.zeros(num_segments)
    current_joules = MAX_JOULES
    
    for i in range(num_segments):
        current_joules -= energy_used_per_segment[i]
        
        # The Hardware Ceiling: Burn off excess solar energy
        if current_joules > MAX_JOULES:
            current_joules = MAX_JOULES
            
        battery_levels[i] = current_joules
        
    return battery_levels

# ==========================================
# 4. OPTIMIZER FUNCTIONS (SCALED)
# ==========================================
def objective_function(velocities):
    """THE RACING GOAL: Minimize Total Race Time (scaled to hours)"""
    times, _, _ = calculate_physics(velocities)
    return np.sum(times) / 100.0

def battery_constraint(velocities):
    """Guardrail 1: The battery must NEVER drop below 20% (MIN_JOULES)"""
    _, _, energy_used_per_segment = calculate_physics(velocities)
    battery_levels = calculate_battery_states(energy_used_per_segment)
    
    # Returns normalized ratio
    return (battery_levels - MIN_JOULES) / MAX_JOULES

def time_constraint(velocities):
    """Guardrail 2: Must arrive before 5:00 PM"""
    times, _, _ = calculate_physics(velocities)
    total_time = np.sum(times)
    return (MAX_DURATION - total_time) / MAX_DURATION

# ==========================================
# 5. EXECUTE OPTIMIZATION
# ==========================================
if __name__ == "__main__":
    print("\nPreparing Optimizer...")
    
    # Initial Guess: 60 km/h
    initial_guess = np.full(num_segments, 90.0 / 3.6)
    
    # Bounds: 1.0 m/s minimum to prevent crashes, up to 100 km/h
    bounds = [(1.0, 100.0 / 3.6) for _ in range(num_segments)]
    
    # Finish line stop (give the solver slight breathing room)
    bounds[-1] = (1.0, 2.0) 
    
    cons = [
        {'type': 'ineq', 'fun': battery_constraint},
        {'type': 'ineq', 'fun': time_constraint}
    ]
    
    print("\nLaunching Time-Minimizing SLSQP Optimizer...")
    start_time = time.time()
    
    result = minimize(
        objective_function, 
        initial_guess, 
        method='SLSQP', 
        bounds=bounds, 
        constraints=cons,
        options={'disp': True, 'maxiter': 500, 'ftol': 1e-4} 
    )
    
    execution_time = (time.time() - start_time) / 60.0
    print(f"\nOptimizer finished in {execution_time:.2f} minutes.")
    
    if result.success:
        print("SUCCESS! Optimal route found.")
        optimal_velocities = result.x
        
        times, _, energy_array = calculate_physics(optimal_velocities)
        final_time_hrs = np.sum(times) / 3600.0
        
        # Calculate final stats using the strict charge controller
        realistic_battery_levels = calculate_battery_states(energy_array)
        final_energy_joules = realistic_battery_levels[-1]
        final_soc = (final_energy_joules / MAX_JOULES) * 100
        
        print("\n--- FINAL STRATEGY STATS ---")
        print(f"Total Trip Time:  {final_time_hrs:.2f} hours")
        print(f"Arrival Time:     {8 + final_time_hrs:.2f} (Decimal hours)")
        print(f"Ending Battery:   {final_soc:.1f}% SOC")
        
        route_df['optimal_velocity_mps'] = optimal_velocities
        route_df['optimal_velocity_kmh'] = optimal_velocities * 3.6
        route_df['expected_soc_percentage'] = (realistic_battery_levels / MAX_JOULES) * 100
        
        route_df.to_csv("optimal_race_strategy.csv", index=False)
        print("Strategy saved to 'optimal_race_strategy.csv'.")
    else:
        print("FAILED: The optimizer could not find a solution.")
        print(f"Reason: {result.message}")