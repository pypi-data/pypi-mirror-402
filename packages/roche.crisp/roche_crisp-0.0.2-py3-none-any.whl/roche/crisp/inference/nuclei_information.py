"""A dataclass for containing properties of detected nucleus."""

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class NucleiInformation:
    """Class for storing information about nucleus."""

    boundary: np.ndarray
    category: int
    center: Tuple[int, int]

    def __init__(
        self, boundary: np.ndarray, category: int, center: Tuple[int, int]
    ) -> None:
        """Initialize the NucleiInformation class with the necessary attributes.

        Parameters
        ----------
        boundary : numpy.ndarray
            The x, y coordinates of the nucleus boundary. Has the shape
            (number_of_points x 1 x 2) (common OpenCV format for storing contours)
        category : int
            The category index of the nucleus, -1 if unclassified.
        center : Tuple[int, int]
            The x, y coordinates of the nucleus center.

        Raises
        ------
        ValueError
            - If input `boundary` has incorrect shape
        """
        self.boundary = boundary
        self.category = category
        self.center = center

        error_message = "Input `boundary` has incorrect shape, must have shape "
        """`(x, 1, 2)`, where `x` is the number of points for a boundary contour."""

        if self.boundary.ndim != 3 or self.boundary.shape[1:] != (1, 2):
            raise ValueError(error_message)
