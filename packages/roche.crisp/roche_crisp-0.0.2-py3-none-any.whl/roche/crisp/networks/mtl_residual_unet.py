"""Module for Unet architecture using resnet encoder."""

from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models


class DilatedConv(nn.Module):
    """Class representing dilated convolutional layer.

    Attributes
    ----------
    in_channel : int
        The number of input channels.
    out_channel : int
        The number of output channels.
    kernel_size : int, optional
        The size of the kernel, by default 3.
    dropout_rate : float, optional
        The dropout rate, by default 0.0.
    activation : function, optional
        The activation function, by default `relu`.
    dilation : int, optional
        The dilation rate, by default 1.
    """

    def __init__(
        self,
        in_channel,
        out_channel,
        kernel_size=3,
        dropout_rate=0.0,
        activation=F.relu,
        dilation=1,
    ):
        """Initialize instance of the class."""
        super().__init__()
        self.conv = nn.Conv2d(
            in_channel, out_channel, kernel_size, padding=dilation, dilation=dilation
        )
        self.norm = nn.BatchNorm2d(out_channel)
        self.activation = activation
        if dropout_rate > 0:
            self.drop = nn.Dropout2d(p=dropout_rate)
        else:
            self.drop = lambda x: x  # no-op

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform forward pass of the network.

        Parameters
        ----------
        x : torch.Tensor
            Input to the network

        Returns
        -------
        torch.Tensor
            Output after applying dilated convolution.
        """
        x = self.norm(self.activation(self.conv(x)))
        x = self.drop(x)
        return x


class ConvDownBlock(nn.Module):
    """Class representing convolutional down block of UNet architecture.

    Attributes
    ----------
    in_channel : int
        The number of input channels.
    out_channel : int
        The number of output channels.
    dropout_rate : float, optional
        The dropout rate, by default 0.0.
    dilation : int, optional
        The dilation rate, by default 1.
    """

    def __init__(self, in_channel, out_channel, dropout_rate=0.0, dilation=1):
        """Initialize instance of the class."""
        super().__init__()
        self.conv1 = DilatedConv(
            in_channel, out_channel, dropout_rate=dropout_rate, dilation=dilation
        )
        self.conv2 = DilatedConv(
            out_channel, out_channel, dropout_rate=dropout_rate, dilation=dilation
        )
        self.pool = nn.MaxPool2d(kernel_size=2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Perform forward pass of the network.

        Parameters
        ----------
        x : torch.Tensor
            Input to the network

        Returns
        -------
        Tuple[torch.Tensor, torch.Tensor]
            Output after applying down convolution and maxpool.
        """
        x = self.conv1(x)
        x = self.conv2(x)
        return self.pool(x), x


class ConvUpBlock(nn.Module):
    """Class representing convolutional up block of UNet architecture.

    Attributes
    ----------
    in_channel : int
        The number of input channels.
    out_channel : int
        The number of output channels.
    dropout_rate : float, optional
        The dropout rate, by default 0.0.
    dilation : int, optional
        The dilation rate, by default 1.
    """

    def __init__(self, in_channel, out_channel, dropout_rate=0.0, dilation=1):
        """Initialize instance of the class."""
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channel, in_channel // 2, 2, stride=2)
        self.conv1 = DilatedConv(
            in_channel // 2 + out_channel,
            out_channel,
            dropout_rate=dropout_rate,
            dilation=dilation,
        )
        self.conv2 = DilatedConv(
            out_channel, out_channel, dropout_rate=dropout_rate, dilation=dilation
        )

    def forward(self, x: torch.Tensor, x_skip: torch.Tensor) -> torch.Tensor:
        """Perform forward pass of the network.

        Parameters
        ----------
        x : torch.Tensor
            Input to the network
        x_skip : torch.Tensor
            Skip connection input

        Returns
        -------
        torch.Tensor
            Output tensor after applying up convolution.
        """
        x = self.up(x)
        H_diff = x.shape[2] - x_skip.shape[2]
        W_diff = x.shape[3] - x_skip.shape[3]
        x_skip = F.pad(x_skip, (0, W_diff, 0, H_diff), mode="reflect")
        x = torch.cat([x, x_skip], 1)
        x = self.conv1(x)
        x = self.conv2(x)
        return x


