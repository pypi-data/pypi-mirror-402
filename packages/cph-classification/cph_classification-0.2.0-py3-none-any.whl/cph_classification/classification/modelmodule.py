"""
Generic PyTorch Lightning Module for classification tasks.

This module provides a reusable Lightning module that handles training,
validation, and testing steps for classification models.
"""

from typing import Optional, Any
import torch
import torch.nn as nn
import lightning as L
from torchmetrics import Accuracy, F1Score, Precision, Recall
from torchmetrics.classification import MulticlassAccuracy, MulticlassF1Score, MulticlassPrecision, MulticlassRecall

from cph_classification.classification.modelfactory import ClassificationModel


class ModelModuleCLS(L.LightningModule):
    """
    Generic PyTorch Lightning Module for classification.
    
    Handles:
    - Training/validation/test steps
    - Loss calculation (CrossEntropyLoss)
    - Optimizer and scheduler configuration
    - Classification metrics logging (Accuracy, F1, Precision, Recall)
    
    Args:
        model: Classification model instance
        lr: Learning rate
        weight_decay: Weight decay for optimizer
        lr_scheduler_factor: Factor for ReduceLROnPlateau scheduler
        lr_scheduler_patience: Patience for ReduceLROnPlateau scheduler
        class_weights: Optional class weights for imbalanced datasets
        save_dir: Directory to save model artifacts
        name: Model name for saving
    """
    
    def __init__(
        self,
        model: ClassificationModel,
        lr: float = 1e-3,
        weight_decay: float = 0.0,
        lr_scheduler_factor: Optional[float] = None,
        lr_scheduler_patience: Optional[int] = None,
        class_weights: Optional[torch.Tensor] = None,
        save_dir: Optional[str] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize the Lightning module.
        
        Args:
            model: Classification model instance
            lr: Learning rate
            weight_decay: Weight decay
            lr_scheduler_factor: LR scheduler factor
            lr_scheduler_patience: LR scheduler patience
            class_weights: Optional class weights tensor
            save_dir: Save directory
            name: Model name
        """
        super().__init__()
        
        self.model = model
        self.lr = lr
        self.weight_decay = weight_decay
        self.lr_scheduler_factor = lr_scheduler_factor
        self.lr_scheduler_patience = lr_scheduler_patience
        self.class_weights = class_weights
        self.save_dir = save_dir
        self.name = name
        
        # Loss function with optional class weights
        self.criterion = nn.CrossEntropyLoss(weight=class_weights)
        
        # Get number of classes from model (may be 0 initially, will be set later)
        num_classes = 0
        if hasattr(model, 'get_num_classes'):
            num_classes = model.get_num_classes()
        elif hasattr(model, 'num_classes'):
            num_classes = model.num_classes
        
        # Initialize metrics (will be re-initialized if num_classes changes)
        # Use a placeholder value if num_classes is 0, will be updated in setup
        self._num_classes = num_classes
        self._initialize_metrics(num_classes if num_classes > 0 else 2)  # Default to 2 if unknown
    
    def _initialize_metrics(self, num_classes: int):
        """Initialize or re-initialize metrics with given number of classes."""
        self.train_accuracy = MulticlassAccuracy(num_classes=num_classes, average='macro')
        self.val_accuracy = MulticlassAccuracy(num_classes=num_classes, average='macro')
        self.test_accuracy = MulticlassAccuracy(num_classes=num_classes, average='macro')
        
        self.train_f1 = MulticlassF1Score(num_classes=num_classes, average='macro')
        self.val_f1 = MulticlassF1Score(num_classes=num_classes, average='macro')
        self.test_f1 = MulticlassF1Score(num_classes=num_classes, average='macro')
        
        self.train_precision = MulticlassPrecision(num_classes=num_classes, average='macro')
        self.val_precision = MulticlassPrecision(num_classes=num_classes, average='macro')
        self.test_precision = MulticlassPrecision(num_classes=num_classes, average='macro')
        
        self.train_recall = MulticlassRecall(num_classes=num_classes, average='macro')
        self.val_recall = MulticlassRecall(num_classes=num_classes, average='macro')
        self.test_recall = MulticlassRecall(num_classes=num_classes, average='macro')
    
    def on_train_start(self):
        """Called at the start of training. Re-initialize metrics if num_classes was updated."""
        # Get current num_classes from model
        if hasattr(self.model, 'get_num_classes'):
            current_num_classes = self.model.get_num_classes()
        elif hasattr(self.model, 'num_classes'):
            current_num_classes = self.model.num_classes
        else:
            current_num_classes = self._num_classes
        
        # Re-initialize metrics if num_classes changed
        if current_num_classes > 0 and current_num_classes != self._num_classes:
            self._num_classes = current_num_classes
            self._initialize_metrics(current_num_classes)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor
            
        Returns:
            Model output (logits)
        """
        return self.model(x)
    
    def training_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        """
        Training step.
        
        Args:
            batch: Batch of (features, targets)
            batch_idx: Batch index
            
        Returns:
            Loss value
        """
        x, y = batch
        y_hat = self.forward(x)
        loss = self.criterion(y_hat, y)
        
        # Get predictions (class indices)
        preds = torch.argmax(y_hat, dim=1)
        
        # Update metrics
        self.train_accuracy(preds, y)
        self.train_f1(preds, y)
        self.train_precision(preds, y)
        self.train_recall(preds, y)
        
        # Log metrics
        self.log("train_loss", loss, on_step=True, on_epoch=True, prog_bar=True, logger=True)
        self.log("train_acc", self.train_accuracy, on_step=False, on_epoch=True, prog_bar=True, logger=True)
        self.log("train_f1", self.train_f1, on_step=False, on_epoch=True, logger=True)
        self.log("train_precision", self.train_precision, on_step=False, on_epoch=True, logger=True)
        self.log("train_recall", self.train_recall, on_step=False, on_epoch=True, logger=True)
        
        return loss
    
    def validation_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        """
        Validation step.
        
        Args:
            batch: Batch of (features, targets)
            batch_idx: Batch index
            
        Returns:
            Loss value
        """
        x, y = batch
        y_hat = self.forward(x)
        loss = self.criterion(y_hat, y)
        
        # Get predictions (class indices)
        preds = torch.argmax(y_hat, dim=1)
        
        # Update metrics
        self.val_accuracy(preds, y)
        self.val_f1(preds, y)
        self.val_precision(preds, y)
        self.val_recall(preds, y)
        
        # Log metrics
        self.log("val_loss", loss, on_step=False, on_epoch=True, prog_bar=True, logger=True)
        self.log("val_acc", self.val_accuracy, on_step=False, on_epoch=True, prog_bar=True, logger=True)
        self.log("val_f1", self.val_f1, on_step=False, on_epoch=True, logger=True)
        self.log("val_precision", self.val_precision, on_step=False, on_epoch=True, logger=True)
        self.log("val_recall", self.val_recall, on_step=False, on_epoch=True, logger=True)
        
        return loss
    
    def test_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        """
        Test step.
        
        Args:
            batch: Batch of (features, targets)
            batch_idx: Batch index
            
        Returns:
            Loss value
        """
        x, y = batch
        y_hat = self.forward(x)
        loss = self.criterion(y_hat, y)
        
        # Get predictions (class indices)
        preds = torch.argmax(y_hat, dim=1)
        
        # Update metrics
        self.test_accuracy(preds, y)
        self.test_f1(preds, y)
        self.test_precision(preds, y)
        self.test_recall(preds, y)
        
        # Log metrics
        self.log("test_loss", loss, on_step=False, on_epoch=True, logger=True)
        self.log("test_acc", self.test_accuracy, on_step=False, on_epoch=True, logger=True)
        self.log("test_f1", self.test_f1, on_step=False, on_epoch=True, logger=True)
        self.log("test_precision", self.test_precision, on_step=False, on_epoch=True, logger=True)
        self.log("test_recall", self.test_recall, on_step=False, on_epoch=True, logger=True)
        
        return loss
    
    def configure_optimizers(self) -> dict[str, Any]:
        """
        Configure optimizer and learning rate scheduler.
        
        Returns:
            Dictionary with optimizer and scheduler configuration
        """
        # Optimizer will be set by Lightning CLI from config
        # This is a fallback if not provided via CLI
        optimizer = torch.optim.Adam(
            self.parameters(),
            lr=self.lr,
            weight_decay=self.weight_decay,
        )
        
        # Scheduler configuration
        if self.lr_scheduler_factor is not None and self.lr_scheduler_patience is not None:
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer,
                mode='min',
                factor=self.lr_scheduler_factor,
                patience=self.lr_scheduler_patience,
                verbose=True,
            )
            return {
                "optimizer": optimizer,
                "lr_scheduler": {
                    "scheduler": scheduler,
                    "monitor": "val_loss",
                },
            }
        
        return {"optimizer": optimizer}
    
    def get_model(self) -> ClassificationModel:
        """Get the underlying model."""
        return self.model

