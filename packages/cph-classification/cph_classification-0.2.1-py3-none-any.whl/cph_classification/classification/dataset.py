"""
Generic PyTorch Dataset for tabular classification data.

This module provides a reusable dataset class that handles feature encoding
and target extraction for classification tasks.
"""

from typing import Optional, Union
import torch
from torch.utils.data import Dataset
import numpy as np
import pandas as pd


class ClassificationDataset(Dataset):
    """
    PyTorch Dataset for tabular classification data.
    
    Handles feature encoding using preprocessors and extracts target values.
    Works with any number of categorical and numeric features.
    Targets are already integers (class labels), no encoding needed.
    
    Args:
        data: DataFrame containing features and target
        preprocessor: Fitted preprocessor (sklearn Pipeline or similar)
        target_col: Name of the target column
        feature_cols: List of feature column names (categorical + numeric)
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        preprocessor,
        target_col: str,
        feature_cols: list[str],
    ):
        """
        Initialize the classification dataset.
        
        Args:
            data: DataFrame with features and target
            preprocessor: Fitted sklearn preprocessor (Pipeline)
            target_col: Name of target column
            feature_cols: List of all feature column names
        """
        self.data = data.copy()
        self.preprocessor = preprocessor
        self.target_col = target_col
        self.feature_cols = feature_cols
        
        # Extract features and target
        self.features = self.data[self.feature_cols]
        self.targets = self.data[self.target_col].values
        
        # Transform features using preprocessor
        self.transformed_features = self.preprocessor.transform(self.features)
        
        # Convert to tensors
        self.features_tensor = torch.FloatTensor(self.transformed_features)
        # Targets are class indices (integers), convert to LongTensor for CrossEntropyLoss
        self.targets_tensor = torch.LongTensor(self.targets.astype(np.int64))
    
    def __len__(self) -> int:
        """Return the size of the dataset."""
        return len(self.data)
    
    def __getitem__(self, idx: Union[int, torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Get a single sample from the dataset.
        
        Args:
            idx: Index of the sample
            
        Returns:
            Tuple of (features, target) as tensors
        """
        if isinstance(idx, torch.Tensor):
            idx = idx.item()
        
        return self.features_tensor[idx], self.targets_tensor[idx]


