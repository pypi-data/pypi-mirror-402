import os
import json
import time
import numpy as np
import pandas as pd 
import torch
import torch.nn as nn

from ..dataloaders.data_module import TrainDataModule
from ..trainers.train import train
from ..inference.inference import inference

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-torch.log(torch.tensor(10000.0)) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.pe = pe.unsqueeze(0)
    
    def forward(self, x):
        return x + self.pe[:, :x.size(1)].to(x.device)

class TransformerClassification(nn.Module):
    def __init__(self, input_dim, hidden_dim, target_size, num_heads=4, num_layers=2):
        super(TransformerClassification, self).__init__()
        self.embedding = nn.Linear(input_dim, hidden_dim)
        self.pos_encoder = PositionalEncoding(hidden_dim)
        self.d_model = hidden_dim
        encoder_layers = nn.TransformerEncoderLayer(d_model=self.d_model, nhead=num_heads, dim_feedforward=4*self.d_model)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        self.fc = nn.Linear(hidden_dim, target_size)
        
    def forward(self, input_):
        x = self.embedding(input_)
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x)
        x = x[:, -1, :]
        scores = self.fc(x)
        return scores


def train_main(sequence_np, label_np, config):
    """
    Main training pipeline for the phase estimation model.
    
    This function initializes the model and data module, executes the training loop, 
    and saves the results (model weights, loss history, hyperparameters, and stats) 
    to a timestamped directory.

    Args:
        sequence_np (numpy.ndarray): Input feature sequences for training.
        label_np (numpy.ndarray): Target labels for the training sequences.
        config (dict): Configuration dictionary containing 'data', 'model', 
            and 'training' sub-dictionaries.

    Returns:
        None: The function saves output files to the local disk.
    """

    data_config = config['data']
    model_config = config['model']
    train_config = config['training']

    device = torch.device(train_config['device'] if torch.cuda.is_available() else 'cpu')
    print(device)
    
    if '1team' in data_config['mode']:
        target_size = model_config['target_size']['1team_mode']
    elif '2team' in data_config['mode']:
        target_size = model_config['target_size']['2team_mode']

    model = TransformerClassification(
        input_dim=(model_config['num_players'] + 1) * 2, 
        hidden_dim=model_config['hidden_dim'], 
        target_size=target_size, 
        num_heads=model_config['num_heads'], 
        num_layers=model_config['num_layers']
    ).to(device)

    batch_size = train_config['batch_size']

    data_module = TrainDataModule(
        sequence_np=sequence_np, 
        label_np=label_np, 
        batch_size=batch_size,
        model=model_config['name']
    )

    train_loader = data_module.train_dataloader()
    valid_loader = data_module.valid_dataloader()

    best_model_state_dict, best_epoch, train_losses, valid_losses, model_stats = train(train_loader, valid_loader, model, config)

    columns = ['train_loss', 'valid_loss']
    data = [train_losses, valid_losses]
    data = np.array(data).T
    loss_df = pd.DataFrame(data, columns=columns)
    loss_df = loss_df.round(4)

    i=1
    current_time = time.strftime("%Y%m%d_%H%M%S")
    save_path = data_config['save_dir']+f"/model/{model_config['name']}/{data_config['mode']}/{current_time}/run_{i}/"
    while os.path.exists(save_path):
        i+=1
        save_path = data_config['save_dir']+f"/model/{model_config['name']}/{data_config['mode']}/{current_time}/run_{i}/"
    os.makedirs(save_path)

    hyperparameters = {'current_time': current_time,
                        'train_sequence_np_path': data_config['train_sequence_np_path'], 'train_label_np_path': data_config['train_label_np_path'], 'save_dir': data_config['save_dir'],
                        'model_name': model_config['name'], 'train_mode':data_config['mode'], 'run':i, 'model_path': model_save_path,
                        
                        'input_dim': (model_config['num_players'] + 1) * 2, 'hidden_dim': model_config['hidden_dim'], 'target_size': target_size, 
                        'num_heads': model_config['num_heads'], 'num_layers': model_config['num_layers'], 
                        
                        'batch_size': train_config['batch_size'], 'num_epochs': train_config['num_epochs'], 'lr': train_config['lr'], 'patience': train_config['patience'], 
                        'device': train_config['device'], 'best_epoch':best_epoch}

    model_save_path = save_path + "best.pth"
    loss_save_path = save_path + "loss.csv"
    hyperparameters_save_path = save_path + "hyperparameters.json"
    model_stats_save_path = save_path + "model_stats.txt"

    torch.save(best_model_state_dict, model_save_path)
    loss_df.to_csv(loss_save_path, index=False)
    with open(hyperparameters_save_path, 'w') as f:
        json.dump(hyperparameters, f, indent=4)
    with open(model_stats_save_path, "w") as f:
        f.write(str(model_stats))
        
    print("Model and loss saved at", save_path)


def inference_main(sequence_np, label_np,  model_config, inference_type):
    """
    Main inference pipeline for the phase estimation model.
    
    Loads a trained model and performs inference on the provided dataset. It handles 
    both quantitative testing (using test splits) and other inference types 
    (qualitative or live prediction) by adjusting data loading strategies.

    Args:
        sequence_np (numpy.ndarray): Input feature sequences for inference.
        label_np (numpy.ndarray): Target labels (can be dummy labels for live prediction).
        model_config (dict): Dictionary containing loaded model hyperparameters 
            and the path to the saved weights.
        inference_type (str): Type of inference. Options: 'quantitative_test', 
            'qualitative_analysis', or 'live_prediction'.

    Returns:
        tuple: A tuple containing:
            - outputs_np (numpy.ndarray): Model prediction probabilities or values.
            - labels_np (numpy.ndarray): Ground truth labels from the dataset.
    """

    model_path = model_config['model_path']

    device = torch.device(model_config['device'] if torch.cuda.is_available() else 'cpu')
    print(device)

    model = TransformerClassification(
        input_dim=model_config['input_dim'], 
        hidden_dim=model_config['hidden_dim'], 
        target_size=model_config['target_size'], 
        num_heads=model_config['num_heads'], 
        num_layers=model_config['num_layers']
    ).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))

    batch_size = model_config['batch_size']

    if inference_type == 'quantitative_test':
        data_module = TrainDataModule(
            sequence_np=sequence_np, 
            label_np=label_np, 
            batch_size=batch_size,
            model=model_config['model_name'],
        )
        inference_loader = data_module.test_dataloader()
    else:
        data_module = TrainDataModule(
            sequence_np=sequence_np, 
            label_np=label_np, 
            batch_size=batch_size,
            model=model_config['model_name'],
            shuffle=False,
            split=False
        )
        inference_loader = data_module.inference_dataloader()

    outputs_np, labels_np = inference(inference_loader, model, model_config)

    return outputs_np, labels_np