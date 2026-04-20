import gymnasium as gym

def run_cartpole_pid():
    # 1. Initialize the environment with rendering enabled
    env = gym.make("CartPole-v1", render_mode="human")
    obs, info = env.reset()

    # 2. Define your PID Constants (Tuning Parameters)
    # Start with these values, then change them to answer the application questions
    Kp = 40.0   # Proportional gain
    Ki = 0.0    # Integral gain
    Kd = 10.0   # Derivative gain

    # Variables to track for the Integral term
    integral_error = 0.0
    
    # Run the simulation for 1000 time steps
    for step in range(1000):
        env.render()

        # 3. Extract the sensor data from the environment
        # obs array contains: [cart_position, cart_velocity, pole_angle, pole_angular_velocity]
        cart_pos, cart_vel, pole_angle, angular_vel = obs

        # 4. Calculate the PID terms
        # The target angle is 0 (straight up), so the error is just the pole_angle itself.
        error = pole_angle
        
        # Accumulate the error for the Integral term
        integral_error += error
        
        # Calculate the control output
        # Note: We use angular_vel directly as the derivative of the angle
        P = Kp * error
        I = Ki * integral_error
        D = Kd * angular_vel
        
        control_output = P + I + D

        # 5. Convert the continuous PID output to a discrete action (0: Left, 1: Right)
        # If the pole is falling right (positive angle), we push the cart right to catch it.
        if control_output > 0:
            action = 1
        else:
            action = 0

        # PRINT THE RESULTS TO YOUR TERMINAL
        print(f"Step: {step} | Angle: {pole_angle:.4f} | PID Output: {control_output:.2f} | Action: {'Right' if action == 1 else 'Left'}")
        # 6. Apply the action to the environment and step forward in time
        obs, reward, terminated, truncated, info = env.step(action)

        # If the pole falls too far, reset the environment
        if terminated or truncated:
            print(f">>> POLE FELL! Survived for {step} steps. Resetting...\n")
            obs, info = env.reset()
            integral_error = 0.0 # Reset the integral memory on failure

    env.close()

if __name__ == "__main__":
    run_cartpole_pid()