"""Pytorch lightning based generic data module for preparing dataloaders."""

from typing import Any, Dict, Literal

import albumentations as A
import lightning as L
from torch.utils.data import DataLoader


class BaseDataModule(L.LightningDataModule):
    """Base class for data preparation.

    All other modules should inherit from this class.
    """

    def __init__(self, **kwargs) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed through configs/datamodule
            yaml.
        """
        super().__init__()
        for k, v in kwargs.items():
            setattr(self, k, v)

    def setup(self, stage: Literal["fit", "val", "test", "predict"]) -> None:
        """Set up datasets for training and validation.

        Parameters
        ----------
        stage : str
            Current stage of the training process.
        """
        transforms: Dict[str, Dict[str, Any]] = getattr(self, "transforms", {})
        for key in ["train_tsfms", "val_tsfms", "test_tsfms"]:
            trans = transforms.get(key)
            if trans:
                setattr(self, key, A.Compose(trans.values()))

    def train_dataloader(self) -> DataLoader:
        """Prepare dataloader for training.

        Returns
        -------
            torch dataloader object
        """
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=True,
            pin_memory=True,
            persistent_workers=True,
            collate_fn=self.collate_fn if hasattr(self, "collate_fn") else None,
            drop_last=True,
        )

    def val_dataloader(self) -> DataLoader:
        """Prepare dataloader for validation.

        Returns
        -------
            torch dataloader object
        """
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False,
            pin_memory=False,
            persistent_workers=True,
            collate_fn=self.collate_fn if hasattr(self, "collate_fn") else None,
        )

    def test_dataloader(self) -> DataLoader:
        """Prepare dataloader for testing.

        Returns
        -------
            torch dataloader object
        """
        return DataLoader(
            dataset=self.test_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False,
            pin_memory=False,
            collate_fn=self.collate_fn if hasattr(self, "collate_fn") else None,
        )

    def predict_dataloader(self) -> DataLoader:
        """Prepare dataloader for prediction.

        Returns
        -------
            torch dataloader object
        """
        return DataLoader(
            dataset=self.test_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False,
            pin_memory=False,
            collate_fn=self.collate_fn if hasattr(self, "collate_fn") else None,
        )
