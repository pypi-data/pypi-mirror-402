"""Module fo the InstanSeg UNet model."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from einops import rearrange


def feature_engineering(
    x: torch.Tensor,
    c: torch.Tensor,
    sigma: torch.Tensor,
    window_size: int,
    mesh_grid_flat: torch.Tensor,
):
    """Feature engineering for the InstanSeg UNet model."""
    E = x.shape[0]
    h, w = x.shape[-2:]
    C = c.shape[0]
    S = sigma.shape[0]

    x = torch.cat([x, sigma])[:, mesh_grid_flat[0], mesh_grid_flat[1]]

    x = rearrange(
        x,
        "(E) (C H W) -> C (E) H W",
        E=E + S,
        C=C,
        H=2 * window_size,
        W=2 * window_size,
    )
    c_shaped = c.view(-1, E, 1, 1)
    x[:, :E] -= c_shaped
    x = rearrange(x, "C (E) H W-> (C H W) (E)", E=E + S)
    return x


def feature_engineering_slow(
    x: torch.Tensor,
    c: torch.Tensor,
    sigma: torch.Tensor,
    window_size: int,
    mesh_grid_flat: torch.Tensor,
):
    """Feature engineering for the InstanSeg UNet model."""
    E = x.shape[0]
    h, w = x.shape[-2:]
    C = c.shape[0]
    S = sigma.shape[0]

    x_slices = (
        x[:, mesh_grid_flat[0], mesh_grid_flat[1]]
        .reshape(E, C, 2 * window_size, 2 * window_size)
        .permute(1, 0, 2, 3)
    )  # C,E,2*window_size,2*window_size
    sigma_slices = (
        sigma[:, mesh_grid_flat[0], mesh_grid_flat[1]]
        .reshape(S, C, 2 * window_size, 2 * window_size)
        .permute(1, 0, 2, 3)
    )  # C,S,2*window_size,2*window_size
    c_shaped = c.reshape(-1, E, 1, 1)

    diff = x_slices - c_shaped

    x = torch.cat([diff, sigma_slices], dim=1)  # C,E+S+1,H,W

    x = x.flatten(2).permute(0, -1, 1)  # C,H*W,E+S+1
    x = x.reshape((x.shape[0] * x.shape[1]), x.shape[2])  # C*H*W,E+S+1

    return x


def feature_engineering_2(
    x: torch.Tensor,
    xxyy: torch.Tensor,
    c: torch.Tensor,
    sigma: torch.Tensor,
    window_size: int,
    mesh_grid_flat: torch.Tensor,
):
    """Feature engineering for the InstanSeg UNet model."""
    E = x.shape[0]
    h, w = x.shape[-2:]
    C = c.shape[0]
    S = sigma.shape[0]

    x_slices = (
        x[:, mesh_grid_flat[0], mesh_grid_flat[1]]
        .reshape(E, C, 2 * window_size, 2 * window_size)
        .permute(1, 0, 2, 3)
    )  # C,E,2*window_size,2*window_size
    sigma_slices = (
        sigma[:, mesh_grid_flat[0], mesh_grid_flat[1]]
        .reshape(S, C, 2 * window_size, 2 * window_size)
        .permute(1, 0, 2, 3)
    )  # C,S,2*window_size,2*window_size
    c_shaped = c.reshape(-1, E, 1, 1)

    norm = torch.sqrt(
        torch.sum(torch.pow(x_slices - c_shaped, 2) + 1e-6, dim=1, keepdim=True)
    )  # C,1,H,W

    diff = x_slices - c_shaped

    x = torch.cat([diff, sigma_slices, norm], dim=1)  # C,E+S+1,H,W

    x = x.flatten(2).permute(0, -1, 1)  # C,H*W,E+S+1
    x = x.reshape((x.shape[0] * x.shape[1]), x.shape[2])  # C*H*W,E+S+1

    return x


def feature_engineering_3(
    x: torch.Tensor,
    xxyy: torch.Tensor,
    c: torch.Tensor,
    sigma: torch.Tensor,
    window_size: int,
    mesh_grid_flat: torch.Tensor,
):
    """Feature engineering for the InstanSeg UNet model."""
    # NO SIGMA
    E = x.shape[0]
    h, w = x.shape[-2:]
    C = c.shape[0]
    S = sigma.shape[0]

    x_slices = (
        x[:, mesh_grid_flat[0], mesh_grid_flat[1]]
        .reshape(E, C, 2 * window_size, 2 * window_size)
        .permute(1, 0, 2, 3)
    )  # C,E,2*window_size,2*window_size
    sigma_slices = (
        sigma[:, mesh_grid_flat[0], mesh_grid_flat[1]]
        .reshape(S, C, 2 * window_size, 2 * window_size)
        .permute(1, 0, 2, 3)
    )  # C,S,2*window_size,2*window_size
    c_shaped = c.reshape(-1, E, 1, 1)

    diff = x_slices - c_shaped

    x = torch.cat([diff, sigma_slices * 0], dim=1)  # C,E+S+1,H,W

    x = x.flatten(2).permute(0, -1, 1)  # C,H*W,E+S+1
    x = x.reshape((x.shape[0] * x.shape[1]), x.shape[2])  # C*H*W,E+S+1

    return x


def feature_engineering_10(
    x: torch.Tensor,
    xxyy: torch.Tensor,
    c: torch.Tensor,
    sigma: torch.Tensor,
    window_size: int,
    mesh_grid_flat: torch.Tensor,
):
    """Feature engineering for the InstanSeg UNet model."""
    # CONV
    E = x.shape[0]
    h, w = x.shape[-2:]
    C = c.shape[0]
    S = sigma.shape[0]

    x_slices = (
        x[:, mesh_grid_flat[0], mesh_grid_flat[1]]
        .reshape(E, C, 2 * window_size, 2 * window_size)
        .permute(1, 0, 2, 3)
    )  # C,E,2*window_size,2*window_size
    sigma_slices = (
        sigma[:, mesh_grid_flat[0], mesh_grid_flat[1]]
        .reshape(S, C, 2 * window_size, 2 * window_size)
        .permute(1, 0, 2, 3)
    )  # C,S,2*window_size,2*window_size
    c_shaped = c.reshape(-1, E, 1, 1)
    diff = x_slices - c_shaped
    x = torch.cat([diff, sigma_slices], dim=1)  # C,E+S+1,H,W

    return x


def feature_engineering_generator(feature_engineering_function):
    """Feature engineering generator for the InstanSeg UNet model."""
    if feature_engineering_function == "0" or feature_engineering_function == "7":
        return feature_engineering, 2
    elif feature_engineering_function == "2":
        return feature_engineering_2, 3
    elif feature_engineering_function == "3":
        return feature_engineering_3, 2
    elif feature_engineering_function == "10":
        return feature_engineering_10, 2

    else:
        raise NotImplementedError(
            "Feature engineering function",
            feature_engineering_function,
            "is not implemented",
        )


def has_pixel_classifier_model(model):
    """Check if the model has a pixel classifier."""
    for module in model.modules():
        if isinstance(module, torch.nn.Module):
            module_class = module.__class__.__name__
            if "ProbabilityNet" in module_class:
                return True
    return False


class ProbabilityNet(nn.Module):
    """Probability network for the InstanSeg UNet model."""

    def __init__(self, embedding_dim=4, width=5):
        """Initialize the probability network."""
        super().__init__()
        self.fc1 = nn.Linear(embedding_dim, width)
        self.fc2 = nn.Linear(width, width)
        self.fc3 = nn.Linear(width, 1)

    def forward(self, x):
        """Forward pass of the probability network."""
        # x is C*H*W,E+S+1 (H,W is the window of crop used here, e.g 100x100, not image)
        #  with torch.cuda.amp.autocast():
        x = self._relu_non_empty(self.fc1(x))
        x = self._relu_non_empty(self.fc2(x))
        x = self.fc3(x)
        return x

    def _relu_non_empty(self, x: torch.Tensor) -> torch.Tensor:
        """Workaround for https://github.com/pytorch/pytorch/issues/118845 on MPS."""
        if x.numel() == 0:
            return x
        else:
            return torch.relu_(x)


