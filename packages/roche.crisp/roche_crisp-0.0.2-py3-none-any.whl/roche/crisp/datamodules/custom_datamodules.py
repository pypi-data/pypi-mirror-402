"""Pytorch lightning based custom data module for various use cases.

Must inherit Base DataModule.
"""

from typing import List, Literal, Tuple

import numpy as np
from torch.utils.data import default_collate

from roche.crisp.datamodules.base_datamodule import BaseDataModule
from roche.crisp.datamodules.base_dataset import BaseDataset
from roche.crisp.datamodules.cellpose_dataset import CellposeDataset


class CellDataModule(BaseDataModule):
    """Data preparation module for cell based models."""

    def __init__(self, **kwargs) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed through configs/datamodule
            yaml.
        """
        super().__init__(**kwargs)

    def setup(self, stage: Literal["fit", "val", "test", "predict"]) -> None:
        """Set up datasets for training, validation and testing.

        Parameters
        ----------
        stage : str
            Current stage of the training process.
        """
        super().setup(stage)
        if stage == "fit":
            self.train_dataset = BaseDataset("train", self.train_data, self.train_tsfms)
            self.val_dataset = BaseDataset("val", self.val_data, self.val_tsfms)
        if stage in ["test", "predict"]:
            self.test_dataset = BaseDataset(
                stage,
                self.test_data,
                self.val_tsfms,
                self.metadata_path,
                self.caption_columns,
            )


class CellPoseDataModule(BaseDataModule):
    """Data preparation module for cellpose model."""

    def __init__(self, **kwargs) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed through configs/datamodule
            yaml.
        """
        super().__init__(**kwargs)

    def setup(self, stage: Literal["fit", "val", "test", "predict"]) -> None:
        """Set up datasets for training, validation and testing.

        Parameters
        ----------
        stage : str
            Current stage of the training process.
        """
        super().setup(stage)
        # Create a dictionary of kwargs to pass to CellposeDataset
        dataset_kwargs = {
            "diam_mean": self.diam_mean,
            "diameter": self.diameter,
            "use_rgb": self.use_rgb,
        }
        if stage == "fit":
            self.train_dataset = CellposeDataset(
                "train",
                self.train_data,
                self.train_tsfms,
                self.segmentation_type,
                **dataset_kwargs,
            )
            self.val_dataset = CellposeDataset(
                "val",
                self.val_data,
                self.val_tsfms,
                self.segmentation_type,
                **dataset_kwargs,
            )
        if stage == "test":
            self.test_dataset = CellposeDataset(
                "test",
                self.test_data,
                self.val_tsfms,
                self.segmentation_type,
                **dataset_kwargs,
            )

        if stage == "predict":
            self.test_dataset = CellposeDataset(
                "predict",
                self.test_data,
                self.val_tsfms,
                self.segmentation_type,
                **dataset_kwargs,
            )

    def collate_fn(
        self, batch: List[Tuple[np.ndarray, np.ndarray]]
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Collate function for the dataset.

        Parameters
        ----------
        batch : list
            List of batch items.

        Returns
        -------
        list
            List of collated batch items.
        """
        batch = list(filter(lambda x: x is not None, batch))
        return default_collate(batch) if len(batch) > 0 else []
