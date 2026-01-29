"""Cellpose-based nuclei detection and segmentation.

This module provides a wrapper class for performing nuclei detection and instance
segmentation using Cellpose models. It supports both CPU and GPU inference, multiple
post-processing backends (Cellpose and Velox), and configurable thresholds for
fine-tuning detection sensitivity.

Examples
--------
>>> detector = NucleiDetectionCellpose(
...     model_checkpoint="path/to/checkpoint.pth",
...     batch_size=8,
...     gpu=True,
...     cellpose_threshold=0.2,
...     flow_threshold=0.55,
... )
>>> masks = detector.get_mask(images)
"""

import sys
from pathlib import Path
from typing import List, Literal, Optional

import cv2
import numpy as np
import torch
from loguru import logger as LOG
from skimage.measure import label, regionprops

from roche.crisp.networks import Cellpose

from .cellpose_inference import run_inference
from .nuclei_detection_base import NucleiDetectionBase
from .nuclei_information import NucleiInformation

LOG.remove()
LOG.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}",
)


class NucleiDetectionCellpose(NucleiDetectionBase):
    """Wrapper class for cellpose based nuclei detection.

    Attributes
    ----------
    model_checkpoint : str
        Path to model checkpoint.
    batch_size : int
        Number of samples to process in one batch.
    nclasses : int
        Number of classes the model outputs, by default 6.
    segmentation_type : str
        Type of segmentation to perform. Either 'instance' or 'semantic'.
    nchan : int
        Number of channels in input image, by default 3.
    gpu : bool
        Flag to indicate whether to use GPU for inference.
    cellpose_threshold : float
        Threshold for cellpose post-processing.
    flow_threshold : float
        Flow threshold for cellpose post-processing.
    min_size : int
        Minimum size of objects to keep during post-processing.
    postprocess_backend : str
        Backend to use for post-processing. Either 'cellpose' or 'velox'.
    model : torch.nn.Module
        Loaded model.

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

    def __init__(
        self,
        model_checkpoint: str,
        batch_size: int,
        nchan: int = 3,
        nclasses: int = 3,
        segmentation_type: Literal["instance", "semantic"] = "instance",
        gpu=False,
        cellpose_threshold: float = 0.2,
        flow_threshold: float = 0.55,
        min_size: int = 32,
        postprocess_backend: Literal["cellpose", "velox"] = "velox",
        seed: Optional[int] = 7,
    ):
        """Initialize the NucleiDetectionCellpose class with necessary attributes.

        Parameters
        ----------
        model_checkpoint : str
            Path to model checkpoint.
        batch_size : int
            Number of samples to process in one batch.
        nchan : int, optional
            Number of channels in input image, by default 3.
        nclasses : int
            Number of classes the model outputs, by default 3.
        segmentation_type : Literal["instance", "semantic"], optional
            Type of segmentation to perform. Either 'instance' or 'semantic'.
        gpu : bool, optional
            Flag to indicate whether to use GPU for inference.
        cellpose_threshold : float, optional
            Threshold for cellpose post-processing, by default 0.2.
        flow_threshold : float, optional
            Flow threshold for cellpose post-processing, by default 0.55.
        min_size : int, optional
            Minimum size of objects to keep during post-processing, by default 32.
        postprocess_backend : Literal["cellpose", "velox"], optional
            Backend to use for post-processing. Either 'cellpose' or 'velox',
                by default "velox".
        seed : Optional[int], optional
            Random seed for reproducibility, by default 7.
        """
        super().__init__()
        self.batch_size = batch_size
        self.model_checkpoint = model_checkpoint
        self.nclasses = nclasses
        self.segmentation_type = segmentation_type
        self.nchan = nchan
        self.gpu = gpu
        self.cellpose_threshold = cellpose_threshold
        self.flow_threshold = flow_threshold
        self.min_size = min_size
        self.seed = seed
        self.postprocess_backend = postprocess_backend
        self.model = self.load_model(
            model_path=self.model_checkpoint,
        )
        LOG.info("Cellpose model loaded successfully.")

    def fix_checkpoint_state_dict(self, state_dict):
        """Fix checkpoint state_dict by removing unwanted keys and adding model prefix.

        Parameters
        ----------
        state_dict : dict
            The original state_dict from checkpoint.

        Returns
        -------
        dict
            Fixed state_dict with proper key names.
        """
        # Keys to remove
        keys_to_remove = ["diam_mean", "diam_labels"]

        # Create new state_dict
        fixed_state_dict = {}

        for key, value in state_dict.items():
            # Skip unwanted keys
            if key in keys_to_remove:
                continue

            # Remove "model." prefix if already present
            if key.startswith("model."):
                new_key = key[6:]
            else:
                new_key = key

            fixed_state_dict[new_key] = value

        return fixed_state_dict

    def load_model(
        self,
        model_path: str,
    ) -> torch.nn.Module:
        """Load model weights.

        Creates an instance of the CellposeModel and loads the model
        check point based on the specified model path. If CUDA is available,
        the model is moved to the GPU and wrapped in a DataParallel module if
        multiple GPUs are available.

        Parameters
        ----------
        model_path : str
            Path to the model file.

        Returns
        -------
        torch.nn.Module
            Loaded model.
        """
        net = Cellpose(
            channels_list=[self.nchan, 32, 64, 128, 256],
            num_classes=self.nclasses,
        )
        if self.gpu and torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
        checkpoint = torch.load(
            model_path,
            map_location=device,
        )
        if "state_dict" in checkpoint.keys():
            fixed_state_dict = self.fix_checkpoint_state_dict(checkpoint["state_dict"])
        else:
            fixed_state_dict = self.fix_checkpoint_state_dict(checkpoint)

        net.load_state_dict(fixed_state_dict)
        net.to(device)
        if torch.cuda.is_available() > 1 and self.gpu:
            net = torch.nn.DataParallel(net)

        return net.eval()

    def get_mask(
        self,
        images: List[np.ndarray],
        use_rgb: bool = False,
        save_dir: Optional[str] = None,
    ) -> List[np.ndarray]:
        """Return segmentation mask.

        Every pixel in the mask contains the category of the cell it belongs to.
        This returns instance segmentation

        Parameters
        ----------
        images : List[np.ndarray]
            A list of numpy np.uint8 images.
        use_rgb : bool, optional
            Whether to use RGB images, by default False.
        save_dir : Optional[str], optional
            Path to save the output masks, by default None.

        Returns
        -------
        List[np.ndarray]
            A list with a nuclei instance segmentation mask for every input image.
        """
        return run_inference(
            images,
            self.model,
            self.batch_size,
            save_dir=save_dir,
            segmentation_type=self.segmentation_type,
            gpu=self.gpu,
            use_rgb=use_rgb,
            postprocess_backend=self.postprocess_backend,
            cellprob_threshold=self.cellpose_threshold,
            flow_threshold=self.flow_threshold,
            min_size=self.min_size,
            seed=self.seed,
        )

    def get_nuclei(
        self, images: List[np.ndarray], use_rgb: bool = False
    ) -> List[List[NucleiInformation]]:
        """Detect nuclei and return information about every nucleus separately.

        Runs the cellpose inference for detecting nuclei,
        and for every input image, converts the
        nuclei mask to a list of NucleiInformation.

        Parameters
        ----------
        images : List[np.ndarray]
            A list of numpy np.uint8 images.
        use_rgb : bool
            Whether to use RGB images.

        Returns
        -------
        List[List[NucleiInformation]]
            A list of nuclei detections, for every input image.
        """
        batch_masks = run_inference(
            images,
            self.model,
            self.batch_size,
            segmentation_type=self.segmentation_type,
            gpu=self.gpu,
            use_rgb=use_rgb,
            postprocess_backend=self.postprocess_backend,
            cellprob_threshold=self.cellpose_threshold,
            flow_threshold=self.flow_threshold,
            min_size=self.min_size,
            seed=self.seed,
        )
        nuclei_information = []
        for mask in batch_masks:
            image_nuclei_information = []
            labels = label(mask, connectivity=1)
            regions = regionprops(labels)
            for i, region in enumerate(regions):
                y, x = region.centroid
                min_row, min_col, max_row, max_col = region.bbox
                object_mask = np.uint8(
                    labels[min_row:max_row, min_col:max_col] == i + 1
                )
                local_coords, _ = cv2.findContours(
                    object_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
                )
                boundary = local_coords[0] + [min_col, min_row]
                image_nuclei_information.append(
                    NucleiInformation(
                        boundary=boundary, category=-1, center=(round(x), round(y))
                    )
                )
            nuclei_information.append(image_nuclei_information)
        return nuclei_information

    def get_onnx_model(
        self, model: torch.nn.Module
    ) -> Optional[torch.onnx.OperatorExportTypes]:
        """Convert the model to ONNX format.

        Parameters
        ----------
        model : torch.nn.Module
            The model to convert.

        Returns
        -------
        Optional[torch.onnx.OperatorExportTypes]
            The ONNX model if the conversion was successful, None otherwise.

        Raises
        ------
        RuntimeError
            If the conversion failed.
        """
        try:
            # set the model to inference mode
            model.eval()

            # constant inputs to the model
            diam_mean = 30.0
            diameter = 24.225065
            resample = False
            num_classes = 6

            # Check if GPU is available
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            # input tensor
            input_tensor = torch.randn(
                1, 2, 224, 224, device=device, requires_grad=True
            )

            # convert constant inputs to tensor
            diam_mean_tensor = torch.tensor(
                diam_mean, device=device, dtype=torch.float32
            )
            diameter_tensor = torch.tensor(diameter, device=device, dtype=torch.float32)
            resample_tensor = torch.tensor(resample, device=device, dtype=torch.bool)
            num_classes_tensor = torch.tensor(
                num_classes, device=device, dtype=torch.int64
            )

            # model arguments
            model_args = (
                input_tensor,
                diam_mean_tensor,
                diameter_tensor,
                resample_tensor,
                num_classes_tensor,
            )

            # Inputs that are not part of the network control flow are hard-coded
            # in the onnx model and removed from inputs. Onnx model will have two
            # inputs: "input" and "nclasses".
            input_names = ["input", "dim_mean", "diameter", "resample", "num_classes"]
            output_names = ["output"]

            # model path
            model_path = Path("cellpose_model.onnx")

            # export torch model to onnx
            torch.onnx.export(
                model,
                model_args,
                model_path,
                export_params=True,  # store the trained parameter
                do_constant_folding=True,  # for optimization
                opset_version=18,  # the ONNX version to export the model to
                input_names=input_names,  # the model's input names
                output_names=output_names,  # the model's output names
            )

            onnx_model = torch.onnx.load(model_path)
            # check the onnx model
            torch.onnx.checker.check_model(onnx_model)
            return onnx_model

        except Exception as e:
            self.output_logger.exception(f"ONNX conversion failed: {e}")
            raise
