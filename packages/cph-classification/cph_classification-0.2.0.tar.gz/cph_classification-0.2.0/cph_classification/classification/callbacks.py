"""
ONNX export callback for PyTorch Lightning.

This module provides a callback to export trained models to ONNX format
for production deployment. Reusable for both regression and classification.
"""

import logging
from pathlib import Path
from typing import Optional
import torch
import lightning as L

# Set up logger
logger = logging.getLogger(__name__)


class ONNXExportCallback(L.pytorch.callbacks.Callback):
    """
    Callback to export model to ONNX format after training.
    
    The callback exports the model after training completes, using
    the input dimension from the datamodule.
    
    Args:
        output_dir: Directory to save ONNX model
        model_name: Name for the saved model file
        input_dim: Input dimension (if None, will try to get from datamodule)
    """
    
    def __init__(
        self,
        output_dir: str = "models",
        model_name: str = "model",
        input_dim: Optional[int] = None,
    ):
        """
        Initialize the ONNX export callback.
        
        Args:
            output_dir: Output directory
            model_name: Model name
            input_dim: Input dimension (auto-detected if None)
        """
        super().__init__()
        self.output_dir = Path(output_dir)
        self.model_name = model_name
        self.input_dim = input_dim
    
    def on_train_end(self, trainer: L.Trainer, pl_module: L.LightningModule) -> None:
        """
        Export model to ONNX format after training ends.
        
        Args:
            trainer: Lightning trainer
            pl_module: Lightning module
        """
        # Get input dimension
        input_dim = self.input_dim
        if input_dim is None:
            # Try to get from datamodule
            if hasattr(trainer.datamodule, 'get_input_dim'):
                input_dim = trainer.datamodule.get_input_dim()
            elif hasattr(trainer.datamodule, 'input_dim'):
                input_dim = trainer.datamodule.input_dim
            else:
                # Try to get from model
                if hasattr(pl_module.model, 'get_input_dim'):
                    input_dim = pl_module.model.get_input_dim()
                elif hasattr(pl_module.model, 'input_dim'):
                    input_dim = pl_module.model.input_dim
                else:
                    raise ValueError(
                        "Could not determine input_dim. Please provide it in callback init_args."
                    )
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the underlying PyTorch model
        model = pl_module.model
        model.eval()
        
        # Create dummy input
        dummy_input = torch.randn(1, input_dim)
        
        # Export to ONNX
        onnx_path = self.output_dir / f"{self.model_name}.onnx"
        
        try:
            torch.onnx.export(
                model,
                dummy_input,
                str(onnx_path),
                export_params=True,
                opset_version=11,
                do_constant_folding=True,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={
                    'input': {0: 'batch_size'},
                    'output': {0: 'batch_size'}
                },
            )
            
            # Log success using Python's logging module
            success_msg = f"Model exported to ONNX: {onnx_path}"
            logger.info(success_msg)
            print(f"✓ {success_msg}")
        
        except Exception as e:
            # Log error using Python's logging module
            error_msg = f"Failed to export model to ONNX: {e}"
            logger.error(error_msg, exc_info=True)
            print(f"✗ {error_msg}")
            raise

