"""Torchmetric custom metric module for evaluating segmentation performance."""

import numpy as np
import torch
import torchmetrics
from torchmetrics.utilities.data import dim_zero_cat

from roche.crisp.metrics._metric_computations import (
    compute_segmentation_confusion_matrix,
)
from roche.crisp.metrics.instanseg_metric import robust_average_precision
from roche.crisp.utils.segmentation_utils import matching_dataset


class F1Stats(torchmetrics.Metric):
    """Compute F1 score using robust average precision."""

    is_differentiable: bool = False
    higher_is_better: bool = True
    full_state_update: bool = False

    def __init__(self):
        """Initialize F1Stats metric."""
        super().__init__()

        # Add states for accumulating F1 scores
        self.add_state("f1_mean", default=[], dist_reduce_fx="cat")
        self.add_state("f1_05", default=[], dist_reduce_fx="cat")

    def update(self, preds: torch.Tensor, target: torch.Tensor) -> None:
        """Update state with predictions and targets.

        Parameters
        ----------
        preds : torch.Tensor
            Predicted labels
        target : torch.Tensor
            Ground truth labels
        """
        f1_05 = robust_average_precision(
            target.cpu().numpy(),
            preds.cpu().numpy(),
            0.5,
        )
        f1_mean = robust_average_precision(
            target.cpu().numpy(),
            preds.cpu().numpy(),
            np.linspace(0.5, 1.0, 10),
        )

        # Update states
        self.f1_mean.append(
            torch.tensor(f1_mean).type(torch.FloatTensor).to(self.device)
        )
        self.f1_05.append(torch.tensor(f1_05).type(torch.FloatTensor).to(self.device))

    def compute(self) -> torch.Tensor:
        """Compute the mean F1 score across all accumulated batches.

        Returns
        -------
        torch.Tensor
            Mean F1 score
        """
        f1_mean = dim_zero_cat(self.f1_mean)
        f1_05 = dim_zero_cat(self.f1_05)
        return {
            "f1_mean": torch.nanmean(f1_mean),
            "f1_05": torch.nanmean(f1_05),
        }


class SegmentationStats(torchmetrics.Metric):
    """Computes iou, dice score and pixel accuracy."""

    is_differentiable: bool = False
    higher_is_better: bool = True
    full_state_update: bool = False

    def __init__(self, num_classes: int):
        """Initialize the SegmentationStats class with the necessary attributes.

        Parameters
        ----------
        num_classes : int
            Number of classes in the dataset
        """
        super().__init__()
        self.num_classes = num_classes
        self.add_state(
            "cm",
            default=torch.zeros(
                (self.num_classes, self.num_classes), dtype=torch.float
            ),
            dist_reduce_fx="sum",
        )

    def update(self, preds: torch.Tensor, targets: torch.Tensor):
        """Generate confusion matrix for given predictions and targets.

        Also updates the matrix with latest values.

        Parameters
        ----------
        preds : torch.Tensor
            tensor with predictions
        targets : torch.Tensor
            tensor with ground truth
        """
        targets = targets.detach().cpu().numpy()
        preds = preds.cpu().numpy()
        cm = compute_segmentation_confusion_matrix(
            preds.flatten(), targets.flatten(), self.num_classes
        )
        self.cm += torch.from_numpy(cm).to(self.cm.device)

    def compute(self) -> dict:
        """Compute iou, dice and pixel accuracy.

        Returns
        -------
        Tuple[float, float, float]
            Tuple of mean dice, mean iou and pixel accuracy
        """
        self.tp = torch.diag(self.cm)
        self.tp_fp = self.cm.sum(axis=1)
        self.tp_fn = self.cm.sum(axis=0)
        dice_score = (2 * self.tp) / (self.tp_fp + self.tp_fn)
        mean_dice = torch.nanmean(dice_score)
        # Above we use nanmean rather than mean inorder to ignore
        # any nan values in the dice score
        iou = self.tp / (self.tp_fp + self.tp_fn - self.tp)

        metrics = {
            "iou": torch.nanmean(iou),  # Jaccard Index
            "dice": mean_dice,
            "pixel_accuracy": self.tp.sum() / self.cm.sum(),
        }
        return metrics


