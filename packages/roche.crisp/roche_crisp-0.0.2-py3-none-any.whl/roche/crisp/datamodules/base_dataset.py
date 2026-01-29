"""Custom pytorch dataset module."""

import logging
import os
from typing import List, Literal, Optional

import albumentations as A
import numpy as np
import pandas as pd
from lightning.pytorch.utilities import rank_zero_only
from torch.utils.data.dataset import Dataset

from roche.crisp.datamodules.input_data import InputData
from roche.crisp.utils import common_utils


class BaseDataset(Dataset):
    """Dataset class for preparing data for training."""

    def __init__(
        self,
        mode: Literal["train", "val", "test", "predict"],
        data_path: str,
        transform: Optional[A.Compose] = None,
        metadata_path: Optional[str] = None,
        caption_columns: Optional[List[str]] = None,
    ) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        mode : str
            Specifies the data requirement for different stages: train, val,
            test, or predict.
            For 'predict' mode, no masks are needed as it is for inference.
        data_path : Path
            Path to csv file containing first column as path to images,
            second column as path to groundtruth masks and
            subsequent columns containing path to any derived masks
        transform : albumentations.Compose, optional
            Compose object with transformations to be applied, by default None
        metadata_path : str, optional
            Path to csv file containing metadata with image identifiers, by default None
        caption_columns : list, optional
            List of column names to extract from metadata for captions, by default None
        """
        super().__init__()
        self.mode = mode
        self.data_path = data_path
        self.transform = transform
        self.metadata_path = metadata_path
        self.caption_columns = caption_columns or []
        self.metadata_df = None

        self.image_mask_pair = common_utils.extract_image_masks_from_csv(self.data_path)

        if rank_zero_only.rank == 0:
            logging.info(f"columns: {self.caption_columns}")
            logging.info(f"metadata_path: {self.metadata_path}")

            # Load metadata if provided
            if self.metadata_path is not None:
                try:
                    self.metadata_df = pd.read_csv(self.metadata_path)
                except FileNotFoundError:
                    logging.error(
                        f"Metadata CSV not found at {self.metadata_path}. "
                        "Proceeding without metadata."
                    )
                    self.metadata_df = None
                else:
                    logging.info(
                        f"Loaded metadata from {self.metadata_path} "
                        f"with columns: {list(self.metadata_df.columns)}"
                    )
                    self._validate_metadata()

            logging.info(f"Number of {mode} images: {len(self.image_mask_pair)}")

    def __len__(self) -> int:
        """Return size of the dataset.

        Returns
        -------
        int
            Dataset length
        """
        return len(self.image_mask_pair)

    def _validate_metadata(self) -> None:
        """Validate metadata consistency with caption columns and images."""
        if self.metadata_df is None:
            return

        # Validate caption columns exist
        if self.caption_columns:
            missing_cols = set(col.lower() for col in self.caption_columns) - set(
                col.lower() for col in self.metadata_df.columns
            )
            if missing_cols:
                logging.warning(f"Missing columns in metadata: {missing_cols}")

    def _extract_caption(self, image_name: str) -> dict:
        """Extract caption from metadata for given image name.

        Parameters
        ----------
        image_name : str
            Name of the image file

        Returns
        -------
        dict
            Dictionary containing caption data
        """
        if self.metadata_df is None or not self.caption_columns:
            return {"Image": str(image_name)}

        # Try to match by first column (contains, case-insensitive)
        row = self.metadata_df[
            self.metadata_df.iloc[:, 0]
            .astype(str)
            .str.lower()
            .str.contains(image_name.lower(), na=False, regex=False)
        ]

        # Fall back to exact match on all columns (case-insensitive)
        if row.empty:
            for col in self.metadata_df.columns:
                row = self.metadata_df[
                    self.metadata_df[col].astype(str).str.lower() == image_name.lower()
                ]
                if not row.empty:
                    break

        if row.empty:
            return {"Image": str(image_name)}

        # Build caption dictionary
        caption = {"Image": str(image_name)}
        for col in self.caption_columns:
            if col.lower() in [c.lower() for c in self.metadata_df.columns]:
                value = row[col].values[0]
                caption[col] = "NA" if pd.isna(value) else str(value)
            else:
                caption[col] = "NA"

        return caption

    def __getitem__(self, index) -> tuple:
        """Fetch data at given index.

        Parameters
        ----------
        index : int
            index of the sample in the dataset.

        Returns
        -------
        tuple
            Non-predict mode without transform: (image, masks_list, caption)
            Non-predict mode with transform: (image, transformed_image, mask, caption)
            Predict mode: (image, caption)
        """
        image_name = os.path.basename(self.image_mask_pair[index][0])
        image = InputData.load(data_path=self.image_mask_pair[index][0])

        # Convert image to float32 if it's uint16 to avoid type promotion issues
        if isinstance(image, np.ndarray) and image.dtype == np.uint16:
            image = image.astype(np.float32)

        # Extract caption from metadata if available
        caption = self._extract_caption(image_name)

        if self.mode != "predict":
            derived_masks = []
            for i in range(1, len(self.image_mask_pair[index])):
                mask = InputData.load(data_path=self.image_mask_pair[index][i])
                # Convert masks based on their data type
                if isinstance(mask, np.ndarray):
                    if mask.dtype in [np.uint8, np.uint16, np.uint32, np.uint64]:
                        # Convert unsigned integer masks to int32 for compatibility
                        mask = mask.astype(np.int32)
                    elif mask.dtype == np.float64:
                        # Convert double precision to single precision if needed
                        mask = mask.astype(np.float32)
                derived_masks.append(mask)

            if self.transform is None:
                return image, derived_masks, caption

            augmented = self.transform(image=image, masks=derived_masks)
            return image, augmented["image"], augmented["masks"][0], caption
        else:
            if self.transform is None:
                return image, caption
            return self.transform(image=image)["image"], caption
