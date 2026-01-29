"""PyTorch implementation of the Cellpose model architecture.

This module provides the building blocks and the main network class for Cellpose,
a deep learning model designed for generalist cellular segmentation. The
architecture is a U-Net-like structure that computes a "style" vector from the
input image, representing global features. This style vector is then used
throughout the upsampling path to modulate the convolutional features, allowing
the network to adapt to a wide variety of image types.

The implementation is based on [Cellpose: a generalist algorithm
for cellular segmentation](https://www.nature.com/articles/s41592-020-01018-x)

Key Components:
- `Cellpose`: The main network class that combines the encoder and decoder.
- `Downsample`: The encoder part of the network.
- `Upsample`: The decoder part of the network.
- `MakeStyle`: Computes the global style vector from the bottleneck features.
- `ResDown`, `ConvDown`: Downsampling blocks (with/without residual connections).
- `ResUp`, `ConvUp`: Upsampling blocks (with/without residual connections).
- `batchconvstyle`: A custom convolutional block that incorporates the style vector.
"""

from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


def batchconv(in_channels: int, out_channels: int, kernel_size: int) -> nn.Sequential:
    """Create a sequential module.

    Consisting of batch normalization, ReLU activation,
    and convolution.

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int
        Size of the convolutional kernel.

    Returns
    -------
    nn.Sequential
        Sequential module consisting of batch normalization, ReLU activation, and
        convolution.
    """
    return nn.Sequential(
        nn.BatchNorm2d(in_channels, eps=1e-5),
        nn.ReLU(inplace=True),
        nn.Conv2d(in_channels, out_channels, kernel_size, padding=kernel_size // 2),
    )


def batchconv0(in_channels: int, out_channels: int, kernel_size: int) -> nn.Sequential:
    """Create a sequential module.

    Consisting of batch normalization and convolution.

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int
        Size of the convolutional kernel.

    Returns
    -------
    nn.Sequential
        Sequential module consisting of batch normalization and convolution.
    """
    return nn.Sequential(
        nn.BatchNorm2d(in_channels, eps=1e-5),
        nn.Conv2d(in_channels, out_channels, kernel_size, padding=kernel_size // 2),
    )


class ResDown(nn.Module):
    """Residual Downsample module.

    This module performs down-sampling with residual
    connections using batch normalization and convolutional layers.

    Attributes
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int
        Size of the convolutional kernel.
    conv : torch.nn.Sequential
        Sequential module consisting of batch normalization and convolution layers.
    proj : torch.nn.Sequential
        Sequential module consisting of batch normalization and 1x1 convolution layer.
    """

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int) -> None:
        """Initialize the ResDown class with the necessary attributes.

        Parameters
        ----------
        in_channels : int
            Number of input channels.
        out_channels : int
            Number of output channels.
        kernel_size : int
            Size of the convolutional kernel.
        """
        super().__init__()
        self.conv = nn.Sequential()
        self.proj = batchconv0(in_channels, out_channels, 1)
        for layer_idx in range(4):
            if layer_idx == 0:
                self.conv.add_module(
                    "conv_%d" % layer_idx,
                    batchconv(in_channels, out_channels, kernel_size),
                )
            else:
                self.conv.add_module(
                    "conv_%d" % layer_idx,
                    batchconv(out_channels, out_channels, kernel_size),
                )

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        """Forward pass of the residual downsample module.

        Parameters
        ----------
        input : torch.Tensor
            Input tensor.

        Returns
        -------
        torch.Tensor
            Output tensor after applying the residual downsample operation.
        """
        input = self.proj(input) + self.conv[1](self.conv[0](input))
        input = input + self.conv[3](self.conv[2](input))
        return input


class ConvDown(nn.Module):
    """Convolutional Downsample module.

    This module performs down-sampling using batch normalization and convolutional
    layers.

    Attributes
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int
        Size of the convolutional kernel.
    conv : torch.nn.Sequential
        Sequential module consisting of batch normalization and convolution layers.
    """

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int) -> None:
        """Initialize the ConvDown class with the necessary attributes.

        Parameters
        ----------
        in_channels : int
            Number of input channels.
        out_channels : int
            Number of output channels.
        kernel_size : int
            Size of the convolutional kernel.
        """
        super().__init__()
        self.conv = nn.Sequential()
        for layer_idx in range(2):
            if layer_idx == 0:
                self.conv.add_module(
                    "conv_%d" % layer_idx,
                    batchconv(in_channels, out_channels, kernel_size),
                )
            else:
                self.conv.add_module(
                    "conv_%d" % layer_idx,
                    batchconv(out_channels, out_channels, kernel_size),
                )

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        """Forward pass of the convolutional downsample module.

        Parameters
        ----------
        input : torch.Tensor
            Input tensor.

        Returns
        -------
        torch.Tensor
            Output tensor after applying the convolutional downsample operation.
        """
        input = self.conv[0](input)
        input = self.conv[1](input)
        return input