class InstanceSegmentationMetrics(torchmetrics.Metric):
    """Compute metrics for instance segmentation."""

    is_differentiable: bool = False
    higher_is_better: bool = True
    full_state_update: bool = False

    def __init__(self, criterion="iou", thresh=0.5):
        """Initialize the InstanceSegmentationMetrics object.

        Parameters
        ----------
        criterion : str, optional
            The matching criterion to use. Can be one of "iou", "precision", or
            "recall". Defaults to "iou".
        thresh : float, optional
            The threshold to use for the matching criterion. Defaults to 0.5.
        """
        super().__init__()
        self.criterion = criterion
        self.thresh = thresh
        self.add_state("tp", default=torch.tensor(0), dist_reduce_fx="sum")
        self.add_state("fp", default=torch.tensor(0), dist_reduce_fx="sum")
        self.add_state("fn", default=torch.tensor(0), dist_reduce_fx="sum")
        self.add_state("n_true", default=torch.tensor(0), dist_reduce_fx="sum")
        self.add_state("n_pred", default=torch.tensor(0), dist_reduce_fx="sum")

    def update(self, y_pred, y_true):
        """Update the metric with a batch of predictions and ground truth.

        Parameters
        ----------
        y_pred : torch.Tensor
            The predicted masks.
        y_true : torch.Tensor or None
            The ground truth masks. Can be None during testing/prediction.
        """
        # Skip update if ground truth is not available
        # (e.g., during testing/prediction)
        if y_true is None:
            return

        # Convert tensors to numpy arrays and handle batch dimension
        y_pred = y_pred.squeeze(1).cpu().numpy()
        y_true = y_true.cpu().numpy()

        # Process each image in the batch
        batch_size = y_pred.shape[0]
        for i in range(batch_size):
            # Get stats for this image pair using matching_dataset
            stats = matching_dataset(
                [y_true[i]],
                [y_pred[i]],
                thresh=self.thresh,
                show_progress=False,
            )

            # Update accumulated metrics
            self.tp += stats.tp
            self.fp += stats.fp
            self.fn += stats.fn
            self.n_true += stats.n_true
            self.n_pred += stats.n_pred

    def _safe_divide_torch(
        self, x: torch.Tensor, y: torch.Tensor, eps: float = 1e-10
    ) -> torch.Tensor:
        """Compute a safe divide which returns 0 if y is zero.

        Parameters
        ----------
        x : torch.Tensor
            Numerator tensor
        y : torch.Tensor
            Denominator tensor
        eps : float, optional
            Small value to prevent division by zero. Defaults to 1e-10.

        Returns
        -------
        torch.Tensor
            Result of safe division
        """
        if torch.is_tensor(x) and torch.is_tensor(y):
            # Create mask where y values are greater than eps
            mask = torch.abs(y) > eps
            # Initialize output tensor with zeros
            out = torch.zeros_like(x, dtype=torch.float32)
            # Perform division only where mask is True
            out[mask] = x[mask] / y[mask]
            return out
        else:
            # Handle scalar case
            return x / y if torch.abs(y) > eps else torch.tensor(0)

    def compute(self):
        """Compute the metric.

        Returns
        -------
        dict
            A dictionary containing the computed metrics.
        """
        precision = self.tp / (self.tp + self.fp) if self.tp + self.fp > 0 else 0
        recall = self.tp / (self.tp + self.fn) if self.tp + self.fn > 0 else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall > 0
            else 0
        )
        accuracy = (
            self.tp / (self.tp + self.fp + self.fn)
            if (self.tp + self.fp + self.fn) > 0
            else 0
        )

        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": precision,
            "recall": recall,
            "accuracy": accuracy,
            "f1": f1,
        }
