"""Torchmetric based custom metric module for evaluating detection performance."""

from typing import Final, List, Optional, Union

import torch
import torchmetrics

from roche.crisp.metrics import _metric_computations
from roche.crisp.utils.detection_utils import DetectionUtils

# Constant for use in metric calculation to avoid division by zero error
EPSILON: Final = 1e-8


class DetectionStats(torchmetrics.Metric):
    """Computes true positives, false positives, false negatives and the support.

    Supports multi-class. To be used if groundtruth array contains points,
    relies on NMS to handle overlapping detections.
    """

    is_differentiable: bool = False
    higher_is_better: bool = True
    full_state_update: bool = False

    def __init__(
        self,
        class_map: dict[int, str],
        neighb_size: int,
        threshold: float,
        radius: int,
        noncell_label: int = 0,
        ignore_label: Optional[Union[int, List[int]]] = None,
        undeterminedcell_label: Optional[int] = None,
    ) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        class_map : dict[int, str]
            Dictionary mapping indices to class names
        neighb_size : int
            Size of the neighborhood for NMS
        threshold : float
            Threshold for NMS
        radius : int
            Radius for computing TP, FP, FN
        noncell_label : int
            Label for non-cell regions, default is 0
        ignore_label : int or list of int, optional
            Label or list of labels to be ignored during evaluation,
            default is None
        undeterminedcell_label : int, optional
            Label for undetermined cells , default is None
        """
        super().__init__()

        self.neighb_size = neighb_size
        self.threshold = threshold
        self.class_map = class_map
        self.noncell_label = noncell_label
        self.radius = radius
        self.ignore_label = ignore_label
        self.class_labels: List[int] = []
        self.undeterminedcell_label = undeterminedcell_label
        self.num_classes = len(self.class_map)

        if undeterminedcell_label is not None:
            self.num_classes += 1

        self.add_state(
            "conf_mat",
            default=torch.zeros(
                (self.num_classes, self.num_classes), device=self.device
            ),
            dist_reduce_fx="sum",
        )

    def update(self, det_probs: torch.Tensor, det_target: torch.Tensor) -> None:
        """Update state variables of the class.

        Parameters
        ----------
        det_probs : torch.Tensor
            Output probability tensor
        det_target : torch.Tensor
            Point based groundtruth tensor

        Returns
        -------
        None
        """
        det_probs = det_probs.cpu().numpy()
        det_target = det_target.cpu().numpy()

        for i in range(len(det_probs)):
            pred_phenotype_mask = DetectionUtils.non_max_suppression_multi_class(
                det_probs[i, ...], self.neighb_size, self.threshold
            )[0]

            (
                conf_mat,
                class_labels,
            ) = _metric_computations.compute_detection_confusion_matrix(
                pred_phenotype_mask,
                det_target[i, ...],
                self.radius,
                self.class_map,
                self.noncell_label,
                ignore_label=self.ignore_label,
                undeterminedcell_label=self.undeterminedcell_label,
            )
            self.conf_mat += torch.from_numpy(conf_mat).to(self.device)
            self.class_labels = class_labels

    def compute(self) -> dict:
        """Compute the final metric values.

        This method will automatically synchronize state variables
        when running in distributed backend.

        Returns
        -------
        dict
            Computed recall, precision & f1 value for each class
            as well as overall.
        """
        return _metric_computations.compute_detection_metrics(
            self.conf_mat,
            self.class_map,
            self.class_labels,
            self.undeterminedcell_label,
        )
