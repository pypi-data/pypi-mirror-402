import os
import json
import time
import numpy as np
import pandas as pd 
import math
import torch
from torch import nn

from ..dataloaders.data_module import TrainDataModule
from ..trainers.train import train
from ..inference.inference import inference

class Baller2Vec(nn.Module):
    def __init__(
        self,
        num_player_ids,
        embedding_dim,
        sigmoid,
        seq_len,
        mlp_layers,
        num_players,
        target_size,
        num_heads,
        dim_feedforward,
        num_layers,
        dropout,
        embed_before_mlp
    ):
        super().__init__()
        self.sigmoid = sigmoid
        self.original_seq_len = seq_len
        self.target_seq_len = 20
        self.seq_len = self.target_seq_len
        self.n_players = num_players
        self.embed_before_mlp = embed_before_mlp

        initrange = 0.1
        self.player_embedding = nn.Embedding(num_player_ids, embedding_dim)
        self.player_embedding.weight.data.uniform_(-initrange, initrange)

        self.ball_embedding = nn.Parameter(torch.Tensor(embedding_dim))
        nn.init.uniform_(self.ball_embedding, -initrange, initrange)
        self.cls_embedding = nn.Parameter(torch.Tensor(mlp_layers[-1]))
        nn.init.uniform_(self.cls_embedding, -initrange, initrange)

        # ----- Player & Ball MLP -----
        player_mlp = nn.Sequential()
        ball_mlp = nn.Sequential()
        in_feats = embedding_dim + 2 if embed_before_mlp else 2
        for (layer_idx, out_feats) in enumerate(mlp_layers):
            if (not embed_before_mlp) and (layer_idx == len(mlp_layers) - 1):
                out_feats = out_feats - embedding_dim

            player_mlp.add_module(f"layer{layer_idx}", nn.Linear(in_feats, out_feats))
            ball_mlp.add_module(f"layer{layer_idx}", nn.Linear(in_feats, out_feats))
            if layer_idx < len(mlp_layers) - 1:
                player_mlp.add_module(f"relu{layer_idx}", nn.ReLU())
                ball_mlp.add_module(f"relu{layer_idx}", nn.ReLU())
            in_feats = out_feats

        self.player_mlp = player_mlp
        self.ball_mlp = ball_mlp

        # ----- Transformer -----
        d_model = mlp_layers[-1]
        self.d_model = d_model
        encoder_layer = nn.TransformerEncoderLayer(d_model, num_heads, dim_feedforward, dropout, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)

        # ----- Classifier -----
        self.event_classifier = nn.Linear(d_model, target_size)
        self.event_classifier.weight.data.uniform_(-initrange, initrange)
        self.event_classifier.bias.data.zero_()

        # ----- Mask -----
        self.register_buffer("mask", self.generate_self_attn_mask())

    def generate_self_attn_mask(self):
        # n players plus the ball and the CLS entity (if used).
        # sz = (n_players + 2) * self.seq_len = (22 + 2) * 10 = 240
        sz = (self.n_players + 2) * self.seq_len
        mask = torch.zeros(sz, sz)

        # ball_start = n_players * seq_len = 22 * 10 = 220
        ball_start = self.n_players * self.seq_len
        # cls_start = ball_start + seq_len = 220 + 10 = 230
        cls_start = ball_start + self.seq_len

        for step in range(self.seq_len):
            start = self.n_players * step
            stop = start + self.n_players
            ball_stop = ball_start + step + 1

            mask[start:stop, :stop] = 1
            mask[start:stop, ball_start:ball_stop] = 1
            mask[ball_start + step, :stop] = 1
            mask[ball_start + step, ball_start:ball_stop] = 1
            cls_stop = cls_start + step + 1
            mask[start:stop, cls_start:cls_stop] = 1
            mask[ball_start + step, cls_start:cls_stop] = 1
            mask[cls_start + step, :stop] = 1
            mask[cls_start + step, ball_start:ball_stop] = 1
            mask[cls_start + step, cls_start:cls_stop] = 1

        mask = mask.masked_fill(mask == 0, float("-inf"))
        mask = mask.masked_fill(mask == 1, float(0.0))
        return mask

    def forward(self, tensors):
        
        device = next(self.parameters()).device
        B = tensors["player_idxs"].shape[0]

        original_seq_len = tensors["player_idxs"].size(1) 
        target_seq_len = self.seq_len

        if original_seq_len > target_seq_len:
            step = original_seq_len // target_seq_len
            indices = torch.arange(0, original_seq_len, step=step, device=device)[:target_seq_len]
            
            tensors["player_idxs"] = tensors["player_idxs"][:, indices, ...]
            tensors["player_xs"] = tensors["player_xs"][:, indices, ...]
            tensors["player_ys"] = tensors["player_ys"][:, indices, ...]
            tensors["ball_xs"] = tensors["ball_xs"][:, indices, ...]
            tensors["ball_ys"] = tensors["ball_ys"][:, indices, ...]

        # --- Players ---
        player_embeddings = self.player_embedding(tensors["player_idxs"].to(device))  # (B, seq_len, n_players, emb)
        if self.sigmoid == "logistic":
            player_embeddings = torch.sigmoid(player_embeddings)
        elif self.sigmoid == "tanh":
            player_embeddings = torch.tanh(player_embeddings)

        player_xs = tensors["player_xs"].to(device).unsqueeze(-1)
        player_ys = tensors["player_ys"].to(device).unsqueeze(-1)

        if self.embed_before_mlp:
            player_input = torch.cat([player_embeddings, player_xs, player_ys], dim=-1)
            player_feats = self.player_mlp(player_input) * math.sqrt(self.d_model)
        else:
            player_pos = torch.cat([player_xs, player_ys], dim=-1)
            pos_feats = self.player_mlp(player_pos) * math.sqrt(self.d_model)
            pos_feats = pos_feats[..., :player_embeddings.shape[-1]]
            player_feats = torch.cat([player_embeddings, pos_feats], dim=-1)

        # reshape to (B, seq_len, n_players, d_model)
        player_feats = player_feats.reshape(B, self.seq_len, self.n_players, -1)

        # --- Ball ---
        ball_emb = self.ball_embedding.unsqueeze(0).unsqueeze(0).repeat(B, self.seq_len, 1)
        ball_xs = tensors["ball_xs"].to(device).unsqueeze(-1)
        ball_ys = tensors["ball_ys"].to(device).unsqueeze(-1)
        if self.embed_before_mlp:
            ball_input = torch.cat([ball_emb, ball_xs, ball_ys], dim=-1)
            ball_feats = self.ball_mlp(ball_input) * math.sqrt(self.d_model)
        else:
            ball_pos = torch.cat([ball_xs, ball_ys], dim=-1)
            pos_feats = self.ball_mlp(ball_pos) * math.sqrt(self.d_model)
            ball_feats = torch.cat([ball_emb, pos_feats], dim=-1)

        ball_feats = ball_feats.unsqueeze(2)  # (B, seq_len, 1, d_model)

        # --- CLS token ---
        cls_feats = self.cls_embedding.unsqueeze(0).unsqueeze(0).repeat(B, self.seq_len, 1).unsqueeze(2)

        # --- Combine ---
        combined = torch.cat([player_feats, ball_feats, cls_feats], dim=2)  # (B, seq_len, n_players+2, d_model)
        combined = combined.view(B, -1, self.d_model)  # (B, seq_len*(n_players+2), d_model)

        # --- Transformer ---
        output = self.transformer(combined, self.mask.to(device))  # (B, L, d_model)
        seq_preds = self.event_classifier(output)  # (B, L, n_seq_labels)

        preds = {"seq_label": seq_preds[:, -1]}
        return preds


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

    model = Baller2Vec(
        num_player_ids=model_config['num_player_ids'],
        embedding_dim=model_config['embedding_dim'],
        sigmoid=None,
        seq_len=model_config['seq_len'],
        mlp_layers=model_config['mlp_layers'],
        num_players=model_config['num_players'],
        target_size=target_size, 
        num_heads=model_config['num_heads'],
        dim_feedforward=model_config['dim_feedforward'],
        num_layers=model_config['num_layers'],
        dropout=model_config['dropout'],
        embed_before_mlp=model_config['embed_before_mlp']
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

    model_save_path = save_path + "best.pth"
    loss_save_path = save_path + "loss.csv"
    hyperparameters_save_path = save_path + "hyperparameters.json"
    model_stats_save_path = save_path + "model_stats.txt"

    hyperparameters = {'current_time': current_time,
                        'train_sequence_np_path': data_config['train_sequence_np_path'], 'train_label_np_path': data_config['train_label_np_path'], 'save_dir': data_config['save_dir'],
                        'model_name': model_config['name'], 'train_mode':data_config['mode'], 'run':i, 'model_path': model_save_path,
                        
                        'num_player_ids': model_config['num_player_ids'], 'embedding_dim': model_config['embedding_dim'], 
                        'sigmoid':  model_config['sigmoid'], 'seq_len': model_config['seq_len'], 'mlp_layers': model_config['mlp_layers'],
                        'num_players': model_config['num_players'], 'target_size': target_size,  'num_heads': model_config['num_heads'],
                        'dim_feedforward': model_config['dim_feedforward'], 'num_layers': model_config['num_layers'], 'dropout': model_config['dropout'],
                        'embed_before_mlp': model_config['embed_before_mlp'],
                        
                        'batch_size': train_config['batch_size'], 'num_epochs': train_config['num_epochs'], 'lr': train_config['lr'], 'patience': train_config['patience'], 
                        'device': train_config['device'], 'best_epoch':best_epoch}

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

    model = Baller2Vec(
        num_player_ids=model_config['num_player_ids'],
        embedding_dim=model_config['embedding_dim'],
        sigmoid=None,
        seq_len=model_config['seq_len'],
        mlp_layers=model_config['mlp_layers'],
        num_players=model_config['num_players'],
        target_size=model_config['target_size'],
        num_heads=model_config['num_heads'],
        dim_feedforward=model_config['dim_feedforward'],
        num_layers=model_config['num_layers'],
        dropout=model_config['dropout'],
        embed_before_mlp=model_config['embed_before_mlp']
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