def initialize_pixel_classifier(
    model,
    MLP_width=10,
    MLP_input_dim=None,
    n_sigma=2,
    dim_coords=2,
    feature_engineering_function="0",
):
    """Initialize the pixel classifier for the InstanSeg UNet model."""
    if MLP_input_dim is None:
        _, feature_engineering_width = feature_engineering_generator(
            feature_engineering_function
        )
        MLP_input_dim = feature_engineering_width + n_sigma - 2 + dim_coords
    model.pixel_classifier = ProbabilityNet(MLP_input_dim, width=MLP_width)
    if feature_engineering_function != "10":
        model.pixel_classifier = ProbabilityNet(MLP_input_dim, width=MLP_width)
    else:
        model.pixel_classifier = ConvProbabilityNet(MLP_input_dim, width=MLP_width)
    return model


def create_gaussian_grid(N, sigma, device="cuda", channels=1):
    """Create a Gaussian grid."""
    # Create a grid of coordinates centered at (0, 0)
    x = torch.linspace(-N // 2, N // 2, N, device=device)
    y = torch.linspace(-N // 2, N // 2, N, device=device)
    xx, yy = torch.meshgrid(x, y, indexing="ij")

    # Compute the Gaussian values
    gaussian_values = torch.exp(-(xx**2 + yy**2) / (2 * sigma**2)).repeat(
        channels, 1, 1
    )

    return gaussian_values


def guide_function(params: torch.Tensor, device="cuda", width: int = 256):
    """Guide function for the InstanSeg UNet model."""
    # params must be depth,3
    depth = params.shape[0]
    xx = (
        torch.linspace(0, 1, width, device=device)
        .view(1, 1, -1)
        .expand(1, width, width)
    )
    yy = (
        torch.linspace(0, 1, width, device=device)
        .view(1, -1, 1)
        .expand(1, width, width)
    )
    xxyy = torch.cat((xx, yy), 0).expand(depth, 2, width, width)

    xx = xxyy[:, 0] * params[:, 0][:, None, None]
    yy = xxyy[:, 1] * params[:, 1][:, None, None]

    return torch.sin(xx + yy + params[:, 2, None, None])[None]


class MyBlock(nn.Sequential):
    """My block for the InstanSeg UNet model."""

    def __init__(self, embedding_dim, width):
        """Initialize the My block."""
        super(MyBlock, self).__init__()
        self.fc1 = nn.Conv2d(embedding_dim, width, 1, padding=0 // 2)
        self.bn1 = nn.BatchNorm2d(width)
        self.relu1 = nn.ReLU(inplace=True)
        self.fc2 = nn.Conv2d(width, width, 1)
        self.bn2 = nn.BatchNorm2d(width)
        self.relu2 = nn.ReLU(inplace=True)
        self.fc3 = nn.Conv2d(width, 1, 1)


class ConvProbabilityNet(nn.Module):
    """Convolutional probability network for the InstanSeg UNet model."""

    def __init__(self, embedding_dim=4, width=5, depth=5):
        """Initialize the Convolutional probability network."""
        super().__init__()
        self.layer1 = MyBlock(embedding_dim + depth, width)
        self.layer2 = MyBlock(embedding_dim, width)
        self.layer3 = MyBlock(embedding_dim + 2, width)

        self.positional_embedding_params = (nn.Parameter(torch.rand(depth, 3) * 10)).to(
            "cuda"
        )

    def forward(self, x):
        """Forward pass of the Convolutional probability network."""
        # x is C*H*W,E+S+1 (H,W is window of crop used here, e.g 100x100, not image)

        positional_embedding = guide_function(
            self.positional_embedding_params, width=100
        )

        one = self.layer1(
            torch.cat((x, positional_embedding.expand(x.shape[0], -1, -1, -1)), dim=1)
        )
        two = self.layer2(x)

        output = self.layer3(torch.cat((x, one, two), dim=1))

        return output


class LocalInstanceNorm(nn.Module):
    """Pytorch class for local instance normalization."""

    def __init__(self, in_channels=1):
        """Initialize the local instance normalization."""
        super(LocalInstanceNorm, self).__init__()
        self.kernel_size = int(64 / (in_channels // 32))
        self.norm = nn.InstanceNorm1d(in_channels, affine=True)
        self.sigma = int(
            64 / (in_channels // 32)
        )  # 30#torch.nn.Parameter(torch.tensor(float(sigma),device = "cuda"),
        # requires_grad = True)
        self.gaussian = (
            create_gaussian_grid(
                self.kernel_size, sigma=self.sigma, device="cuda", channels=in_channels
            )
            .flatten()
            .view(1, -1, 1)
            + 1e-5
        )

    def forward(self, x):
        """Forward pass of the local instance normalization."""
        assert x.dim() == 4, print("Only implemented for batch 4d tensor", x.dim())

        b, c, h, w = x.shape
        x = F.unfold(
            x,
            kernel_size=(self.kernel_size, self.kernel_size),
            stride=self.kernel_size // 2,
        )
        x = rearrange(
            x,
            "b (c k1 k2) n -> (b n) c (k1 k2)",
            c=c,
            k1=self.kernel_size,
            k2=self.kernel_size,
        )
        # x = self.norm(x)

        x = x - x.mean(dim=1, keepdim=True)
        x = x / (x.std(dim=1, keepdim=True) + 1e-5)

        x = rearrange(
            x,
            "(b n) c (k1 k2) -> b (c k1 k2) n",
            b=b,
            c=c,
            k1=self.kernel_size,
            k2=self.kernel_size,
        )

        x = x * self.gaussian
        counter = F.fold(
            torch.ones_like(x) * self.gaussian,
            (h, w),
            kernel_size=(self.kernel_size, self.kernel_size),
            stride=self.kernel_size // 2,
        )  # .view(1,1,10,10,-1)
        x = F.fold(
            x,
            (h, w),
            kernel_size=(self.kernel_size, self.kernel_size),
            stride=self.kernel_size // 2,
        )

        result = x / counter

        return result


def conv_norm_act(in_channels, out_channels, sz, norm, act="ReLU"):
    """Convolutional normalization and activation function."""
    if norm == "None" or norm is None:
        norm_layer = nn.Identity()
    elif norm.lower() == "batch":
        norm_layer = nn.BatchNorm2d(out_channels, eps=1e-5, momentum=0.05)
    elif norm.lower() == "instance":
        norm_layer = nn.InstanceNorm2d(
            out_channels, eps=1e-5, track_running_stats=False, affine=True
        )
    elif norm.lower() == "local":
        norm_layer = LocalInstanceNorm(in_channels=out_channels)
    else:
        raise ValueError("Norm must be None, batch or instance")

    if act == "None" or act is None:
        act_layer = nn.Identity()
    elif act.lower() == "relu":
        act_layer = nn.ReLU(inplace=True)
    elif act.lower() == "mish":
        act_layer = nn.Mish(inplace=True)
    else:
        raise ValueError("Act must be None, ReLU or Mish")

    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, sz, padding=sz // 2),
        norm_layer,
        act_layer,
    )


class DecoderBlock(nn.Module):
    """Decoder block for the InstanSeg UNet model."""

    def __init__(
        self,
        in_channels,
        skip_channels,
        out_channels,
        norm="BATCH",
        act="ReLU",
        shallow=False,
    ):
        """Initialize the decoder block."""
        super().__init__()

        self.conv0 = conv_norm_act(in_channels, out_channels, 1, norm, act)
        self.conv_skip = conv_norm_act(skip_channels, out_channels, 1, norm, act)
        self.conv1 = conv_norm_act(in_channels, out_channels, 3, norm, act)
        self.conv2 = conv_norm_act(out_channels, out_channels, 3, norm, act)
        self.conv3 = conv_norm_act(out_channels, out_channels, 3, norm, act)
        self.conv4 = conv_norm_act(out_channels, out_channels, 3, norm, act)

        if shallow:
            self.conv3 = nn.Identity()

    def forward(self, x, skip=None):
        """Forward pass of the decoder block."""
        x = F.interpolate(x, scale_factor=2, mode="nearest")
        proj = self.conv0(x)
        x = self.conv1(x)
        x = proj + self.conv2(x + self.conv_skip(skip))
        x = x + self.conv4(self.conv3(x))
        return x


class EncoderBlock(nn.Module):
    """Pytorch class for the encoder block."""

    def __init__(
        self,
        in_channels,
        out_channels,
        pool=True,
        norm="BATCH",
        act="ReLU",
        shallow=False,
    ):
        """Initialize the encoder block."""
        super().__init__()

        if pool:
            self.maxpool = nn.MaxPool2d(2, 2)
        else:
            self.maxpool = nn.Identity()
        self.conv0 = conv_norm_act(in_channels, out_channels, 1, norm, act)
        self.conv1 = conv_norm_act(in_channels, out_channels, 3, norm, act)
        self.conv2 = conv_norm_act(out_channels, out_channels, 3, norm, act)
        self.conv3 = conv_norm_act(out_channels, out_channels, 3, norm, act)
        self.conv4 = conv_norm_act(out_channels, out_channels, 3, norm, act)

        if shallow:
            self.conv2 = nn.Identity()
            self.conv3 = nn.Identity()

    def forward(self, x):
        """Forward pass of the encoder block."""
        x = self.maxpool(x)
        proj = self.conv0(x)
        x = self.conv1(x)
        x = proj + self.conv2(x)
        x = x + self.conv4(self.conv3(x))
        return x


class Decoder(nn.Module):
    """Decoder for the InstanSeg UNet model."""

    def __init__(self, layers, out_channels, norm, act):
        """Initialize the decoder."""
        super().__init__()

        self.decoder = nn.ModuleList(
            [
                DecoderBlock(
                    layers[i], layers[i + 1], layers[i + 1], norm=norm, act=act
                )
                for i in range(len(layers) - 1)
            ]
        )

        self.final_block = nn.ModuleList(
            [
                conv_norm_act(
                    layers[-1],
                    out_channel,
                    1,
                    norm=norm
                    if (norm is not None) and norm.lower() != "instance"
                    else None,
                    act=None,
                )
                for out_channel in out_channels
            ]
        )

    def forward(self, x, skips):
        """Forward pass of the decoder."""
        for layer, skip in zip(self.decoder, skips[::-1]):
            x = layer(x, skip)

        x = torch.cat([final_block(x) for final_block in self.final_block], dim=1)
        return x


class InstanSeg_UNet(nn.Module):
    """Pytorch class for the InstanSeg UNet model."""

    def __init__(
        self,
        in_channels,
        out_channels,
        layers=[256, 128, 64, 32],
        norm="BATCH",
        dropout=0,
        act="ReLu",
    ):
        """Initialize the InstanSeg UNet model."""
        super().__init__()
        layers = layers[::-1]
        self.encoder = nn.ModuleList(
            [EncoderBlock(in_channels, layers[0], pool=False, norm=norm, act=act)]
            + [
                EncoderBlock(layers[i], layers[i + 1], norm=norm, act=act)
                for i in range(len(layers) - 1)
            ]
        )
        layers = layers[::-1]

        # out_channels should be a list of lists [[2,2,1],[2,2,1]] means two decoders,
        # each with 3 output blocks. The output will be of shape 10.

        if isinstance(out_channels, int):
            out_channels = [[out_channels]]
        if isinstance(out_channels[0], int):
            out_channels = [out_channels]

        self.decoders = nn.ModuleList(
            [Decoder(layers, out_channel, norm, act) for out_channel in out_channels]
        )

    def forward(self, x):
        """Forward pass of the InstanSeg UNet model."""
        skips = []
        for n, layer in enumerate(self.encoder):
            x = layer(x)
            if n < len(self.encoder) - 1:
                skips.append(x)

        return torch.cat([decoder(x, skips) for decoder in self.decoders], dim=1)


if __name__ == "__main__":
    net = InstanSeg_UNet(
        in_channels=3,
        out_channels=[5, 3],
    )

    print(net(torch.randn(1, 3, 256, 256)).shape)
