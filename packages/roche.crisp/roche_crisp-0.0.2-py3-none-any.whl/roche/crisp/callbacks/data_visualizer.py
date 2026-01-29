"""Callback to log prediction samples to wandb."""

from typing import Any, Dict, Literal, Optional

import lightning as L
import numpy as np
import torch
import torch.nn.functional as F
import wandb
from lightning.pytorch.callbacks import Callback
from lightning.pytorch.utilities import rank_zero_only
from lightning.pytorch.utilities.types import STEP_OUTPUT
from scipy.ndimage import grey_dilation
from skimage import morphology

from roche.crisp.metrics.region_segmentation_stats import RegionSegmentationStats
from roche.crisp.utils import common_utils, transforms
from roche.crisp.utils.cellpose_utils import postprocess
from roche.crisp.utils.detection_utils import DetectionUtils
from roche.crisp.utils.instanseg_utils import (
    postprocessing,
)

RADIUS: int = 5


def create_wandb_instance_image(
    image: np.ndarray,
    gt_instance_mask: Optional[np.ndarray] = None,
    pred_instance_mask: Optional[np.ndarray] = None,
) -> wandb.Image:
    """Create a wandb Image object with instance masks."""
    masks = {}
    if gt_instance_mask is not None:
        masks["ground_truth_instances"] = {
            "mask_data": gt_instance_mask
            # No class_labels for instance masks
        }
    else:
        masks["predicted_instances"] = {
            "mask_data": pred_instance_mask
            # No class_labels for instance masks
        }
    return wandb.Image(image, masks=masks)


def create_wandb_image(
    image: np.ndarray,
    target: np.ndarray,
    pred: Optional[np.ndarray] = None,
    class_map: Optional[Dict] = None,
) -> wandb.Image:
    """Create a wandb Image object with masks.

    The function creates a wandb Image from the input image,
    target (ground truth) mask, and optionally a prediction mask.

    Masks are dilated for better visualization.

    Parameters
    ----------
    image : np.ndarray
        The input image.
    target : np.ndarray
        The ground truth mask.
    pred : np.ndarray, optional
        The predicted mask.
    class_map : dict, optional
        The mapping from indices to class names
    """
    masks = {
        "ground_truth": {
            "mask_data": grey_dilation(
                target, footprint=morphology.disk(radius=RADIUS)
            ),
            "class_labels": class_map,
        }
    }

    if pred is not None:
        masks["predictions"] = {
            "mask_data": grey_dilation(pred, footprint=morphology.disk(radius=RADIUS)),
            "class_labels": class_map,
        }

    return wandb.Image(image, masks=masks)


def create_wandb_region_image(
    image: np.ndarray,
    target: np.ndarray,
    pred: Optional[np.ndarray] = None,
    class_map: Optional[Dict] = None,
    caption: Optional[str] = None,
) -> wandb.Image:
    """Create a wandb Image object with masks.

    The function creates a wandb Image from the input image,
    target (ground truth) mask, and optionally a prediction mask.

    Parameters
    ----------
    image : np.ndarray
        The input image.
    target : np.ndarray
        The ground truth mask.
    pred : np.ndarray, optional
        The predicted mask.
    class_map : dict, optional
        The mapping from indices to class names
    """
    # Ensure image is uint8
    if isinstance(image, torch.Tensor):
        image = image.cpu().numpy()
    image = image.astype(np.uint8)

    masks = {
        "ground_truth": {
            "mask_data": target,
            "class_labels": class_map,
        }
    }

    if pred is not None:
        masks["predictions"] = {
            "mask_data": pred,
            "class_labels": class_map,
        }

    return wandb.Image(image, masks=masks, caption=caption)


