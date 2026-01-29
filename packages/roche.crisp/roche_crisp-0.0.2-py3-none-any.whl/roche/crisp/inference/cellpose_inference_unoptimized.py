"""Inference pipeline for cellpose based segmentation-classification."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Final, List, Optional, Tuple, Union

import imageio.v3 as imageio
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data.dataloader import default_collate
from torch.utils.data.dataset import Dataset
from tqdm import tqdm

from roche.crisp.networks import Cellpose
from roche.crisp.utils import cellpose_utils, common_utils, transforms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s\n",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger(__name__)

# set of constant values and flags for inference
SEED: Final = 7
NITER: Final = 200
MIN_SIZE: Final = 32
DIAMETER: Final = 24.225065
DIAM_MEAN: Final = 30.0
RESAMPLE: Final = True
PANOP_MASKS: Final = False
# note: cellprob & flow thresholds set below are for panoptic segmentation model
CELLPROB_THRESHOLD: Final = 0.2
FLOW_THRESHOLD: Final = 0.55
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class CellposeDataset(Dataset):
    """Custom dataset class to handling cell data.

    Attributes
    ----------
    input_imgs : list
        List of input image paths.
    transform : callable, optional
        A function/transform to apply to the images. Default is None.
    """

    def __init__(
        self,
        input_imgs,
        transform=None,
    ):
        """Instantiate."""
        super().__init__()
        self.transform = transform
        self.images = input_imgs

    def __getitem__(self, index: int):
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
            orig_img = self.images[index]
            filename = str()
            if isinstance(orig_img, str):
                image_path = Path(orig_img)
                filename = os.path.join(
                    image_path.parent.name, "phenotype_mask_" + image_path.name
                )
                orig_img = imageio.imread(image_path)
            orig_img = np.expand_dims(orig_img, 0)
            if len(np.unique(orig_img)) != 1:  # (1, 512, 512, 3)
                converted_img = transforms.convert_image(
                    orig_img,
                    channels=[0, 0],
                    channel_axis=3,
                    z_axis=0,  # (512, 512, 2)
                    do_3D=False,
                    normalize=False,
                    invert=False,
                    nchan=2,
                )

                if converted_img.ndim < 4:
                    converted_img = converted_img[np.newaxis, ...]
                    # (1, 512, 512, 2)

                converted_img = transforms.normalize_img(
                    converted_img, invert=False
                )  # (1, 512, 512, 2)

                rescale = DIAM_MEAN / DIAMETER  # 1.238386770066458

                if rescale != 1.0:
                    converted_img = transforms.resize_image(
                        converted_img, rsz=rescale
                    )  # (1, 634, 634, 2)
                return converted_img, filename

        except Exception as e:
            print(
                f"Processing FAILED for {self.images[index]} with exception, {e}",
                flush=True,
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


def post_process(
    dP: torch.Tensor,
    cellprob: torch.Tensor,
    niter: int = 200,
    cellprob_threshold: float = 0.2,
    flow_threshold: float = 0.55,
    interp: bool = True,
    resize: Optional[bool] = None,
    use_gpu: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """Perform post-processing on the model output."""
    p, cp_mask = cellpose_utils.compute_masks_flow(
        dP,
        cellprob,
        niter=niter,
        cellprob_threshold=cellprob_threshold,
        flow_threshold=flow_threshold,
        interp=interp,
        resize=resize,
        use_gpu=use_gpu,
        device=DEVICE,
    )
    return p, cp_mask


def load_data(
    images: Union[List[np.ndarray], List[str]], batch_size: int = 4
) -> torch.utils.data.DataLoader:
    """Create dataLoader object to pre-load input images.

    Parameters
    ----------
    images : Union[List[np.ndarray], List[str]]
        List of NumPy arrays containing the input images.

    batch_size : int, optional
        Batch size for the DataLoader, by default is 4.

    Returns
    -------
    torch.utils.data.DataLoader
        DataLoader object containing the loaded dataset.
    """
    test_dataset = CellposeDataset(images)

    return torch.utils.data.DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=0,
        collate_fn=test_dataset.my_collate,
    )


def load_model(
    model_path: str, nchan: int = 2, nout: int = 6, sz: int = 3, device="cpu"
) -> nn.Module:
    """Load model weights.

    Creates an instance of the CellposeModel and loads the model
    check point based on the specified model path. If CUDA is available,
    the model is moved to the GPU and wrapped in a DataParallel module if
    multiple GPUs are available.

    Parameters
    ----------
    model_path : str
        Path to the model file.
    nchan : int, optional
        No. of channels in input image, by default 2
    nout : int, optional.
        No. of output channels, by default 6
    sz : int, optional
        Kernel size, by default 3
    device : str, optional
        Device to load the model on, by default 'cpu'

    Returns
    -------
    torch.nn.Module
        Loaded model.
    """
    net = Cellpose(
        channels_list=[nchan, 32, 64, 128, 256],
        num_classes=nout,
        kernel_size=sz,
    )
    net = net.to(device)
    state_dict = torch.load(model_path, map_location=device)
    net.load_state_dict(state_dict)

    if torch.cuda.is_available() > 1:
        net = torch.nn.DataParallel(net)

    return net.eval()


def run_inference(
    images: Union[List[np.ndarray], List[str]],
    model_path: str,
    batch_size: int = 4,
    nclasses: int = 6,
    save_dir: Optional[str] = None,
) -> List[np.ndarray]:
    """Run inference on the loaded data using the loaded model.

    Loads the data using `load_data` and the model using `load_model`.
    Performs inference on each sample in the data using the loaded model.

    Parameters
    ----------
    images : Union[List[np.ndarray], List[str]]
        A list of numpy np.uint8 images.
    model_path : str
        Path to model checkpoint.
    batch_size : int
        Batch size for the dataLoader, by default 4.
    nclasses : int
        number of classes for classification, by default 6
    save_dir : Optional[str], optional
        Path to save the output masks, by default None

    Returns
    -------
    List[numpy.ndarray]
        List of instance masks if nclasses = 6, or list of semantic
        masks if nclasses = 3.
    """
    common_utils.seed_everything(SEED)

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = True

    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)

    dataloader = load_data(images, batch_size)
    net = load_model(model_path, nchan=2, nout=nclasses, device=DEVICE)

    process_start = datetime.now().replace(microsecond=0)
    final_masks = []

    for _, sample in enumerate(tqdm(dataloader)):
        if len(sample) != 0:
            imgs, filenames = sample
            imgs = np.squeeze(imgs, 1)

            if imgs.ndim == 4:
                imgs = np.transpose(imgs, (0, 3, 1, 2))
            else:
                imgs = np.transpose(imgs, (2, 0, 1))

            imgs = imgs.to(DEVICE)

            if RESAMPLE:
                resampled_width = int((imgs.shape[-2] + 1) / (DIAM_MEAN / DIAMETER))
                resampled_height = int((imgs.shape[-1] + 1) / (DIAM_MEAN / DIAMETER))

            input_data, ysub_pad, xsub_pad = common_utils.pad_image_ND_gpu(imgs)

            with torch.no_grad():
                yf = net(input_data)[0]

            yf = common_utils.remove_padding(yf, ysub_pad, xsub_pad)

            if RESAMPLE:
                yf = transforms.resize_image_gpu(yf, resampled_width, resampled_height)

            softmax = torch.nn.Softmax(dim=1)
            sem_output_softmax = softmax(yf[:, 2:])
            cellprob = (
                1 - sem_output_softmax[:, 0]
                if nclasses != 3
                else sem_output_softmax[:, 0]
            )
            dP = yf[:, :2]
            do_3D = True

            imask = []
            ip = []
            for dp, cp in zip(dP, cellprob):
                p, cp_mask = post_process(
                    dp,
                    cp,
                    NITER,
                    CELLPROB_THRESHOLD,
                    FLOW_THRESHOLD,
                    True,
                    None,
                    torch.cuda.is_available(),
                )
                ip.append(p)
                imask.append(cp_mask)

            argument_set_p = [(p, mask) for mask, p in zip(imask, ip)]
            masks = []
            for p, mask in argument_set_p:
                result = cellpose_utils.get_masks(p, mask)
                masks.append(result)

            cleaned_masks = []
            for mask, dp, p in zip(masks, dP, ip):
                mask = cellpose_utils.compute_masks_rm_flow(
                    mask,
                    dp,
                    p,
                    FLOW_THRESHOLD,
                    torch.cuda.is_available(),
                    DEVICE,
                    do_3D,
                )
                cleaned_masks.append(mask)

            argument_set = [(mask, None, MIN_SIZE) for mask in cleaned_masks]
            instance_masks = []
            for mask, resize, min_size in argument_set:
                result = cellpose_utils.compute_masks_fl_rm(mask, resize, min_size)
                instance_masks.append(result)

            instance_masks = np.array(instance_masks)

            if save_dir is not None:
                Path(save_dir).mkdir(exist_ok=True, parents=True)
                filenames = [Path(save_dir, name) for name in filenames]

                for segm, name in zip(instance_masks, filenames):
                    save_output(segm, Path(save_dir, name))

            else:
                if not PANOP_MASKS:
                    final_masks.extend(instance_masks)
                else:
                    sem_output_max = torch.argmax(sem_output_softmax[:, 1:], dim=1) + 1
                    sem_output_max = sem_output_max.cpu().numpy()
                    panoptic_seg_masks = []
                    for mask, sem in zip(instance_masks, sem_output_max):
                        panoptic_mask = cellpose_utils.inst_sem_2_panoptic_seg_mask(
                            mask, sem
                        )
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


if __name__ == "__main__":
    model_path = (
        "./cellpose_residual_on_style_on_concatenation_off_tr"
        "ain_2022_10_13_02_27_25.924486_epoch_501"
    )
    im = imageio.imread(
        "data/fovs/be8b3a5e-cee9-4087-8aa1-1cc795e8dd78_7dc1a5b9-7f01-482e-83ed-86c6a0e11892__SCANRES0.25_TILESIZE256_OVERLAP0_X9824_Y78432.png"
    )
    result = run_inference([im], model_path)
