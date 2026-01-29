"""Common utility functions."""

import logging
import os
import random
from pathlib import Path
from typing import List, Optional, Tuple, Union

import click
import cv2
import imageio.v2 as imageio
import numpy as np
import pandas as pd
import torch
from scipy.ndimage import (
    binary_fill_holes,
    find_objects,
    gaussian_filter,
)
from skimage.measure import label, regionprops
from skimage.segmentation import watershed
from tqdm import tqdm

output_logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Provide common utilities for data preparation."""
    pass


def seed_everything(seed):
    """Set the random seed for reproducibility across multiple runs.

    Parameters
    ----------
    seed : int
        The seed value to use for random number generation.

    Returns
    -------
    None
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def distance_to_boundary(masks: np.ndarray) -> np.ndarray:
    """Get distance to boundary of mask pixels.

    Parameters
    ----------
    masks : np.ndarray
        size [Ly x Lx], 0=NO masks; 1,2,...=mask labels

    Returns
    -------
    dist_to_bound : np.ndarray
        size [Ly x Lx]
    """
    if masks.ndim > 3 or masks.ndim < 2:
        raise ValueError(
            "distance_to_boundary takes 2D or 3D array, not %dD array" % masks.ndim
        )
    dist_to_bound = np.zeros(masks.shape, np.float64)

    if masks.ndim == 3:
        for i in range(masks.shape[0]):
            dist_to_bound[i] = distance_to_boundary(masks[i])
        return dist_to_bound
    else:
        slices = find_objects(masks)
        for i, si in enumerate(slices):
            if si is not None:
                sr, sc = si
                mask = (masks[sr, sc] == (i + 1)).astype(np.uint8)
                contours = cv2.findContours(
                    mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
                )
                pvc, pvr = np.concatenate(contours[-2], axis=0).squeeze().T
                ypix, xpix = np.nonzero(mask)
                y_dist = (ypix[:, np.newaxis] - pvr) ** 2
                x_dist = (xpix[:, np.newaxis] - pvc) ** 2
                total_dist = y_dist + x_dist
                min_dist = total_dist.min(axis=1)
                dist_to_bound[ypix + sr.start, xpix + sc.start] = min_dist
        return dist_to_bound


def masks_to_edges(masks: np.ndarray, threshold: float = 1.0) -> np.ndarray:
    """Get edges of masks as a 0-1 array.

    Parameters
    ----------
    masks : np.ndarray
        size [Ly x Lx], 0=NO masks; 1,2,...=mask labels

    Returns
    -------
    edges : np.ndarray
        size [Ly x Lx], True pixels are edge pixels
    """
    dist_to_bound = distance_to_boundary(masks)
    edges = (dist_to_bound < threshold) * (masks > 0)
    return edges


def remove_edge_masks(masks: np.ndarray, change_index=True):
    """Remove masks with pixels on edge of image.

    Parameters
    ----------
    masks : np.ndarray
        size [Ly x Lx], 0=NO masks; 1,2,...=mask labels

    change_index : bool, optional
        if True, after removing masks change indexing so no missing label
        numbers

    Returns
    -------
    outlines : np.ndarray
        size [Ly x Lx], 0=NO masks; 1,2,...=mask labels
    """
    slices = find_objects(masks.astype(int))
    for i, si in enumerate(slices):
        remove = False
        if si is not None:
            for d, sid in enumerate(si):
                if sid.start == 0 or sid.stop == masks.shape[d]:
                    remove = True
                    break
            if remove:
                masks[si][masks[si] == i + 1] = 0
    shape = masks.shape
    if change_index:
        _, masks = np.unique(masks, return_inverse=True)
        masks = np.reshape(masks, shape).astype(np.int32)

    return masks


def masks_to_outlines(masks: np.ndarray) -> np.ndarray:
    """Get outlines of masks as a 0-1 array.

    Parameters
    ----------
    masks : np.ndarray
        size [Ly x Lx], 0=NO masks; 1,2,...=mask labels

    Returns
    -------
    outlines : np.ndarray
        size [Ly x Lx], True pixels are outlines
    """
    if masks.ndim > 3 or masks.ndim < 2:
        raise ValueError("masks_to_outlines takes only 2D, not %dD array" % masks.ndim)
    outlines = np.zeros(masks.shape, bool)

    slices = find_objects(masks.astype(int))
    for i, si in enumerate(slices):
        if si is not None:
            sr, sc = si
            mask = (masks[sr, sc] == (i + 1)).astype(np.uint8)
            contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            pvc, pvr = np.concatenate(contours[-2], axis=0).squeeze().T
            vr, vc = pvr + sr.start, pvc + sc.start
            outlines[vr, vc] = 1
    return outlines


