"""An implementation of NucleiDetectionBase for the STUDIO cell detection modules.

This assumes the STUDIO API is installed.
"""

from typing import List

import cv2
import numpy as np

from .nuclei_detection_base import NucleiDetectionBase
from .nuclei_information import NucleiInformation


class NucleiDetectionStudio(NucleiDetectionBase):
    """Wrapper for STUDIO nuclei detection.

    Returns the results in a common format.

    Attributes
    ----------
    deployer : Any
        The STUDIO deployer object. Implements "deploy_image_batch".
    """

    def __init__(self, deployer):
        """Instantiate.

        Attributes
        ----------
        deployer : Any
            The STUDIO deployer object. Implements "deploy_image_batch".
        """
        super().__init__()
        self.deployer = deployer

    def get_nuclei(self, images: List[np.ndarray]) -> List[List[NucleiInformation]]:
        """Detect nuclei and return information about every nucleus separetely.

        Runs the
        STUDIO API for detecting nuclei, and for every input image, converts the
        detections to a list of NucleiInformation.

        Parameters
        ----------
        images : List[np.ndarray]
            A list of numpy np.uint8 images.

        Returns
        -------
        List[List[NucleiInformation]]
            A list of nuclei detections, for every input image.
        """
        batch_detections = self.deployer.deploy_image_batch(rgb_images=images)
        nuclei_information = []
        for image_detections in batch_detections:
            image_nuclei_information = []
            for detection in image_detections["polygons"]:
                x, y = detection["center"]
                boundary = np.int32(detection["polygon"])
                # # change output format of boundary points
                # # as per opencv format of (num_points, 1, 2) for storing contours
                boundary = np.swapaxes(boundary, 0, 1)

                image_nuclei_information.append(
                    NucleiInformation(boundary=boundary, category=-1, center=(x, y))
                )
            nuclei_information.append(image_nuclei_information)
        return nuclei_information

    def get_mask(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """Return segmentation mask.

        Every pixel in the mask contains the category of the cell it belongs to.
        Note: Overlapping nuclei are NOT handled here,
        this returns semantic segmentation and not instance segmentation

        Parameters
        ----------
        images : List[np.ndarray]
            A list of numpy np.uint8 images.

        Returns
        -------
        List[np.ndarray]
            A list of nuclei semantic segmentation mask for every input image.
        """
        masks = []
        detections = self.get_nuclei(images)
        for image, image_detections in zip(images, detections):
            mask = np.zeros(shape=image.shape, dtype=np.uint8)
            for detection in image_detections:
                cv2.drawContours(mask, [detection.boundary], -1, detection.category, -1)
            masks.append(mask)
        return masks
