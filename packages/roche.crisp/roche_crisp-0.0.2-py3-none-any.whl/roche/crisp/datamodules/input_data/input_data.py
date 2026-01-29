"""Class for handling input data."""

from pathlib import Path

import imageio.v3 as imageio
import numpy as np


class InputData:
    """Class for handling input data."""

    @staticmethod
    def load(data_path: str) -> np.ndarray:
        """Load data from a file.

        It supports .png, .tiff, .npy and .tif data formats.

        Parameters
        ----------
        data_path : str
            Path to the data file.

        Returns
        -------
        np.ndarray
            The data as a numpy array.

        Raises
        ------
        ValueError
            If the file type is not supported.
        FileNotFoundError
            If the specified file is not found.
        """
        valid_data_formats = [".png", ".tiff", ".tif", ".npy"]
        path = Path(data_path)
        path_suffix = path.suffix.lower()

        if path_suffix not in valid_data_formats:
            raise ValueError(
                f"Invalid file type: {path.suffix}. "
                f"Only {', '.join(valid_data_formats)} data are supported."
            )

        try:
            return np.load(path) if path_suffix == ".npy" else imageio.imread(data_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {data_path}")
