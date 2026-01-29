import numpy as np

def augmentation(sequence_np: np.ndarray, label_np: np.ndarray, mode: str):
    """
    Performs data augmentation by flipping spatial coordinates and swapping team data.
    
    This function creates an augmented version of the input sequence by inverting 
    coordinates and swapping the positions of Team 1 and Team 2. It also adjusts 
    the labels accordingly based on the specified mode.

    Args:
        sequence_np (np.ndarray): The input sequence data (e.g., tracking data).
                                  Expected shape: (samples, timesteps, features).
        label_np (np.ndarray): The corresponding labels for the sequence.
        mode (str): A string to determine the augmentation logic for labels 
                    (e.g., '1team' or '2team').

    Returns:
        tuple: (sequence_np, label_np)
            - sequence_np (np.ndarray): The concatenated original and augmented sequences.
            - label_np (np.ndarray): The concatenated original and augmented labels.
    """
    
    # --- Sequence Augmentation ---
    # Flip coordinates by multiplying by -1.0
    augmented_sequence_np = sequence_np.copy() * -1.0
    
    # Split the data into ball, team 1, and team 2
    # Ball: first 2 columns, Team 1: next 22 columns, Team 2: following 22 columns
    ball = augmented_sequence_np[:, :, :2]
    team1 = augmented_sequence_np[:, :, 2:24]   # 22 columns (11 players)
    team2 = augmented_sequence_np[:, :, 24:46]  # 22 columns (11 players)
    
    # Recombine by swapping the team positions
    augmented_sequence_np = np.concatenate([ball, team2, team1], axis=2)
    
    # Concatenate the original data with the augmented data along the batch axis
    sequence_np = np.concatenate([sequence_np, augmented_sequence_np], axis=0)

    # --- Label Augmentation ---
    if '1team' in mode:
        # Split labels into two halves and stack them vertically
        team1_label_np = label_np[:, :9]
        team2_label_np = label_np[:, 9:]
        label_np = np.concatenate([team1_label_np, team2_label_np], axis=0)

    elif '2team' in mode:
        # Create augmented labels by swapping the first 9 columns with the last 9 columns
        augmented_label_np = np.concatenate([label_np[:, 9:], label_np[:, :9]], axis=1)
        
        # Concatenate the original labels with the swapped labels along the batch axis
        label_np = np.concatenate([label_np, augmented_label_np], axis=0)

    print(f"  Augmented ({mode}): {sequence_np.shape}, {label_np.shape}")

    return sequence_np, label_np