class DataVisualizer(Callback):
    """Callback to log prediction samples to wandb.

    It logs the first batch of image and ground truth samples from the training dataset
    at the start of training. It also logs image, ground truth and prediction samples
    from first batch of the validation datasets.
    """

    def __init__(
        self,
        class_map: Dict,
    ) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        class_map : dict
            The mapping from indices to class names
        """
        super().__init__()
        self.class_map = class_map

    def on_train_start(self, trainer: L.Trainer, pl_module: L.LightningModule) -> None:
        """Log samples at the start of training.

        Log the first batch of image and ground truth
        samples from the training dataset.

        Parameters
        ----------
        trainer : Trainer
            Pytorch Lightning Trainer instance
        pl_module : Module
            Pytorch Lightning Module instance
        """
        dataloader = trainer.train_dataloader
        batch = next(iter(dataloader))
        images, targets = batch
        images = images.cpu().numpy()
        targets = targets.cpu().numpy()
        self._log_samples_to_wandb(images, targets, "train")

    def on_validation_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: STEP_OUTPUT,
        batch: Any,
        batch_idx: int,
    ) -> None:
        """Log samples at the end of a validation batch.

        Log image, ground truth and prediction samples from the
        first batch of validation dataset.

        Parameters
        ----------
        trainer : Trainer
            Pytorch Lightning Trainer instance
        pl_module : Module
            Pytorch Lightning Module instance
        outputs : dict
            Dictionary of outputs from the model
        batch : tuple
            Tuple of input data and masks
        batch_idx : int
            Index of the current batch
        """
        if batch_idx == 2:
            images, targets = batch

            out = pl_module.forward(images)
            prob = F.softmax(out, dim=1)

            prob = prob.cpu().numpy()
            images = images.cpu().numpy()
            targets = targets.cpu().numpy()

            pred_list = []
            for i in range(len(prob)):
                pred = DetectionUtils.non_max_suppression_multi_class(
                    prob[i, ...],
                    pl_module.metrics["val_metrics"].detection_stats.neighb_size,
                    pl_module.metrics["val_metrics"].detection_stats.threshold,
                )[0]
                pred_list.append(pred)
            preds = np.array(pred_list)

            self._log_samples_to_wandb(
                images,
                targets,
                "val",
                preds,
            )

    def on_test_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: STEP_OUTPUT,
        batch: Any,
        batch_idx: int,
    ) -> None:
        """Log samples at the end of a validation batch.

        Log image, ground truth and prediction samples from the
        first batch of validation dataset.

        Parameters
        ----------
        trainer : Trainer
            Pytorch Lightning Trainer instance
        pl_module : Module
            Pytorch Lightning Module instance
        outputs : dict
            Dictionary of outputs from the model
        batch : tuple
            Tuple of input data and masks
        batch_idx : int
            Index of the current batch
        """
        images, targets = batch

        out = pl_module.forward(images)
        prob = F.softmax(out, dim=1)

        prob = prob.cpu().numpy()
        images = images.cpu().numpy()
        targets = targets.cpu().numpy()

        pred_list = []
        for i in range(len(prob)):
            pred = DetectionUtils.non_max_suppression_multi_class(
                prob[i, ...],
                pl_module.metrics["val_metrics"].detection_stats.neighb_size,
                pl_module.metrics["val_metrics"].detection_stats.threshold,
            )[0]
            pred_list.append(pred)
        preds = np.array(pred_list)

        self._log_samples_to_wandb(
            images,
            targets,
            "test",
            preds,
        )

    @rank_zero_only
    def _log_samples_to_wandb(
        self,
        images: np.ndarray,
        targets: np.ndarray,
        stage: Literal["train", "val", "test", "predict"],
        preds: Optional[np.ndarray] = None,
    ) -> None:
        """Log images, ground truth and optionally predictions to wandb.

        Parameters
        ----------
        images : np.ndarray
            The input images.
        targets : np.ndarray
            The ground truth masks.
        preds : np.ndarray, optional
            The predicted masks.
        stage : str
            The stage of training.
        """
        if preds is not None:
            overlays = [
                create_wandb_image(img.transpose(1, 2, 0), target, pred, self.class_map)
                for img, target, pred in zip(images, targets, preds)
            ]
        else:
            overlays = [
                create_wandb_image(img.transpose(1, 2, 0), target, self.class_map)
                for img, target in zip(images, targets)
            ]

        wandb.log({f"{stage} samples": overlays})


class RegionDataVisualizer(Callback):
    """Callback to log prediction samples to wandb.

    It logs the first batch of image and ground truth samples from the training dataset
    at the start of training. It also logs image, ground truth and prediction samples
    from first batch of the validation datasets.
    """

    def __init__(
        self,
        class_map: Dict,
        num_classes: int = 3,
        ignore_index: int = 255,
    ) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        class_map : dict
            The mapping from indices to class names
        num_classes : int, optional
            Number of classes for region segmentation, by default 3
        ignore_index : int, optional
            Index to ignore in segmentation metrics, by default 255
        """
        super().__init__()
        self.class_map = class_map
        self.num_classes = num_classes
        self.ignore_index = ignore_index

    def on_train_start(self, trainer: L.Trainer, pl_module: L.LightningModule) -> None:
        """Log samples at the start of training.

        Log the first batch of image and ground truth
        samples from the training dataset.

        Parameters
        ----------
        trainer : Trainer
            Pytorch Lightning Trainer instance
        pl_module : Module
            Pytorch Lightning Module instance
        """
        dataloader = trainer.train_dataloader
        batch = next(iter(dataloader))
        original_images, images, targets, _ = batch
        original_images = original_images.cpu().numpy()
        targets = targets.cpu().numpy()
        self._log_samples_to_wandb(original_images, targets, "train")

    def on_validation_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: STEP_OUTPUT,
        batch: Any,
        batch_idx: int,
    ) -> None:
        """Log samples at the end of a validation batch.

        Log image, ground truth and prediction samples from the
        first batch of validation dataset.

        Parameters
        ----------
        trainer : Trainer
            Pytorch Lightning Trainer instance
        pl_module : Module
            Pytorch Lightning Module instance
        outputs : dict
            Dictionary of outputs from the model
        batch : tuple
            Tuple of input data and masks
        batch_idx : int
            Index of the current batch
        """
        if batch_idx == 2:
            original_images, images, targets, _ = batch

            out = pl_module.forward(images)
            pred_sgm_masks = torch.argmax(out, dim=1, keepdim=True).squeeze(dim=1)

            pred_sgm_masks = pred_sgm_masks.cpu().numpy()
            original_images = original_images.cpu().numpy()
            targets = targets.cpu().numpy()

            self._log_samples_to_wandb(
                original_images,
                targets,
                "val",
                pred_sgm_masks,
            )

    def on_test_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: STEP_OUTPUT,
        batch: Any,
        batch_idx: int,
    ) -> None:
        """Accumulate FOV data for final wandb table logging."""
        if batch_idx == 0:
            self._fov_table_data = []
            self._caption_keys = None
            self._metric_keys = None

        original_images, images, targets, caption = batch
        out = pl_module.forward(images)
        pred_sgm_masks = torch.argmax(out, dim=1, keepdim=True).squeeze(dim=1)
        for i in range(pred_sgm_masks.shape[0]):
            device = targets.device
            pred = pred_sgm_masks[i].unsqueeze(0).to(device)
            target = targets[i].unsqueeze(0).to(device)
            fov_metric = RegionSegmentationStats(
                num_classes=self.num_classes,
                class_map=self.class_map,
                ignore_index=self.ignore_index,
            ).to(device)
            fov_metric.update(pred, target)
            metrics = fov_metric.compute()

            def safe_value(val):
                if isinstance(val, torch.Tensor):
                    val = val.item()
                if isinstance(val, float) and val != val:  # NaN check
                    return float("nan")
                return val

            # Store keys on first iteration
            if self._caption_keys is None and caption:
                self._caption_keys = sorted(caption.keys())
            if self._metric_keys is None:
                self._metric_keys = sorted(metrics.keys())

            # Build row dynamically
            row = [
                batch_idx * pred_sgm_masks.shape[0] + i,
                create_wandb_region_image(
                    image=original_images[i],
                    target=targets[i],
                    pred=pred_sgm_masks[i],
                    class_map=self.class_map,
                ),
            ]

            # Add all metrics
            for metric_key in self._metric_keys:
                row.append(safe_value(metrics[metric_key]))

            # Add all caption fields
            for caption_key in self._caption_keys:
                if i < len(caption[caption_key]):
                    row.append(safe_value(caption[caption_key][i]))
                else:
                    row.append(None)

            self._fov_table_data.append(row)

        pred_sgm_masks = pred_sgm_masks.cpu().numpy()
        original_images = original_images.cpu().numpy()
        targets = targets.cpu().numpy()

        self._log_samples_to_wandb(
            original_images,
            targets,
            "test",
            pred_sgm_masks,
            caption,
        )

    def on_test_epoch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
    ) -> None:
        """Log the final wandb table after all test batches."""
        if hasattr(self, "_fov_table_data") and self._fov_table_data:
            # Build column names dynamically
            columns = ["FOV", "Overlay"]

            # Add metric columns
            if hasattr(self, "_metric_keys") and self._metric_keys:
                columns.extend(self._metric_keys)

            # Add caption columns
            if hasattr(self, "_caption_keys") and self._caption_keys:
                columns.extend(self._caption_keys)

            table = wandb.Table(columns=columns)
            for row in self._fov_table_data:
                table.add_data(*row)
            wandb.log({"FOV Results": table})

    @rank_zero_only
    def _log_samples_to_wandb(
        self,
        images: np.ndarray,
        targets: np.ndarray,
        stage: Literal["train", "val", "test", "predict"],
        preds: Optional[np.ndarray] = None,
        caption: Optional[Dict[str, list]] = None,
    ) -> None:
        """Log images, ground truth and optionally predictions to wandb, with captions.

        Parameters
        ----------
        images : np.ndarray
            The input images.
        targets : np.ndarray
            The ground truth masks.
        preds : np.ndarray, optional
            The predicted masks.
        stage : str
            The stage of training.
        caption : dict, optional
            Dictionary containing caption data for each image.
        """

        def build_caption(idx: int) -> Optional[str]:
            if caption is None:
                return None
            parts = []
            for key in caption:
                if idx < len(caption[key]):
                    parts.append(f"{key}: {caption[key][idx]}")
            return " | ".join(parts) if parts else None

        if preds is not None:
            overlays = [
                create_wandb_region_image(
                    img,
                    target,
                    pred,
                    class_map=self.class_map,
                    caption=build_caption(idx),
                )
                for idx, (img, target, pred) in enumerate(zip(images, targets, preds))
            ]
        else:
            overlays = [
                create_wandb_region_image(
                    img, target, class_map=self.class_map, caption=build_caption(idx)
                )
                for idx, (img, target) in enumerate(zip(images, targets))
            ]

        wandb.log({f"{stage} samples": overlays})


