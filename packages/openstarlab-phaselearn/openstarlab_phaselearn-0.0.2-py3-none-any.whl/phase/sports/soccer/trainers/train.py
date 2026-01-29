import time
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Any, Dict, Tuple, Union
import warnings
import torchprofile

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

def get_flops(model: torch.nn.Module, dataloader: torch.utils.data.DataLoader, model_name: str, device: str = 'cpu') -> int:
    """
    Retrieves the first batch from the DataLoader and calculates the model's FLOPs (MACs * 2).

    Uses torchprofile to perform a symbolic trace of the model given a specific input 
    format determined by the model_name.

    Args:
        model (torch.nn.Module): The PyTorch model to analyze.
        dataloader (torch.utils.data.DataLoader): DataLoader to provide the input sample format.
        model_name (str): The type of model ('transformer', 'baller2vec', etc.).
        device (str): Device to place the sample tensors on. Defaults to 'cpu'.
        
    Returns:
        int: The calculated Floating Point Operations (FLOPs). Returns 0 if calculation fails.
    """

    warnings.filterwarnings("ignore")
    
    model.to(device)
    model.eval()
    
    try:
        tensors = next(iter(dataloader))
    except StopIteration:
        print("Warning: DataLoader is empty. Cannot calculate FLOPs.")
        return 0

    model_inputs = None

    if model_name in ['transformer']:
        inputs, _ = tensors
        model_inputs = inputs.to(device)
        profile_args = (model_inputs,)

    elif model_name in ['baller2vec']:
        model_inputs = {k: v.to(device) for k, v in tensors.items()}
        profile_args = ({k: v for k, v in model_inputs.items() if k != 'events'},)

    elif model_name in ['gcn_transformer', 'gat_transformer']:
        x_seq, _, edge_index = tensors
        x_seq, edge_index = x_seq.to(device), edge_index.to(device)
        profile_args = (x_seq, edge_index)

    else:
        raise ValueError(f"Unknown model name: {model_name} for FLOPs calculation.")

    macs = torchprofile.profile_macs(model, profile_args)
    
    flops = macs * 2
    
    return int(flops)


def train(train_loader, valid_loader, model, config):
    """
    Executes the training and validation loop for soccer phase models.

    The function handles optimization, loss calculation, early stopping, and 
    logging. It supports multiple architectures through the extract_data_and_predict utility.

    Args:
        train_loader (DataLoader): DataLoader for the training set.
        valid_loader (DataLoader): DataLoader for the validation set.
        model (nn.Module): The PyTorch model to be trained.
        config (Dict[str, Any]): Configuration dictionary containing 'model' and 'training' parameters.

    Returns:
        Tuple[Dict[str, torch.Tensor], int, List[float], List[float], Dict[str, Any]]:
            - best_model_state_dict (Dict): The state dictionary of the model from the best validation epoch.
            - best_epoch (int): The index of the best epoch.
            - train_losses (List[float]): List of average training losses per epoch.
            - valid_losses (List[float]): List of average validation losses per epoch.
            - model_stats (Dict[str, Any]): Dictionary containing 'flops' and 'num_params'.
    """

    model_name = config['model']['name']
    num_epochs = config['training']['num_epochs']
    lr = config['training']['lr']
    patience = config['training']['patience']
    device = config['training']['device']

    train_losses = []
    valid_losses = []
    
    best_model_state_dict = None
    best_epoch = 0
    
    final_epoch = 0
    final_model_state_dict = model.state_dict()

    model = model.to(device)

    train_params = [params for params in model.parameters()]

    optimizer = optim.Adam(train_params, lr=lr)
    criterion = nn.HuberLoss().to(device)

    best_train_loss = float("inf")
    best_valid_loss = float("inf")
    test_loss_best_valid = float("inf")
    current_train_loss = None
    no_improvement = 0

    # ---------------------------------------------
    # Start Training Loop
    # ---------------------------------------------
    for epoch in range(num_epochs):
        print(f"\nepoch: {epoch}", flush=True)

        # ---------------------------------------------
        # 1. Validation Phase
        # ---------------------------------------------
        model.eval()
        current_valid_loss = 0.0
        n_valid = 0
        with torch.no_grad():
            for valid_tensors in valid_loader:
                
                preds, labels, _ = extract_data_and_predict(valid_tensors, model, device, model_name)
                
                loss = criterion(preds, labels)
                current_valid_loss += loss.item()
                n_valid += 1
            
            print(torch.cat((preds[:1], preds[-1:]), dim=0), flush=True)
            print(torch.cat((labels[:1], labels[-1:]), dim=0), flush=True)

        current_valid_loss /= n_valid
        valid_losses.append(current_valid_loss)

        # ---------------------------------------------
        # 2. Early Stopping and Model Saving
        # ---------------------------------------------
        if current_valid_loss < best_valid_loss:
            best_valid_loss = current_valid_loss
            best_epoch = epoch
            no_improvement = 0

            best_model_state_dict = model.state_dict()
            
        else:
            no_improvement += 1
            print(f" ⚠️ No improvement for {no_improvement} epoch(s).")

            if no_improvement >= patience:
                print(f"\n⏹ Early stopping triggered after {patience} epochs with no improvement.")
                final_epoch = best_epoch
                break

        # ---------------------------------------------
        # 3. Training Phase
        # ---------------------------------------------
        model.train()
        current_train_loss = 0.0
        n_train = 0
        start_time = time.time()
        
        for train_tensors in train_loader:
            
            optimizer.zero_grad()
            
            preds, labels, _ = extract_data_and_predict(train_tensors, model, device, model_name)
            
            loss = criterion(preds, labels)
            
            loss.backward()
            
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0) 
            
            optimizer.step()
            current_train_loss += loss.item()
            n_train += 1
        
        current_train_loss /= n_train
        train_losses.append(current_train_loss)

        if current_train_loss < best_train_loss:
            best_train_loss = current_train_loss

        epoch_time = time.time() - start_time

        # ---------------------------------------------
        # 4. Logging Output
        # ---------------------------------------------
        print(f"total_train_loss: {current_train_loss}")
        print(f"best_train_loss: {best_train_loss}")
        print(f"total_valid_loss: {current_valid_loss}")
        print(f"best_valid_loss: {best_valid_loss}")
        if model_name in ['transformer', 'gcn_transformer', 'gat_transformer']:
            print(f"test_loss_best_valid: {test_loss_best_valid}")
        print(f"epoch_time: {epoch_time:.2f}", flush=True)
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {current_train_loss:.4f}")

    # ---------------------------------------------
    # 5. Prepare Final Return Values
    # ---------------------------------------------
    if best_model_state_dict is None:
        best_model_state_dict = final_model_state_dict

    flops = get_flops(model, train_loader, model_name, device='cpu')
    
    num_params = sum(p.numel() for p in best_model_state_dict.values())

    model_stats = {"flops": flops, "num_params": num_params}
    print(f"\n--- Training Summary ---")
    print(f"Best epoch: {best_epoch + 1} | Best validation loss: {best_valid_loss:.4f} | Corresponding training loss: {train_losses[best_epoch]:.4f}")
    print(f"FLOPs: {flops} | Number of parameters: {num_params}")

    return best_model_state_dict, best_epoch, train_losses, valid_losses, model_stats