def outlines_list(masks: np.ndarray) -> List[np.ndarray]:
    """Get outlines of masks as a list to loop over for plotting.

    Parameters
    ----------
    masks : np.ndarray
        size [Ly x Lx], 0=NO masks; 1,2,...=mask labels

    Returns
    -------
    outlines : List[np.ndarray]
        List of outlines
    """
    outpix = []
    for n in np.unique(masks)[1:]:
        mn = masks == n
        if mn.sum() > 0:
            contours = cv2.findContours(
                mn.astype(np.uint8),
                mode=cv2.RETR_EXTERNAL,
                method=cv2.CHAIN_APPROX_NONE,
            )
            contours = contours[-2]
            cmax = np.argmax([c.shape[0] for c in contours])
            pix = contours[cmax].astype(int).squeeze()
            if len(pix) > 4:
                outpix.append(pix)
            else:
                outpix.append(np.zeros((0, 2)))
    return outpix


def circleMask(d0):
    """Create an array of radii based on the indices of a patch.

    Parameters
    ----------
    d0 : tuple
        The patch dimensions represented as a tuple (rows, columns). The patch
        covers the range (-d0[1], d0[1] + 1) for columns and
        (-d0[0], d0[0] + 1) for rows.

    Returns
    -------
    rs : ndarray
        An array of radii with shape (2*d0[0]+1, 2*d0[1]+1).
    dx : ndarray
        The indices of the patch for the columns.
    dy : ndarray
        The indices of the patch for the rows.
    """
    dx = np.tile(np.arange(-d0[1], d0[1] + 1), (2 * d0[0] + 1, 1))
    dy = np.tile(np.arange(-d0[0], d0[0] + 1), (2 * d0[1] + 1, 1))
    dy = dy.transpose()

    rs = (dy**2 + dx**2) ** 0.5
    return rs, dx, dy


def create_binary_mask_from_instance_mask(data: np.ndarray) -> np.ndarray:
    """Create a binary mask from instance mask.

    Parameters
    ----------
    data : numpy.ndarray
        The instance mask.

    Returns
    -------
    numpy.ndarray
        The binary mask.
    """
    instance_mask = data

    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(instance_mask.astype("uint8"), cv2.MORPH_GRADIENT, kernel)
    edges[edges != 0] = 1
    # _, thresh = cv2.threshold(edges, 0, 1, cv2.THRESH_BINARY)

    for i in range(edges.shape[1]):
        for j in range(edges.shape[0]):
            if instance_mask[j, i] != 0 and edges[j, i] != 1:
                edges[j, i] = 2

    bin_mask = edges
    bin_mask[bin_mask == 1] = 0
    bin_mask[bin_mask == 2] = 1

    return bin_mask


def create_panoptic_mask_from_instance_and_semantic_masks(
    instance_mask: np.ndarray, sem_mask: np.ndarray
) -> np.ndarray:
    """Convert instance segmentation mask to panoptic segmentation mask.

    Requires instance segmentation mask along with semantic mask.

    Parameters
    ----------
    instance_mask : numpy.ndarray
        The instance segmentation mask.
    sem_mask : numpy.ndarray
        The semantic mask.

    Returns
    -------
    numpy.ndarray
        The panoptic segmentation mask.
    """
    regions = regionprops(label(instance_mask))  # inst mask
    pred_point_output = np.zeros(
        (instance_mask.shape[0], instance_mask.shape[1]), dtype=np.int32
    )
    empty = 0
    for i in range(len(regions)):
        bbox = regions[i].bbox
        cntrd = regions[i].centroid
        crop = sem_mask[bbox[0] : bbox[2], bbox[1] : bbox[3]]
        a, b = np.unique(crop, return_counts=True)
        if 0 in a and len(a) != 1:
            j = np.where(a == 0)
            a = np.delete(a, j)
            b = np.delete(b, j)
        else:
            empty += 1
        c = a[b == b.max()]
        if len(c) > 1:
            c = 1
        pred_point_output[int(cntrd[0]), int(cntrd[1])] = c
    # inst_mask = mask
    mask = create_binary_mask_from_instance_mask(instance_mask)
    # bin_mask = mask
    mask = label(mask, connectivity=1)
    mask = mask.astype(np.int32)
    phenotype_mask = watershed(image=mask, markers=pred_point_output, mask=mask)
    phenotype_mask = phenotype_mask.astype("uint8")
    return phenotype_mask


