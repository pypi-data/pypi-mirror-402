"""Torchmetric based custom metric module for evaluating CCC performance."""

from typing import Dict, List, Optional

import torch
import torchmetrics
from torchmetrics.functional import concordance_corrcoef


class ConcordanceCorrCoef(torchmetrics.Metric):
    """Computes the Concordance Correlation and Coefficient.

    Uses the wikipedia implementation:
    Ref: https://en.wikipedia.org/wiki/Concordance_correlation_coefficient
    """

    def __init__(
        self, class_map: Dict[int, str], ignore_index: Optional[List[int]] = None
    ) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        class_map : Dict[int, str]
            Dictionary mapping indices to class names
        ignore_index : List[int], optional
            Specifies a gt value that is ignored and does not contribute to the metric
            calculation
        """
        super().__init__()
        self.class_map = class_map
        self.ignore_index = ignore_index if ignore_index is not None else []
        self.class_map_without_ignore = {}

        for label, class_name in self.class_map.items():
            if label in self.ignore_index:
                continue

            self.class_map_without_ignore[label] = class_name
            self.add_state(f"{label}_gt", default=[], dist_reduce_fx="cat")
            self.add_state(f"{label}_pred", default=[], dist_reduce_fx="cat")

    def update(self, pred: torch.Tensor, target: torch.Tensor) -> None:
        """Update state variables of the class.

        Parameters
        ----------
        pred : torch.Tensor
            tensor with predictions
        target : torch.Tensor
            tensor with true labels
        """
        if target.shape != pred.shape:
            raise ValueError("gt and pred have different shape. Must be equal")

        for x, y in zip(pred, target):
            x = x.ravel()
            y = y.ravel()

            x_labels, x_counts = x.unique(return_counts=True)
            y_labels, y_counts = y.unique(return_counts=True)

            for label in self.class_map_without_ignore.keys():
                if torch.any(y_labels == label):
                    y_count = int(y_counts[torch.where(y_labels == label)])
                else:
                    y_count = 0

                if torch.any(x_labels == label):
                    x_count = int(x_counts[torch.where(x_labels == label)])
                else:
                    x_count = 0

                getattr(self, f"{label}_gt").append(y_count)
                getattr(self, f"{label}_pred").append(x_count)

    def compute(self) -> Dict[str, torch.Tensor]:
        """Compute the CCC value for each class and the mean CCC.

        This method will automatically synchronize state variables when running in
        distributed backend.

        Returns
        -------
        Dict[str, torch.Tensor]
            Computed CCC for each class and the mean CCC
        """
        metrics = {}
        accum_ccc = torch.tensor(0.0)

        for label, class_name in self.class_map_without_ignore.items():
            gt = torch.tensor(getattr(self, f"{label}_gt"), dtype=torch.float)
            pred = torch.tensor(getattr(self, f"{label}_pred"), dtype=torch.float)
            ccc = concordance_corrcoef(pred, gt)[0]
            accum_ccc += torch.tensor(0.0) if torch.isnan(ccc) else ccc
            metrics[f"{class_name}_ccc"] = ccc

        metrics["mean_ccc"] = accum_ccc / len(self.class_map_without_ignore.keys())

        return metrics
