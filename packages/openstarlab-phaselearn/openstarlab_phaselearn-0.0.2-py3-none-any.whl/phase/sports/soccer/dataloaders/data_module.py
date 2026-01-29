import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, TensorDataset
from typing import Tuple, Dict

class Baller2VecDataset(Dataset):
    """
    Dataset for the Baller2Vec model.
    Extracts features from raw coordinate arrays and returns them in a dictionary format.
    """
    def __init__(self, X: np.ndarray, y: np.ndarray, n_players: int):
        """
        Args:
            X (np.ndarray): Input sequence data [N, Seq, Features].
            y (np.ndarray): Target labels [N, Labels].
            n_players (int): Number of players in the sequence.
        """
        self.X = X
        self.y = y.astype(np.float32)
        self.n_players = n_players

    def __len__(self) -> int:
        """Returns the total number of samples."""
        return len(self.X)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Retrieves a single sample and formats it for Baller2Vec.
        
        Returns:
            Dict[str, torch.Tensor]: Dictionary containing player indices, 
            player/ball coordinates, and event labels.
        """
        seq_data = self.X[idx]
        events = self.y[idx]

        player_xs = seq_data[:, 2::2]
        player_ys = seq_data[:, 3::2]

        return {
            "player_idxs": torch.arange(self.n_players).unsqueeze(0).repeat(seq_data.shape[0], 1),
            "player_xs": torch.tensor(player_xs, dtype=torch.float32),
            "player_ys": torch.tensor(player_ys, dtype=torch.float32),
            "ball_xs": torch.tensor(seq_data[:, 0], dtype=torch.float32),
            "ball_ys": torch.tensor(seq_data[:, 1], dtype=torch.float32),
            "events": torch.tensor(events, dtype=torch.float32),
        }


class GNNDataset(Dataset):
    """
    Dataset for GNN models (GCN/GAT Transformer).
    Constructs a spatio-temporal graph representation where players and the ball are nodes.
    """
    def __init__(self, X: np.ndarray, y: np.ndarray, n_players: int):
        """
        Args:
            X (np.ndarray): Input sequence data.
            y (np.ndarray): Target labels.
            n_players (int): Total number of players.
        """
        self.X = X
        self.y = y.astype(np.float32)
        self.n_players = n_players
        self.player_goal_sides_vec = torch.tensor([1] * 11 + [2] * 11, dtype=torch.long)
        self.edge_index = self._create_edge_index()

    def __len__(self) -> int:
        """Returns the total number of samples."""
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Constructs node features and retrieves the static edge index.
        
        Returns:
            Tuple: (node_features [Seq, Nodes, Feats], labels, edge_index)
        """
        seq_data_np = self.X[idx]
        events_np = self.y[idx]

        ball_xs = torch.tensor(seq_data_np[:, 0], dtype=torch.float32)
        ball_ys = torch.tensor(seq_data_np[:, 1], dtype=torch.float32)
        
        player_xs = torch.tensor(seq_data_np[:, 2::2], dtype=torch.float32)
        player_ys = torch.tensor(seq_data_np[:, 3::2], dtype=torch.float32)
        
        player_features = torch.stack([player_xs, player_ys], dim=-1)
        player_goal_sides_tiled = self.player_goal_sides_vec.unsqueeze(0).repeat(seq_data_np.shape[0], 1).unsqueeze(-1)
        player_features = torch.cat((player_features, player_goal_sides_tiled), dim=-1)

        ball_id_indicator = torch.zeros_like(ball_xs).unsqueeze(-1)
        ball_features = torch.stack([ball_xs, ball_ys, ball_id_indicator.squeeze(-1)], dim=-1).unsqueeze(1)

        x_seq = torch.cat((ball_features, player_features), dim=1)

        return x_seq, torch.tensor(events_np, dtype=torch.float32), self.edge_index

    def _create_edge_index(self) -> torch.Tensor:
        """
        Creates a static adjacency list (edge_index) for the GNN.
        1. Connects ball to all players (bidirectional).
        2. Connects players within the same team (fully connected sub-graphs).
        
        Returns:
            torch.Tensor: Edge index in COO format [2, E].
        """
        edges = []
        num_nodes = self.n_players + 1
        
        for i in range(1, num_nodes):
            edges.append((0, i))
            edges.append((i, 0))
        
        for i in range(1, num_nodes):
            for j in range(1, num_nodes):
                if i != j:
                    if self.player_goal_sides_vec[i - 1] == self.player_goal_sides_vec[j - 1]:
                        edges.append((i, j))
        
        edge_index = torch.tensor(edges, dtype=torch.long).T.contiguous()
        return edge_index


