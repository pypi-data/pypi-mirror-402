"""Interface for cell detection implementations.

Every nuclei detection module should implement an interface that gets a list of numpy
np.uint8 images, and supports both computing the segmentation mask where pixels contain
the classification categories, and computing the list of nuclei boundaries and
categories. Since the mask can be computed from the nuclei detections without any loss
of information, but not the other way around, this provides a default implementation for
get_mask.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

import numpy as np

from .nuclei_information import NucleiInformation


class NucleiDetectionBase(ABC):
    """Base abstract class for nuclei detection."""

    def __init__(self):
        """Initialize the NucleiDetectionBase class with necessary attributes."""
        self.output_logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_nuclei(self, images: List[np.ndarray]) -> List[List[NucleiInformation]]:
        """Detect nuclei and return information about every nucleus separetely.

        Parameters
        ----------
        images : List[numpy.ndarray]
            A list of numpy np.uint8 images.

        Returns
        -------
        List[List[NucleiInformation]]
            A list of nuclei detections, for every input image.
        """
        pass

    @abstractmethod
    def get_mask(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """Return segmentation mask.

        Every pixel in the mask contains the category of the cell it belongs to.
        Note: Overlapping nuclei are NOT handled here,
        this returns semantic segmentation and not instance segmentation

        Parameters
        ----------
        images : List[numpy.ndarray]
            A list of numpy np.uint8 images.

        Returns
        -------
        List[numpy.ndarray]
            A list with a nuclei semantic segmentation mask for every input image.
        """
        pass
