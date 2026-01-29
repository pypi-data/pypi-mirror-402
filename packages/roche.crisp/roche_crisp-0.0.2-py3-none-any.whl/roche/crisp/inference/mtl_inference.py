"""Inference pipeline for multi-task segmentation-classification model."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Final, List, Optional, Union

import imageio.v3 as imageio
import numpy as np
import torch
from loguru import logger as LOG
from skimage.segmentation import watershed
from torch.nn import functional as F
from torch.utils.data.dataloader import default_collate
from torch.utils.data.dataset import Dataset
from torchvision import transforms
from tqdm import tqdm

from roche.crisp.networks.mtl_residual_unet import ResUNet
from roche.crisp.utils import common_utils, mtl_utils

LOG.remove()
LOG.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")

# set of constant values and flags for inference
SEED: Final = 7
MEAN: Final = [0.66285152, 0.4618157, 0.67189521]
STD: Final = [
    0.20342005,
    0.22243348,
    0.15656173,
]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class CellDataset(Dataset):
    """Custom dataset class for pre-loading of images."""

    def __init__(
        self,
        input_imgs: Union[List[np.ndarray], List[str]],
        transform=None,
    ):
        """Initialize instance of the class.

        Parameters
        ----------
        input_imgs : Union[List[np.ndarray], List[str]]
            A list of numpy np.uint8 images or path to image files.
        transform : callable, optional
            A function/transform to apply to the images. Default is None.
        """
        self.output_logger = LOG
        super().__init__()
        self.transform = transform
        self.images = input_imgs

    def __getitem__(self, index: int) -> Union[None, tuple]:
        """Get an item from the dataset.

        Parameters
        ----------
        index : int
            Index of the item to retrieve.

        Returns
        -------
        tuple
            A tuple containing the converted image and its name.
        """
        try:
            image = self.images[index]
            filename = str()
            if isinstance(image, str):
                image_path = Path(image)
                filename = os.path.join(
                    image_path.parent.name, "phenotype_mask_" + image_path.name
                )
                image = imageio.imread(image_path)

            if self.transform:
                image = self.transform(image)

            return image, filename

        except Exception as e:
            self.output_logger.exception(
                f"Processing FAILED for {self.images[index]} with exception, {e}"
            )
            return None

    def __len__(self):
        """Get the length of the dataset.

        Returns
        -------
        int
            Length of the dataset.
        """
        return len(self.images)

    def my_collate(self, batch: List):
        """Collate batch of data.

        Filters out `None` values and if no items, returns empty list.

        Parameters
        ----------
        batch : List
            List of batch items.

        Returns
        -------
        list
            List of collated batch items.
        """
        batch = list(filter(lambda x: x is not None, batch))
        if len(batch) > 0:
            return default_collate(batch)
        else:
            return []


def load_model(model_path: str) -> torch.nn.Module:
    """Load model weights.

    Creates an instance of the ResUnet model and loads the model
    check point based on the specified model path. If CUDA is available,
    the model is moved to the GPU and wrapped in a DataParallel module if
    multiple GPUs are available.

    Returns
    -------
    torch.nn.Module
        Loaded model.
    """
    net = ResUNet(seg_c=3, det_c=4)
    net = net.to(DEVICE)
    weights = torch.load(model_path, map_location=DEVICE)
    net.load_state_dict(weights)

    if torch.cuda.device_count() > 1:
        net = torch.nn.DataParallel(net)

    return net.eval()


def load_data(
    images: Union[List[np.ndarray], List[str]], batch_size: int, num_workers: int = 8
) -> torch.utils.data.DataLoader:
    """Create dataLoader object to pre-load input images.

    Parameters
    ----------
    images : Union[List[np.ndarray], List[str]]
        A list of numpy np.uint8 images or path to image files.
    batch_size : int
        Batch size for the DataLoader.
    num_workers : int, optional
        Number of workers for the DataLoader, by default is 8.

    Returns
    -------
    torch.utils.data.DataLoader
        DataLoader object containing the loaded dataset.
    """
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=MEAN, std=STD),
        ]
    )

    test_dataset = CellDataset(images, transform)

    dataloader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=num_workers,
        collate_fn=test_dataset.my_collate,
    )

    return dataloader


def run_inference(
    images: Union[List[np.ndarray], List[str]],
    model_path: str,
    batch_size: int,
    num_workers: Optional[int] = 8,
    save_dir: Optional[str] = None,
) -> Optional[List[np.ndarray]]:
    """Run model inference on given input images.

    Loads the data using `load_data` and the model using `load_model`,
    and performs inference on batches of data.

    Parameters
    ----------
    images : Union[List[numpy.ndarray], List[str]]
        A list of numpy np.uint8 images or path to image files.
    model_path : str
        Path to model checkpoint.
    batch_size : int
        Batch size for the dataLoader.
    num_workers : Optional[int]
        Number of workers for the dataLoader, by default 8.
    save_dir : Optional[str]
        Optional directory path for saving generated masks.
        Required if `images` is provided as list of file paths
        as output file name is inferred from that.

    Returns
    -------
    Optional[List[np.ndarray]]
        List of semantic masks if `save_dir` is not provided.

    Raises
    ------
    ValueError
        If `images` is a list of file paths and `save_dir` is not provided.
    """
    common_utils.seed_everything(SEED)

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = True

    if isinstance(images[0], str) and save_dir is None:
        raise ValueError(
            "`images` is a list of file paths,"
            " so by default `save-dir` is required for saving the output to the disk."
            " Alternatively if you do not wish to save the output,"
            " you can pass `images` as list of numpy arrays."
        )

    dataloader = load_data(images, batch_size, num_workers)
    net = load_model(model_path)

    process_start = datetime.now().replace(microsecond=0)
    out_masks = []
    for sample in tqdm(dataloader):
        if len(sample) != 0:
            input_data, filenames = sample
            input_data = input_data.to(DEVICE)

            with torch.no_grad():
                # compute output
                seg_out, det_out = net(input_data)

            # get segmentation predictions
            seg_pred = torch.argmax(seg_out, dim=1).cpu().numpy()

            # get detection predictions
            det_prob = F.softmax(det_out, dim=1).cpu().numpy()

            for idx in range(len(seg_pred)):
                seg_pred_id = seg_pred[idx]
                det_prob_id = det_prob[idx]
                filename = filenames[idx]

                binary_mask, det_points = mtl_utils.post_process_mask(
                    seg_pred_id, det_prob_id
                )

                semantic_mask = watershed(
                    image=binary_mask,
                    markers=det_points,
                    mask=binary_mask,
                )

                if save_dir:
                    save_path = Path(save_dir, filename)
                    Path(save_path).parent.mkdir(exist_ok=True, parents=True)
                    imageio.imwrite(save_path, semantic_mask.astype("uint8"))
                else:
                    out_masks.append(semantic_mask)

    LOG.info(
        "Total time taken for inferencing"
        f" {datetime.now().replace(microsecond=0) - process_start}"
    )
    if not save_dir:
        return out_masks
    return None
