import pandas as pd
import re
import os
from typing import Dict, Tuple

def load_train_data() -> Tuple[Dict[str, Dict[str, pd.DataFrame]], Dict[str, Dict[str, pd.DataFrame]]]:
    """
    Loads and aggregates tracking and annotation data for all predefined match IDs into single dictionaries.

    Args:
        None

    Returns:
        Tuple[Dict, Dict]: A tuple containing (all_tracking_data, all_annotation_data).
            Structure: {match_id: {segment_id: filtered_df, ...}, ...}
    """
    match_ids = [117092, 117093, 118575, 118576, 118577, 118578, 128057, 128058, 132831, 132877]
    
    all_match_tracking_data: Dict[str, Dict[str, pd.DataFrame]] = {}
    all_match_annotation_data: Dict[str, Dict[str, pd.DataFrame]] = {}

    for match_id in match_ids:
        match_id_str = str(match_id)
        phase_data_path = f'./data/phase_data/bepro/{match_id_str}/{match_id_str}_main_data.csv'
        phase_annotation_data_dir = f'./data/phase_annotation_data/{match_id_str}'
        tracking_segments, annotation_segments = get_train_data(phase_data_path, phase_annotation_data_dir)
        all_match_tracking_data[match_id_str] = tracking_segments
        all_match_annotation_data[match_id_str] = annotation_segments
        
    return all_match_tracking_data, all_match_annotation_data

def get_train_data(tracking_csv_path: str, annotation_file_dir: str) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """
    Segments tracking data based on time ranges extracted from annotation filenames within a directory.

    Args:
        tracking_csv_path (str): Path to the main tracking data CSV file.
        annotation_file_dir (str): Directory containing segment-specific annotation CSV files.

    Returns:
        Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]: 
            A tuple of (tracking_segment_dict, annotation_segment_dict) keyed by segment ID.
    """
    segment_data: Dict[str, Tuple[str, int, int]] = {}
    
    if not os.path.exists(annotation_file_dir):
        print(f"Annotation directory not found: {annotation_file_dir}")
        return {},{}
    try:
        file_names = [f for f in os.listdir(annotation_file_dir) if f.endswith('.csv')]
    except FileNotFoundError:
        print(f"Error reading directory: {annotation_file_dir}")
        return {},{}

    for file_name_with_ext in file_names:
        file_name_without_ext = os.path.splitext(file_name_with_ext)[0]
        segment_id = file_name_without_ext.removesuffix('_annotation')

        if segment_id == '117093_09_22-10_07' or segment_id == '128058_03_51-05_07':
            continue
        
        game_id, start_sec, end_sec = parse_time_range(segment_id)
        
        if start_sec is not None and end_sec is not None:
            segment_data[segment_id] = (game_id, start_sec * 1000, end_sec * 1000, file_name_with_ext)
    
    
    if not os.path.exists(tracking_csv_path):
        print(f"Tracking data file not found: {tracking_csv_path}")
        return {},{}
    try:
        tracking_data = pd.read_csv(tracking_csv_path)
    except Exception as e:
        print(f"Error reading tracking CSV {tracking_csv_path}: {e}")
        return {},{}
    
    filtered_tracking_segments: Dict[str, pd.DataFrame] = {}
    annotation_segments: Dict[str, pd.DataFrame] = {}

    for segment_id, (game_id, start_time_ms, end_time_ms, annotation_filename) in segment_data.items():
        
        filtered_df = tracking_data[
            (tracking_data["match_time"] >= start_time_ms) &
            (tracking_data["match_time"] <= end_time_ms)
        ].copy()

        if not filtered_df.empty:
            filtered_tracking_segments[segment_id] = filtered_df
            
            annotation_path = os.path.join(annotation_file_dir, annotation_filename)
            try:
                annotation_df = pd.read_csv(annotation_path)
                annotation_segments[segment_id] = annotation_df.copy()
                print(f"Extracted segment: {segment_id} (Tracking: {len(filtered_df)} rows, Annotation: {len(annotation_df)} rows)")
            except Exception as e:
                print(f"Warning: Failed to read annotation file {annotation_filename}: {e}")
        else:
            print(f"Warning: Segment {segment_id} yielded no tracking data. Skipping segment.")
            
    return filtered_tracking_segments, annotation_segments

