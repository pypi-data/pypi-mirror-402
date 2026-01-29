"""Custom metric modules for evaluating segmentation and detection models.

It provides a collection of custom metrics built upon the `torchmetrics`
framework. These metrics are tailored for common tasks in biomedical image
analysis, such as object detection, instance segmentation, and semantic
segmentation.

Key Components:

- `DetectionStats`: Computes precision, recall, and F1-score for object detection.
- `SegmentationStats`: Calculates pixel-level segmentation metrics like IoU.
- `InstanceSegmentationMetrics`: Provides a suite of metrics for instance segmentation.
- `F1Stats`: A specific metric for F1 score calculation.
- `ConcordanceCorrCoef`: Computes the concordance correlation coefficient.
- `RegionSegmentationStats`: Calculates segmentation statistics for specific regions.
"""

from .concordance_corr_coef import ConcordanceCorrCoef
from .detection_stats import DetectionStats
from .region_segmentation_stats import RegionSegmentationStats
from .segmentation_stats import (
    F1Stats,
    InstanceSegmentationMetrics,
    SegmentationStats,
)

__all__ = [
    "DetectionStats",
    "SegmentationStats",
    "ConcordanceCorrCoef",
    "RegionSegmentationStats",
    "InstanceSegmentationMetrics",
    "F1Stats",
]
