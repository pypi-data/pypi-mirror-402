"""Vision Transformer U-Net model."""

import logging
from collections import OrderedDict
from typing import Dict, Optional, Union

import timm
import torch
import torch.nn as nn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s\n",
    datefmt="%Y-%m-%d %H:%M:%S",
)

output_logger = logging.getLogger(__name__)


class Conv2DBlock(nn.Module):
    """Create a Convolutional block."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        dropout: float = 0,
    ) -> None:
        """Initialize the Conv2DBlock.

        Parameters
        ----------
        in_channels : int
            number of channels in the input tensor
        out_channels : int
            number of channels in the output tensor
        kernel_size : int, optional
            size of the kernel, by default 3
        dropout : float, optional
            dropout rate, by default 0
        """
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=kernel_size,
                stride=1,
                padding=((kernel_size - 1) // 2),
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(True),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform forward pass of the network.

        Parameters
        ----------
        x : torch.Tensor
            Input to the network

        Returns
        -------
        torch.Tensor
            Outputs predictions
        """
        return self.block(x)


class Deconv2DBlock(nn.Module):
    """Create a Deconvolutional block."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        dropout: float = 0,
    ) -> None:
        """Initialize the Deconv2DBlock.

        Parameters
        ----------
        in_channels : int
            number of channels in the input tensor
        out_channels : int
            number of channels in the output tensor
        kernel_size : int, optional
            size of the kernel, by default 3
        dropout : float, optional
            dropout rate, by default 0
        """
        super().__init__()
        self.block = nn.Sequential(
            nn.ConvTranspose2d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=2,
                stride=2,
                padding=0,
                output_padding=0,
            ),
            nn.Conv2d(
                in_channels=out_channels,
                out_channels=out_channels,
                kernel_size=kernel_size,
                stride=1,
                padding=((kernel_size - 1) // 2),
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(True),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform forward pass of the network.

        Parameters
        ----------
        x : torch.Tensor
            Input to the network

        Returns
        -------
        torch.Tensor
            Outputs predictions
        """
        return self.block(x)