def load_qualitative_analysis_data(phase_data_path, phase_annotation_data_path, match_id: str):
    """
    Prepares tracking and annotation data specifically for qualitative analysis of a single match.

    Args:
        phase_data_path (str): Path to the tracking data CSV.
        phase_annotation_data_path (str): Path to the specific annotation CSV file.
        match_id (str): Identifier for the match.

    Returns:
        Tuple[Dict, Dict]: Nested dictionaries for tracking and annotation data.
    """
    all_match_tracking_data: Dict[str, Dict[str, pd.DataFrame]] = {}
    all_match_annotation_data: Dict[str, Dict[str, pd.DataFrame]] = {}
    tracking_segments, annotation_segments = get_qualitative_analysis_data(phase_data_path, phase_annotation_data_path)
    all_match_tracking_data[match_id] = tracking_segments
    all_match_annotation_data[match_id] = annotation_segments
    return all_match_tracking_data, all_match_annotation_data

def get_qualitative_analysis_data(tracking_csv_path: str, annotation_file_path: str) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """
    Loads and filters a single segment of data for qualitative review based on a specific annotation file path.

    Args:
        tracking_csv_path (str): Path to the main tracking data CSV.
        annotation_file_path (str): Path to the annotation CSV file.

    Returns:
        Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]: Filtered tracking and annotation DataFrames in dictionaries.
    """
    if not os.path.exists(annotation_file_path):
        print(f"Annotation path not found: {annotation_file_path}")
        return {},{}
    annotation_file_name = os.path.splitext(annotation_file_path)[0]
    segment_id = annotation_file_name.removesuffix('_annotation')
    
    game_id, start_sec, end_sec = parse_time_range(segment_id)

    start_time_ms = start_sec * 1000
    end_time_ms = end_sec * 1000
    
    if not os.path.exists(tracking_csv_path):
        print(f"Tracking data file not found: {tracking_csv_path}")
        return {},{}
    try:
        tracking_data = pd.read_csv(tracking_csv_path)
    except Exception as e:
        print(f"Error reading tracking CSV {tracking_csv_path}: {e}")
        return {},{}
    
    filtered_tracking_segments: Dict[str, pd.DataFrame] = {}
    annotation_segments: Dict[str, pd.DataFrame] = {}
    
    filtered_df = tracking_data[
        (tracking_data["match_time"] >= start_time_ms) &
        (tracking_data["match_time"] <= end_time_ms)
    ].copy()

    if not filtered_df.empty:
        filtered_tracking_segments[segment_id] = filtered_df
        try:
            annotation_df = pd.read_csv(annotation_file_path)
            annotation_segments[segment_id] = annotation_df.copy()
            print(f"Extracted segment: {segment_id} (Tracking: {len(filtered_df)} rows, Annotation: {len(annotation_df)} rows)")
        except Exception as e:
            print(f"Warning: Failed to read annotation file {annotation_file_name}: {e}")
    else:
        print(f"Warning: Segment {segment_id} yielded no tracking data. Skipping segment.")
            
    return filtered_tracking_segments, annotation_segments

def load_live_prediction_data(phase_data_path, match_id: str):
    """
    Loads raw tracking data for live prediction without time-segment filtering.

    Args:
        phase_data_path (str): Path to the phase tracking data CSV.
        match_id (str): Identifier for the match.

    Returns:
        Dict[str, pd.DataFrame]: Dictionary containing the full match tracking DataFrame.
    """
    all_match_tracking_data: Dict[str, Dict[str, pd.DataFrame]] = {}
    tracking_data = pd.read_csv(phase_data_path)
    all_match_tracking_data[match_id] = tracking_data
    return all_match_tracking_data

def parse_time_range(filename):
    """
    Extracts the game ID, start time, and end time from a filename string using regex.

    Args:
        filename (str): The filename string (Expected format: GAMEID_MM_SS-MM_SS).

    Returns:
        Tuple[Union[str, None], Union[int, None], Union[int, None]]: 
            (game_id, start_total_seconds, end_total_seconds). Returns (None, None, None) if no match found.
    """
    regex = r"(\d+)_(\d{2})_(\d{2})-(\d{2})_(\d{2})"
    match = re.search(regex, filename)
    
    if match:
        game_id = match.group(1)
        start_min, start_sec, end_min, end_sec = map(int, match.groups()[1:])
        start_time = start_min * 60 + start_sec
        end_time = end_min * 60 + end_sec
        return game_id, start_time, end_time
    else:
        print(f"Warning: Filename format does not match required pattern: {filename}")
        return None, None, None