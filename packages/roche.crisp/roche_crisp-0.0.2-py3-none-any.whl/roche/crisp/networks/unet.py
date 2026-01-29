"""U-Net networks for image segmentation and related tasks.

This module provides several implementations of the U-Net architecture, a
convolutional neural network designed for biomedical image segmentation. It
includes a from-scratch implementation (`VanillaUNet`) as well as more advanced
versions that leverage pre-trained encoder backbones from the `timm` library
(`SingleTaskUnet`, `MultiTaskUnet`).

The key components are:
- `VanillaUNet`: A classic U-Net implementation based on the original paper.
- `SingleTaskUnet`: A U-Net using a `timm` model as the encoder for a single
  output task.
- `MultiTaskUnet`: An extension of `SingleTaskUnet` with two output heads for
  multi-task learning.
- `EncoderBlock`, `DecoderBlock`, `ConvBlock`: Helper modules that form the
  building blocks of the U-Net architectures.
"""

from typing import Dict, List, Literal, Optional, Tuple, Union

import timm
import torch
from torch import nn
from torch.nn import ModuleList
from torch.nn import functional as F


class VanillaUNet(nn.Module):
    """Vanilla U-Net architecture.

    The implementation is based on `U-Net: Convolutional Networks for Biomedical
    Image Segmentation <https://arxiv.org/abs/1505.04597>`_.

    The U-Net is a convolutional encoder-decoder neural network. Contextual spatial
    information (from the decoding, expansive pathway) about an input tensor is merged
    with information representing the localization of details (from the encoding,
    compressive pathway). Modifications to the original paper:

    1. Padding is used in 3x3 convolutions to prevent loss of border pixels.
    2. Merging outputs does not require cropping due to the padding in point 1.
    3. Residual connections can be used by specifying `merge_mode='add'`.
    4. If non-parametric upsampling (`upmode='interpolation'`) is used in the
       decoder pathway, an additional 1x1 convolution is applied after
       upsampling to halve the number of channels. This channel-halving is
       handled automatically by the transpose convolution (`upmode='transpose'`).
    """

    def __init__(
        self,
        in_channels: int,
        num_classes: int,
        start_filters: int,
        depth: int,
        up_mode: Literal["transpose", "interpolation"],
        merge_mode: Literal["concat", "add"],
        weight_init_mode: Literal["kaiming_normal", "kaiming_uniform", "none"],
        weights: Optional[str] = None,
        activation_func: nn = nn.ReLU(),
        encoder_dropout_rate: Optional[List[float]] = None,
        apply_batch_normalization: bool = True,
        apply_padding: bool = False,
    ):
        """Initialize the SingleTaskUnet class with the necessary attributes.

        Parameters
        ----------
        in_channels : int
            number of channels in the input tensor
        num_classes : int
            number of classes
        start_filters : int
            number of convolutional filters for the first convolutional block
        depth : int
            defines the depth of the U-Net, each level is a convolutional block
        up_mode : Literal["transpose", "interpolation"]
            Type of upsampling to use. One of 'interpolation' or 'transpose'.
            If 'interpolation', uses bilinear interpolation followed by a 3x3 conv to
            match the number of channels for the skip connection.
            If 'transpose', uses transpose convolution
        merge_mode : Literal["concat", "add"]
            Type of skip connection to use. One of 'add' or 'concat'
        weight_init_mode : Literal["kaiming_normal", "kaiming_uniform", "none"]
            defines the initialization method, if none, no init method applied
        weights : Optional[str], optional
            initialize the model with a pre-trained model, by default None
        activation_func : nn, optional
            defines which activation function use for all convolutional blocks, by
            default nn.ReLU
        apply_encoder_dropout : bool, optional
            apply a 2D Dropout layer before and after the last encoder block before the
            decoding part, by default False
        encoder_dropout_rate : List[float], optional
            a list of dropout rates for the encoder part. The length of the list must
            be equal to the depth of the network. Set to None if no dropout is to be
            applied. If a value in the list is 0.0, no dropout is applied for that
            specific encoder block at that depth level. The default is None
        apply_batch_normalization : bool, optional
            add a 2D Batch Normalization layer after each 2D convolutional, by default
            False
        apply_padding : bool, optional
            apply padding while decoding, by default False

        Raises
        ------
        ValueError
            if up_mode option is not supported
        ValueError
            if merge_mode is not supported
        ValueError
            if activation_function is None
        ValueError
            if init mode is not supported
        """
        super().__init__()

        if encoder_dropout_rate is not None and len(encoder_dropout_rate) != depth:
            raise ValueError(
                "Error, the encoder_dropout_rate length must be equal to the depth of "
                "the network"
            )

        self.up_mode = up_mode
        self.merge_mode = merge_mode
        self.depth = depth
        self.num_classes = num_classes
        self.in_channels = in_channels

        self.encoder_blocks: ModuleList[EncoderBlock] = ModuleList()
        self.decoder_blocks: ModuleList[DecoderBlock] = ModuleList()

        outs: int = 0

        for i in range(depth):
            ins = in_channels if i == 0 else outs
            outs = start_filters * (2**i)
            pooling = True if i < depth - 1 else False

            encoder_block = EncoderBlock(
                in_channels=ins,
                out_channels=outs,
                activation_func=activation_func,
                apply_batch_normalization=apply_batch_normalization,
                apply_pooling=pooling,
                encoder_dropout_rate=(
                    encoder_dropout_rate[i] if encoder_dropout_rate is not None else 0.0
                ),
                bias=True,
                padding=1,
                num_conv=2,
            )
            self.encoder_blocks.append(encoder_block)

        for i in range(depth - 1):
            ins = outs
            outs = ins // 2
            decoder_block = DecoderBlock(
                in_channels=ins,
                out_channels=outs,
                activation_func=activation_func,
                apply_batch_normalization=apply_batch_normalization,
                up_mode=self.up_mode,
                merge_mode=self.merge_mode,
                apply_padding=apply_padding,
                apply_spatial_dimension_match=False,
                bias=True,
                padding=1,
                num_conv=2,
            )
            self.decoder_blocks.append(decoder_block)

        self.conv_final = nn.Conv2d(
            outs, num_classes, kernel_size=1, groups=1, stride=1
        )

        self.encoder_blocks = nn.ModuleList(self.encoder_blocks)
        self.decoder_blocks = nn.ModuleList(self.decoder_blocks)
        self.weight_init_mode = weight_init_mode
        self.reset_params(self.weight_init_mode)

        if weights is not None:
            self._load_from_state_dict(torch.load(weights))

    def reset_params(
        self, weight_init_mode: Literal["kaiming_normal", "kaiming_uniform", "none"]
    ) -> None:
        """Initialize the model layers.

        Parameters
        ----------
        weight_init_mode : Literal["kaiming_normal", "kaiming_uniform", "none"]
            defines the initialization method, if none, no init method applied

        Raises
        ------
        ValueError
            if init mode is not supported
        """
        if weight_init_mode not in ["kaiming_normal", "kaiming_uniform", "none"]:
            raise ValueError(
                "Error, weight_init_mode is incorrect. Choices: kaiming_normal, "
                "kaiming_uniform and none"
            )

        if weight_init_mode == "none":
            return

        for module in self.modules():
            if isinstance(module, nn.Conv2d):
                if weight_init_mode == "kaiming_normal":
                    nn.init.kaiming_normal_(module.weight)
                else:
                    nn.init.kaiming_uniform_(
                        module.weight, mode="fan_in", nonlinearity="relu"
                    )
                nn.init.constant_(module.bias, 0)
            if isinstance(module, nn.BatchNorm2d):
                nn.init.constant_(module.weight, 1)
                nn.init.constant_(module.bias, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Propagate an input tensor through the full U-Net architecture.

        This method passes the input tensor through the encoder path, collecting
        feature maps for skip connections at each level. It then processes these
        through the decoder path, merging the skip connection features at each
        stage. Finally, a 1x1 convolution is applied to produce the output
        prediction map.

        Parameters
        ----------
        x : torch.Tensor
            The input image tensor.

        Returns
        -------
        torch.Tensor
            The final prediction map from the network.
        """
        encoder_outs = []

        for i, encoder_block in enumerate(self.encoder_blocks):
            x, before_pool = encoder_block(x)
            encoder_outs.append(before_pool)

        for i, decoder_block in enumerate(self.decoder_blocks):
            before_pool = encoder_outs[-(i + 2)]
            x = decoder_block(x, before_pool)

        return self.conv_final(x)


class SingleTaskUnet(nn.Module):
    """U-Net model that performs single task, can be detection or segmentation."""

    def __init__(
        self,
        in_channels: int,
        num_classes: int,
        up_mode: Literal["transpose", "interpolation"],
        merge_mode: Literal["concat", "add"],
        encoder_freeze: bool,
        encoder_kwargs: Dict[str, Union[str, float, bool]],
        decoder_add_3rd_conv: bool = False,
        decoder_dropout_rate: Optional[float] = 0.0,
    ) -> None:
        """Initialize the SingleTaskUnet class with the necessary attributes.

        Parameters
        ----------
        in_channels : int
            number of channels in the input tensor
        task1_num_classes : int
            number of classes for the first task
        task2_num_classes : int
            number of classes for the second task
        up_mode : Literal["transpose", "interpolation"]
            type of upsampling to use. One of 'interpolation' or 'transpose'.
        merge_mode : Literal["concat", "add"]
            type of skip connection to use. One of 'add' or 'concat'
        encoder_freeze : bool
            if set to True, the layers of the encoder (backbone model) will be
            non-trainable
        encoder_kwargs : Dict[str, Union[str, float, bool]]
            Keyword arguments for the encoder, created using the timm wrapper.
            It should contain the following keys:

                - `model_name` (str): Name of classification model.
                - `pretrained` (bool, optional): If true, download pre-trained weights.
                - `out_indices` (List[int], optional): Indices of feature block
                    extractor.
                - `checkpoint_path` (str, optional): Path to a checkpoint to load.
                - `drop_rate` (float, optional): Classifier dropout rate.
                - `drop_path_rate` (float, optional): Stochastic depth drop rate.
                - `global_pool` (str, optional): Classifier global pooling type.

        decoder_add_3rd_conv : bool, optional
            whether to add a third 3x3 conv layer after the first two conv layers in
            decoder blocks.
        decoder_dropout_rate : float, optional, default 0.0
            defines the dropout probability

        Raises
        ------
        ValueError
            If encoder_kwargs is None, model_name is missing, or an
            unsupported up_mode or merge_mode is provided.

        FileNotFoundError
            If the weights file does not exist
        RuntimeError
            Unknown model_name

        Notes
        -----
        1. If weights is not None, finetune_mode must be defined.

        2. If merge_mode is 'add', the number of channels in the skip connection
        is the same as the number of channels in the upsampled tensor.
        If merge_mode is 'concat', the number of channels in the skip
        connection is doubled. This behavior is made possible by (1) with
        up_mode = interpolation, adding a 1x1 conv layer after upsampling with
        interpolation or (2) with up_mode = transpose, using a transpose
        convolution layer to match the number of channels in the skip connection.

        3. If add_3rd_conv is True, an additional 3x3 conv layer is added after the
        first two conv layers in the decoder blocks.
        """
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.up_mode = up_mode
        self.merge_mode = merge_mode
        self.encoder_kwargs = encoder_kwargs
        self.encoder_freeze = encoder_freeze
        self.decoder_add_3rd_conv = decoder_add_3rd_conv
        self.decoder_dropout_rate = decoder_dropout_rate

        if encoder_kwargs is None:
            raise ValueError("Error, encoder_kwargs is None")

        if encoder_kwargs.get("model_name", None) is None:
            raise ValueError("Error, model_name not found in the encoder_kwargs")

        self.encoder = timm.create_model(
            in_chans=self.in_channels, features_only=True, **self.encoder_kwargs
        )

        if self.encoder_freeze:
            for _, param in self.encoder.named_parameters():
                param.requires_grad = False

        encoder_channels: List[int] = self.encoder.feature_info.channels()

        self.decoder_ins = encoder_channels.copy()
        self.decoder_ins.reverse()
        self.decoder_outs = self.decoder_ins[1:]

        self.decoder_blocks: ModuleList[DecoderBlock] = ModuleList()
        for ins, outs in zip(self.decoder_ins[:-1], self.decoder_outs):
            self.decoder_blocks.append(
                DecoderBlock(
                    in_channels=ins,
                    out_channels=outs,
                    activation_func=nn.ReLU(inplace=True),
                    apply_batch_normalization=True,
                    up_mode=self.up_mode,
                    merge_mode=self.merge_mode,
                    apply_padding=False,
                    apply_spatial_dimension_match=True,
                    bias=True,
                    padding=1,
                    num_conv=3 if self.decoder_add_3rd_conv else 2,
                    dropout_rate=self.decoder_dropout_rate,
                )
            )

        if self.up_mode == "interpolation":
            self.decoder_up_sample = nn.Upsample(
                scale_factor=2, mode="bilinear", align_corners=True
            )
        else:
            self.decoder_up_sample = nn.ConvTranspose2d(
                in_channels=self.decoder_blocks[-1].out_channels,
                out_channels=self.decoder_blocks[-1].out_channels,
                kernel_size=2,
                stride=2,
            )

        self.conv_final = nn.ConvTranspose2d(
            in_channels=self.decoder_blocks[-1].out_channels,
            out_channels=self.num_classes,
            kernel_size=2,
            stride=2,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Propagate an input tensor through the U-Net for a single task.

        This method uses a pre-trained encoder backbone to extract features at
        multiple scales. These features are then passed up through the decoder,
        which combines them with skip connections from the encoder to generate a
        final, high-resolution prediction map.

        Parameters
        ----------
        x : torch.Tensor
            The input image tensor.

        Returns
        -------
        torch.Tensor
            The output prediction map for the single task.
        """
        encoder_outputs = self.encoder(x)

        out = encoder_outputs[-1]

        for i, decoder_block in enumerate(self.decoder_blocks, start=1):
            out = decoder_block(out, encoder_outputs[-1 - i])

        return self.conv_final(out)


class MultiTaskUnet(SingleTaskUnet):
    """U-Net model that performs multi-task: detection and segmentation."""

    def __init__(
        self,
        in_channels: int,
        task1_num_classes: int,
        task2_num_classes: int,
        up_mode: Literal["transpose", "interpolation"],
        merge_mode: Literal["concat", "add"],
        encoder_freeze: bool,
        encoder_kwargs: Dict[str, Union[str, float, bool]],
        decoder_add_3rd_conv: bool = False,
        decoder_dropout_rate: Optional[float] = 0.0,
    ) -> None:
        """Initialize the MultiTaskUnet class with the necessary attributes.

        Parameters
        ----------
        in_channels : int
            Number of channels in the input tensor
        num_classes : int
            Number of classes for the output.
        up_mode : Literal["transpose", "interpolation"]
            type of upsampling to use. One of 'interpolation' or 'transpose'.
            If 'interpolation', uses bilinear interpolation followed by a 3x3 conv to
            match the number of channels for the skip connection.
            If 'transpose', uses transpose convolution
        merge_mode : Literal["concat", "add"]
            Type of skip connection to use. One of 'add' or 'concat'
        encoder_freeze : bool
            If set to True, the layers of the encoder (backbone model) will be
            non-trainable
        encoder_kwargs : Dict[str, Union[str, float, bool]]
            Keyword arguments for the encoder, created using the timm wrapper.
            It should contain the following keys:

                - `model_name` (str): Name of classification model.
                - `pretrained` (bool, optional): If true, download pre-trained weights.
                - `out_indices` (List[int], optional): Indices of
                    feature block extractor.
                - `checkpoint_path` (str, optional): Path to a checkpoint to load.
                - `drop_rate` (float, optional): Classifier dropout rate.
                - `drop_path_rate` (float, optional): Stochastic depth drop rate.
                - `global_pool` (str, optional): Classifier global pooling type.

        decoder_add_3rd_conv : bool, optional
            Whether to add a third 3x3 conv layer after the first two conv layers in
            decoder blocks.
        decoder_dropout_rate : float, optional, default 0.0
            Defines the dropout probability.

        Raises
        ------
        ValueError
            If encoder_kwargs is None, model_name is missing, or an
            unsupported up_mode or merge_mode is provided.

        FileNotFoundError
            If the weights file does not exist
        RuntimeError
            Unknown model_name

        Notes
        -----
        1. If weights is not None, finetune_mode must be defined.

        2. If merge_mode is 'add', the number of channels in the skip connection
        is the same as the number of channels in the upsampled tensor.
        If merge_mode is 'concat', the number of channels in the skip
        connection is doubled. This behavior is made possible by (1) with
        up_mode = interpolation, adding a 1x1 conv layer after upsampling with
        interpolation or (2) with up_mode = transpose, using a transpose
        convolution layer to match the number of channels in the skip connection.

        3. If add_3rd_conv is True, an additional 3x3 conv layer is added after the
        first two conv layers in the decoder blocks.
        """
        super().__init__(
            in_channels=in_channels,
            num_classes=task1_num_classes,
            up_mode=up_mode,
            merge_mode=merge_mode,
            encoder_freeze=encoder_freeze,
            encoder_kwargs=encoder_kwargs,
            decoder_add_3rd_conv=decoder_add_3rd_conv,
            decoder_dropout_rate=decoder_dropout_rate,
        )

        self.task2_num_classes = task2_num_classes

        self.task1_conv_final = self.conv_final
        self.task2_conv_final = nn.ConvTranspose2d(
            in_channels=self.decoder_blocks[-1].out_channels,
            out_channels=task2_num_classes,
            kernel_size=2,
            stride=2,
        )

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """Propagate an input tensor through the multi-task U-Net.

        The method passes the input through the shared encoder and decoder, then
        generates a separate output for each of the two tasks using dedicated
        final convolutional layers.

        Parameters
        ----------
        x : torch.Tensor
            The input image tensor to the network.

        Returns
        -------
        List[torch.Tensor]
            A list containing two tensors: the prediction map for the first task
            and the prediction map for the second task.
        """
        encoder_outputs = self.encoder(x)

        out = encoder_outputs[-1]

        for i, decoder_block in enumerate(self.decoder_blocks, start=1):
            out = decoder_block(out, encoder_outputs[-1 - i])

        return [self.task1_conv_final(out), self.task2_conv_final(out)]


class EncoderBlock(nn.Module):
    """Defines the U-Net endecoder block."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        activation_func: nn,
        apply_batch_normalization: bool,
        apply_pooling: bool,
        encoder_dropout_rate: float,
        bias: bool,
        padding: int,
        num_conv: int,
    ) -> None:
        """Initialize the EncoderBlock class with the necessary attributes.

        Parameters
        ----------
        in_channels : int
            Number of channels in the input tensor.
        out_channels : int
            Number of dimensions of the output tensor.
        activation_func : torch.nn.Module
            Defines which activation function use for all convolutional blocks.
        apply_batch_normalization : bool
            Add a 2D Batch Normalization layer after each 2D convolutional, by default
            False.
        apply_pooling : bool
            Add a 2D Max Pooling layer to the encoder block.
        encoder_dropout_rate : float
            If apply_encoder_dropout is enabled, defines the dropout probability.
        bias : bool
            If True, adds a learnable bias to the output.
        padding : int
            Padding added to all four sides of the input.
        num_conv : int
            How many convolutional layers per block.
        """
        super().__init__()

        self.encoder_block = nn.Sequential()

        for i in range(0, num_conv):
            self.encoder_block.append(
                ConvBlock(
                    in_channels=in_channels if i == 0 else out_channels,
                    out_channels=out_channels,
                    bias=bias,
                    padding=padding,
                    activation_func=activation_func,
                    apply_batch_normalization=apply_batch_normalization,
                ),
            )

        if apply_pooling:
            self.pooling_layer = nn.MaxPool2d(kernel_size=2, stride=2)
        else:
            self.pooling_layer = lambda x: x

        if encoder_dropout_rate > 0.0:
            self.dropout = nn.Dropout2d(p=encoder_dropout_rate)
        else:
            self.dropout = lambda x: x

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Process one stage of the U-Net encoder.

        This method passes the input feature map through convolutional layers.
        It returns the feature map both before and after applying max pooling and
        dropout. The "before" tensor is used for the skip connection to the
        decoder.

        Parameters
        ----------
        x : torch.Tensor
            The input feature map from the previous encoder block or the initial
            image.

        Returns
        -------
        Tuple[torch.Tensor, torch.Tensor]
            A tuple containing:
            - The output feature map after pooling and dropout (to be passed to
              the next encoder block).
            - The feature map before pooling (to be used as a skip connection).
        """
        x = self.encoder_block(x)
        before_pool = x
        x = self.pooling_layer(x)
        x = self.dropout(x)

        return x, before_pool


class DecoderBlock(nn.Module):
    """Defines the U-Net decoder block."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        activation_func: nn,
        apply_batch_normalization: bool,
        up_mode: Literal["transpose", "interpolation"],
        merge_mode: Literal["concat", "add"],
        apply_padding: bool,
        apply_spatial_dimension_match: bool,
        bias: bool,
        padding: int,
        num_conv: int,
        dropout_rate: Optional[float] = 0.0,
    ) -> None:
        """Initialize the DecoderBlock class with the necessary attributes.

        Parameters
        ----------
        in_channels : int
            Number of channels in the input tensor.
        out_channels : int
            Number of dimensions of the output tensor.
        activation_func : torch.nn.Module
            Defines which activation function use for all convolutional blocks.
        apply_batch_normalization : bool
            Add a 2D Batch Normalization layer after each 2D convolutional, by default
            False.
        up_mode : Literal["transpose", "interpolation"]
            Type of upsampling to use. One of 'interpolation' or 'transpose'.
            If 'interpolation', uses bilinear interpolation followed by a 3x3 conv to
            match the number of channels for the skip connection.
            If 'transpose', uses transpose convolution.
        merge_mode : Literal["concat", "add"]
            Type of skip connection to use. One of 'add' or 'concat'.
        apply_padding : bool
            Apply padding while decoding.
        apply_spatial_dimension_match : bool
            Apply spatial dimension check.
        bias : bool
            Whether to add a learnable bias to the output.
        padding : int
            Padding added to all four sides of the input.
        num_conv : int
            How many convolutional layers per block.
        dropout_rate : float, optional, default 0.0
            Defines the dropout probability.

        Raises
        ------
        ValueError
            if up_mode option is not supported
        ValueError
            if merge_mode is not supported
        ValueError
            if activation_function is None
        """
        super().__init__()

        if up_mode not in ["transpose", "interpolation"]:
            raise ValueError(
                "Error, up_mode option is incorrect. Choices: transpose and "
                "interpolation"
            )

        if merge_mode not in ["concat", "add"]:
            raise ValueError("Error, merge_mode is incorrect. Choices: concat and add")

        if activation_func is None:
            raise ValueError("Error, activation function cannot be None")

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.merge_mode = merge_mode
        self.apply_spatial_dimension_match = apply_spatial_dimension_match
        self.apply_padding = apply_padding
        self.dropout_rate = dropout_rate

        if up_mode == "transpose":
            self.up_conv = nn.ConvTranspose2d(
                self.in_channels, self.out_channels, kernel_size=2, stride=2
            )
        else:
            self.up_conv = nn.Sequential(
                nn.Upsample(mode="bilinear", scale_factor=2, align_corners=True),
                nn.Conv2d(
                    self.in_channels,
                    self.out_channels,
                    kernel_size=1,
                    groups=1,
                    stride=1,
                    padding=0,
                ),
            )

        self.decoder_block = nn.Sequential()
        for i in range(0, num_conv):
            self.decoder_block.append(
                ConvBlock(
                    in_channels=(
                        self.out_channels * 2
                        if merge_mode == "concat" and i == 0
                        else self.out_channels
                    ),
                    out_channels=self.out_channels,
                    bias=bias,
                    padding=padding,
                    activation_func=activation_func,
                    apply_batch_normalization=apply_batch_normalization,
                    dropout_rate=self.dropout_rate,
                ),
            )

    def forward(self, x: torch.Tensor, skip_x: torch.Tensor) -> torch.Tensor:
        """Process one stage of the U-Net decoder.

        This method upsamples the feature map from the previous decoder layer,
        combines it with the feature map from the corresponding encoder layer (the
        skip connection), and then passes the result through a series of
        convolutional layers.

        Parameters
        ----------
        x : torch.Tensor
            The feature map tensor from the previous, deeper decoder block.
        skip_x : torch.Tensor
            The feature map tensor from the corresponding encoder block (skip
            connection).

        Returns
        -------
        torch.Tensor
            The output feature map of the decoder block, to be passed to the next,
            shallower block.
        """
        x = self.up_conv(x)

        if self.apply_padding:
            diffY = skip_x.size()[2] - x.size()[2]
            diffX = skip_x.size()[3] - x.size()[3]

            x = F.pad(
                x,
                (diffX // 2, diffX - diffX // 2, diffY // 2, diffY - diffY // 2),
            )

        if self.apply_spatial_dimension_match:
            x = nn.functional.interpolate(
                x,
                size=(skip_x.size()[2], skip_x.size()[3]),
                mode="bilinear",
                align_corners=True,
            )

        x = torch.cat((skip_x, x), dim=1) if self.merge_mode == "concat" else x + skip_x

        return self.decoder_block(x)


class ConvBlock(nn.Module):
    """Class for standard convolutional block for image processing."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        bias: bool,
        padding: int,
        activation_func: nn = nn.ReLU,
        apply_batch_normalization: bool = True,
        dropout_rate: float = 0.0,
    ) -> None:
        """Initialize the ConvBlock class with the necessary attributes.

        Block composition and execution order:
        - 2D Convolutional layer (3x3)
        - Optionally:
            - 2D Batch Normalization
        - Activation Function (e.g. sigmoid, relu, etc.)

        Parameters
        ----------
        in_channels : int
            number of channels in the input image
        out_channels : int
            number of channels produced by the convolution
        bias : bool
            if True, adds a learnable bias to the output
        padding : int
            padding added to all four sides of the input
        activation_func : nn, optional
            pytorch activation function, by default nn.ReLU
        apply_batch_normalization : bool, optional
            add a 2D Batch Normalization layer after each 2D convolutional, by default
            False
        dropout_rate : float, default=0.0
        """
        super().__init__()

        self.block = nn.Sequential(
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                stride=1,
                padding=padding,
                dilation=1,
                groups=1,
                bias=bias,
            )
        )

        self.block.append(activation_func)

        if apply_batch_normalization:
            self.block.append(nn.BatchNorm2d(out_channels))

        if dropout_rate > 0.0:
            self.block.append(nn.Dropout2d(p=dropout_rate))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the convolutional block to an input tensor.

        The input is passed through a sequence of Conv2d, an activation
        function, and optional BatchNorm2d and Dropout2d layers.

        Parameters
        ----------
        x : torch.Tensor
            The input feature map.

        Returns
        -------
        torch.Tensor
            The output feature map after processing.
        """
        return self.block(x)