class VitUnet(nn.Module):
    """U-Net model with vision transformer encoder."""

    def __init__(
        self,
        num_classes: int,
        encoder_freeze: bool,
        encoder_kwargs: Dict[str, Union[str, float, bool]],
        extract_layers: Optional[list] = [2, 5, 8, 11],
        decoder_dropout_rate: Optional[float] = 0.0,
    ) -> None:
        """Initialize the Vit U-Net model.

        Parameters
        ----------
        num_classes : int
            number of classes
        encoder_freeze : bool
            if set to True, the layers of the encoder (backbone model) will be
            non-trainable
        encoder_kwargs:
            model_name : str
                name of the ViT model used as
                feature extractor. The backbone is created
                using the timm wrapper.
            pretrained : bool, optional
                if true, it download the weights of the pre-trained backbone network
            checkpoint_path : str, optional
                path of checkpoint to load after the model is initialized
        decoder_dropout_rate : float, optional, default 0.0
            defines the dropout probability

        Raises
        ------
        ValueError
            encoder_kwargs is None
        ValueError
            encoder model_name not found in the encoder_kwargs
        FileNotFoundError:
            if the weights file does not exist
        RuntimeError
            Unknown model_name
        """
        super().__init__()
        self.num_classes = num_classes
        self.extract_layers = extract_layers
        self.encoder_kwargs = encoder_kwargs
        self.encoder_freeze = encoder_freeze
        self.decoder_dropout_rate = decoder_dropout_rate

        if encoder_kwargs is None:
            raise ValueError("Error, encoder_kwargs is None")

        if encoder_kwargs.get("model_name", None) is None:
            raise ValueError("Error, model_name not found in the encoder_kwargs")

        self.encoder = timm.create_model(**self.encoder_kwargs, num_classes=0)
        self.embed_dim = self.encoder.embed_dim
        self.num_transformer_blocks = len(self.encoder.blocks)

        output_logger.info(f"Embedding dimension: {self.embed_dim}")
        output_logger.info(
            f"Number of transformer blocks: {self.num_transformer_blocks}"
        )

        if self.encoder_freeze:
            for _, param in self.encoder.named_parameters():
                param.requires_grad = False

        # ----------------- DECODER -----------------
        if self.embed_dim < 512:
            self.skip_dim_11 = 256
            self.skip_dim_12 = 128
            self.bottleneck_dim = 312
        else:
            self.skip_dim_11 = 512
            self.skip_dim_12 = 256
            self.bottleneck_dim = 512

        # version with shared skip_connections
        self.decoder0 = nn.Sequential(
            Conv2DBlock(3, 32, 3, dropout=self.decoder_dropout_rate),
            Conv2DBlock(32, 64, 3, dropout=self.decoder_dropout_rate),
        )  # skip connection after positional encoding, shape should be H, W, 64
        self.decoder1 = nn.Sequential(
            Deconv2DBlock(
                self.embed_dim, self.skip_dim_11, dropout=self.decoder_dropout_rate
            ),
            Deconv2DBlock(
                self.skip_dim_11, self.skip_dim_12, dropout=self.decoder_dropout_rate
            ),
            Deconv2DBlock(self.skip_dim_12, 128, dropout=self.decoder_dropout_rate),
        )  # skip connection 1
        self.decoder2 = nn.Sequential(
            Deconv2DBlock(
                self.embed_dim, self.skip_dim_11, dropout=self.decoder_dropout_rate
            ),
            Deconv2DBlock(self.skip_dim_11, 256, dropout=self.decoder_dropout_rate),
        )  # skip connection 2
        self.decoder3 = nn.Sequential(
            Deconv2DBlock(
                self.embed_dim, self.bottleneck_dim, dropout=self.decoder_dropout_rate
            )
        )  # skip connection 3

        self.upsampling_decoder = self.create_upsampling_branch(self.num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform forward pass of the network.

        Parameters
        ----------
        x : torch.Tensor
            Input to the network

        Returns
        -------
        List[torch.Tensor]
            Outputs a prediction
        """
        output, intermediates = self.encoder.forward_intermediates(
            x, self.extract_layers
        )

        z0 = x
        z1, z2, z3, z4 = intermediates

        out = self._forward_upsample(z0, z1, z2, z3, z4, self.upsampling_decoder)

        return out

    def _forward_upsample(
        self,
        z0: torch.Tensor,
        z1: torch.Tensor,
        z2: torch.Tensor,
        z3: torch.Tensor,
        z4: torch.Tensor,
        branch_decoder: nn.Sequential,
    ) -> torch.Tensor:
        """Forward upsample branch.

        Parameters
        ----------
        z0 (torch.Tensor) : Highest skip
        z1 (torch.Tensor) : 1. Skip
        z2 (torch.Tensor) : 2. Skip
        z3 (torch.Tensor) : 3. Skip
        z4 (torch.Tensor) : Bottleneck
        branch_decoder (nn.Sequential) : Branch decoder network

        Returns
        -------
            torch.Tensor: Branch Output
        """
        b4 = branch_decoder.bottleneck_upsampler(z4)
        b3 = self.decoder3(z3)
        b3 = branch_decoder.decoder3_upsampler(torch.cat([b3, b4], dim=1))
        b2 = self.decoder2(z2)
        b2 = branch_decoder.decoder2_upsampler(torch.cat([b2, b3], dim=1))
        b1 = self.decoder1(z1)
        b1 = branch_decoder.decoder1_upsampler(torch.cat([b1, b2], dim=1))
        b0 = self.decoder0(z0)
        branch_output = branch_decoder.decoder0_header(torch.cat([b0, b1], dim=1))

        return branch_output

    def create_upsampling_branch(self, num_classes: int) -> nn.Module:
        """Create the upsampling branch of the network.

        This method constructs a sequential upsampling branch consisting of multiple
        upsampling and convolutional blocks. The upsampling branch is used to increase
        the spatial resolution of the feature maps and generate the final output with
        the specified number of classes.

        Parameters
        ----------
        num_classes : int
            The number of output classes for the final layer.

        Returns
        -------
        nn.Module
            A sequential container of the upsampling branch.
        """
        bottleneck_upsampler = nn.ConvTranspose2d(
            in_channels=self.embed_dim,
            out_channels=self.bottleneck_dim,
            kernel_size=2,
            stride=2,
            padding=0,
            output_padding=0,
        )
        decoder3_upsampler = nn.Sequential(
            Conv2DBlock(
                self.bottleneck_dim * 2,
                self.bottleneck_dim,
                dropout=self.decoder_dropout_rate,
            ),
            Conv2DBlock(
                self.bottleneck_dim,
                self.bottleneck_dim,
                dropout=self.decoder_dropout_rate,
            ),
            Conv2DBlock(
                self.bottleneck_dim,
                self.bottleneck_dim,
                dropout=self.decoder_dropout_rate,
            ),
            nn.ConvTranspose2d(
                in_channels=self.bottleneck_dim,
                out_channels=256,
                kernel_size=2,
                stride=2,
                padding=0,
                output_padding=0,
            ),
        )
        decoder2_upsampler = nn.Sequential(
            Conv2DBlock(256 * 2, 256, dropout=self.decoder_dropout_rate),
            Conv2DBlock(256, 256, dropout=self.decoder_dropout_rate),
            nn.ConvTranspose2d(
                in_channels=256,
                out_channels=128,
                kernel_size=2,
                stride=2,
                padding=0,
                output_padding=0,
            ),
        )
        decoder1_upsampler = nn.Sequential(
            Conv2DBlock(128 * 2, 128, dropout=self.decoder_dropout_rate),
            Conv2DBlock(128, 128, dropout=self.decoder_dropout_rate),
            nn.ConvTranspose2d(
                in_channels=128,
                out_channels=64,
                kernel_size=2,
                stride=2,
                padding=0,
                output_padding=0,
            ),
        )
        decoder0_header = nn.Sequential(
            Conv2DBlock(64 * 2, 64, dropout=self.decoder_dropout_rate),
            Conv2DBlock(64, 64, dropout=self.decoder_dropout_rate),
            nn.Conv2d(
                in_channels=64,
                out_channels=num_classes,
                kernel_size=1,
                stride=1,
                padding=0,
            ),
        )

        decoder = nn.Sequential(
            OrderedDict(
                [
                    ("bottleneck_upsampler", bottleneck_upsampler),
                    ("decoder3_upsampler", decoder3_upsampler),
                    ("decoder2_upsampler", decoder2_upsampler),
                    ("decoder1_upsampler", decoder1_upsampler),
                    ("decoder0_header", decoder0_header),
                ]
            )
        )

        return decoder


if __name__ == "__main__":
    checkpt = (
        "/projects/site/dia/rds-csi/cell-vision/pretrained-models/"
        "dino_vit_small_patch16_ep200.torch"
    )

    net = VitUnet(
        num_classes=4,
        extract_layers=[2, 5, 8, 11],
        encoder_freeze=False,
        encoder_kwargs=dict(
            model_name="vit_small_patch16_224", pretrained=True, checkpoint_path=checkpt
        ),
        decoder_dropout_rate=0,
    )

    dummy_input = torch.randn(1, 3, 224, 224)
    output = net(dummy_input)
    output_logger.info(f"Model architecture: \n{net}")
    output_logger.info(f"Output shape: {output.shape}")
