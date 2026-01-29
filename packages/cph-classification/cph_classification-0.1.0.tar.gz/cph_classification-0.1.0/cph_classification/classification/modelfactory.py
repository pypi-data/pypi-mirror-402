"""
Neural network model factory for classification tasks.

This module provides a flexible feedforward neural network architecture
that can be configured via hyperparameters for classification.
"""

from typing import Optional
import torch
import torch.nn as nn


class ClassificationModel(nn.Module):
    """
    Flexible feedforward neural network for classification.
    
    Supports configurable:
    - Input dimension (auto-detected from data)
    - Hidden layers (list of sizes)
    - Dropout rates (list matching hidden layers)
    - Activation functions
    - Output dimension (auto-detected from number of classes)
    
    Args:
        input_dim: Number of input features
        num_classes: Number of output classes
        hidden_layers: List of hidden layer sizes, e.g., [128, 64, 32]
        dropout_rates: List of dropout rates matching hidden layers, e.g., [0.15, 0.1, 0.05]
        activation: Activation function name ('relu', 'tanh', 'gelu', etc.)
    """
    
    def __init__(
        self,
        input_dim: int,
        num_classes: int,
        hidden_layers: list[int],
        dropout_rates: Optional[list[float]] = None,
        activation: str = "relu",
    ):
        """
        Initialize the classification model.
        
        Args:
            input_dim: Number of input features (can be 0 if will be set later)
            num_classes: Number of output classes (can be 0 if will be set later)
            hidden_layers: List of hidden layer sizes
            dropout_rates: List of dropout rates (must match hidden_layers length)
            activation: Activation function name
        """
        super().__init__()
        
        # Allow input_dim=0 temporarily (will be set later)
        if input_dim < 0:
            raise ValueError(f"input_dim must be non-negative, got {input_dim}")
        
        if num_classes < 0:
            raise ValueError(f"num_classes must be non-negative, got {num_classes}")
        
        if num_classes == 0 and input_dim > 0:
            raise ValueError("num_classes must be positive when input_dim is set")
        
        if not hidden_layers:
            raise ValueError("hidden_layers cannot be empty")
        
        if dropout_rates is None:
            dropout_rates = [0.0] * len(hidden_layers)
        
        if len(dropout_rates) != len(hidden_layers):
            raise ValueError(
                f"dropout_rates length ({len(dropout_rates)}) must match "
                f"hidden_layers length ({len(hidden_layers)})"
            )
        
        # Validate dropout rates
        for i, rate in enumerate(dropout_rates):
            if not 0 <= rate < 1:
                raise ValueError(f"dropout_rates[{i}] must be in [0, 1), got {rate}")
        
        # Store configuration
        self._input_dim = input_dim
        self._num_classes = num_classes
        self._hidden_layers = hidden_layers
        self._dropout_rates = dropout_rates
        self._activation = activation
        
        # Only build model if both input_dim and num_classes are set
        if input_dim > 0 and num_classes > 0:
            self._build_model()
        else:
            # Create placeholder - will be built when dimensions are set
            self.model = None
            self.input_dim = input_dim
            self.num_classes = num_classes
    
    def _build_model(self):
        """Build the model architecture."""
        if self._input_dim <= 0 or self._num_classes <= 0:
            return
        
        # Get activation function
        activation_fn = self._get_activation(self._activation)
        
        # Build layers
        layers = []
        prev_dim = self._input_dim
        
        for i, (hidden_dim, dropout_rate) in enumerate(zip(self._hidden_layers, self._dropout_rates)):
            # Linear layer
            layers.append(nn.Linear(prev_dim, hidden_dim))
            
            # Batch normalization
            layers.append(nn.BatchNorm1d(hidden_dim))
            
            # Activation
            layers.append(activation_fn)
            
            # Dropout
            if dropout_rate > 0:
                layers.append(nn.Dropout(dropout_rate))
            
            prev_dim = hidden_dim
        
        # Output layer (no activation - outputs logits for CrossEntropyLoss)
        layers.append(nn.Linear(prev_dim, self._num_classes))
        
        self.model = nn.Sequential(*layers)
        self.input_dim = self._input_dim
        self.num_classes = self._num_classes
    
    def set_dimensions(self, input_dim: int, num_classes: int):
        """
        Set input dimension and number of classes, then build the model.
        
        Args:
            input_dim: Number of input features
            num_classes: Number of output classes
        """
        if input_dim <= 0:
            raise ValueError(f"input_dim must be positive, got {input_dim}")
        
        if num_classes <= 0:
            raise ValueError(f"num_classes must be positive, got {num_classes}")
        
        if self.model is not None:
            raise RuntimeError("Model already built. Cannot change dimensions.")
        
        self._input_dim = input_dim
        self._num_classes = num_classes
        self._build_model()
    
    def _get_activation(self, activation: str) -> nn.Module:
        """
        Get activation function module.
        
        Args:
            activation: Activation function name
            
        Returns:
            Activation function module
        """
        activation_map = {
            "relu": nn.ReLU(),
            "tanh": nn.Tanh(),
            "gelu": nn.GELU(),
            "sigmoid": nn.Sigmoid(),
            "leaky_relu": nn.LeakyReLU(),
            "elu": nn.ELU(),
        }
        
        activation_lower = activation.lower()
        if activation_lower not in activation_map:
            raise ValueError(
                f"Unknown activation '{activation}'. "
                f"Supported: {list(activation_map.keys())}"
            )
        
        return activation_map[activation_lower]
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, input_dim)
            
        Returns:
            Output tensor of shape (batch_size, num_classes) - logits (no softmax)
        """
        if self.model is None:
            raise RuntimeError("Model not built. input_dim and num_classes must be set before forward pass.")
        return self.model(x)
    
    def get_input_dim(self) -> int:
        """Get the input dimension."""
        return self.input_dim
    
    def get_num_classes(self) -> int:
        """Get the number of classes."""
        return self.num_classes

