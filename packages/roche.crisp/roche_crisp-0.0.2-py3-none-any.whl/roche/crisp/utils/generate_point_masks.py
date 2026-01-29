"""Generate point masks for images and save the masks and overlays.

This module provides functionality to read images from a specified directory, generate
point masks using the `text2point` function, create overlays of the images and masks,
and save the masks and overlays to specified directories.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union

import imageio
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from roche.crisp.utils.common_utils import text2point


def generate_point_masks_from_directory(
    image_dir: Union[str, Path],
    label_dir: Union[str, Path],
    mask_save_dir: Union[str, Path],
    overlay_save_dir: Union[str, Path],
    image_extension: str = ".png",
    label_suffix: str = "_yxlabel.txt",
    label_extension: str = ".txt",
    index_error: int = 1,
    color_mapping: Optional[Dict[int, str]] = None,
    point_size: int = 3,
    image_cmap: str = "gray",
) -> None:
    """Generate point masks for images and save the masks and overlays.

    Args:
        image_dir: Directory containing input images
        label_dir: Directory containing label files
        mask_save_dir: Directory to save generated masks
        overlay_save_dir: Directory to save generated overlays
        image_extension: File extension for images to process
        label_suffix: Suffix to add to image filename for label files
        label_extension: File extension for label files
        index_error: Index error parameter for text2point function
        color_mapping: Dictionary mapping label values to colors for visualization
        point_size: Size of points in the overlay visualization
        image_cmap: Colormap for displaying images in overlays

    Raises
    ------
        FileNotFoundError: If any of the specified directories don't exist
        ValueError: If no images are found in the image directory
    """
    # Convert to Path objects
    image_dir = Path(image_dir)
    label_dir = Path(label_dir)
    mask_save_dir = Path(mask_save_dir)
    overlay_save_dir = Path(overlay_save_dir)

    # Check if directories exist
    if not image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")
    if not label_dir.exists():
        raise FileNotFoundError(f"Label directory not found: {label_dir}")

    # Create output directories if they don't exist
    mask_save_dir.mkdir(parents=True, exist_ok=True)
    overlay_save_dir.mkdir(parents=True, exist_ok=True)

    # Default color mapping
    if color_mapping is None:
        color_mapping = {1: "red", 2: "green", 3: "blue", 4: "cyan", 5: "magenta"}

    # Get list of image files
    image_files = [f for f in os.listdir(image_dir) if f.endswith(image_extension)]

    if not image_files:
        raise ValueError(f"No {image_extension} files found in {image_dir}")

    # Process each image
    for image_filename in tqdm(image_files, desc="Generating point masks"):
        try:
            # Construct paths
            image_path = image_dir / image_filename
            label_filename = (
                os.path.splitext(image_filename)[0] + label_suffix + label_extension
            )
            label_path = label_dir / label_filename

            # Check if label file exists
            if not label_path.exists():
                print(f"Warning: Label file not found: {label_path}")
                continue

            # Generate point mask
            point_mask = text2point(
                str(image_path), str(label_path), index_error=index_error
            )

            # Load the image
            image = imageio.imread(image_path)

            # Get the x, y coordinates and labels of the points in the mask
            y, x = np.where(point_mask)
            labels = point_mask[y, x]

            # Create a scatter plot of the points
            plt.figure(figsize=(10, 10))
            plt.imshow(image, cmap=image_cmap)
            c = [color_mapping.get(label, "white") for label in labels]
            plt.scatter(x, y, c=c, s=point_size)
            plt.axis("off")

            # Save the overlay
            overlay_path = overlay_save_dir / image_filename
            plt.savefig(overlay_path, bbox_inches="tight", dpi=150)
            plt.close()

            # Save the mask
            mask_path = mask_save_dir / image_filename
            imageio.imwrite(mask_path, point_mask)

        except Exception as e:
            print(f"Error processing {image_filename}: {e}")
            continue


def main():
    """Run the script with default parameters."""
    # Define directories
    image_dir = (
        "/projects/site/dia/rds-csi/crisp/mosaic-PDL1-CK7/PDL1-CK7-Training-Data/Images"
    )
    label_dir = (
        "/projects/site/dia/rds-csi/crisp/mosaic-PDL1-CK7/PDL1-CK7-Training-Data/Labels"
    )
    mask_save_dir = (
        "/projects/site/dia/rds-csi/crisp/mosaic-PDL1-CK7/PDL1-CK7-Training-Data/Masks"
    )
    overlay_save_dir = "/projects/site/dia/rds-csi/crisp/mosaic-PDL1-CK7/"
    """PDL1-CK7-Training-Data/Overlays."""

    generate_point_masks_from_directory(
        image_dir=image_dir,
        label_dir=label_dir,
        mask_save_dir=mask_save_dir,
        overlay_save_dir=overlay_save_dir,
    )


if __name__ == "__main__":
    main()
