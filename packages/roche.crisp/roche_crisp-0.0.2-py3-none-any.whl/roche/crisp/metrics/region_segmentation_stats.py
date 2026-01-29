"""Torchmetric metric module for evaluating region segmentation performance."""

from typing import Dict, Final, List, Optional

import torch
from torchmetrics.classification import MulticlassConfusionMatrix

from roche.crisp.metrics import _metric_computations

# Constant for use in metric calculation to avoid division by zero error
EPSILON: Final = 1e-8


class RegionSegmentationStats(MulticlassConfusionMatrix):
    """Computes Iou and F-Score per class and mean."""

    def __init__(
        self,
        num_classes: int,
        class_map: Dict[int, str],
        ignore_index: int = None,
        label_grouping: Optional[List[int]] = None,
        label_grouping_name: str = None,
    ) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        num_classes : int
            Number of classes in the dataset
        class_map : Dict[int, str]
            Dictionary mapping indices to class names
        ignore_index : int, optional
            Specifies a gt value that is ignored and does not contribute
            to the metric calculation, defaults is None. No label is ignored
        label_grouping : List[int], optional
            when compute method is called, all labels in this list will be
            grouped and treated as a one class. All other labels will be
            treated as independent, defaults is None. No grouping is applied
        label_grouping_name : str
            define a name for the new label for the grouping labels, defaults
            is None. If the label_grouping is not None, the name must not be
            None
        """
        self.num_classes = num_classes
        self.class_map = class_map
        self.ignore_index = ignore_index
        self.label_grouping = label_grouping
        self.label_grouping_name = label_grouping_name

        super().__init__(
            num_classes=self.num_classes,
            normalize="none",
            ignore_index=self.ignore_index,
        )

    def compute(self) -> Dict[str, torch.Tensor]:
        """Compute the region segmentation metrics.

        This method will automatically synchronize state variables when
        running in distributed backend.

        Returns
        -------
        Dict[str, torch.Tensor]
            For each metric will compute: class metric and mean(class_values)
        """
        multi_class_conf_mat = super().compute()

        if self.label_grouping is not None:
            (
                class_map,
                multi_class_conf_mat,
            ) = _metric_computations.group_labels_from_confusion_matrix(
                self.class_map,
                self.label_grouping,
                self.label_grouping_name,
                multi_class_conf_mat,
            )

        metrics = {}
        iou = []
        f1 = []
        for label, class_name in self.class_map.items():
            tp = multi_class_conf_mat[label, label]
            fp = torch.sum(multi_class_conf_mat[label, :]) - tp
            fn = torch.sum(multi_class_conf_mat[:, label]) - tp

            label_iou = tp / (tp + fp + fn + EPSILON)
            label_f1 = tp / (tp + 0.5 * (fp + fn) + EPSILON)

            metrics[f"{class_name}_iou"] = label_iou
            metrics[f"{class_name}_f1"] = label_f1
            iou.append(label_iou)
            f1.append(label_f1)

        metrics["mean_iou"] = torch.mean(torch.tensor(iou)).to(self.device)
        metrics["mean_f1"] = torch.mean(torch.tensor(f1)).to(self.device)

        return metrics
