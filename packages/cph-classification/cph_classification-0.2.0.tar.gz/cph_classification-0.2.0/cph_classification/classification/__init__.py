"""
Classification module for generic classification tasks.

This module provides reusable components for training classification models
using PyTorch Lightning. All components are fully config-driven and can
be used for any classification task by simply changing the YAML configuration.
"""

from cph_classification.classification.modelmodule import ModelModuleCLS
from cph_classification.classification.datamodule import DataModuleCLS
from cph_classification.classification.modelfactory import ClassificationModel
from cph_classification.classification.dataset import ClassificationDataset
from cph_classification.classification.callbacks import ONNXExportCallback

__all__ = [
    "ModelModuleCLS",
    "DataModuleCLS",
    "ClassificationModel",
    "ClassificationDataset",
    "ONNXExportCallback",
]