class Downsample(nn.Module):
    """Downsample Module.

    This module performs down-sampling using max pooling and convolutional layers.

    Attributes
    ----------
    channels_list : list of int
        List containing the number of channels for each layer.
    kernel_size : int
        Size of the convolutional kernel.
    residual_on : bool, optional
        Flag indicating whether to use residual connections, by default True.
    down : nn.Sequential
        Sequential module consisting of down-sampling layers.
    maxpool : nn.MaxPool2d
        Max pooling layer for down-sampling.
    """

    def __init__(
        self, channels_list: list, kernel_size: int, residual_on: bool = True
    ) -> None:
        """Initialize the Downsample class with the necessary attributes.

        Parameters
        ----------
        channels_list : list of int
            List containing the number of channels for each layer.
        kernel_size : int
            Size of the convolutional kernel.
        residual_on : bool, optional
            Flag indicating whether to use residual connections, by default True.
        """
        super().__init__()
        self.down = nn.Sequential()
        self.maxpool = nn.MaxPool2d(2, 2)
        for layer_idx in range(len(channels_list) - 1):
            if residual_on:
                self.down.add_module(
                    "res_down_%d" % layer_idx,
                    ResDown(
                        channels_list[layer_idx],
                        channels_list[layer_idx + 1],
                        kernel_size,
                    ),
                )
            else:
                self.down.add_module(
                    "conv_down_%d" % layer_idx,
                    ConvDown(
                        channels_list[layer_idx],
                        channels_list[layer_idx + 1],
                        kernel_size,
                    ),
                )

    def forward(self, input: torch.Tensor) -> list[torch.Tensor]:
        """Forward pass of the downsample module.

        Parameters
        ----------
        input : torch.Tensor
            Input tensor.

        Returns
        -------
        list of torch.Tensor
            List of output tensors after applying the downsample operation.
        """
        downsampled_inputs: list = []
        for layer_idx in range(len(self.down)):
            if layer_idx > 0:
                y = self.maxpool(downsampled_inputs[layer_idx - 1])
            else:
                y = input
            downsampled_inputs.append(self.down[layer_idx](y))
        return downsampled_inputs