class CellposeInstanceMaskVisualizer(Callback):
    """Callback to log cellpose instance mask prediction samples to wandb.

    Logs the first batch of image and instance mask samples from the training dataset
    at the start of training. Also logs image, ground truth, and predicted instance
    masks from the first batch of the validation and test datasets.
    """

    def __init__(self, use_rgb: bool = True) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        use_rgb : bool, optional
            Whether to use RGB channels (True) or just first channel (False),
            by default True
        """
        super().__init__()
        self.use_rgb = use_rgb

    def on_train_start(self, trainer: L.Trainer, pl_module: L.LightningModule) -> None:
        """Log instance mask samples at the start of training."""
        dataloader = trainer.train_dataloader
        batch = next(iter(dataloader))
        flows, original_image = batch["flows"], batch["original_image"]
        instance_masks = flows[:, 0, :, :]
        original_image = original_image.cpu().numpy()
        instance_masks = instance_masks.cpu().numpy()
        self._log_instance_masks_to_wandb(original_image, instance_masks, "train")

    def on_validation_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: STEP_OUTPUT,
        batch: Any,
        batch_idx: int,
    ) -> None:
        """Log instance mask samples at the end of a validation batch."""
        if batch_idx == 0:
            input_data, input_label, original_image = (
                batch["image"],
                batch["flows"],
                batch["original_image"],
            )
            input_label = input_label[:, 0, :, :]

            diam_mean = pl_module.diam_mean
            diameter = pl_module.diameter
            resample = pl_module.resample

            if resample:
                resampled_width = int(
                    (input_data.shape[-2] + 1) / (diam_mean / diameter)
                )
                resampled_height = int(
                    (input_data.shape[-1] + 1) / (diam_mean / diameter)
                )
            input_data, ysub_pad, xsub_pad = common_utils.pad_image_ND_gpu(input_data)
            with torch.no_grad():
                output = pl_module.forward(input_data)[0]
            output = common_utils.remove_padding(output, ysub_pad, xsub_pad)
            if resample:
                output = transforms.resize_image_gpu(
                    output, resampled_width, resampled_height
                )
                input_label = transforms.resize_image_gpu(
                    input_label, resampled_width, resampled_height
                )
                original_image = transforms.resize_image_gpu(
                    original_image.moveaxis(-1, 1), resampled_width, resampled_height
                )
            with torch.no_grad():
                masks = postprocess(
                    output,
                    vectorized=pl_module.vectorized,
                    segmentation_type=pl_module.segmentation_type,
                    cellprob_threshold=pl_module.cellprob_threshold,
                    flow_threshold=pl_module.flow_threshold,
                )
            original_image = original_image.moveaxis(1, -1)
            original_image = original_image.cpu().numpy()
            masks = masks.cpu().numpy()
            input_label = input_label.cpu().numpy()
            self._log_instance_masks_to_wandb(
                original_image,
                input_label,
                "val",
                masks,
            )

    def on_test_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: STEP_OUTPUT,
        batch: Any,
        batch_idx: int,
    ) -> None:
        """Log instance mask samples at the end of a test batch."""
        input_data, input_label, original_image = (
            batch["image"],
            batch["instance_label"],
            batch["original_image"],
        )
        diam_mean = pl_module.diam_mean
        diameter = pl_module.diameter
        resample = pl_module.resample

        if resample:
            resampled_width = int((input_data.shape[-2] + 1) / (diam_mean / diameter))
            resampled_height = int((input_data.shape[-1] + 1) / (diam_mean / diameter))
        input_data, ysub_pad, xsub_pad = common_utils.pad_image_ND_gpu(input_data)
        with torch.no_grad():
            output = pl_module.forward(input_data)[0]
        output = common_utils.remove_padding(output, ysub_pad, xsub_pad)
        input_data = common_utils.remove_padding(input_data, ysub_pad, xsub_pad)
        if resample:
            output = transforms.resize_image_gpu(
                output, resampled_width, resampled_height
            )
            input_label = transforms.resize_image_gpu(
                input_label, resampled_width, resampled_height
            )
            input_data = transforms.resize_image_gpu(
                input_data, resampled_width, resampled_height
            )
        with torch.no_grad():
            masks = postprocess(
                output,
                vectorized=pl_module.vectorized,
                segmentation_type=pl_module.segmentation_type,
                cellprob_threshold=pl_module.cellprob_threshold,
                flow_threshold=pl_module.flow_threshold,
            )
        original_image = original_image.cpu().numpy()
        masks = masks.cpu().numpy()
        input_label = input_label.cpu().numpy()
        self._log_instance_masks_to_wandb(
            original_image,
            input_label,
            "test",
            masks,
        )

    def on_predict_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: STEP_OUTPUT,
        batch: Any,
        batch_idx: int,
    ) -> None:
        """Log instance mask samples at the end of a test batch."""
        input_data, original_image = (
            batch["image"],
            batch["original_image"],
        )
        diam_mean = pl_module.diam_mean
        diameter = pl_module.diameter
        resample = pl_module.resample

        if resample:
            resampled_width = int((input_data.shape[-2] + 1) / (diam_mean / diameter))
            resampled_height = int((input_data.shape[-1] + 1) / (diam_mean / diameter))
        input_data, ysub_pad, xsub_pad = common_utils.pad_image_ND_gpu(input_data)

        with torch.no_grad():
            output = pl_module.forward(input_data)[0]

        output = common_utils.remove_padding(output, ysub_pad, xsub_pad)

        if resample:
            output = transforms.resize_image_gpu(
                output, resampled_width, resampled_height
            )

        with torch.no_grad():
            masks = postprocess(
                output,
                vectorized=pl_module.vectorized,
                segmentation_type=pl_module.segmentation_type,
                cellprob_threshold=pl_module.cellprob_threshold,
                flow_threshold=pl_module.flow_threshold,
            )
        original_image = original_image.cpu().numpy()
        masks = masks.cpu().numpy()
        self._log_instance_masks_to_wandb(
            original_image,
            None,
            "predict",
            masks,
        )

    @rank_zero_only
    def _log_instance_masks_to_wandb(
        self,
        images: np.ndarray,
        gt_instance_masks: np.ndarray,
        stage: Literal["train", "val", "test", "predict"],
        pred_instance_masks: Optional[np.ndarray] = None,
    ) -> None:
        """Log images and instance masks."""
        if stage in ["train", "val", "test"]:
            if pred_instance_masks is not None:
                overlays = [
                    create_wandb_instance_image(
                        img,
                        gt.astype(np.uint8),
                        pred.astype(np.uint8),
                    )
                    for img, gt, pred in zip(
                        images, gt_instance_masks, pred_instance_masks
                    )
                ]
            else:
                overlays = [
                    create_wandb_instance_image(
                        img,
                        gt.astype(np.uint8),
                    )
                    for img, gt in zip(images, gt_instance_masks)
                ]
        else:
            overlays = [
                create_wandb_instance_image(
                    img,
                    None,
                    pred.astype(np.uint8),
                )
                for img, pred in zip(images, pred_instance_masks)
            ]
        wandb.log({f"{stage} instance mask samples": overlays})


class InstanSegMaskVisualizer(Callback):
    """Callback to log instance mask prediction samples to wandb."""

    def __init__(self) -> None:
        """Initialize instance of the class."""
        super().__init__()

    def on_train_start(self, trainer: L.Trainer, pl_module: L.LightningModule) -> None:
        """Log instance mask samples at the start of training."""
        dataloader = trainer.train_dataloader
        batch = next(iter(dataloader))
        images, targets = batch
        images = images.numpy()
        targets = targets.numpy()
        images = np.moveaxis(images, 1, -1)
        self._log_instance_masks_to_wandb(images, targets, "train")

    def on_validation_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: STEP_OUTPUT,
        batch: Any,
        batch_idx: int,
    ) -> None:
        """Log instance mask samples at the end of a validation batch."""
        if batch_idx == 0:
            input_data, targets = batch
            with torch.no_grad():
                output = pl_module.forward(input_data)
                predicted_labels = torch.stack(
                    [
                        postprocessing(
                            out,
                            device=pl_module.device,
                            classifier=pl_module.pixel_classifier,
                        )
                        for out in output
                    ]
                )
            input_data = input_data.cpu().numpy()
            targets = targets.cpu().numpy()
            predicted_labels = predicted_labels.cpu().numpy()
            input_data = np.moveaxis(input_data, 1, -1)
            predicted_labels = np.squeeze(predicted_labels, 1)
            self._log_instance_masks_to_wandb(
                input_data,
                targets,
                "val",
                predicted_labels,
            )

    def on_test_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: STEP_OUTPUT,
        batch: Any,
        batch_idx: int,
    ) -> None:
        """Log instance mask samples at the end of a test batch."""
        input_data, targets = batch
        with torch.no_grad():
            output = pl_module.forward(input_data)
            predicted_labels = torch.stack(
                [
                    postprocessing(
                        out,
                        device=pl_module.device,
                        classifier=pl_module.pixel_classifier,
                    )
                    for out in output
                ]
            )
        input_data = input_data.cpu().numpy()
        targets = targets.cpu().numpy()
        predicted_labels = predicted_labels.cpu().numpy()
        input_data = np.moveaxis(input_data, 1, -1)
        predicted_labels = np.squeeze(predicted_labels, 1)
        self._log_instance_masks_to_wandb(
            input_data,
            targets,
            "test",
            predicted_labels,
        )

    @rank_zero_only
    def _log_instance_masks_to_wandb(
        self,
        images: np.ndarray,
        gt_instance_masks: np.ndarray,
        stage: Literal["train", "val", "test", "predict"],
        pred_instance_masks: Optional[np.ndarray] = None,
    ) -> None:
        """Log images and instance masks."""
        if stage in ["train", "val", "test"]:
            if pred_instance_masks is not None:
                overlays = [
                    create_wandb_instance_image(
                        img,
                        gt.astype(np.uint8),
                        pred.astype(np.uint8),
                    )
                    for img, gt, pred in zip(
                        images, gt_instance_masks, pred_instance_masks
                    )
                ]
            else:
                overlays = [
                    create_wandb_instance_image(
                        img,
                        gt.astype(np.uint8),
                    )
                    for img, gt in zip(images, gt_instance_masks)
                ]
        else:
            if pred_instance_masks is not None:
                overlays = [
                    create_wandb_instance_image(
                        img,
                        None,
                        pred.astype(np.uint8),
                    )
                    for img, pred in zip(images, pred_instance_masks)
                ]
            else:
                overlays = [
                    create_wandb_instance_image(
                        img,
                        None,
                        None,
                    )
                    for img in images
                ]
        wandb.log({f"{stage} instance mask samples": overlays})
