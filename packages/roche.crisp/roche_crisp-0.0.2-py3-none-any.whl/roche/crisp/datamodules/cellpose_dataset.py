"""Custom cellpose pytorch dataset."""

from pathlib import Path
from typing import Dict, Literal, Optional

import albumentations as A
import numpy as np

from roche.crisp.datamodules.base_dataset import BaseDataset
from roche.crisp.datamodules.input_data import InputData
from roche.crisp.utils import common_utils
from roche.crisp.utils.transforms import (
    convert_image,
    normalize_img,
    random_rotate_and_resize,
    resize_image,
)


class CellposeDataset(BaseDataset):
    """Dataset class for preparing data for cellpose training."""

    def __init__(
        self,
        mode: Literal["train", "val", "test", "predict"],
        data_path: str = None,
        image_arrays: Optional[list[np.ndarray]] = None,
        transform: Optional[A.Compose] = None,
        segmentation_type: Optional[Literal["instance", "semantic"]] = "instance",
        **kwargs: Optional[Dict],
    ) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        mode : Literal["train", "val", "test", "predict"]
            Specifies the data requirement for different stages: train, val,
            test, or predict.
            For 'predict' mode, no masks are needed as it is for inference.
        data_path : str
            The path to the directory containing the input images and labels.
        image_arrays : Optional[list[np.ndarray]], optional
            The list of input images.
        transform : Optional[albumentations.Compose], optional
            A composition of Albumentations transforms to apply to the input
            images and labels. If None, no transforms are applied.
        segmentation_type : Optional[Literal["instance", "semantic"]], optional
            The type of segmentation to use.
        kwargs : Optional[Dict], optional
            Additional keyword arguments to pass to the dataset.
        """
        super().__init__(mode, data_path, transform)
        self.image_arrays = image_arrays
        self.segmentation_type = segmentation_type
        for k, v in kwargs.items():
            setattr(self, k, v)

    def _process_image(
        self,
        image: np.ndarray,
        channels: Optional[list] = None,
    ) -> np.ndarray:
        """Process image with standard transformations.

        Parameters
        ----------
        image : np.ndarray
            Input image array of shape (1, height, width, 3)
        channels : Optional[list]
            Channel configuration for conversion

        Returns
        -------
        np.ndarray
            Processed image
        """
        # Convert image to appropriate format
        converted_img = convert_image(
            image,
            channels=channels,
            channel_axis=3,
            z_axis=0,  # (512, 512, ch)
            do_3D=False,
            normalize=False,
            invert=False,
            nchan=3 if self.use_rgb else 2,  # 2 for grayscale, 3 for rgb
        )

        if converted_img.ndim < 4:
            converted_img = converted_img[np.newaxis, ...]  # e.g (1, 512, 512, ch)

        converted_img = normalize_img(converted_img, invert=False)  # (1, 512, 512, ch)

        return converted_img

    def __getitem__(self, index: int) -> Dict[str, np.ndarray]:
        """Fetch data at given index.

        Parameters
        ----------
        index : int
            index of the sample in the dataset.

        Returns
        -------
        Dict[str, np.ndarray]
            Dictionary containing processed image and associated data
        """
        # load the input image, shape: (height, width, 3)
        if self.mode == "predict" and self.image_arrays is not None:
            image = self.image_arrays[index]
        else:
            image = InputData.load(data_path=self.image_mask_pair[index][0])

        output = {}

        # if the dataset is in "train" or "val" mode, load the flow file
        # flows: (3, height, width) or (4, height, width)
        # chan 0 - instance mask, chan 1 - semantic mask (optional)
        # chan 2 - horiz gradient, chan 3 - vert gradient
        if self.mode in ["train", "val"]:
            flows = InputData.load(data_path=self.image_mask_pair[index][1])
            out = self.transform(image=image, masks=[np.moveaxis(flows, 0, 2)])

            image = np.asarray(out["image"])
            mask0 = np.asarray(out["masks"][0])

            image = np.moveaxis(image, 0, -1)
            flows = np.moveaxis(mask0, 2, 0)
            instance_label = flows[0]

            if self.segmentation_type == "semantic":
                semantic_label = flows[1].copy()
                # convert semantic mask to binary mask
                flows[1] = (flows[1] > 0).astype(np.uint8)

            # Process image for training
            image = np.moveaxis(image, 2, 0)
            # if rescale is enabled, rescale images to have same cell diameter,
            # refer: https://cellpose.readthedocs.io/en/latest/settings.html
            cell_diameter = common_utils.get_diameters(flows[0])
            # rescale factor to rescale image to have same cell diameter
            rescale_factor = cell_diameter / self.diameter

            if self.mode == "train":
                # perform random rotation and resize
                image, flows = random_rotate_and_resize(
                    [image],
                    Y=[flows],
                    rescale=[rescale_factor],
                    scale_range=0.5,
                    xy=(image.shape[1], image.shape[2]),
                )
                image = np.moveaxis(image, 1, -1)  # (height, width, 3)
            else:
                image = np.moveaxis(image, 0, -1)  # (height, width, 3)
                image = image[np.newaxis, ...]  # (1, height, width, 3)

            # Process final image
            processed_image = self._process_image(
                image, channels=[0, 0] if not self.use_rgb else None
            )  # (1, height, width, ch)

            # image shape: (1, height, width, ch)
            # flows shape: (3, height, width)  # includes instance label
            output.update(
                {
                    "image": np.moveaxis(np.squeeze(processed_image), -1, 0),
                    "flows": np.squeeze(flows),
                    "original_image": np.squeeze(image),
                }
            )

        elif self.mode == "test":
            # otherwise, load the mask file
            # label: (height, width)
            label = InputData.load(self.image_mask_pair[index][1]).copy()
            if self.transform is not None:
                if self.segmentation_type == "semantic":
                    out = self.transform(image=image, masks=[label[0], label[1]])
                    image = out["image"]
                    label = out["masks"]
                else:
                    out = self.transform(image=image, masks=[label])
                    image = out["image"]
                    label = out["mask"]

            image = np.asarray(image)

            if self.segmentation_type == "semantic":
                instance_label = np.asarray(label[0]).copy()
                semantic_label = np.asarray(label[1]).copy()
                # convert semantic mask to binary mask for metrics computation
                label[1] = (label[1] > 0).astype(np.uint8)
            else:
                label = np.asarray(label)
                instance_label = label.copy()

            # Resize image
            # image = np.moveaxis(image, 0, -1)  # (height, width, 3)
            original_image = image.copy()
            image = np.expand_dims(image, axis=0)  # e.g (1, 512, 512, 3)
            rescale = self.diam_mean / self.diameter
            image = resize_image(image, rsz=rescale)  # e.g (1, 224, 224, 3)

            # Process final image
            processed_image = self._process_image(
                image, channels=[0, 0] if not self.use_rgb else None
            )  # (1, height, width, ch)

            # image shape: (1, height, width, ch)
            # label shape: (height, width)
            output.update(
                {
                    "image": np.squeeze(
                        np.moveaxis(processed_image, -1, 1)
                    ),  # (ch, height, width)
                    "instance_label": instance_label,  # (height, width)
                    "original_image": np.squeeze(original_image),  # (height, width, 3)
                }
            )

            if self.segmentation_type == "semantic":
                output.update(
                    {
                        "binary_label": label[1].astype(np.uint8),
                        "semantic_label": semantic_label.astype(np.uint8),
                    }
                )

        elif self.mode == "predict":
            if self.transform is not None:
                out = self.transform(image=image)
                image = out["image"]
            else:
                image = np.asarray(image)

            # Resize image
            # image = np.moveaxis(image, 0, -1)  # (height, width, 3)
            original_image = image.copy()
            image = np.expand_dims(image, axis=0)  # e.g (1, 512, 512, 3)
            rescale = self.diam_mean / self.diameter
            image = resize_image(image, rsz=rescale)  # e.g (1, 224, 224, 3)

            # Process final image
            processed_image = self._process_image(
                image, channels=[0, 0] if not self.use_rgb else None
            )  # (1, height, width, ch)

            # image shape: (1, height, width, ch)
            # label shape: (height, width)
            output.update(
                {
                    "image": np.squeeze(
                        np.moveaxis(processed_image, -1, 1)
                    ),  # (ch, height, width)
                    "original_image": np.squeeze(original_image),  # (height, width, 3)
                    "filename": Path(self.image_mask_pair[index][0]).name,
                    "index": index,
                }
            )

        return output