class ResUNet(nn.Module):
    """Class for UNet architecture with ResNet as encoder.

    Attributes
    ----------
    seg_c : int, optional
        Number of segmentation classes, by default 2.
    det_c : int, optional
        Number of detection classes, by default 4.
    arch : str, optional
        Encoder architecuture to use, by default "resnet18".
    weights : str, optional
        Pre-trained weights to use for initialization,
        obtained from torchvision.models, by default ResNet18_Weights.IMAGENET1K_V1.
    fixed_feature : bool, optional
        Flag to freeze encoder, by default False.
    """

    def __init__(
        self,
        seg_c=2,
        det_c=4,
        arch="resnet18",
        weights="ResNet18_Weights.IMAGENET1K_V1",
        fixed_feature=False,
    ):
        """Initialize instance of the class."""
        super().__init__()
        # load weights of pre-trained resnet
        if arch == "resnet18":
            self.resnet = models.resnet18(weights=weights)
            # up conv
            num_layer_feat = [64, 64, 128, 256, 512]
        elif arch == "resnet50":
            self.resnet = models.resnet50(weights=weights)
            num_layer_feat = [64, 256, 512, 1024, 2048]

        if fixed_feature:
            for param in self.resnet.parameters():
                param.requires_grad = False

            for module in self.resnet.modules():
                if isinstance(module, torch.nn.modules.BatchNorm1d) or isinstance(
                    module, torch.nn.modules.BatchNorm2d
                ):
                    for param in module.parameters():
                        param.requires_grad = True

        # segmentation decoder
        self.u5 = ConvUpBlock(num_layer_feat[4], num_layer_feat[3], dropout_rate=0.1)
        self.u6 = ConvUpBlock(num_layer_feat[3], num_layer_feat[2], dropout_rate=0.1)
        self.u7 = ConvUpBlock(num_layer_feat[2], num_layer_feat[1], dropout_rate=0.1)
        self.u8 = ConvUpBlock(num_layer_feat[1], num_layer_feat[0], dropout_rate=0.1)
        self.seg_ce = nn.ConvTranspose2d(num_layer_feat[0], seg_c, 2, stride=2)

        # detection decoder
        self.det_u5 = ConvUpBlock(
            num_layer_feat[4], num_layer_feat[3], dropout_rate=0.1
        )
        self.det_u6 = ConvUpBlock(
            num_layer_feat[3], num_layer_feat[2], dropout_rate=0.1
        )
        self.det_u7 = ConvUpBlock(
            num_layer_feat[2], num_layer_feat[1], dropout_rate=0.1
        )
        self.det_u8 = ConvUpBlock(
            num_layer_feat[1], num_layer_feat[0], dropout_rate=0.1
        )
        self.det_ce = nn.ConvTranspose2d(num_layer_feat[0], det_c, 2, stride=2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Perform forward pass of the network.

        Parameters
        ----------
        x : torch.Tensor
            Input to the network

        Returns
        -------
        Tuple[torch.Tensor, torch.Tensor]
            Outputs segmentation and detection predictions
        """
        x = self.resnet.conv1(x)
        x = self.resnet.bn1(x)
        x = c1 = self.resnet.relu(x)
        x = self.resnet.maxpool(x)
        x = c2 = self.resnet.layer1(x)
        x = c3 = self.resnet.layer2(x)
        x = c4 = self.resnet.layer3(x)
        enc_out = self.resnet.layer4(x)

        # segmentation decoder
        x = self.u5(enc_out, c4)
        x = self.u6(x, c3)
        x = self.u7(x, c2)
        x = self.u8(x, c1)
        seg_out = self.seg_ce(x)

        # detection decoder
        x = self.det_u5(enc_out, c4)
        x = self.det_u6(x, c3)
        x = self.det_u7(x, c2)
        x = self.det_u8(x, c1)
        det_out = self.det_ce(x)

        return seg_out, det_out


if __name__ == "__main__":
    net = ResUNet(3, 4)
    out = net(torch.randn((32, 3, 1024, 1024)))
    print(net)
