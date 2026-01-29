"""
CPH Classification - A generic, reusable PyTorch Lightning pipeline for classification tasks.

This package provides a config-driven classification training framework that can be
used for any tabular classification problem by simply providing a YAML configuration file.
"""

__version__ = "0.1.0"
__author__ = "chandra"
__email__ = "chandra385123@gmail.com"

from cph_classification.classification import (
    ModelModuleCLS,
    DataModuleCLS,
    ClassificationModel,
    ClassificationDataset,
    ONNXExportCallback,
)

__all__ = [
    "ModelModuleCLS",
    "DataModuleCLS",
    "ClassificationModel",
    "ClassificationDataset",
    "ONNXExportCallback",
]
