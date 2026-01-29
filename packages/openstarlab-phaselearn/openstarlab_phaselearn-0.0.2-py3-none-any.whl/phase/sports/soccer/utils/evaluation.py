import numpy as np
import pandas as pd
from collections import defaultdict
from sklearn.metrics import precision_recall_curve

play_phase_name_list = ['Build up 1', 'Progression 1', 'Final third 1', 'Counter-attack 1', 'High press 1', 'Mid block 1', 'Low block 1', 'Counter-press 1', 'Recovery 1',
                                'Build up 2', 'Progression 2', 'Final third 2', 'Counter-attack 2', 'High press 2', 'Mid block 2', 'Low block 2', 'Counter-press 2', 'Recovery 2']

def quantitative_test(outputs_np, labels_np, team_mode='1team_mode'):
    """Performs a comprehensive quantitative evaluation of tactical action predictions.
    
    This function evaluates model performance across three dimensions: 
    1. Regression (MAE, MSE, RMSE).
    2. Ranking (Top-K accuracy within teams).
    3. Classification (F1-score, Precision, Recall) using optimized thresholds.

    Args:
        outputs_np (np.ndarray): Predicted probabilities or values from the model.
        labels_np (np.ndarray): Ground truth labels.
        team_mode (str, optional): Team mode. Defaults to '1team_mode'.

    Returns:
        tuple: A tuple containing three pandas DataFrames:
            - regression_df: Regression metrics per tactical action.
            - top_k_df: Ranking metrics (Top-1, 2, 3 ratios) per tactical action.
            - classification_df: Binary classification metrics with optimized thresholds.
    """
    num_tactics = 9
    unique_play_phase_names = [name.rsplit(" ", 1)[0] for name in play_phase_name_list]

    if team_mode=='1team_mode':
        num_teams = 1
        unique_play_phase_names = unique_play_phase_names[:num_tactics]
    else:
        num_teams = 2

    # --- Regression Evaluation ---
    abs_errors = np.abs(outputs_np - labels_np)
    squared_errors = (outputs_np - labels_np) ** 2
    mae = np.mean(abs_errors, axis=0)
    mse = np.mean(squared_errors, axis=0)
    rmse = np.sqrt(mse)

    overall_mae, overall_mse, overall_rmse = np.mean(mae), np.mean(mse), np.mean(rmse)

    regression_df = pd.DataFrame({
        "Tactical Action": unique_play_phase_names + ["Overall"],
        "MAE": np.append(mae, overall_mae),
        "MSE": np.append(mse, overall_mse),
        "RMSE": np.append(rmse, overall_rmse)
    })

    # --- Intra-team Ranking Analysis ---
    num_actions_per_team = num_tactics

    total_count = np.zeros(num_tactics*num_teams)
    top1_count = np.zeros(num_tactics*num_teams)
    top2_count = np.zeros(num_tactics*num_teams)
    top3_count = np.zeros(num_tactics*num_teams)

    for i in range(labels_np.shape[0]):
        label_indices = np.where(labels_np[i] >= 0.75)[0]

        if len(label_indices) == 0:
            continue

        for team_id in range(num_teams):
            start_idx = team_id * num_actions_per_team
            end_idx = (team_id + 1) * num_actions_per_team
            team_pred_ranking = np.argsort(outputs_np[i, start_idx:end_idx])[::-1] + start_idx

            for label_idx in label_indices:
                if start_idx <= label_idx < end_idx:
                    total_count[label_idx] += 1
                    if label_idx == team_pred_ranking[0]:
                        top1_count[label_idx] += 1
                    if label_idx in team_pred_ranking[:2]:
                        top2_count[label_idx] += 1
                    if label_idx in team_pred_ranking[:3]:
                        top3_count[label_idx] += 1

    aggregated_data = defaultdict(lambda: {"Total Count (1.0)": 0, "Top-1 Count": 0, "Top-2 Count": 0, "Top-3 Count": 0})

    for idx, action in enumerate(play_phase_name_list[:num_tactics*num_teams]):
        base_action = action.rsplit(" ", 1)[0]
        
        aggregated_data[base_action]["Total Count (1.0)"] += total_count[idx]
        aggregated_data[base_action]["Top-1 Count"] += top1_count[idx]
        aggregated_data[base_action]["Top-2 Count"] += top2_count[idx]
        aggregated_data[base_action]["Top-3 Count"] += top3_count[idx]

    final_data = []
    for action, values in aggregated_data.items():
        total = values["Total Count (1.0)"]
        final_data.append({
            "Tactical Action": action,
            "Total Count (1.0)": total,
            "Top-1 Count": values["Top-1 Count"],
            "Top-1 Ratio": values["Top-1 Count"] / max(total, 1),
            "Top-2 Count": values["Top-2 Count"],
            "Top-2 Ratio": values["Top-2 Count"] / max(total, 1),
            "Top-3 Count": values["Top-3 Count"],
            "Top-3 Ratio": values["Top-3 Count"] / max(total, 1),
        })

    top_k_df = pd.DataFrame(final_data)

    overall_top_k_df = pd.DataFrame({
        "Tactical Action": ["Overall"],
        "Total Count (1.0)": [np.sum(top_k_df["Total Count (1.0)"])],
        "Top-1 Count": [np.sum(top_k_df["Top-1 Count"])],
        "Top-1 Ratio": [np.mean(top_k_df["Top-1 Ratio"])],
        "Top-2 Count": [np.sum(top_k_df["Top-2 Count"])],
        "Top-2 Ratio": [np.mean(top_k_df["Top-2 Ratio"])],
        "Top-3 Count": [np.sum(top_k_df["Top-3 Count"])],
        "Top-3 Ratio": [np.mean(top_k_df["Top-3 Ratio"])],
    })

    top_k_df = pd.concat([top_k_df, overall_top_k_df], ignore_index=True)

    # --- Binary Classification Evaluation ---
    binarized_labels = (labels_np >= 0.75).astype(int)
    best_thresholds, _ = optimize_threshold(outputs_np, binarized_labels)
    binarized_outputs = (outputs_np >= best_thresholds).astype(int)

    from sklearn.metrics import accuracy_score, recall_score, precision_score, f1_score
    accuracy = np.mean(binarized_labels == binarized_outputs, axis=0)
    recall = recall_score(binarized_labels, binarized_outputs, average=None, zero_division=0)
    precision = precision_score(binarized_labels, binarized_outputs, average=None, zero_division=0)
    f1 = f1_score(binarized_labels, binarized_outputs, average=None, zero_division=0)

    classification_df = pd.DataFrame({
        "Tactical Action": unique_play_phase_names + ["Overall"],
        "Threshold": np.append(best_thresholds, np.mean(best_thresholds)),
        "Accuracy": np.append(accuracy, accuracy_score(binarized_labels.flatten(), binarized_outputs.flatten())),
        "Recall": np.append(recall, recall_score(binarized_labels, binarized_outputs, average="macro", zero_division=0)),
        "Precision": np.append(precision, precision_score(binarized_labels, binarized_outputs, average="macro", zero_division=0)),
        "F1-score": np.append(f1, f1_score(binarized_labels, binarized_outputs, average="macro", zero_division=0))
    })
    
    return regression_df, top_k_df, classification_df


