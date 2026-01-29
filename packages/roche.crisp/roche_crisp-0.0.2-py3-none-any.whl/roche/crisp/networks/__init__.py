"""Neural network modules for pixel-level image segmentation & detection tasks.

It serves as the main entry point for accessing different network architectures
like U-Net and its variants, Cellpose, and InstanSeg.

The following networks are available for direct import from this module:

- `VanillaUNet`: A classic U-Net implementation.
- `SingleTaskUnet`: A U-Net with a pre-trained encoder for single-task output.
- `MultiTaskUnet`: A U-Net with a pre-trained encoder for multi-task output.
- `Cellpose`: The Cellpose architecture for generalist cell segmentation.
- `InstanSeg_UNet`: A U-Net variant for cellinstance segmentation.
"""

from .cellpose import Cellpose
from .instanseg_unet import InstanSeg_UNet
from .unet import MultiTaskUnet, SingleTaskUnet, VanillaUNet
from .vitunet import VitUnet

__all__ = [
    "Cellpose",
    "VanillaUNet",
    "SingleTaskUnet",
    "MultiTaskUnet",
    "InstanSeg_UNet",
    "VitUnet",
]
