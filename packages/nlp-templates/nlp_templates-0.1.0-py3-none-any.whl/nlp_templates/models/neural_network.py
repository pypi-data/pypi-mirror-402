"""
Custom neural network implementation for classification.

Built from scratch with PyTorch, supporting configurable hidden layer dimensions.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple, Optional


class NeuralNetworkModel(nn.Module):
    """
    Feedforward neural network for classification.

    Args:
        input_size (int): Number of input features
        hidden_dims (list): List of hidden layer dimensions, e.g., [128, 64, 32]
        output_size (int): Number of output classes
        dropout_rate (float): Dropout probability between layers
        activation (str): Activation function ('relu', 'tanh', 'sigmoid')
    """

    def __init__(
        self,
        input_size: int,
        hidden_dims: List[int],
        output_size: int,
        dropout_rate: float = 0.2,
        activation: str = "relu",
    ):
        super().__init__()

        self.input_size = input_size
        self.hidden_dims = hidden_dims
        self.output_size = output_size
        self.dropout_rate = dropout_rate

        # Choose activation function
        if activation == "relu":
            self.activation = nn.ReLU()
        elif activation == "tanh":
            self.activation = nn.Tanh()
        elif activation == "sigmoid":
            self.activation = nn.Sigmoid()
        else:
            raise ValueError(f"Unknown activation: {activation}")

        # Build layers
        layers = []
        prev_dim = input_size

        # Hidden layers
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(self.activation)
            if dropout_rate > 0:
                layers.append(nn.Dropout(dropout_rate))
            prev_dim = hidden_dim

        # Output layer
        layers.append(nn.Linear(prev_dim, output_size))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through network."""
        return self.network(x)


class NeuralNetworkClassifier:
    """
    Sklearn-compatible neural network classifier wrapper.

    Provides fit/predict interface compatible with SimpleMulticlassClassifier.
    """

    def __init__(
        self,
        hidden_dims: List[int] = None,
        activation: str = "relu",
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
        epochs: int = 100,
        batch_size: int = 32,
        random_state: int = 42,
        verbose: bool = False,
    ):
        """
        Initialize Neural Network Classifier.

        Args:
            hidden_dims (list): Hidden layer dimensions, e.g., [128, 64]
            activation (str): Activation function
            dropout_rate (float): Dropout probability
            learning_rate (float): Learning rate for optimizer
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
            random_state (int): Random seed for reproducibility
            verbose (bool): Print training progress
        """
        if hidden_dims is None:
            hidden_dims = [128, 64]

        self.hidden_dims = hidden_dims
        self.activation = activation
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.random_state = random_state
        self.verbose = verbose

        # Set seeds for reproducibility
        torch.manual_seed(random_state)
        np.random.seed(random_state)

        self.model = None
        self.classes_ = None
        self.n_classes_ = None
        self.n_features_ = None
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "NeuralNetworkClassifier":
        """
        Train the neural network.

        Args:
            X (np.ndarray): Training features (n_samples, n_features)
            y (np.ndarray): Training labels (n_samples,)

        Returns:
            self
        """
        # Store class information
        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        self.n_features_ = X.shape[1]

        # Create label mapping
        self.class_to_idx_ = {c: i for i, c in enumerate(self.classes_)}
        self.idx_to_class_ = {i: c for c, i in self.class_to_idx_.items()}

        # Convert labels to indices
        y_indices = np.array([self.class_to_idx_[label] for label in y])

        # Build model
        self.model = NeuralNetworkModel(
            input_size=self.n_features_,
            hidden_dims=self.hidden_dims,
            output_size=self.n_classes_,
            dropout_rate=self.dropout_rate,
            activation=self.activation,
        ).to(self.device)

        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Convert to tensors
        X_tensor = torch.FloatTensor(X).to(self.device)
        y_tensor = torch.LongTensor(y_indices).to(self.device)

        # Training loop
        self.model.train()
        for epoch in range(self.epochs):
            # Shuffle data
            indices = np.arange(len(X))
            np.random.shuffle(indices)

            epoch_loss = 0.0
            n_batches = 0

            # Mini-batch training
            for i in range(0, len(X), self.batch_size):
                batch_indices = indices[i : i + self.batch_size]
                X_batch = X_tensor[batch_indices]
                y_batch = y_tensor[batch_indices]

                # Forward pass
                optimizer.zero_grad()
                outputs = self.model(X_batch)
                loss = criterion(outputs, y_batch)

                # Backward pass
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            if self.verbose and (epoch + 1) % 10 == 0:
                avg_loss = epoch_loss / n_batches
                print(
                    f"Epoch [{epoch + 1}/{self.epochs}], Loss: {avg_loss:.4f}"
                )

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Args:
            X (np.ndarray): Features to predict on

        Returns:
            np.ndarray: Predicted class labels
        """
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            outputs = self.model(X_tensor)
            predictions = torch.argmax(outputs, dim=1)
            predictions = predictions.cpu().numpy()

        # Convert indices back to original classes
        return np.array([self.idx_to_class_[idx] for idx in predictions])

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Args:
            X (np.ndarray): Features to predict on

        Returns:
            np.ndarray: Predicted probabilities (n_samples, n_classes)
        """
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            outputs = self.model(X_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            probabilities = probabilities.cpu().numpy()

        return probabilities
