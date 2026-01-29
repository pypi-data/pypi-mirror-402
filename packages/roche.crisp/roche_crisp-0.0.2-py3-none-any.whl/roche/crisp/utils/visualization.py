"""Helper module for generating visualizations."""

import colorsys
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision
import wandb
from matplotlib.colors import ListedColormap
from matplotlib.markers import MarkerStyle
from sklearn.metrics import ConfusionMatrixDisplay
from typeguard import typechecked

from roche.crisp.utils import common_utils

plt.switch_backend("Agg")

output_logger = logging.getLogger(__name__)


def colorize_mask(mask: torch.Tensor, ax: plt.Axes, random_colors=True):
    """Display a colorized instance mask on a matplotlib axis.

    Creates a colormap with unique colors for each instance in the mask and
    displays it on the provided matplotlib axis. Colors are generated using
    HSV color space for good visual separation between instances.

    Parameters
    ----------
    mask : torch.Tensor
        Instance mask where each unique non-zero value represents a different
        instance. Background (value 0) is displayed in black.
    ax : matplotlib.axes.Axes
        Matplotlib axis object on which to display the colorized mask.
    random_colors : bool, optional
        If True, randomly shuffle the instance colors while keeping background
        black. If False, use sequential HSV colors. Default is True.

    Returns
    -------
    None
        The function modifies the provided axis in-place by displaying the
        colorized mask and turning off axis labels.

    Notes
    -----
    - Background pixels (value 0) are always colored black
    - Instance colors are generated using HSV color space with full saturation
      and value, varying only the hue
    - Random seed is fixed at 42 for reproducible color shuffling
    - Axis labels and ticks are turned off for cleaner visualization
    """
    n = int(mask.max())
    colors = []
    for i in range(n + 1):
        if i == 0:
            colors.append((0, 0, 0))
        else:
            hue = (i - 1) / n
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            colors.append(rgb)  # type: ignore
    if random_colors:
        rng = np.random.default_rng(42)
        background_color = colors[0]
        instance_colors = colors[1:]
        rng.shuffle(instance_colors)
        colors = [background_color] + instance_colors
    cmap = ListedColormap(colors)
    ax.imshow(mask, cmap=cmap, interpolation="nearest")
    ax.set_axis_off()


def plot_det_results(
    imgs: List[torch.Tensor],
    gts: List[torch.Tensor],
    guass_mask: List[torch.Tensor],
    preds: List[torch.Tensor],
    probs: List[torch.Tensor],
    filepath: str,
    labels_cmap: dict,
):
    """Visualize detection results comparing ground truth and predictions.

    Creates a comprehensive visualization showing original images, ground truth
    annotations, predictions, and probability maps for detection model evaluation.

    Parameters
    ----------
    imgs : array-like
        Batch of input images to visualize. Should contain at least 4 images.
    gts : array-like
        Ground truth point annotations corresponding to the images.
    guass_mask : array-like or None
        Gaussian masks generated from ground truth points. If None, uses
        ground truth points directly.
    preds : array-like
        Model predictions for each image.
    probs : array-like
        Probability maps output by the model. Expected to have multiple channels.
    filepath : str
        File path where the visualization will be saved.
    labels_cmap : dict
        Color mapping for different labels/classes in the format {label: color}.

    Returns
    -------
    None
        The function saves the figure to the specified filepath and closes it.

    Notes
    -----
    - Creates a 6x4 subplot grid showing different aspects of the detection
    - Ground truth and predictions are overlaid as colored scatter plots
    - Probability maps show individual channels from the model output
    - Figure is automatically saved and closed to free memory
    """
    #
    fig, ax = plt.subplots(6, 4, figsize=(20, 16))
    rows = ["groundtruth", "prediction", "prob_map"]

    for axs, row in zip(ax[:][0], rows):
        axs.set_ylabel(row, rotation=0, labelpad=48, size="large")

    for i, (im, gt, gm, pd, prb) in enumerate(
        zip(
            imgs[:4],
            gts[:4],
            guass_mask[:4] if guass_mask is not None else gts,
            preds[:4],
            probs[:4],
        )
    ):
        ax[0][i].axis("off")
        ax[0][i].imshow(im)
        for j in np.unique(gt):
            if j != 0:
                _, cell_coords = common_utils.generate_cell_coords_output(gt == j)
                ax[0][i].scatter(
                    x=cell_coords[:, 1],
                    y=cell_coords[:, 0],
                    marker=MarkerStyle("o"),
                    facecolors=labels_cmap[j],
                    s=3,
                )
        ax[1][i].axis("off")
        ax[1][i].imshow(im)
        for k in np.unique(pd):
            if k != 0:
                _, cell_coords = common_utils.generate_cell_coords_output(pd == k)
                ax[1][i].scatter(
                    x=cell_coords[:, 1],
                    y=cell_coords[:, 0],
                    marker=MarkerStyle("o"),
                    facecolors=labels_cmap[k],
                    s=3,
                )
        if guass_mask is not None:
            ax[2][i].axis("off")
            ax[2][i].imshow(gm[1:].transpose(1, 2, 0))
        ax[3][i].axis("off")
        ax[3][i].imshow(prb[1])
        ax[4][i].axis("off")
        ax[4][i].imshow(prb[2])
        ax[5][i].axis("off")
        ax[5][i].imshow(prb[3])

    plt.savefig(filepath)
    plt.close()


