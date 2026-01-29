"""Inference pipelines for nuclei detection and segmentation models.

It offers a standardized interface for obtaining predictions from different model
architectures, handling pre-processing and post-processing steps specific to each model.

The main components are:

- `NucleiDetectionBase`: An abstract base class that defines the common
  interface for all inference deployers.
- `NucleiDetectionCellpose`: An inference class for nuclei segmentation model based on
  the Cellpose architecture.
- `NucleiInformation`: A data class used to store the results of a nuclei
  detection, such as boundaries and categories.
"""

from .nuclei_detection_base import NucleiDetectionBase
from .nuclei_detection_cellpose import (
    NucleiDetectionCellpose,
)
from .nuclei_information import NucleiInformation

__all__ = [
    "NucleiDetectionBase",
    "NucleiInformation",
    "NucleiDetectionCellpose",
]
