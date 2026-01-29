import pandas as pd
import numpy as np
from typing import Dict, Tuple, List


def preprocessing_data(
    all_match_tracking_data: Dict[str, Dict[str, pd.DataFrame]], sequence_np_path: str, 
    all_match_annotation_data: Dict[str, Dict[str, pd.DataFrame]] = None, label_np_path: str = None, 
    time_np_path: str = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generates temporal sequences, ground truth labels, and center timestamps from tracking and annotation data for model training and inference.

    Args:
        all_match_tracking_data (Dict[str, Dict[str, pd.DataFrame]]): Nested dictionary containing tracking DataFrames keyed by match_id and segment_id.
        sequence_np_path (str): File path to save the generated sequence NumPy array.
        all_match_annotation_data (Dict[str, Dict[str, pd.DataFrame]], optional): Nested dictionary containing annotation DataFrames keyed by match_id and segment_id. Required for training mode.
        label_np_path (str, optional): File path to save the generated label NumPy array. Required for training mode.
        time_np_path (str, optional): File path to save the generated timestamp NumPy array.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: A tuple containing:
            - sequence_np (np.ndarray): The feature sequences of shape (N, SEQ_LEN, TRACKING_CHANNELS).
            - label_np (np.ndarray): The target labels of shape (N, LABEL_CHANNELS) (empty if no labels provided).
            - time_np (np.ndarray): The center match time for each sequence in milliseconds.
    """

    TRACKING_FPS = 25
    SAMPLING_FPS = 5
    SEQUENCE_SECONDS = 20

    SEQ_LEN = int(SEQUENCE_SECONDS * SAMPLING_FPS)
    STEP_MS = int(1000 / SAMPLING_FPS)
    PADDING_FRAMES = int(SEQUENCE_SECONDS / 2 * SAMPLING_FPS)

    TRACKING_CHANNELS = 46
    LABEL_CHANNELS = 18    

    all_sequences: List[np.ndarray] = []
    all_labels: List[np.ndarray] = []
    all_times: List[int] = []
    
    tracking_channel_cols = ['ball_x', 'ball_y']
    for side in ['left', 'right']:
        for i in range(1, 12):
            tracking_channel_cols.extend([f'{side}_{i}_x', f'{side}_{i}_y'])
            
    
    if label_np_path:
        label_cols = [f'Build up {i}' for i in range(1, 3)] + [f'Progression {i}' for i in range(1, 3)] + \
                    [f'Final third {i}' for i in range(1, 3)] + [f'Counter-attack {i}' for i in range(1, 3)] + \
                    [f'High press {i}' for i in range(1, 3)] + [f'Mid block {i}' for i in range(1, 3)] + [f'Low block {i}' for i in range(1, 3)] + \
                    [f'Counter-press {i}' for i in range(1, 3)] + [f'Recovery {i}' for i in range(1, 3)]
        
        for match_id, tracking_segments in all_match_tracking_data.items():
            annotation_segments = all_match_annotation_data.get(match_id, {})
            
            for segment_id, t_df in tracking_segments.items():
                a_df = annotation_segments.get(segment_id)
                if a_df is None or t_df.empty:
                    print(f"Skipping {match_id}/{segment_id}: Missing tracking or annotation data.")
                    continue

                required_cols = tracking_channel_cols + ['match_time']
                if not all(col in t_df.columns for col in required_cols):
                    print(f"Skipping {segment_id}: Missing required tracking columns.")
                    continue

                t_df['time_mod'] = t_df['match_time'] % STEP_MS
                sampled_df = t_df[t_df['time_mod'] < 10].reset_index(drop=True)
                if sampled_df.empty:
                    continue

                for i in range(len(sampled_df)):
                    current_match_time = sampled_df.loc[i, 'match_time']

                    start_index = i - PADDING_FRAMES
                    end_index = i + PADDING_FRAMES + 1

                    sequence_data = sampled_df.iloc[max(0, start_index) : min(len(sampled_df), end_index)][tracking_channel_cols].values
                    
                    sequence_tensor = np.zeros((SEQ_LEN, TRACKING_CHANNELS), dtype=np.float32)
                    pad_past = -start_index if start_index < 0 else 0 
                    pad_future = end_index - len(sampled_df) if end_index > len(sampled_df) else 0
                    
                    embed_start = pad_past
                    embed_len = SEQ_LEN - pad_past - pad_future
                    
                    if embed_len > 0:
                        sequence_tensor[embed_start : embed_start + embed_len] = sequence_data[:embed_len]
                    
                    if np.isnan(sequence_tensor).any():
                        continue

                    target_match_time = round(current_match_time / 40) * 40
                    label_row = a_df[a_df['match_time'] == target_match_time][label_cols]
                    
                    if not label_row.empty:
                        label_vector = label_row.iloc[0].values.astype(np.float32)
                    else:
                        continue

                    all_sequences.append(sequence_tensor)
                    all_labels.append(label_vector)
                    all_times.append(current_match_time)

        sequence_np = np.stack(all_sequences) if all_sequences else np.empty((0, SEQ_LEN, TRACKING_CHANNELS))
        label_np = np.stack(all_labels) if all_labels else np.empty((0, LABEL_CHANNELS))
        time_np = np.array(all_times) if all_times else np.empty((0,))

        print(f"\n--- Preprocessing Summary ---")
        print(f"Total samples: {len(all_times)}")
        print(f"sequence_np shape: {sequence_np.shape}")
        print(f"label_np shape: {label_np.shape}")
        print(f"time_np shape: {time_np.shape}")
        
        if time_np_path:
            np.save(time_np_path, time_np)

        print("--- Data Processing Complete ---")
        print(f"✅ Time data was successfully saved to: {time_np_path}")

        return sequence_np, label_np, time_np
    
    else:
        for match_id, tracking_segments in all_match_tracking_data.items():

            # 1. Loop per in-play sequence (inplay_num)
            for inplay_val, group in tracking_segments.groupby('inplay_num'):
                sampled_inplay_df = group[group['match_time'] % STEP_MS == 0].reset_index(drop=True)
                
                if len(sampled_inplay_df) < SEQ_LEN:
                    continue

                # 2. Slide the center timestamp
                for i in range(len(sampled_inplay_df)):
                    
                    current_match_time = sampled_inplay_df.loc[i, 'match_time']

                    # 3. Extract 20-second window (10 frames before/after center)
                    start_idx = i - PADDING_FRAMES
                    end_idx = i + PADDING_FRAMES
                    
                    sequence_data = sampled_inplay_df.iloc[start_idx : end_idx][tracking_channel_cols].values
                    
                    if sequence_data.shape[0] != SEQ_LEN:
                        continue
                    
                    if np.isnan(sequence_data).any():
                        continue

                    all_sequences.append(sequence_data.astype(np.float32))
                    all_times.append(current_match_time)

        sequence_np = np.stack(all_sequences) if all_sequences else np.empty((0, SEQ_LEN, TRACKING_CHANNELS))
        time_np = np.array(all_times) if all_times else np.empty((0,))

        np.save(sequence_np_path, sequence_np)
        np.save(time_np_path, time_np)

        print(f"Total samples generated: {len(all_times)}")
        print(f"sequence_np shape: {sequence_np.shape}")
        
        return sequence_np, time_np