@typechecked
def denormalize(image: torch.Tensor, std: np.ndarray, mean: np.ndarray) -> np.ndarray:
    """Revert normalization applied to an image tensor.

    Converts a normalized tensor back to the original pixel value range (0-255)
    by applying the inverse of the normalization transformation.

    Parameters
    ----------
    image : torch.Tensor
        Normalized image tensor with shape (C, H, W) where C is the number
        of channels.\
    std : np.ndarray
        Standard deviation values used during normalization. Should have
        the same length as the number of channels.
    mean : np.ndarray
        Mean values used during normalization. Should have the same length
        as the number of channels.

    Returns
    -------
    np.ndarray
        Denormalized image as a uint8 numpy array with shape (H, W, C)
        and pixel values in the range [0, 255].

    Notes
    -----
    - Applies the inverse transformation: (normalized_pixel * std + mean) * 255
    - Automatically transposes from (C, H, W) to (H, W, C) format
    - Output is clipped and converted to uint8 for standard image format
    """
    return ((std * image.numpy().transpose((1, 2, 0)) + mean) * 255).astype(np.uint8)


@typechecked
def print_sample_with_gaussian_mask(
    images: List[np.ndarray],
    point_mask: Union[torch.Tensor, np.ndarray],
    gaussian_masks: Union[torch.Tensor, np.ndarray],
    save_path: Union[Path, None] = None,
):
    """Create visualization of training data with point annotations and Gaussian masks.

    Generates a 3x4 subplot figure showing original images, point overlays,
    and corresponding Gaussian masks for training data visualization.

    Parameters
    ----------
    images : List[np.ndarray]
        List of sample images to visualize. Should contain at least 4 images
        for proper display in the 4-column layout.
    point_mask : Union[torch.Tensor, np.ndarray]
        Point masks containing ground truth annotations. Each unique non-zero
        value represents a different cell type or instance.
    gaussian_masks : Union[torch.Tensor, np.ndarray]
        Gaussian masks generated from point annotations for training.
        Expected to have shape (N, C, H, W) where C > 1.
    save_path : Union[Path, None], optional
        File path to save the generated figure. If None, figure is not saved
        but returned for display, by default None.

    Returns
    -------
    matplotlib.figure.Figure
        The generated figure object containing the visualization.

    Notes
    -----
    - Uses fixed color mapping: {1: 'r', 2: 'g', 3: 'b'} for point overlays
    - Gaussian masks exclude the first channel (background) for display
    - Figure layout is 3 rows (original, point overlay, Gaussian mask) x 4 columns
    - Point coordinates are displayed as colored scatter plots
    """
    labels_cmap: dict = {1: "r", 2: "g", 3: "b"}

    fig, ax = plt.subplots(3, 4, figsize=(8, 6))
    rows = ["orig", "point_overlay", "gauss_mask"]
    for axs, row in zip(ax[:][0], rows):
        axs.set_ylabel(row, rotation=0, labelpad=36, size="large")
    for i, (n_im, pmk, gauss) in enumerate(zip(images, point_mask, gaussian_masks)):
        ax[0][i].imshow(n_im)
        ax[0][i].axis("off")
        ax[1][i].imshow(n_im)
        ax[1][i].axis("off")
        for j in np.unique(pmk):
            if j != 0:
                _, cell_coords = common_utils.generate_cell_coords_output(
                    pmk.numpy() == j
                )
                ax[1][i].scatter(
                    x=cell_coords[:, 1],
                    y=cell_coords[:, 0],
                    marker=MarkerStyle("o"),
                    facecolors=labels_cmap[j],
                    s=3,
                )
        ax[2][i].axis("off")
        ax[2][i].imshow(gauss[1:].numpy().transpose((1, 2, 0)))

    if save_path is not None:
        save_path.parent.mkdir(exist_ok=True, parents=True)
        plt.savefig(save_path)
        plt.close()
    return fig


