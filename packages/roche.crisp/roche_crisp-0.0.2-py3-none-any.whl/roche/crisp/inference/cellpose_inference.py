"""Inference pipeline for cellpose based segmentation-classification."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional, Union

import albumentations
import imageio
import numpy as np
import torch
from loguru import logger as LOG
from tqdm import tqdm

from roche.crisp.datamodules import CellposeDataset
from roche.crisp.utils import common_utils, transforms, visualization
from roche.crisp.utils.cellpose_utils import postprocess
from roche.crisp.utils.common_utils import (
    create_panoptic_mask_from_instance_and_semantic_masks,
)
from roche.crisp.utils.velox_postprocessing import velox_post_process

LOG.remove()
LOG.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}")


def load_data(
    input_data: Union[str, List[np.ndarray]],
    batch_size: int = 4,
    use_rgb: bool = False,
    segmentation_type: str = "instance",
    diameter: float = 24.225065,
    diam_mean: float = 30.0,
) -> torch.utils.data.DataLoader:
    """Create dataLoader object to pre-load input images.

    Parameters
    ----------
    input_data : Union[str, List[np.ndarray]]
        Path to the csv file containing the image paths or list of numpy arrays.
    batch_size : int, optional
        Batch size for the DataLoader, by default is 4.
    use_rgb : bool, optional
        Whether to use RGB images, by default False.
    segmentation_type : str, optional
        Type of segmentation to perform. Either 'instance' or 'semantic'.
    diameter : float, optional
        Estimated diameter of objects to segment, by default 24.225065.
    diam_mean : float, optional
        Mean diameter for resampling, by default 30.0.

    Returns
    -------
    torch.utils.data.DataLoader
        DataLoader object containing the loaded dataset.
    """
    if isinstance(input_data, str):
        image_arrays = None
    else:
        image_arrays = input_data

    transforms = albumentations.Compose(
        [
            albumentations.CenterCrop(height=224, width=224),
        ]
    )

    test_dataset = CellposeDataset(
        "predict",
        input_data,
        image_arrays=image_arrays,
        transform=transforms,
        segmentation_type=segmentation_type,
        use_rgb=use_rgb,
        diameter=diameter,
        diam_mean=diam_mean,
    )

    return torch.utils.data.DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=4,
        # collate_fn=test_dataset.my_collate,
    )


def run_inference(
    input_data: Union[str, List[np.ndarray]],
    net: torch.nn.Module,
    batch_size: int = 4,
    postprocess_backend: Literal["cellpose", "velox"] = "velox",
    segmentation_type: Literal["instance", "semantic"] = "instance",
    use_rgb: bool = False,
    diameter: float = 24.225065,
    diam_mean: float = 30.0,
    cellprob_threshold: float = 0.2,
    flow_threshold: float = 0.55,
    min_size: int = 32,
    save_dir: Optional[str] = None,
    gpu: bool = True,
    seed: int = 7,
) -> List[np.ndarray]:
    """Run inference on the loaded data using the loaded model.

    Loads the data using `load_data` and the model using `load_model`.
    Performs inference on each sample in the data using the loaded model.

    Parameters
    ----------
    input_data : Union[str, List[np.ndarray]]
        Path to the csv file containing the image paths or list of numpy arrays.
    net : torch.nn.Module
        Model to use for inference.
    batch_size : int
        Batch size for the dataLoader, by default 4.
    postprocess_backend : Literal["cellpose", "velox"], optional
        Backend to use for post-processing. Either 'cellpose' or 'velox',
    segmentation_type : Literal["instance", "semantic"], optional
        Type of segmentation to perform. Either 'instance' or 'semantic',
    use_rgb : bool, optional
        Whether to use RGB images, by default False.
    diameter : float, optional
        Estimated diameter of objects to segment, by default 24.225065.
    diam_mean : float, optional
        Mean diameter for resampling, by default 30.0.
    cellprob_threshold : float, optional
        Cell probability threshold for post-processing, by default 0.2.
    flow_threshold : float, optional
        Flow threshold for post-processing, by default 0.55.
    min_size : int, optional
        Minimum size of objects to keep during post-processing, by default 32.
    save_dir : Optional[str], optional
        Path to save the output masks, by default None
    gpu : bool, optional
        Whether to use GPU for inference, by default True.
    seed : int, optional
        Random seed for reproducibility, by default 7.

    Returns
    -------
    List[numpy.ndarray]
        List of instance masks if nclasses = 6, or list of semantic
        masks if nclasses = 3.

    Raises
    ------
    ValueError
        If `postprocess_backend` is not 'cellpose' or 'velox'.

    Notes
    -----
    Cellpose Threshold:
        Decrease this threshold if cellpose is not returning as many ROIs as
        you would expect. Similarly, increase this threshold if cellpose is
        returning too many ROIs
    Flow Threshold:
        Increase this threshold if cellpose is not returning as many ROIs as
        you would expect. Similarly, decrease this threshold if cellpose is
        returning too many ill-shaped ROIs.
    """
    if postprocess_backend not in {"cellpose", "velox"}:
        raise ValueError(
            "postprocess_backend must be either 'cellpose' or 'velox', "
            f"got {postprocess_backend!r}."
        )

    common_utils.seed_everything(seed)

    if torch.cuda.is_available() and gpu:
        torch.cuda.empty_cache()
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = True

    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)

    if gpu and torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    dataloader = load_data(
        input_data,
        batch_size,
        use_rgb=use_rgb,
        segmentation_type=segmentation_type,
        diameter=diameter,
        diam_mean=diam_mean,
    )

    process_start = datetime.now().replace(microsecond=0)
    final_masks = []
    softmax = torch.nn.Softmax(dim=1)

    for _, sample in enumerate(tqdm(dataloader)):
        if len(sample):
            imgs = sample["image"]
            orig_imgs = sample["original_image"]

            imgs = imgs.to(device)

            resampled_width = int((imgs.shape[-2] + 1) / (diam_mean / diameter))
            resampled_height = int((imgs.shape[-1] + 1) / (diam_mean / diameter))

            input_data, ysub_pad, xsub_pad = common_utils.pad_image(imgs)

            with torch.no_grad():
                output = net(input_data)[0]

            output = common_utils.remove_padding(output, ysub_pad, xsub_pad)

            output = transforms.resize_image_gpu(
                output, resampled_width, resampled_height
            )
            gradients = output[:, :2]
            if segmentation_type == "instance":
                cellprobs = output[:, 2:].squeeze(1)
            else:
                sem_logits = output[:, 2:]
                sem_output_softmax = softmax(sem_logits)
                cellprobs = 1 - sem_output_softmax[:, 0]
            if postprocess_backend == "cellpose":
                instance_masks_tensor = postprocess(
                    output,
                    vectorized=True,
                    segmentation_type=segmentation_type,
                    cellprob_threshold=cellprob_threshold,
                    flow_threshold=flow_threshold,
                )
                instance_masks = instance_masks_tensor.numpy()
            else:
                instance_masks_tensor = velox_post_process(
                    cellprobs,
                    gradients,
                    cellprob_threshold=cellprob_threshold,
                    min_pixels=min_size,
                )

                instance_masks = instance_masks_tensor.cpu().numpy()

            filenames = sample["filename"]
            if save_dir is not None:
                Path(save_dir).mkdir(exist_ok=True, parents=True)

                for segm, name, img in zip(instance_masks, filenames, orig_imgs):
                    save_output(segm, Path(save_dir, "mask_" + name))
                    overlay = visualization.create_instance_mask_overlay(
                        segm, img.numpy()
                    )
                    save_output(overlay, Path(save_dir, "overlay_" + name))

            else:
                if segmentation_type == "instance":
                    final_masks.extend(instance_masks)
                else:
                    sem_output_max = torch.argmax(sem_output_softmax[:, 1:], dim=1) + 1
                    sem_output_max = sem_output_max.cpu().numpy()
                    sem_output_max = sem_output_max.astype(np.uint8)
                    panoptic_seg_masks = []
                    create_panoptic_mask = (
                        create_panoptic_mask_from_instance_and_semantic_masks
                    )
                    for mask, sem in zip(instance_masks, sem_output_max):
                        panoptic_mask = create_panoptic_mask(mask, sem)
                        panoptic_seg_masks.append(panoptic_mask)
                    final_masks.extend(panoptic_seg_masks)

    LOG.info(
        f"Total time taken for mask generation \
            {datetime.now().replace(microsecond=0) - process_start}"
    )

    return final_masks if not save_dir else None


def save_output(seg_pred: np.ndarray, save_path: Path = None):
    """Perform parallel post processing on model predictions and return the result.

    Optional save the result to disk if `save_path` is provided.

    Parameters
    ----------
    seg_mask : numpy.ndarray
        nuclei mask
    save_path : pathlib.Path, optional
        Path for saving the mask.
        Works only if save_dir is passed to `run_inference` function
    """
    if save_path:
        Path(save_path).parent.mkdir(exist_ok=True, parents=True)
        imageio.imwrite(save_path, seg_pred.astype("uint8"))

    return seg_pred