class TrainDataModule:
    """
    Integrated class for data cleaning, splitting, and DataLoader generation.
    Handles different dataset types based on the selected model.
    """
    def __init__(self, sequence_np: np.ndarray, label_np: np.ndarray, batch_size: int, n_players: int = 22, worker_count: int = 4, seed: int = 42, shuffle: bool = True, split: bool = True, model: str = 'transformer'):
        """
        Initializes the data module, prepares data, and sets up datasets.

        Args:
            sequence_np (np.ndarray): Raw feature array.
            label_np (np.ndarray): Raw label array.
            batch_size (int): Batch size for DataLoader.
            n_players (int): Number of players.
            worker_count (int): Parallel workers for data loading.
            seed (int): Random seed for reproducibility.
            shuffle (bool): Whether to shuffle the data.
            split (bool): Whether to perform train/val/test split.
            model (str): Architecture type ('transformer', 'baller2vec', 'gcn_transformer', 'gat_transformer').
        """
        self.batch_size = batch_size
        self.n_players = n_players
        self.worker_count = worker_count
        self.seed = seed
        
        sequence_np, label_np = self._prepare_data(sequence_np, label_np, shuffle=shuffle)

        if split:
            (train_sequence_np, train_label_np, valid_sequence_np, valid_label_np, test_sequence_np, test_label_np) = self._split_data(sequence_np, label_np)

        # self._check_numpy("train_sequence_np", train_sequence_np)
        # self._check_numpy("valid_sequence_np", valid_sequence_np)
        # self._check_numpy("label_np", label_np)
        
        if model == 'transformer':
            DatasetClass = TensorDataset
            is_tensor_dataset = True
        elif model == 'baller2vec':
            DatasetClass = Baller2VecDataset
            is_tensor_dataset = False
        elif model == 'gcn_transformer' or model == 'gat_transformer':
            DatasetClass = GNNDataset
            is_tensor_dataset = False
        else:
            raise ValueError(f"Unknown model type: {model}")

        if is_tensor_dataset:
            if split:
                self.train_dataset = DatasetClass(torch.tensor(train_sequence_np, dtype=torch.float32), torch.tensor(train_label_np, dtype=torch.float32))
                self.valid_dataset = DatasetClass(torch.tensor(valid_sequence_np, dtype=torch.float32), torch.tensor(valid_label_np, dtype=torch.float32))
                self.test_dataset = DatasetClass(torch.tensor(test_sequence_np, dtype=torch.float32), torch.tensor(test_label_np, dtype=torch.float32))
            else:
                self.inference_dataset = DatasetClass(torch.tensor(sequence_np, dtype=torch.float32), torch.tensor(label_np, dtype=torch.float32))
        else:
            if split:
                self.train_dataset = DatasetClass(X=train_sequence_np, y=train_label_np, n_players=self.n_players)
                self.valid_dataset = DatasetClass(X=valid_sequence_np, y=valid_label_np, n_players=self.n_players)
                self.test_dataset = DatasetClass(X=test_sequence_np, y=test_label_np, n_players=self.n_players)
            else:
                self.inference_dataset = DatasetClass(X=sequence_np, y=label_np, n_players=self.n_players)

    def _prepare_data(self, sequence_np: np.ndarray, label_np: np.ndarray, shuffle: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cleans data by ensuring length is a multiple of 10 and shuffles if requested.
        """
        slice_len = len(sequence_np) % 10
        if slice_len > 0:
            sequence_np = np.delete(sequence_np, slice(len(sequence_np) - slice_len, len(sequence_np)), 0)
            label_np = np.delete(label_np, slice(len(label_np) - slice_len, len(label_np)), 0)
        
        if shuffle:
            np.random.seed(self.seed)
            indices = np.arange(len(sequence_np))
            np.random.shuffle(indices)
            return sequence_np[indices], label_np[indices]
        else:
            return sequence_np, label_np

    def _split_data(self, sequence_np: np.ndarray, label_np: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Splits data into Training (80%), Validation (10%), and Test (10%) sets.
        """
        total_size = len(sequence_np)
        train_size = int(total_size * 0.8)
        val_size = int(total_size * 0.1)
        
        train_sequence_np = sequence_np[:train_size]
        train_label_np = label_np[:train_size]
        valid_sequence_np = sequence_np[train_size:train_size + val_size]
        valid_label_np = label_np[train_size:train_size + val_size]
        test_sequence_np = sequence_np[train_size + val_size:]
        test_label_np = label_np[train_size + val_size:]

        return (train_sequence_np, train_label_np, valid_sequence_np, valid_label_np, test_sequence_np, test_label_np)
    
    def _check_numpy(self, name, arr):
        """
        Validates if the NumPy array contains any NaN or Infinite values.
        """
        if not np.isfinite(arr).all():
            idx = np.where(~np.isfinite(arr))
            print(f"❌ {name} contains NaN or Inf")
            print("indices (first 5):", list(zip(*idx))[:5])
            print("values:", arr[idx][:5])
            raise RuntimeError
        else:
            print(f"✅ {name} is finite")

    def train_dataloader(self) -> DataLoader:
        """Returns the training DataLoader."""
        return DataLoader(
            dataset=self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.worker_count,
            pin_memory=True
        )

    def valid_dataloader(self) -> DataLoader:
        """Returns the validation DataLoader."""
        return DataLoader(
            dataset=self.valid_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.worker_count,
            pin_memory=True
        )

    def test_dataloader(self) -> DataLoader:
        """Returns the test DataLoader."""
        return DataLoader(
            dataset=self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.worker_count,
            pin_memory=True
        )

    def inference_dataloader(self) -> DataLoader:
        """Returns the inference DataLoader."""
        return DataLoader(
            dataset=self.inference_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.worker_count,
            pin_memory=True
        )