def get_diameters(mask):
    """Calculate the diameter of the objects in the given instance mask.

    Parameters
    ----------
    mask : ndarray
        Instance mask representing objects.

    Returns
    -------
    tuple
        A tuple containing two elements.
    md : float
        Median diameter of the objects.
    radii : ndarray
        Radii of the objects, calculated as the square root of counts
        divided by 2.
    """
    # Get unique values and their counts in the mask
    _, counts = np.unique(np.int32(mask), return_counts=True)
    # Remove the background count
    counts = counts[1:]
    # Calculate the median diameter of the objects
    md = np.median(counts**0.5)
    # If the median diameter is NaN, set it to 0
    if np.isnan(md):
        md = 0
    # Convert the median diameter to actual diameter
    md /= (np.pi**0.5) / 2
    # Calculate the radii of the objects
    # radii = counts**0.5
    return md


def generate_cell_coords_output(prediction_mask: np.ndarray) -> tuple:
    """Extract cell coordinates and labels from a binary prediction mask.

    Processes a binary mask to extract the coordinates of all non-zero pixels
    along with their corresponding labels for further analysis or visualization.

    Parameters
    ----------
    prediction_mask : np.ndarray
        Binary mask of shape (H, W) containing cell predictions.
        Non-zero values represent cell pixels with their respective labels.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]

    Tuple containing:
        - cell_labels: 1D array of label values for each non-zero pixel
        - cell_coords: 2D array of shape (N, 2) with (row, col) coordinates
            of non-zero pixels.

    Notes
    -----
    - Input mask is automatically converted to uint8 if not already.
    - Function expects 2D input and will log an error for other dimensions.
    - Coordinates are returned in (row, col) format, not (x, y).

    Examples
    --------
    >>> mask = np.array([[0, 1, 1], [0, 2, 0], [3, 3, 0]])
    >>> labels, coords = generate_cell_coords_output(mask)
    >>> print(coords)  # [[0, 1], [0, 2], [1, 1], [2, 0], [2, 1]]
    """
    if len(np.shape(prediction_mask)) != 2:
        output_logger.error(
            f"Mask should be of size HxW but input is: {np.shape(prediction_mask)}"
        )

    if prediction_mask.dtype != "uint8":
        prediction_mask = prediction_mask.astype("uint8")

    cell_coords = np.transpose(np.nonzero(prediction_mask))
    cell_labels = prediction_mask[np.nonzero(prediction_mask)]
    cell_coords_and_labels = []

    for elem in range(0, len(cell_labels)):
        cell_coords_and_labels.append(
            [cell_coords[elem][0], cell_coords[elem][1], cell_labels[elem]]
        )

    return cell_labels, cell_coords


def fill_holes_and_remove_small_masks(masks, min_size=15):
    """Fill holes in masks (2D/3D) and discard masks smaller than min_size(2D).

    Fill holes in each mask using scipy.ndimage.morphology.binary_fill_holesS
    (might have issues at borders between cells, todo: check and fix)

    Parameters
    ----------
    masks : int, 2D
        labelled masks, 0=NO masks; 1,2,...=mask labels,
        size [Ly x Lx]
    min_size : int (optional, default 15)
        minimum number of pixels per mask, can turn off with -1

    Returns
    -------
    masks : int, 2D
        masks with holes filled and masks smaller than min_size removed,
        0=NO masks; 1,2,...=mask labels,
        size [Ly x Lx]
    """
    if masks.ndim > 3 or masks.ndim < 2:
        raise ValueError(
            "masks_to_outlines takes 2D or 3D array, not %dD array" % masks.ndim
        )

    slices = find_objects(masks)
    j = 0
    for i, slc in enumerate(slices):
        if slc is not None:
            msk = masks[slc] == (i + 1)
            npix = msk.sum()
            if min_size > 0 and npix < min_size:
                masks[slc][msk] = 0
            elif npix > 0:
                if msk.ndim == 3:
                    for k in range(msk.shape[0]):
                        msk[k] = binary_fill_holes(msk[k])
                else:
                    msk = binary_fill_holes(msk)
                masks[slc][msk] = j + 1
                j += 1
    return masks


