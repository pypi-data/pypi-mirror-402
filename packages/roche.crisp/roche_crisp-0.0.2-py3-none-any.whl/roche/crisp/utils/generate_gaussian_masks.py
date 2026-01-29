"""Generate Gaussian masks from point masks in a dataset.

This module provides functionality to read a CSV file containing paths to point masks,
generate a Gaussian mask for each point mask using the `point2gauss` function, and save
the Gaussian mask as a TIFF file in the same directory as the point mask.
"""

import os
from pathlib import Path
from typing import Union

import pandas as pd
from tifffile import tifffile
from tqdm import tqdm

from roche.crisp.utils.common_utils import point2gauss


def generate_gaussian_masks_from_csv(
    csv_file: Union[str, Path],
    point_mask_column: str = "point_mask",
    num_classes: int = 6,
    output_prefix: str = "gaussian_mask_",
    output_suffix: str = ".tiff",
) -> None:
    """Generate Gaussian masks from point masks specified in a CSV file.

    Args:
        csv_file: Path to the CSV file containing point mask paths
        point_mask_column: Name of the column containing point mask file paths
        num_classes: Number of classes for the Gaussian mask generation
        output_prefix: Prefix for the output Gaussian mask files
        output_suffix: Suffix for the output Gaussian mask files

    Raises
    ------
        FileNotFoundError: If the CSV file or any point mask file is not found
        KeyError: If the specified column is not found in the CSV
    """
    csv_path = Path(csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    data = pd.read_csv(csv_file)

    if point_mask_column not in data.columns:
        raise KeyError(f"Column '{point_mask_column}' not found in CSV file")

    for index, row in tqdm(
        data.iterrows(), total=len(data), desc="Generating Gaussian masks"
    ):
        point_mask_path = row[point_mask_column]

        if not os.path.exists(point_mask_path):
            print(f"Warning: Point mask file not found: {point_mask_path}")
            continue

        file_name = os.path.basename(point_mask_path)
        path = os.path.dirname(point_mask_path)

        try:
            gauss_mask = point2gauss(data_path=point_mask_path, num_classes=num_classes)

            # Create output filename
            base_name = file_name.split(".")[0]  # Remove extension
            output_filename = f"{output_prefix}{base_name}{output_suffix}"
            output_path = os.path.join(path, output_filename)

            tifffile.imwrite(output_path, gauss_mask)

        except Exception as e:
            print(f"Error processing {point_mask_path}: {e}")
            continue


def main():
    """Run the script with default parameters."""
    csv_file = (
        "/projects/site/dia/rds-csi/crisp/"
        "mosaic-PDL1-CK7/PDL1-CK7-Training-Data/train_data_v1.csv"
    )

    generate_gaussian_masks_from_csv(csv_file)


if __name__ == "__main__":
    main()