class batchconvstyle(nn.Module):
    """BatchConvStyle Module.

    This module performs convolutional operations with style conditioning.

    Attributes
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    style_channels : int
        Number of channels in the style conditioning tensor.
    kernel_size : int
        Size of the convolutional kernel.
    concatenation : bool, optional
        Flag indicating whether to concatenate the input tensor with the conditioning
        tensor, by default False.
    concatenation : bool
        Flag indicating whether concatenation is used for input and conditioning
        tensors.
    conv : batchconv
        BatchConv module for performing convolutional operations.
    full : torch.nn.Linear
        Linear layer for transforming the style conditioning tensor.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        style_channels: int,
        kernel_size: int,
        concatenation: bool = False,
    ) -> None:
        """Initialize the BatchConvStyle class with the necessary attributes."""
        super().__init__()
        self.concatenation = concatenation
        if concatenation:
            self.conv = batchconv(in_channels * 2, out_channels, kernel_size)
            self.full = nn.Linear(style_channels, out_channels * 2)
        else:
            self.conv = batchconv(in_channels, out_channels, kernel_size)
            self.full = nn.Linear(style_channels, out_channels)

    def forward(
        self, style: torch.Tensor, x: torch.Tensor, y: torch.Tensor = None
    ) -> torch.Tensor:
        """Forward pass of the batchconvstyle module.

        Parameters
        ----------
        style : torch.Tensor
            Style conditioning tensor.
        x : torch.Tensor
            Input tensor.
        y : torch.Tensor, optional
            Conditioning tensor, by default None.

        Returns
        -------
        torch.Tensor
            Output tensor after applying the batchconvstyle operation.
        """
        if y is not None:
            if self.concatenation:
                x = torch.cat((y, x), dim=1)
            else:
                x = x + y
        feat = self.full(style)
        y = x + feat.unsqueeze(-1).unsqueeze(-1)
        y = self.conv(y)
        return y


class ResUp(nn.Module):
    """ResUp Module.

    This module performs upsampling operations with residual connections and style
    conditioning.

    Attributes
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    style_channels : int
        Number of channels in the style conditioning tensor.
    kernel_size : int
        Size of the convolutional kernel.
    concatenation : bool, optional
        Flag indicating whether to concatenate the input tensor with the conditioning
        tensor, by default False.
    conv : torch.nn.Sequential
        Sequential module containing convolutional operations.
    proj : batchconv0
        BatchConv0 module for projection convolution.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        style_channels: int,
        kernel_size: int,
        concatenation: bool = False,
    ) -> None:
        """Initialize the ResUp class with the necessary attributes.

        Parameters
        ----------
        in_channels : int
            Number of input channels.
        out_channels : int
            Number of output channels.
        style_channels : int
            Number of channels in the style conditioning tensor.
        kernel_size : int
            Size of the convolutional kernel.
        concatenation : bool, optional
            Flag indicating whether to concatenate the input tensor with
            the conditioning tensor, by default False.
        """
        super().__init__()
        self.conv = nn.Sequential()
        self.conv.add_module(
            "conv_0", batchconv(in_channels, out_channels, kernel_size)
        )
        self.conv.add_module(
            "conv_1",
            batchconvstyle(
                out_channels,
                out_channels,
                style_channels,
                kernel_size,
                concatenation=concatenation,
            ),
        )
        self.conv.add_module(
            "conv_2",
            batchconvstyle(out_channels, out_channels, style_channels, kernel_size),
        )
        self.conv.add_module(
            "conv_3",
            batchconvstyle(out_channels, out_channels, style_channels, kernel_size),
        )
        self.proj = batchconv0(in_channels, out_channels, 1)

    def forward(
        self,
        input_tensor: torch.Tensor,
        conditioning_tensor: torch.Tensor,
        style_tensor: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass of the resup module.

        Parameters
        ----------
        input_tensor : torch.Tensor
            Input tensor.
        conditioning_tensor : torch.Tensor
            Conditioning tensor.
        style_tensor : torch.Tensor
            Style conditioning tensor.

        Returns
        -------
        torch.Tensor
            Output tensor after applying the resup operation.
        """
        input_tensor = self.proj(input_tensor) + self.conv[1](
            style_tensor,
            self.conv[0](input_tensor),
            y=conditioning_tensor,
        )
        input_tensor = input_tensor + self.conv[3](
            style_tensor,
            self.conv[2](style_tensor, input_tensor),
        )
        return input_tensor


class ConvUp(nn.Module):
    """ConvUp Module.

    This module performs upsampling operations with convolutional layers and style
    conditioning.

    Attributes
    ----------
    conv : torch.nn.Sequential
        Sequential module containing convolutional operations.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        style_channels: int,
        kernel_size: int,
        concatenation: bool = False,
    ) -> None:
        """Initialize the ConvUp class with the necessary attributes.

        Parameters
        ----------
        in_channels : int
            Number of input channels.
        out_channels : int
            Number of output channels.
        style_channels : int
            Number of channels in the style conditioning tensor.
        kernel_size : int
            Size of the convolutional kernel.
        concatenation : bool, optional
            Flag indicating whether to concatenate the input tensor with
            the conditioning tensor, by default False.
        """
        super().__init__()
        self.conv = nn.Sequential()
        self.conv.add_module(
            "conv_0", batchconv(in_channels, out_channels, kernel_size)
        )
        self.conv.add_module(
            "conv_1",
            batchconvstyle(
                out_channels,
                out_channels,
                style_channels,
                kernel_size,
                concatenation=concatenation,
            ),
        )

    def forward(
        self,
        input_tensor: torch.Tensor,
        conditioning_tensor: torch.Tensor,
        style_tensor: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass of the ConvUp module.

        Parameters
        ----------
        input_tensor : torch.Tensor
            Input tensor.
        output_tensor : torch.Tensor
            Conditioning tensor.
        style_tensor : torch.Tensor
            Style conditioning tensor.

        Returns
        -------
        torch.Tensor
            Output tensor after applying the ConvUp operation.
        """
        output_tensor = self.conv[1](
            style_tensor, self.conv[0](input_tensor), y=conditioning_tensor
        )
        return output_tensor


class MakeStyle(nn.Module):
    """MakeStyle Module.

    This module generates style conditioning tensor from input tensor.

    Attributes
    ----------
    flatten : torch.nn.Flatten
        Flatten module for flattening the input tensor.
    """

    def __init__(self) -> None:
        """Initialize the MakeStyle class with the necessary attributes."""
        super().__init__()
        self.flatten = nn.Flatten()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        """Forward pass of the MakeStyle module.

        Parameters
        ----------
        input : torch.Tensor
            Input tensor.

        Returns
        -------
        torch.Tensor
            Style conditioning tensor.
        """
        kernel_size = [int(s) for s in input.shape[2:]]
        style = F.avg_pool2d(input, kernel_size=kernel_size)
        style = self.flatten(style)
        style = style / torch.sum(style**2, axis=1, keepdim=True) ** 0.5

        return style


class Upsample(nn.Module):
    """Upsample Module.

    This module performs upsampling operations with residual connections and style
    conditioning.

    Attributes
    ----------
    upsampling : torch.nn.Upsample
        Upsampling module for upsampling the input tensor.
    up : torch.nn.Sequential
        Sequential module containing upsampling operations.
    """

    def __init__(
        self,
        channels_list: list[int],
        kernel_size: int,
        residual_on: bool = True,
        concatenation: bool = False,
    ) -> None:
        """Initialize the Upsample class with the necessary attributes.

        Parameters
        ----------
        channels_list : list[int]
            List of number of channels for each upsampling layer.
        kernel_size : int
            Size of the convolutional kernel.
        residual_on : bool, optional
            Flag indicating whether to use residual connections, by default True.
        concatenation : bool, optional
            Flag indicating whether to concatenate the input tensor
            with the conditioning tensor, by default False.
        """
        super().__init__()
        self.upsampling = nn.Upsample(scale_factor=2, mode="nearest")
        self.up = nn.Sequential()
        for layer_idx in range(1, len(channels_list)):
            if residual_on:
                self.up.add_module(
                    "res_up_%d" % (layer_idx - 1),
                    ResUp(
                        channels_list[layer_idx],
                        channels_list[layer_idx - 1],
                        channels_list[-1],
                        kernel_size,
                        concatenation,
                    ),
                )
            else:
                self.up.add_module(
                    "conv_up_%d" % (layer_idx - 1),
                    ConvUp(
                        channels_list[layer_idx],
                        channels_list[layer_idx - 1],
                        channels_list[-1],
                        kernel_size,
                        concatenation,
                    ),
                )

    def forward(
        self,
        style: torch.Tensor,
        downsampled_tensors: list[torch.Tensor],
    ) -> torch.Tensor:
        """Forward pass of the upsample module.

        Parameters
        ----------
        style : torch.Tensor
            Style conditioning tensor.
        downsampled_tensors : list
            List of intermediate tensors from the downsample operation.

        Returns
        -------
        torch.Tensor
            Output tensor after applying the upsample operation.
        """
        output_tensor = self.up[-1](
            downsampled_tensors[-1], downsampled_tensors[-1], style
        )
        for layer_idx in range(len(self.up) - 2, -1, -1):
            output_tensor = self.upsampling(output_tensor)
            output_tensor = self.up[layer_idx](
                output_tensor, downsampled_tensors[layer_idx], style
            )
        return output_tensor


class Cellpose(nn.Module):
    """Cellpose model architecture.

    The implementation is based on `Cellpose: a generalist algorithm
    for cellular segmentation <https://www.nature.com/articles/s41592-020-01018-x>`_.

    This module provides the building blocks and the main network class for Cellpose,
    a deep learning model designed for generalist cellular segmentation. The
    architecture is a U-Net-like structure that computes a "style" vector from the
    input image, representing global features. This style vector is then used
    throughout the upsampling path to modulate the convolutional features, allowing
    the network to adapt to a wide variety of image types.

    Attributes
    ----------
    num_classes : int
            Number of classes in the dataset.
    channels_list : list
        List of number of channels for each downsampling layer.
    kernel_size : int
        Size of the convolutional kernel.
    residual_on : bool
        Flag indicating whether to use residual connections.
    style_on : bool
        Flag indicating whether to use style conditioning.
    concatenation : bool
        Flag indicating whether to concatenate the input tensor with the conditioning
        tensor.
    downsample : roche.crisp.networks.cellpose.Downsample
        Downsample module for downsampling the input tensor.
    upsample : roche.crisp.networks.cellpose.Upsample
        Upsample module for upsampling the input tensor.
    make_style : roche.crisp.networks.cellpose.MakeStyle
        MakeStyle module for generating style conditioning tensor.
    output : roche.crisp.networks.cellpose.batchconv
        BatchConv module for the final output convolution.

    Raises
    ------
    ValueError
        If channels_list is None or has less than 3 channels.
        If channels_list has odd channels.
    """

    def __init__(
        self,
        num_classes: int,
        channels_list: list,
        kernel_size: int = 3,
        residual_on: bool = True,
        style_on: bool = True,
        concatenation: bool = False,
    ) -> None:
        """Initialize the Cellpose class with the necessary attributes.

        Parameters
        ----------
        num_classes : int
            Number of classes in the dataset.
        channels_list : list
            List of number of channels for each downsampling layer.
        kernel_size : int
            Size of the convolutional kernel, by default 3.
        residual_on : bool, optional
            Flag indicating whether to use residual connections, by default True.
        style_on : bool, optional
            Flag indicating whether to use style conditioning, by default True.
        concatenation : bool, optional
            Flag indicating whether to concatenate the input tensor
            with the conditioning tensor, by default False.
        """
        super().__init__()
        self.num_classes = num_classes
        self.channels_list = channels_list
        if channels_list is None:
            raise ValueError("channels_list cannot be None")
        if len(channels_list) < 3:
            raise ValueError("channels_list must have at least 3 channels")

        for channel in channels_list:
            if channel % 2 != 0:
                raise ValueError("channels_list must have even channels")
        self.kernel_size = kernel_size
        self.residual_on = residual_on
        self.style_on = style_on
        self.concatenation = concatenation
        self.downsample = Downsample(
            channels_list, kernel_size, residual_on=residual_on
        )
        channels_listup = channels_list[1:]
        channels_listup.append(channels_listup[-1])
        self.upsample = Upsample(
            channels_listup,
            kernel_size,
            residual_on=residual_on,
            concatenation=concatenation,
        )
        self.make_style = MakeStyle()
        self.output = batchconv(channels_listup[0], self.num_classes, 1)

    def forward(self, input_data: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Propagate an input tensor through the Cellpose network.

        This method implements the forward pass of the Cellpose model. It first
        processes the input through a downsampling path (encoder) to extract
        features at multiple scales. A style vector is then computed from the
        deepest feature map. This style vector and the encoder features are used
        in the upsampling path (decoder) to reconstruct the final output map.

        Parameters
        ----------
        input_data : torch.Tensor
            The input image tensor, typically of shape (N, C, H, W).

        Returns
        -------
        Tuple[torch.Tensor, torch.Tensor]
            A tuple containing:
            - The final prediction map from the network.
            - The computed style vector, representing global features of the input.
        """
        downsampled_output = self.downsample(input_data)
        style = self.make_style(downsampled_output[-1])
        if not self.style_on:
            style = style * 0
        upsampled_output = self.upsample(style, downsampled_output)
        final_output = self.output(upsampled_output)

        return final_output, style
