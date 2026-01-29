"""Module for normalization utilities."""

import logging
from pathlib import Path
from typing import List

import imageio.v3 as imageio
import numpy as np
import torch
from tqdm import tqdm

output_logger = logging.getLogger(__name__)


def compute_mean_std(image_paths: List[str], save_file_dir: Path):
    """Compute mean and standard deviation of rgb image batch.

    Parameters
    ----------
    image_paths : List[str]
        List of paths to the images
    save_file_dir : pathlib.Path
        Path to save computed mean and std deviation values
    """
    total_sum = np.zeros(3)  # total sum of all pixel values in each channel
    total_square_sum = np.zeros(3)
    num_pixel = 0  # total num of all pixels
    output_logger.info(f"Computing mean and std for {len(image_paths)} images...")
    for img_name in tqdm(image_paths):
        img = imageio.imread(img_name)
        if len(img.shape) != 3 or img.shape[2] < 3:
            continue
        img = img[:, :, :3].astype(int)
        total_sum += img.sum(axis=(0, 1))
        total_square_sum += (img**2).sum(axis=(0, 1))
        num_pixel += img.shape[0] * img.shape[1]

    # compute the mean values of each channel
    mean_values = total_sum / num_pixel

    # compute the standard deviation
    std_values = np.sqrt(total_square_sum / num_pixel - mean_values**2)

    # normalization
    mean_values = mean_values / 255
    std_values = std_values / 255

    np.save(
        Path(save_file_dir).joinpath("train_normalization.npy"),
        np.array([mean_values, std_values]),
    )
    output_logger.info(f"Done! Mean values: {mean_values}, Std values: {std_values}")


class Normalization:
    """Class that handles and calculates mean and std for multiple datasets."""

    files: List[Path] = []
    __mean: torch.Tensor = np.zeros((3,))
    __std: torch.Tensor = np.zeros((3,))

    def __init__(self, paths: List[Path]) -> None:
        """Init class.

        Parameters
        ----------
        paths : List[Path]
            List of paths to files where are stored
            mean and std for datasets in numpy format
        """
        self.add_normalizations(paths)

    def add_normalizations(self, paths: List[Path]) -> None:
        """Add list of files with normalization data.

        Add list of files with normalization data to calculate normalizations
        factor for multiple datasets.

        Parameters
        ----------
        paths : List[Path]
            List of files with normalization data in numpy format.
        """
        for file in paths:
            self.add_normalization(file)

    def add_normalization(self, file_path: Path):
        """Add single file to with normalization.

        Add single file to with normalization data to calculate normalization
        factors for multiple datasets.

        Parameters
        ----------
        file_path : Path
            Path to file with normalization data in numpy format.
            Array of sie (3,)
        """
        self.files.append(file_path)
        norm = np.load(file_path)
        if len(self.files) <= 1:
            self.__mean = norm[0]
        else:
            self.__mean += norm[0]

        if len(self.files) <= 1:
            self.__std = norm[1]
        else:
            self.__std += norm[1]

    @property
    def mean(self):
        """Computed property returns mean of means for all datasets.

        Returns
        -------
        3 elements numpy array
            array with mean

        Raises
        ------
        ValueError
            Error thrown when no files were not added
        """
        if len(self.files) < 1:
            raise ValueError("Ther was no normalization data provided")
        return self.__mean / len(self.files)

    @property
    def mean_torch(self, convert_to_cuda: bool = False):
        """Convert mean numpy array to torch.Tensor.

        Parameters
        ----------
        convert_to_cuda : bool, optional
            Determine if tensor will be converted to cuda,
            by default False

        Returns
        -------
        torch.Tensor
            Tensor with mean values for all datasets.
        """
        mean_t = torch.from_numpy(self.mean)
        if convert_to_cuda:
            return mean_t.cuda()
        return mean_t

    @property
    def std(self):
        """Computed porperty returns mean std of all datasets.

        Returns
        -------
        numpy array
            mean of std for of all datasets.

        Raises
        ------
        ValueError
            Raise exception when no files were added.
        """
        if len(self.files) < 1:
            raise ValueError("Ther was no normalization data provided")
        return self.__std / len(self.files)

    @property
    def std_torch(self, convert_to_cuda: bool = False):
        """Convert std numpy array to torch.Tensor.

        Parameters
        ----------
        convert_to_cuda : bool, optional
            Determine if tensor will be converted to cuda,
            by default False

        Returns
        -------
        torch.Tensor
            Tensor with std values for all datasets.
        """
        std_t = torch.from_numpy(self.std)
        if convert_to_cuda:
            return std_t.cuda()
        return std_t
