"""
Generic PyTorch Lightning DataModule for classification tasks.

This module provides a reusable data module that handles data loading,
preprocessing, and train/val/test splits for tabular classification data.
"""

from typing import Optional
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import lightning as L
from torch.utils.data import DataLoader

from cph_classification.classification.dataset import ClassificationDataset


class DataModuleCLS(L.LightningDataModule):
    """
    Generic PyTorch Lightning DataModule for classification.
    
    Handles:
    - Data loading from CSV
    - Preprocessing (categorical encoding, numeric scaling)
    - Train/val/test splits
    - Preprocessor persistence
    - Auto-calculation of input dimensions
    - Auto-detection of number of classes
    
    Args:
        csv_path: Path to CSV file
        batch_size: Batch size for data loaders
        num_workers: Number of worker processes for data loading
        val_split: Validation split ratio (0.0 to 1.0)
        test_split: Test split ratio (0.0 to 1.0), optional
        random_seed: Random seed for reproducibility
        categorical_cols: List of categorical column names
        numeric_cols: List of numeric column names
        target_col: Name of target column
        save_preprocessor: Whether to save preprocessor
        preprocessor_path: Path to save/load preprocessor
    """
    
    def __init__(
        self,
        csv_path: str,
        batch_size: int = 32,
        num_workers: int = 0,
        val_split: float = 0.2,
        test_split: Optional[float] = None,
        random_seed: int = 42,
        categorical_cols: Optional[list[str]] = None,
        numeric_cols: Optional[list[str]] = None,
        target_col: str = "target",
        save_preprocessor: bool = True,
        preprocessor_path: Optional[str] = None,
    ):
        """
        Initialize the data module.
        
        Args:
            csv_path: Path to CSV file
            batch_size: Batch size
            num_workers: Number of workers
            val_split: Validation split ratio
            test_split: Test split ratio (optional)
            random_seed: Random seed
            categorical_cols: List of categorical columns
            numeric_cols: List of numeric columns
            target_col: Target column name
            save_preprocessor: Whether to save preprocessor
            preprocessor_path: Preprocessor save path
        """
        super().__init__()
        
        self.csv_path = Path(csv_path)
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.val_split = val_split
        self.test_split = test_split
        self.random_seed = random_seed
        self.categorical_cols = categorical_cols or []
        self.numeric_cols = numeric_cols or []
        self.target_col = target_col
        self.save_preprocessor = save_preprocessor
        self.preprocessor_path = preprocessor_path
        
        # Validate inputs
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        if not 0 < val_split < 1:
            raise ValueError(f"val_split must be in (0, 1), got {val_split}")
        
        if test_split is not None and not 0 < test_split < 1:
            raise ValueError(f"test_split must be in (0, 1), got {test_split}")
        
        if val_split + (test_split or 0) >= 1:
            raise ValueError(
                f"val_split ({val_split}) + test_split ({test_split or 0}) must be < 1"
            )
        
        if not self.categorical_cols and not self.numeric_cols:
            raise ValueError("At least one of categorical_cols or numeric_cols must be provided")
        
        # Will be set during setup
        self.preprocessor: Optional[ColumnTransformer] = None
        self.input_dim: Optional[int] = None
        self.num_classes: Optional[int] = None
        self.train_dataset: Optional[ClassificationDataset] = None
        self.val_dataset: Optional[ClassificationDataset] = None
        self.test_dataset: Optional[ClassificationDataset] = None
    
    def prepare_data(self):
        """Download or prepare data (called only on main process)."""
        # Data loading happens in setup() to allow access to all processes
        pass
    
    def setup(self, stage: Optional[str] = None):
        """
        Setup datasets for training, validation, and testing.
        
        Args:
            stage: 'fit', 'validate', 'test', or 'predict'
        """
        # Load data
        df = pd.read_csv(self.csv_path)
        
        # Validate columns exist
        all_feature_cols = set(self.categorical_cols + self.numeric_cols)
        missing_cols = all_feature_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing columns in CSV: {missing_cols}")
        
        if self.target_col not in df.columns:
            raise ValueError(f"Target column '{self.target_col}' not found in CSV")
        
        # Validate and encode target column
        target_values = df[self.target_col].values
        target_is_categorical = not np.issubdtype(target_values.dtype, np.integer)
        
        if target_is_categorical:
            # Target is categorical (strings), need to encode to integers
            from sklearn.preprocessing import LabelEncoder
            
            # Create and fit label encoder
            self.label_encoder = LabelEncoder()
            df[self.target_col] = self.label_encoder.fit_transform(df[self.target_col].astype(str))
            
            # Get class names for reference (original labels)
            self.class_names = self.label_encoder.classes_.tolist()
            
        elif not np.issubdtype(target_values.dtype, np.integer):
            # Try to convert to integers if numeric but not integer
            try:
                df[self.target_col] = df[self.target_col].astype(int)
                # Continue to check if 0-indexed (fall through to else block)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Target column '{self.target_col}' must contain integer class labels or categorical strings. "
                    f"Got dtype: {target_values.dtype}"
                )
        
        # Handle integer labels (either originally integers or converted above)
        if np.issubdtype(df[self.target_col].dtype, np.integer):
            # Already integers - check if they're 0-indexed
            unique_ints = sorted(df[self.target_col].unique())
            min_class = min(unique_ints)
            
            # Store original class names before remapping
            self.class_names = [str(c) for c in unique_ints]
            
            if min_class != 0:
                # Labels are not 0-indexed, need to remap to 0-indexed
                # Use LabelEncoder to ensure proper mapping while preserving order
                from sklearn.preprocessing import LabelEncoder
                
                self.label_encoder = LabelEncoder()
                # Fit on sorted unique values to preserve order
                self.label_encoder.fit(sorted(unique_ints))
                # Transform to 0-indexed labels
                df[self.target_col] = self.label_encoder.transform(df[self.target_col])
            else:
                # Already 0-indexed, no remapping needed
                self.label_encoder = None
        
        # Detect number of classes from all data (after encoding)
        unique_classes = sorted(df[self.target_col].unique())
        num_classes = len(unique_classes)
        self.num_classes = num_classes
        
        # Validate class labels are 0-indexed consecutive (after encoding)
        min_class = min(unique_classes)
        max_class = max(unique_classes)
        expected_classes = set(range(min_class, max_class + 1))
        actual_classes = set(unique_classes)
        
        if actual_classes != expected_classes:
            import warnings
            warnings.warn(
                f"Target classes are not consecutive after encoding. Found: {sorted(unique_classes)}. "
                f"Expected: {sorted(expected_classes)}. "
                "This may cause issues with some metrics."
            )
        
        # Split data with stratification (use num_classes variable, not self.num_classes)
        if self.test_split:
            # Train + Val, Test split
            train_val_df, test_df = train_test_split(
                df,
                test_size=self.test_split,
                random_state=self.random_seed,
                shuffle=True,
                stratify=df[self.target_col] if num_classes > 1 else None,
            )
            # Train, Val split
            train_df, val_df = train_test_split(
                train_val_df,
                test_size=self.val_split / (1 - self.test_split),
                random_state=self.random_seed,
                shuffle=True,
                stratify=train_val_df[self.target_col] if num_classes > 1 else None,
            )
        else:
            # Train, Val split only
            train_df, val_df = train_test_split(
                df,
                test_size=self.val_split,
                random_state=self.random_seed,
                shuffle=True,
                stratify=df[self.target_col] if num_classes > 1 else None,
            )
            test_df = None
        
        # Create and fit preprocessor
        if stage == "fit" or stage is None:
            self.preprocessor = self._create_preprocessor(train_df)
            
            # Calculate input dimension from preprocessor output
            # This is the most accurate way as it uses the actual transformer output
            feature_cols = self.categorical_cols + self.numeric_cols
            sample_features = train_df[feature_cols].iloc[:1]
            transformed = self.preprocessor.transform(sample_features)
            self.input_dim = transformed.shape[1]
            
            # Save preprocessor if requested
            if self.save_preprocessor and self.preprocessor_path:
                preprocessor_dir = Path(self.preprocessor_path).parent
                preprocessor_dir.mkdir(parents=True, exist_ok=True)
                joblib.dump(self.preprocessor, self.preprocessor_path)
                
                # Save label encoder if target was categorical
                if hasattr(self, 'label_encoder') and self.label_encoder is not None:
                    label_encoder_path = preprocessor_dir / "label_encoder.joblib"
                    joblib.dump(self.label_encoder, label_encoder_path)
        
        # Load preprocessor if not fitted
        if self.preprocessor is None and self.preprocessor_path and Path(self.preprocessor_path).exists():
            self.preprocessor = joblib.load(self.preprocessor_path)
            
            # Try to load label encoder if it exists
            preprocessor_dir = Path(self.preprocessor_path).parent
            label_encoder_path = preprocessor_dir / "label_encoder.joblib"
            if label_encoder_path.exists():
                self.label_encoder = joblib.load(label_encoder_path)
                self.class_names = self.label_encoder.classes_.tolist()
            
            # Calculate input_dim from preprocessor (approximate)
            # This is a fallback - ideally should be saved separately
            if self.input_dim is None:
                # Estimate from data
                sample_df = train_df if 'train_df' in locals() else pd.read_csv(self.csv_path, nrows=1)
                self.input_dim = self._estimate_input_dim(sample_df)
        
        # Create datasets
        feature_cols = self.categorical_cols + self.numeric_cols
        
        if stage == "fit" or stage is None:
            self.train_dataset = ClassificationDataset(
                train_df, self.preprocessor, self.target_col, feature_cols
            )
            self.val_dataset = ClassificationDataset(
                val_df, self.preprocessor, self.target_col, feature_cols
            )
        
        if stage == "test" or stage is None:
            if test_df is not None:
                self.test_dataset = ClassificationDataset(
                    test_df, self.preprocessor, self.target_col, feature_cols
                )
            else:
                # Use validation set as test if no test split
                self.test_dataset = self.val_dataset
    
    def _create_preprocessor(self, train_df: pd.DataFrame) -> ColumnTransformer:
        """
        Create and fit preprocessor pipeline.
        
        Args:
            train_df: Training dataframe for fitting
            
        Returns:
            Fitted ColumnTransformer
        """
        transformers = []
        
        # Categorical encoding (one-hot)
        if self.categorical_cols:
            categorical_transformer = Pipeline([
                ('onehot', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
            ])
            transformers.append(('cat', categorical_transformer, self.categorical_cols))
        
        # Numeric scaling
        if self.numeric_cols:
            numeric_transformer = Pipeline([
                ('scaler', StandardScaler())
            ])
            transformers.append(('num', numeric_transformer, self.numeric_cols))
        
        preprocessor = ColumnTransformer(
            transformers=transformers,
            remainder='drop',
            verbose_feature_names_out=False
        )
        
        # Fit on training data
        feature_cols = self.categorical_cols + self.numeric_cols
        preprocessor.fit(train_df[feature_cols])
        
        return preprocessor
    
    def _estimate_input_dim(self, sample_df: pd.DataFrame) -> int:
        """
        Estimate input dimension from sample data.
        
        Args:
            sample_df: Sample dataframe
            
        Returns:
            Estimated input dimension
        """
        input_dim = 0
        
        if self.categorical_cols:
            for col in self.categorical_cols:
                n_categories = sample_df[col].nunique()
                # OneHotEncoder with drop='first' creates n_categories - 1 columns
                input_dim += (n_categories - 1)
        
        input_dim += len(self.numeric_cols)
        
        return input_dim
    
    def train_dataloader(self) -> DataLoader:
        """Create training data loader."""
        if self.train_dataset is None:
            raise RuntimeError("train_dataset not set. Call setup('fit') first.")
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=True,
        )
    
    def val_dataloader(self) -> DataLoader:
        """Create validation data loader."""
        if self.val_dataset is None:
            raise RuntimeError("val_dataset not set. Call setup('fit') first.")
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=True,
        )
    
    def test_dataloader(self) -> DataLoader:
        """Create test data loader."""
        if self.test_dataset is None:
            raise RuntimeError("test_dataset not set. Call setup('test') first.")
        return DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=True,
        )
    
    def get_input_dim(self) -> int:
        """
        Get the input dimension after preprocessing.
        
        Returns:
            Input dimension
        """
        if self.input_dim is None:
            raise RuntimeError("input_dim not set. Call setup() first.")
        return self.input_dim
    
    def get_num_classes(self) -> int:
        """
        Get the number of classes from target column.
        
        Returns:
            Number of classes
        """
        if self.num_classes is None:
            raise RuntimeError("num_classes not set. Call setup() first.")
        return self.num_classes
    
    def get_class_names(self) -> list[str]:
        """
        Get the class names (original labels before encoding).
        
        Returns:
            List of class names in order (0-indexed)
        """
        if not hasattr(self, 'class_names'):
            raise RuntimeError("class_names not set. Call setup() first.")
        return self.class_names
    
    def get_label_encoder(self):
        """
        Get the label encoder if target was categorical.
        
        Returns:
            LabelEncoder instance or None if target was already integers
        """
        return getattr(self, 'label_encoder', None)

