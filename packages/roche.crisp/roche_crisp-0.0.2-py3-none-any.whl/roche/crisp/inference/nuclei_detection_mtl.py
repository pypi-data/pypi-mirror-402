"""An implementation of NucleiDetectionBase for multi-task classification module."""

from typing import List

import cv2
import numpy as np
from skimage.measure import label, regionprops

from . import mtl_inference
from .nuclei_detection_base import NucleiDetectionBase
from .nuclei_information import NucleiInformation


class NucleiDetectionMTL(NucleiDetectionBase):
    """Wrapper for MTL based nuclei detection-classification model.

    Model classifies nucleus into tumor, lymphocyte & other,
    and generates semantic masks.

    Attributes
    ----------
    model_checkpoint : str
        Path to model checkpoint.
    batch_size : int
        Number of samples to process in one batch.
    """

    def __init__(self, model_checkpoint: str, batch_size: int):
        """Initialize instance of the class."""
        super().__init__()
        self.model_checkpoint = model_checkpoint
        self.batch_size = batch_size

    def get_mask(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """Return segmentation mask.

        Every pixel in the mask contains the category of the cell it belongs to.
        This returns semantic segmentation

        Parameters
        ----------
        images : List[np.ndarray]
            A list of numpy np.uint8 images.

        Returns
        -------
        List[np.ndarray]
            A list with a nuclei semantic segmentation mask for every input image.
        """
        return mtl_inference.run_inference(
            images, self.model_checkpoint, self.batch_size
        )

    def get_nuclei(self, images: List[np.ndarray]) -> List[List[NucleiInformation]]:
        """Detect nuclei and return information about every nucleus separetely.

        Runs the mtl inference for detecting nuclei,
        and for every input image, converts the
        nuclei mask to a list of NucleiInformation.

        Parameters
        ----------
        images : List[np.ndarray]
            A list of numpy np.uint8 images.

        Returns
        -------
        List[List[NucleiInformation]]
            A list of nuclei detections, for every input image.
        """
        batch_masks = mtl_inference.run_inference(
            images, self.model_checkpoint, self.batch_size
        )
        nuclei_information = []
        for mask in batch_masks:
            image_nuclei_information = []
            labels = label(mask, connectivity=1)
            regions = regionprops(labels)
            for i, region in enumerate(regions):
                y, x = region.centroid
                min_row, min_col, max_row, max_col = region.bbox
                object_mask = np.uint8(
                    labels[min_row:max_row, min_col:max_col] == i + 1
                )
                local_coords, _ = cv2.findContours(
                    object_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
                )
                boundary = local_coords[0] + [min_col, min_row]
                image_nuclei_information.append(
                    NucleiInformation(
                        boundary=boundary, category=-1, center=(round(x), round(y))
                    )
                )
            nuclei_information.append(image_nuclei_information)
        return nuclei_information