def optimize_threshold(outputs_np, labels_np):
    """Optimizes the decision threshold for each tactical action based on F1-score.
    
    Iterates through each class and finds the probability threshold that maximizes 
        the harmonic mean of precision and recall.

    Args:
        outputs_np (np.ndarray): Model output probabilities.
        labels_np (np.ndarray): Binarized ground truth labels.

    Returns:
        tuple: A tuple containing:
            - best_thresholds (np.ndarray): Optimized threshold for each action class.
            - best_f1_scores (np.ndarray): The corresponding maximum F1-score for each class.
    """
    thresholds = np.linspace(0, 1, 100)
    best_thresholds = []
    best_f1_scores = []
    
    for i in range(labels_np.shape[1]):
        precision, recall, thresh = precision_recall_curve(labels_np[:, i], outputs_np[:, i])
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
        best_idx = np.nanargmax(f1_scores)  # NaN回避
        best_thresholds.append(thresh[best_idx] if best_idx < len(thresh) else 0.5)
        best_f1_scores.append(f1_scores[best_idx])
    
    return np.array(best_thresholds), np.array(best_f1_scores)


def generate_sequence_result(time_np, outputs_np, labels_np, inference_type, team_mode='1team_mode'):
    """Combines time, predictions, and labels into a single DataFrame for analysis.

    Used for qualitative inspection of sequences, either during post-training 
    analysis or real-time (live) prediction.

    Args:
        time_np (np.ndarray): Array of match timestamps.
        outputs_np (np.ndarray): Predicted tactical phase probabilities.
        labels_np (np.ndarray): Ground truth labels (used in qualitative analysis).
        inference_type (str): Type of task ('qualitative_analysis' or 'live_prediction').

    Returns:
        pd.DataFrame: A concatenated DataFrame containing time and prediction results.
    """
    num_tactics=9
    if team_mode == '1team_mode':
        num_teams=1
    else:
        num_teams=2

    output_df = pd.DataFrame(outputs_np[:, :num_tactics*num_teams], columns=play_phase_name_list[:num_tactics*num_teams])
    time_df = pd.DataFrame(time_np, columns=['time'])
    if inference_type == 'qualitative_analysis':
        label_df = pd.DataFrame(labels_np[:, :num_tactics*num_teams], columns=play_phase_name_list[:num_tactics*num_teams])
        return pd.concat([time_df, label_df, output_df], axis=1)
    elif inference_type == 'live_prediction':
        return pd.concat([time_df, output_df], axis=1)