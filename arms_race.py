import pandas as pd

PANEL_EFFICIENCY = 0.21
PANEL_AREA = 4.6

def get_highest_yield_segment(target_ids: list, telemetry_logs: list) -> int | None:
   
    df = pd.DataFrame(telemetry_logs, columns=['segment_id', 'param1', 'param2']) # impoting data from lists into pandas
    
    df_filtered = df[df['segment_id'].isin(target_ids)].drop_duplicates(subset=['segment_id'], keep='last') # removes duplicated data
    
    if df_filtered.empty:
        return None
    
    # calculation of energy by using vectorisation 
    df_filtered['energy'] = (
        df_filtered['param1'] * df_filtered['param2'] * PANEL_EFFICIENCY * PANEL_AREA   
    )
    
    best_index = df_filtered['energy'].idxmax() # finds the maximum value of energy
    
    return df_filtered.loc[best_index, 'segment_id']

if __name__ == "__main__":
    # The segment IDs we actually care about evaluating
    target_segments = [101, 103, 105]

    # Raw telemetry logs format: [segment_id, param1 (e.g., irradiance), param2]
    mock_telemetry_data = [
        [100, 850.0, 2.5],  # Ignored: Not in target_segments
        [101, 900.0, 3.2],  # Evaluated: Yield is ~2782.08
        [102, 1050.0, 1.8], # Ignored: Not in target_segments
        [103, 1100.0, 4.0], # Evaluated: Yield is ~4250.40 (This should be the winner)
        [104, 700.0, 5.0],  # Ignored: Not in target_segments
        [105, 950.0, 2.1],  # Evaluated: Yield is ~1927.59
        [101, 800.0, 3.0],  # Duplicate 101: The code keeps this last occurrence instead of the first
    ]

    # Run the function
    best_segment = get_highest_yield_segment(target_segments, mock_telemetry_data)
    
    print("-" * 40)
    print(f"Target Segments: {target_segments}")
    print(f"Winning Segment ID: {best_segment}")
    print("-" * 40)