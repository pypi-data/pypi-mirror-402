"""Data handling and preparation modules for cell segmentation and detection tasks.

It provides PyTorch Lightning DataModules and PyTorch Datasets
designed to handle data loading, transformations, and batching for training
and evaluating cell segmentation models.

Key Components:

- `BaseDataModule`: An abstract base class for all data modules.
- `BaseDataset`: An abstract base class for datasets.
- `CellDataModule`: A DataModule for general cell image datasets.
- `CellPoseDataModule`: A DataModule specifically for CellPose-style datasets.
"""

from .base_datamodule import BaseDataModule
from .base_dataset import BaseDataset
from .cellpose_dataset import CellposeDataset
from .custom_datamodules import (
    CellDataModule,
    CellPoseDataModule,
)
from .input_data import InputData

__all__ = [
    "CellPoseDataModule",
    "CellDataModule",
    "BaseDataModule",
    "BaseDataset",
    "CellposeDataset",
    "InputData",
]