def pad_image(
    img0: Union[np.ndarray, torch.Tensor], div: int = 16, extra: int = 1
) -> Union[
    tuple[np.ndarray, np.ndarray, np.ndarray],
    tuple[torch.Tensor, torch.Tensor, torch.Tensor],
]:
    """Pad image for test-time so that its dimensions are a multiple of div.

    Parameters
    ----------
    img0 : Union[numpy.ndarray, torch.Tensor]
        image of size [nchan x Ly x Lx]
    div : int, optional
        padding divisor, by default 16
    extra : int, optional
        extra padding, by default 1

    Returns
    -------
    Union[tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray],
          tuple[torch.Tensor, torch.Tensor, torch.Tensor]]
        Tuple containing the padded image, the y-range of pixels in the padded
        image corresponding to the original image, and the x-range of pixels in
        the padded image corresponding to the original image.
    """
    is_torch = isinstance(img0, torch.Tensor)

    # Common padding calculations (same for both torch and numpy)
    if is_torch:
        # PyTorch uses integer division for ceiling
        Lpad = int(div * ((img0.shape[-2] + div - 1) // div) - img0.shape[-2])
        Lpad_y = int(div * ((img0.shape[-1] + div - 1) // div) - img0.shape[-1])
    else:
        # NumPy uses np.ceil for ceiling
        Lpad = int(div * np.ceil(img0.shape[-2] / div) - img0.shape[-2])
        Lpad_y = int(div * np.ceil(img0.shape[-1] / div) - img0.shape[-1])

    xpad1 = extra * div // 2 + Lpad // 2
    xpad2 = extra * div // 2 + Lpad - Lpad // 2
    ypad1 = extra * div // 2 + Lpad_y // 2
    ypad2 = extra * div // 2 + Lpad_y - Lpad_y // 2

    if is_torch:
        # PyTorch implementation
        if img0.ndim > 3:
            pads = tuple((ypad1, ypad2, xpad1, xpad2, 0, 0, 0, 0))
        elif img0.ndim == 2:
            pads = tuple((ypad1, ypad2, xpad1, xpad2))
        elif img0.ndim == 3:
            pads = tuple((ypad1, ypad2, xpad1, xpad2, 0, 0))

        img_pad = torch.nn.functional.pad(img0, pads, mode="constant")
        Ly, Lx = img0.shape[-2:]
        ysub = torch.arange(xpad1, xpad1 + Ly, dtype=torch.int32)
        xsub = torch.arange(ypad1, ypad1 + Lx, dtype=torch.int32)

    else:
        # NumPy implementation
        if img0.ndim > 3:
            pads = np.array([[0, 0], [0, 0], [xpad1, xpad2], [ypad1, ypad2]])
        elif img0.ndim == 3:
            pads = np.array([[0, 0], [xpad1, xpad2], [ypad1, ypad2]])
        elif img0.ndim == 2:
            pads = np.array([[xpad1, xpad2], [ypad1, ypad2]])

        img_pad = np.pad(img0, pads, mode="constant")
        Ly, Lx = img0.shape[-2:]
        ysub = np.arange(xpad1, xpad1 + Ly)
        xsub = np.arange(ypad1, ypad1 + Lx)

    return img_pad, ysub, xsub


def remove_padding(
    padded_img: torch.Tensor, ysub: torch.Tensor, xsub: torch.Tensor
) -> torch.Tensor:
    """Remove padding from the padded image.

    Parameters
    ----------
    padded_img : torch.Tensor
        Padded image of size [nchan x Ly x Lx]

    ysub : torch.Tensor, int
        yrange of pixels in padded_img corresponding to the original image

    xsub : torch.Tensor, int
        xrange of pixels in padded_img corresponding to the original image

    Returns
    -------
    torch.Tensor
        Image with padding removed
    """
    if padded_img.ndim == 2:
        img = padded_img[ysub[0] : ysub[-1] + 1, xsub[0] : xsub[-1] + 1]
    elif padded_img.ndim == 3:
        img = padded_img[:, ysub[0] : ysub[-1] + 1, xsub[0] : xsub[-1] + 1]
    elif padded_img.ndim > 3:
        img = padded_img[:, :, ysub[0] : ysub[-1] + 1, xsub[0] : xsub[-1] + 1]
    return img


def extract_image_masks_from_csv(csv_file_path: str) -> List[Tuple[str, ...]]:
    """Extract image paths and corresponding mask paths from a CSV file.

    The CSV file should have the image paths in the first column and the mask
    paths in the subsequent columns.

    Parameters
    ----------
    csv_file_path : str
        Path to the CSV file.

    Returns
    -------
    List[Tuple[str, ...]]
        List of tuples, where each tuple contains an image path and a list of
        corresponding mask paths.
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path)

    # If the DataFrame only has one column, return a list of images
    if len(df.columns) == 1:
        image_list: List[Tuple[str, ...]] = [(image,) for image in df.iloc[:, 0]]
        return image_list

    # The first column is 'image', the rest are masks
    image_mask_list = [
        tuple([image] + masks.tolist())
        for image, masks in zip(df.iloc[:, 0], df.iloc[:, 1:].values)
    ]

    return image_mask_list


def _find_image_mask_pairs(parent_dir: str) -> List[Tuple[str, str]]:
    """Find pairs of image and mask files in the given directory structure.

    Parameters
    ----------
    parent_dir : str
        Path to the parent directory containing 'fovs' and 'labels' subdirectories

    Returns
    -------
    List[Tuple[str, str]]
        List of tuples containing (image_path, mask_path) pairs

    Notes
    -----
    This function expects the following directory structure:
        parent_directory/
            ├── images/         # Contains original images
            └── masks/       # Contains mask images
    """
    parent_dir_path = Path(parent_dir)
    images_dir = parent_dir_path / "images"
    masks_dir = parent_dir_path / "masks"

    if not images_dir.exists() or not masks_dir.exists():
        raise ValueError(
            "Both 'images' and 'labels' directories must exist in the parent directory"
        )

    image_mask_pairs = []

    # Get all image files from fovs directory
    image_files = [f for f in images_dir.glob("*") if f.is_file()]
    for img_path in tqdm(image_files):
        # Construct the corresponding mask path in labels directory
        mask_name = img_path.name.replace("image", "mask")
        # mask_name = f"mask_{img_path.name.split('img_')[1]}"
        mask_path = masks_dir / mask_name
        # Check if mask exists
        if mask_path.exists():
            image_mask_pairs.append((str(img_path), str(mask_path)))

    return image_mask_pairs


@cli.command()
@click.argument(
    "parent_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--output_csv",
    "-o",
    default="image_mask_pairs.csv",
    help="Output CSV file path (default: image_mask_pairs.csv)",
)
def create_image_mask_csv(parent_dir: str, output_csv: str):
    """Create a CSV file mapping image paths to mask paths.

    Parameters
    ----------
    parent_dir : str
        Path to the parent directory containing 'fovs' and 'labels' subdirectories
    output_csv : str
        Path where the CSV file should be saved

    Example
    -------
    python create-image-mask-csv /path/to/parent/dir -o /path/to/output.csv
    """
    # Find all image-mask pairs
    pairs = _find_image_mask_pairs(parent_dir)
    print(f"Found {len(pairs)} image-mask pairs")

    # Create DataFrame
    df = pd.DataFrame(pairs, columns=["image_path", "mask_path"])

    # Save to CSV
    df.to_csv(output_csv, index=False)
    print(f"Created CSV file at: {output_csv}")


def calculate_class_weights(
    batch_masks: torch.Tensor, total_classes: int
) -> torch.Tensor:
    """Calculate normalized class weights for a batch of masks.

    Parameters
    ----------
    batch_masks : torch.Tensor
        Batch of masks.
    total_classes : int
        Total number of classes.

    Returns
    -------
    torch.Tensor
        Normalized class weights.
    """
    class_frequencies = torch.zeros(total_classes)

    for class_id in range(total_classes):
        class_frequencies[class_id] = torch.sum(batch_masks == class_id)
    mask = class_frequencies != 0
    class_weights = torch.zeros_like(class_frequencies)
    class_weights[mask] = 1 / class_frequencies[mask]
    norm_class_weights = class_weights / torch.sum(class_weights)
    return norm_class_weights


def get_effective_sample_based_classweights(
    batch_masks: torch.Tensor,
    beta: float,
    total_classes: int,
    ignore_label: Optional[int] = None,
) -> torch.Tensor:
    """Calculate class weights based on effective number of samples.

    This method is based on the approach described in:
    Cui, Y., Jia, M., Lin, T-Y., Song, Y., Belongie, S. (2019).
    "Class-Balanced Loss Based on Effective Number of Samples."
    Proceedings of the IEEE/CVF Conference on Computer Vision and
    Pattern Recognition (CVPR).

    Parameters
    ----------
    batch_masks : torch.Tensor
        Batch of masks.
    total_classes : int
        Total number of classes.

    Returns
    -------
    torch.Tensor
        Normalized class weights.
    """
    epsilon = 1e-8  # small constant to avoid division by zero
    class_frequencies = torch.stack(
        [
            torch.bincount(
                mask[mask != ignore_label].view(-1).long(), minlength=total_classes
            )
            for mask in batch_masks
        ]
    )
    mean_class_frequencies = class_frequencies.float().mean(dim=0)

    effective_samples = 1.0 - torch.pow(beta, mean_class_frequencies)
    weights = (1.0 - beta) / (effective_samples + epsilon)
    weights = weights / (torch.sum(weights)) * total_classes

    return weights


@cli.command()
@click.argument(
    "data_path", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
@click.argument("num_classes", type=int)
@click.argument("radius", type=int)
@click.option("--normalize", is_flag=True, default=True)
@click.option("--ignore_class", type=int, default=None)
def point2gauss(
    data_path: str,
    num_classes: int,
    radius: int,
    normalize: bool = True,
    ignore_class: Optional[Union[List, int]] = None,
) -> np.ndarray:
    """Create a gaussian mask for each class in the point mask.

    Parameters
    ----------
    data_path : str
        Path to the data.
    num_classes : int
        Number of classes.
    radius : int
        Radius of the gaussian kernel.
    normalize : bool, optional
        Whether to normalize the gaussian mask, by default True.
    ignore_class : Union[List, int], optional
        Classes to ignore, by default None.

    Returns
    -------
    reg_map : numpy.ndarray
        Gaussian mask for each class in the point mask.

    Notes
    -----
    If the ignore_class is not None the final gaussian mask will have ignore
    regions labelled as 2.
    """
    pt_mk = imageio.imread(data_path)
    # pt_mk = np.where(pt_mk == 255, 6, pt_mk) # edit mask
    gauss_mask = np.zeros(
        [pt_mk.shape[0], pt_mk.shape[1], num_classes], dtype="float32"
    )
    all_cells = np.zeros([pt_mk.shape[0], pt_mk.shape[1]], dtype="uint8")

    for i in range(num_classes):
        i_mask = pt_mk == i
        i_mask_gauss = gaussian_filter(
            i_mask.astype(np.float32), sigma=1, order=0, radius=radius
        )

        if i > 0:
            i_mask_gauss_logical = i_mask_gauss > 0
            all_cells = np.logical_or(all_cells, i_mask_gauss_logical)
            gauss_mask[:, :, i] = i_mask_gauss

    all_cells_dilated = gaussian_filter(all_cells.astype(np.float32), sigma=2, order=0)
    mask_all_cells_dilated = (all_cells_dilated > 0).astype("uint8")

    bg_class = np.logical_not(mask_all_cells_dilated)
    reg_map = gauss_mask.astype("float32")
    reg_map[:, :, 0] = bg_class

    if normalize:
        reg_map = reg_map / (reg_map.sum(axis=2, keepdims=True) + 1e-9)

        ignore_mask = np.isin(pt_mk, ignore_class)
        ignore_mask_gauss = gaussian_filter(
            ignore_mask.astype(np.float32), sigma=1, order=0, radius=radius
        )
        ignore_mask_gauss_logical = ignore_mask_gauss > 0
        ignore_cells_dilated = gaussian_filter(
            ignore_mask_gauss_logical.astype(np.float32), sigma=2, order=0
        )
        mask_ignore_cells_dilated = (ignore_cells_dilated > 0).astype("uint8")
        reg_map[:, :, 0][mask_ignore_cells_dilated == 1] = 2

    return reg_map


def text2point(imagefile: str, txtfile: str, index_error: int = 0) -> np.ndarray:
    """Convert text label to point mask.

    Generate a point mask of the size of the image file where coordinates in
    the text file are labeled with class values and the rest of the pixels
    are 0's.

    Parameters
    ----------
    imagefile : str
        Path to the image file.
    txtfile : str
        Path to the text file containing pixel coordinates and class
        labels.
    index_error : int, optional
        Value to subtract from the coordinates in the text file to account
        for the difference in indexing between the image file and the text
        file, by default 0.

    Returns
    -------
    numpy.ndarray
        Generated point mask.
    """
    # Open the image file and get its size
    img = imageio.imread(imagefile)
    height, width = img.shape[:2]

    # Initialize the mask with zeros
    mask = np.zeros((height, width), dtype=np.uint8)

    # Open the text file and assign class labels to the mask
    with open(txtfile, "r") as f:
        for line in f:
            delimiter = "," if "," in line else None
            y, x, label = map(int, [i.strip() for i in line.split(delimiter)])
            mask[y - index_error, x - index_error] = label

    return mask


def patch_image(
    img: np.ndarray, patch_size: int, stride: int, mask: Optional[np.ndarray] = None
) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Extract patches from image and optionally from mask.

    Parameters
    ----------
    img : numpy.ndarray
        Input image to be patched
    patch_size : int
        Size of patched image
    stride : int
        Overlap between patches
    mask : numpy.ndarray, optional
        Optional mask to be patched. If provided, must have same spatial
        dimensions as img.

    Returns
    -------
    all_patches : numpy.ndarray
        Numpy array containing image patches
    all_coords : numpy.ndarray
        Numpy array containing coordinates of the patches in the original image
    all_masks : numpy.ndarray, optional
        Numpy array containing mask patches (only returned if mask is provided)
    """
    # Get image dimensions
    if len(img.shape) == 3:
        img_h, img_w, num_channels = img.shape
        num_patches = int(np.ceil(img_h / stride)) * int(np.ceil(img_w / stride))
        all_patches = np.zeros([num_patches, patch_size, patch_size, num_channels])
    else:
        img_h, img_w = img.shape
        num_patches = int(np.ceil(img_h / stride)) * int(np.ceil(img_w / stride))
        all_patches = np.zeros([num_patches, patch_size, patch_size])

    # Handle mask if provided
    if mask is not None:
        if len(mask.shape) == 3:
            mask_h, mask_w, mask_channels = mask.shape
            all_masks = np.zeros([num_patches, patch_size, patch_size, mask_channels])
        else:
            mask_h, mask_w = mask.shape
            all_masks = np.zeros([num_patches, patch_size, patch_size])

        # Check dimension compatibility
        if img_h != mask_h or img_w != mask_w:
            raise ValueError("Image and mask dimensions do not match")

    all_coords = np.zeros([num_patches, 4])
    patch_idx = 0

    for i in range(0, img_h, stride):
        for j in range(0, img_w, stride):
            patch_h = i + patch_size
            patch_w = j + patch_size

            # Adjust patch boundaries if they exceed image dimensions
            if patch_h > img_h:
                i = img_h - patch_size
                patch_h = img_h
            if patch_w > img_w:
                j = img_w - patch_size
                patch_w = img_w

            # Extract image patch
            if len(img.shape) == 3:
                patch = img[i:patch_h, j:patch_w, :]
            else:
                patch = img[i:patch_h, j:patch_w]

            all_patches[patch_idx, ...] = patch

            # Extract mask patch if mask is provided
            if mask is not None:
                if len(mask.shape) == 3:
                    mask_patch = mask[i:patch_h, j:patch_w, :]
                else:
                    mask_patch = mask[i:patch_h, j:patch_w]
                all_masks[patch_idx, ...] = mask_patch

            # Store coordinates
            coords = np.array([i, patch_h, j, patch_w])
            all_coords[patch_idx, ...] = coords
            patch_idx += 1

    if mask is not None:
        return all_patches, all_masks, all_coords
    else:
        return all_patches, all_coords


if __name__ == "__main__":
    cli()
