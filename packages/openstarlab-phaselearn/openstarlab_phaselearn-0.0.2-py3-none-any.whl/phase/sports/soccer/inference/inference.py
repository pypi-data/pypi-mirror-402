import time
import torch
import torch.nn as nn
from typing import Any, Dict, Tuple, Union

def extract_data_and_predict(tensors: Union[Dict[str, Any], Tuple], model: nn.Module, device: str, model_name: str) -> Tuple[torch.Tensor, torch.Tensor, Union[torch.Tensor, None]]:
    """
    Extracts data from the DataLoader, feeds it into the model, and retrieves predictions and labels.

    This utility abstracts the differences in data structures across different model types 
    (Transformer, Baller2Vec, and GNNs) to provide a unified interface for training and evaluation.

    Args:
        tensors (Union[Dict[str, Any], Tuple]): The batch data returned by the DataLoader. 
            Can be a tuple of (inputs, labels) or a dictionary of tensors.
        model (nn.Module): The PyTorch model to perform inference.
        device (str): The device (cpu or cuda) to move tensors to.
        model_name (str): The architecture name ('transformer', 'baller2vec', 'gcn_transformer', or 'gat_transformer').

    Returns:
        Tuple[torch.Tensor, torch.Tensor, Union[torch.Tensor, None]]: 
            - preds (torch.Tensor): Model predictions with shape (B, C).
            - labels (torch.Tensor): Ground truth labels with shape (B, C).
            - edge_index (torch.Tensor | None): The edge index tensor for GNN-based models; otherwise None.
    """
    edge_index = None

    if model_name in ['transformer']:
        inputs, labels = tensors
        inputs, labels = inputs.to(device), labels.to(device)
        labels = labels.float() 
        preds = model(inputs)
    
    elif model_name in ['baller2vec']:
        tensors = {k: v.to(device) for k, v in tensors.items()}
        labels = tensors["events"]
        preds = model(tensors)["seq_label"]
    
    elif model_name in ['gcn_transformer', 'gat_transformer']:
        x_seq, labels, edge_index = tensors
        x_seq, labels, edge_index = x_seq.to(device), labels.to(device), edge_index.to(device)
        preds = model(x_seq, edge_index)
    
    else:
        raise ValueError(f"Unknown model name: {model_name}")

    return preds, labels, edge_index


def inference(inference_loader, model, model_config):
    """
    Executes model inference and collects predictions and ground truth labels.

    This function performs a full pass over the provided data loader in evaluation mode. 
    It focuses solely on generating outputs and does not include training-related 
    logic such as loss calculation, backpropagation, or optimization.

    Args:
        inference_loader (torch.utils.data.DataLoader): The DataLoader containing the 
            dataset to be evaluated.
        model (torch.nn.Module): The PyTorch model to use for inference.
        model_config (dict): Configuration dictionary containing model metadata. 
            Expected keys include:
            - 'model_name' (str): The name/type of the model architecture.
            - 'device' (str, optional): The device to run inference on (e.g., 'cuda:0', 'cpu'). 
                Defaults to 'cuda:0'.

    Returns:
        tuple: A tuple containing:
            - final_preds (numpy.ndarray): Concatenated array of all model predictions.
            - final_labels (numpy.ndarray): Concatenated array of all corresponding 
                ground truth labels.
    """
    model_name = model_config['model_name']
    device = model_config.get('device', 'cuda:0')

    model = model.to(device)
    model.eval()

    all_preds = []
    all_labels = []
    
    start_time = time.time()
    
    print(f"--- Starting Inference ({model_name}) ---", flush=True)

    with torch.no_grad():
        for i, batch_tensors in enumerate(inference_loader):
            
            preds, labels, _ = extract_data_and_predict(batch_tensors, model, device, model_name)
            
            all_preds.append(preds.cpu())
            all_labels.append(labels.cpu())

            if i % 10 == 0:
                print(f"Batch {i} processed...", end='\r')

    final_preds = torch.cat(all_preds, dim=0).numpy()
    final_labels = torch.cat(all_labels, dim=0).numpy()

    inference_time = time.time() - start_time

    print(f"\n--- Inference Summary ---")
    print(f"Total samples: {len(final_preds)}")
    print(f"Inference time: {inference_time:.2f}s")

    return final_preds, final_labels