def visualize_cellpose_samples(
    batch: Tuple[torch.Tensor, torch.Tensor],
    output: torch.Tensor,
    split: str,
    instance_masks: Optional[torch.Tensor] = None,
):
    """Visualizes a batch of images, masks and predictions using WandB.

    Parameters
    ----------
    batch : tuple of tensors
        A tuple of two tensors representing the images and masks.
    output : tensor
        A tensor representing the output of the model.
    split : str
        A string indicating the split of the data (e.g. 'train', 'val', 'test').
    instance_masks : tensor, optional
        A tensor representing the instance masks.

    Returns
    -------
    None
    """
    # Unpack the batch
    images, masks = batch

    softmax = torch.nn.Softmax(dim=1)
    sem_output_softmax = softmax(output[:, 2:, :, :])
    sem_output_max = torch.argmax(sem_output_softmax[:, :, :, :], dim=1)

    # Create a grid of the images and masks
    image_grid = torchvision.utils.make_grid(images)
    ver_grad_mask_grid = torchvision.utils.make_grid(masks[:, 1:2, :, :])
    hor_grad_mask_grid = torchvision.utils.make_grid(masks[:, 2:3, :, :])
    phenotype_mask_grid = torchvision.utils.make_grid(masks[:, 0:1, :, :])
    output1_grid = torchvision.utils.make_grid(output[:, 0:1, :, :])
    output2_grid = torchvision.utils.make_grid(output[:, 1:2, :, :])
    sem_output_max_grid = torchvision.utils.make_grid(
        torch.unsqueeze(sem_output_max.to(torch.float32), dim=1)
    )

    if instance_masks is not None:
        instance_mask_grid = torchvision.utils.make_grid(instance_masks)
        wandb.log({f"{split}_instance_masks": [wandb.Image(instance_mask_grid)]})

    # Log the grids to WandB
    wandb.log({f"{split}_image_samples": [wandb.Image(image_grid)]})
    wandb.log({f"{split}_vert_mask_samples": [wandb.Image(ver_grad_mask_grid)]})
    wandb.log({f"{split}_horz_mask_samples": [wandb.Image(hor_grad_mask_grid)]})
    wandb.log({f"{split}_phenotype_mask_samples": [wandb.Image(phenotype_mask_grid)]})
    wandb.log({f"{split}_vertgrad_outputs": [wandb.Image(output1_grid)]})
    wandb.log({f"{split}_horizgrad_outputs": [wandb.Image(output2_grid)]})
    wandb.log({f"{split}_semseg_outputs": [wandb.Image(sem_output_max_grid)]})


def plot_confusion_matrix(
    confusion_matrix: np.ndarray, class_names: list[str]
) -> plt.Figure:
    """Plot a confusion matrix using sklearn's ConfusionMatrixDisplay.

    Parameters
    ----------
    confusion_matrix : np.ndarray
        The confusion matrix to be plotted. It should be a 2D numpy array.
    class_names : List[str]
        The names of the classes, to be used as labels on the x and y axes.

    Returns
    -------
    plt.Figure
        The matplotlib Figure object with the plot.
    """
    fig, ax = plt.subplots()
    disp = ConfusionMatrixDisplay(
        confusion_matrix=confusion_matrix.astype(int),
        display_labels=class_names,
    )
    disp.plot()
    return plt


def create_instance_contour_overlay(
    instance_mask: np.ndarray,
    image: np.ndarray,
) -> np.ndarray:
    """Overlay contours of instance mask labels onto an image.

    Extracts contours for each unique instance in the mask and draws them
    on the image using randomly generated colors for visual distinction.

    Parameters
    ----------
    instance_mask : np.ndarray
        Instance segmentation mask where each unique non-zero value represents
        a different instance. Background should be labeled as 0.
    image : np.ndarray
        Input image on which to draw the contours. The image is modified in-place.

    Returns
    -------
    np.ndarray
        The input image with instance contours overlaid. Each instance is
        outlined with a unique random color.

    Notes
    -----
    - Background pixels (value 0) are skipped
    - Contours are drawn with 1-pixel thickness
    - Random colors are generated for each instance using RGB values 0-255
    - Uses OpenCV's RETR_EXTERNAL to find only outer contours
    """
    unique_labels = np.unique(instance_mask)
    for label in unique_labels:
        if label == 0:
            continue  # Skip background
        label_mask = (instance_mask == label).astype(np.uint8)
        contours, _ = cv2.findContours(
            label_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        # Random color for each nucleus
        color = tuple(np.random.randint(0, 255, 3).tolist())
        cv2.drawContours(image, contours, -1, color, 1)
    return image


def create_gradient_overlay(
    gradient_mask: np.ndarray,
    image: np.ndarray,
    alpha: float = 0.1,
    colormap: int = cv2.COLORMAP_JET,
) -> np.ndarray:
    """Overlay a gradient mask onto an image with transparency.

    Creates a colored overlay from a gradient mask (e.g., probability or flow map)
    and blends it with the original image for visualization purposes.

    Parameters
    ----------
    gradient_mask : np.ndarray
        2D gradient or probability mask to overlay. Values are normalized to 0-255
        range automatically.
    image : np.ndarray
        Input image on which to overlay the gradient. Can be grayscale or RGB.
    alpha : float, optional
        Transparency factor for the overlay, by default 0.1. Range is 0.0-1.0
        where 0.0 is fully transparent and 1.0 is fully opaque.
    colormap : int, optional
        OpenCV colormap to apply to the gradient mask, by default cv2.COLORMAP_JET.

    Returns
    -------
    np.ndarray
        RGB image with the gradient overlay applied. The result is always 3-channel.

    Notes
    -----
    - Gradient mask is automatically normalized to 0-255 range
    - Grayscale images are converted to RGB before overlay
    - The overlay uses cv2.addWeighted for alpha blending
    """
    # Normalize the gradient mask to 0-255
    grad_norm = cv2.normalize(gradient_mask, None, 0, 255, cv2.NORM_MINMAX)
    grad_uint8 = grad_norm.astype(np.uint8)
    grad_color = cv2.applyColorMap(grad_uint8, colormap)

    # Ensure image is 3-channel
    if image.ndim == 2:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        image_rgb = image.copy()

    overlay = cv2.addWeighted(image_rgb, 1 - alpha, grad_color, alpha, 0)
    return overlay


def compute_mask_difference(mask_a: torch.Tensor, mask_b: torch.Tensor):
    """Compute the pixel-wise differences between two instance masks.

    This function finds the best matching instances between two masks using IoU
    and creates a difference mask showing non-overlapping regions and unmatched
    instances.

    Parameters
    ----------
    mask_a : torch.Tensor
        First instance mask where each unique value represents a different instance.
    mask_b : torch.Tensor
        Second instance mask to compare against mask_a. Must have the same shape
        as mask_a.

    Returns
    -------
    torch.Tensor
        Difference mask showing:
        - Pixels from mask_a that don't overlap with their best match in mask_b
        - Pixels from mask_b that don't overlap with their best match in mask_a
        - Unmatched instances from mask_b (instances with zero IoU)

    Notes
    -----
    - Background pixels (value 0) are ignored in the comparison
    - Instance matching is based on the highest IoU score
    - The returned mask uses the same data type as the input masks
    """
    assert mask_a.shape == mask_b.shape

    def _calc_iou(a, b):
        """Calculate the intersection over union between two masks."""
        intersection = torch.logical_and(a, b).sum()
        union = torch.logical_or(a, b).sum()
        return intersection / union if union > 0 else 0

    diffs = torch.zeros_like(mask_a, dtype=mask_a.dtype)
    labels_a, labels_b = torch.unique(mask_a), torch.unique(mask_b)

    pairs = {}
    for la in labels_a:
        bin_mask_a = mask_a == la
        best_iou, matching_label_b = 0, -1

        # For each mask in A find the mask in be with the highest IOU in B.
        for lb in labels_b:
            if la == 0 or lb == 0:
                continue
            bin_mask_b = mask_b == lb
            iou = _calc_iou(bin_mask_a, bin_mask_b)
            if iou > best_iou:
                best_iou = iou
                matching_label_b = lb

        if matching_label_b != -1:
            pairs[la] = matching_label_b

    # Add masks from b which we could not match to a (bc the IOU was 0):
    for lb in labels_b:
        if lb not in pairs.values():
            diffs += (mask_b == lb) * lb

    for la, lb in pairs.items():
        bin_mask_a = mask_a == la
        bin_mask_b = mask_b == lb
        diffs += (bin_mask_a & ~bin_mask_b) * la
        diffs += (bin_mask_b & ~bin_mask_a) * lb

    return diffs


def make_comparison_fig(
    tile: np.ndarray,
    pred_mask: torch.Tensor,
    velox_pred_masks: np.ndarray,
    gt_mask: np.ndarray,
    tile_title="",
):
    """Create a comparison figure showing different mask predictions and ground truth.

    Generates a side-by-side visualization comparing the original image,
    prediction masks, differences, and ground truth for visual analysis.

    Parameters
    ----------
    tile : np.ndarray
        Original image tile to display.
    pred_mask : torch.Tensor
        Predicted instance mask from the model.
    velox_pred_masks : np.ndarray
        Alternative prediction mask (e.g., from Velox system) for comparison.
    gt_mask : np.ndarray
        Ground truth instance mask.
    tile_title : str, optional
        Title to display above the original image, by default "".

    Returns
    -------
    matplotlib.figure.Figure
        Figure object containing the comparison visualization with 5 subplots:
        original image, prediction, velox prediction, differences, and ground truth.

    Notes
    -----
    - Instance counts are displayed in subplot titles
    - Differences are computed using IoU-based matching
    - All masks are colorized using the same color scheme for consistency
    """
    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    axes[0].imshow(tile)
    axes[0].set_axis_off()
    if tile_title:
        axes[0].set_title(tile_title)

    colorize_mask(pred_mask, axes[1])
    ninstances = len(np.unique(pred_mask)) - 1
    axes[1].set_title(f"Cellpose pred: {ninstances} instances")

    colorize_mask(velox_pred_masks, axes[2])
    ninstances = len(np.unique(velox_pred_masks)) - 1
    axes[2].set_title(f"velox pred: {ninstances} instances")

    diff_mask = compute_mask_difference(pred_mask, torch.from_numpy(velox_pred_masks))
    colorize_mask(diff_mask.numpy(), axes[3])
    axes[3].set_title("differences")

    ninstances = len(np.unique(gt_mask)) - 1
    colorize_mask(gt_mask, axes[4])
    axes[4].set_title(f"gt: {ninstances} instances")

    return fig


def create_instance_mask_overlay(
    instance_mask: np.ndarray,
    image: np.ndarray,
    alpha: float = 0.5,
    random_colors: bool = True,
) -> np.ndarray:
    """Overlay an instance segmentation mask on an image with transparency.

    Creates a colorized version of the instance mask and blends it with the
    original image, allowing for visualization of segmentation results.

    Parameters
    ----------
    instance_mask : np.ndarray
        Instance segmentation mask where each unique non-zero value represents
        a different instance. Background should be labeled as 0.
    image : np.ndarray
        Input image on which to overlay the mask. Can be grayscale or RGB.
    alpha : float, optional
        Transparency factor for the overlay, by default 0.5. Range is 0.0-1.0
        where 0.0 is fully transparent and 1.0 is fully opaque.
    random_colors : bool, optional
        If True, randomly shuffle the instance colors while keeping background
        black. If False, use sequential HSV colors. Default is True.

    Returns
    -------
    np.ndarray
        RGB image with the instance mask overlay applied.

    Notes
    -----
    - Background pixels (value 0) are not overlaid.
    - Grayscale images are converted to RGB before overlay.
    - The overlay uses cv2.addWeighted for alpha blending.
    """
    # Create a colorized version of the instance mask
    labels = np.unique(instance_mask)
    labels = labels[labels != 0]  # Exclude background
    n_instances = len(labels)

    color_mask = np.zeros_like(image, dtype=np.uint8)

    # Generate colors
    hsv_colors = []
    for i in range(n_instances):
        hue = i / n_instances if n_instances > 0 else 0
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        hsv_colors.append(tuple(int(c * 255) for c in rgb))

    if random_colors:
        rng = np.random.default_rng(42)
        rng.shuffle(hsv_colors)

    color_map = {label: color for label, color in zip(labels, hsv_colors)}

    for label in labels:
        color_mask[instance_mask == label] = color_map[label]

    # Blend the color mask and the image
    overlay = cv2.addWeighted(image, 1, color_mask, alpha, 0)

    return overlay
