"""Lovasz-Softmax and Jaccard hinge loss in PyTorch."""

from itertools import filterfalse
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

from roche.crisp.networks.instanseg_unet import (
    feature_engineering_generator,
    feature_engineering_slow,
)
from roche.crisp.utils.instanseg_utils import (
    compute_crops,
    connected_components,
    convert,
    eccentricity_batch,
    fast_sparse_iou,
    find_connected_components,
    generate_coordinate_map,
    instanseg_padding,
    recover_padding,
    remap_values,
    resolve_cell_and_nucleus_boundaries,
    torch_fastremap,
    torch_onehot,
    torch_peak_local_max,
)

binary_xloss = torch.nn.BCEWithLogitsLoss()
l1_loss = torch.nn.L1Loss()


def lovasz_grad(gt_sorted):
    """Compute gradient of the Lovasz extension w.r.t sorted errors.

    See Alg. 1 in paper
    """
    p = len(gt_sorted)
    gts = gt_sorted.sum()
    intersection = gts.float() - gt_sorted.float().cumsum(0)
    union = gts.float() + (1 - gt_sorted.float()).float().cumsum(
        0
    )  # T.G. original was union = gts.float() + (1 - gt_sorted).float().cumsum(0)
    jaccard = 1.0 - intersection / union
    if p > 1:  # cover 1-pixel case
        jaccard[1:p] = jaccard[1:p] - jaccard[0:-1]
    return jaccard


def iou_binary(preds, labels, EMPTY=1.0, ignore=None, per_image=True):
    """Compute IoU for foreground class.

    binary: 1 foreground, 0 background
    """
    if not per_image:
        preds, labels = (preds,), (labels,)
    ious = []
    for pred, label in zip(preds, labels):
        intersection = ((label == 1) & (pred == 1)).sum()
        union = ((label == 1) | ((pred == 1) & (label != ignore))).sum()
        if not union:
            iou = EMPTY
        else:
            iou = float(intersection) / union
        ious.append(iou)
    iou = mean(ious)  # mean accross images if per_image
    return 100 * iou


def iou(preds, labels, C, EMPTY=1.0, ignore=None, per_image=False):
    """Array of IoU for each (non ignored) class."""
    if not per_image:
        preds, labels = (preds,), (labels,)
    ious = []
    for pred, label in zip(preds, labels):
        iou = []
        for i in range(C):
            # The ignored label is sometimes among predicted classes (ENet - CityScapes)
            if i != ignore:
                intersection = ((label == i) & (pred == i)).sum()
                union = ((label == i) | ((pred == i) & (label != ignore))).sum()
                if not union:
                    iou.append(EMPTY)
                else:
                    iou.append(float(intersection) / union)
        ious.append(iou)
    ious = map(mean, zip(*ious))  # mean accross images if per_image
    return 100 * np.array(ious)


# --------------------------- BINARY LOSSES ---------------------------


def lovasz_hinge(logits, labels, per_image=True, ignore=None):
    """Compute Binary Lovasz hinge loss.

    logits: [B, H, W] Variable, logits at each pixel (between -infty and +infty)
    labels: [B, H, W] Tensor, binary ground truth masks (0 or 1)
    per_image: compute the loss per image instead of per batch
    ignore: void class id
    """
    if per_image:
        loss = mean(
            lovasz_hinge_flat(
                *flatten_binary_scores(log.unsqueeze(0), lab.unsqueeze(0), ignore)
            )
            for log, lab in zip(logits, labels)
        )
    else:
        loss = lovasz_hinge_flat(*flatten_binary_scores(logits, labels, ignore))
    return loss


def lovasz_hinge_flat(logits, labels):
    """Compute Binary Lovasz hinge loss.

    logits: [P] Variable, logits at each prediction (between -infty and +infty)
    labels: [P] Tensor, binary ground truth labels (0 or 1)
    ignore: label to ignore
    """
    if len(labels) == 0:
        # only void pixels, the gradients should be 0
        return logits.sum() * 0.0
    signs = 2.0 * labels.float() - 1.0
    errors = 1.0 - logits * Variable(signs)
    errors_sorted, perm = torch.sort(errors, dim=0, descending=True)
    perm = perm.data
    gt_sorted = labels[perm]
    grad = lovasz_grad(gt_sorted)
    loss = torch.dot(F.relu(errors_sorted), Variable(grad))
    return loss


def flatten_binary_scores(scores, labels, ignore=None):
    """Flatten predictions in the batch (binary case).

    Remove labels equal to 'ignore'
    """
    scores = scores.view(-1)
    labels = labels.view(-1)
    if ignore is None:
        return scores, labels
    valid = labels != ignore
    vscores = scores[valid]
    vlabels = labels[valid]
    return vscores, vlabels


class StableBCELoss(torch.nn.modules.Module):
    """Stable Binary Cross entropy loss."""

    def __init__(self):
        """Initialize the StableBCELoss class."""
        super(StableBCELoss, self).__init__()

    def forward(self, input, target):
        """Forward pass.

        Args:
            input: [B, H, W] Variable, logits at each pixel (between -infty and +infty)
            target: [B, H, W] Tensor, binary ground truth masks (0 or 1)
        """
        neg_abs = -input.abs()
        loss = input.clamp(min=0) - input * target + (1 + neg_abs.exp()).log()
        return loss.mean()


def stable_binary_xloss(logits, labels, ignore=None):
    """Compute binary Cross entropy loss.

    logits: [B, H, W] Variable, logits at each pixel (between -infty and +infty)
    labels: [B, H, W] Tensor, binary ground truth masks (0 or 1)
    ignore: void class id
    """
    logits, labels = flatten_binary_scores(logits, labels, ignore)
    loss = StableBCELoss()(logits, Variable(labels.float()))
    return loss


# --------------------------- MULTICLASS LOSSES ---------------------------


def lovasz_softmax(probas, labels, only_present=False, per_image=False, ignore=None):
    """Compute Multi-class Lovasz-Softmax loss.

    Parameters
    ----------
    probas : torch.Tensor
        [B, C, H, W] Variable, class probabilities at each prediction (between 0 and 1)
    labels : torch.Tensor
        [B, H, W] Tensor, ground truth labels (between 0 and C - 1)
    only_present : bool
        average only on classes present in ground truth
    per_image : bool
        compute the loss per image instead of per batch
    ignore : int
        void class labels
    """
    if per_image:
        loss = mean(
            lovasz_softmax_flat(
                *flatten_probas(prob.unsqueeze(0), lab.unsqueeze(0), ignore),
                only_present=only_present,
            )
            for prob, lab in zip(probas, labels)
        )
    else:
        loss = lovasz_softmax_flat(
            *flatten_probas(probas, labels, ignore), only_present=only_present
        )
    return loss


def lovasz_softmax_flat(probas, labels, only_present=False):
    """Compute Multi-class Lovasz-Softmax loss.

    probas: [P, C] Variable, class probabilities at each prediction (between 0 and 1)
    labels: [P] Tensor, ground truth labels (between 0 and C - 1)
    only_present: average only on classes present in ground truth
    """
    C = probas.size(1)
    losses = []
    for c in range(C):
        fg = (labels == c).float()  # foreground for class c
        if only_present and fg.sum() == 0:
            continue
        errors = (Variable(fg) - probas[:, c]).abs()
        errors_sorted, perm = torch.sort(errors, 0, descending=True)
        perm = perm.data
        fg_sorted = fg[perm]
        losses.append(torch.dot(errors_sorted, Variable(lovasz_grad(fg_sorted))))
    return mean(losses)


def flatten_probas(probas, labels, ignore=None):
    """Flatten predictions in the batch."""
    B, C, H, W = probas.size()
    probas = probas.permute(0, 2, 3, 1).contiguous().view(-1, C)  # B * H * W, C = P, C
    labels = labels.view(-1)
    if ignore is None:
        return probas, labels
    valid = labels != ignore
    vprobas = probas[valid.nonzero().squeeze()]
    vlabels = labels[valid]
    return vprobas, vlabels


def xloss(logits, labels, ignore=None):
    """Compute Cross entropy loss."""
    return F.cross_entropy(logits, Variable(labels), ignore_index=255)


# --------------------------- HELPER FUNCTIONS ---------------------------


def mean(inp, ignore_nan=False, empty=0):
    """Compute mean of a generator."""
    inp = iter(inp)
    if ignore_nan:
        inp = filterfalse(np.isnan, inp)
    try:
        n = 1
        acc = next(inp)
    except StopIteration:
        if empty == "raise":
            raise ValueError("Empty mean")
        return empty
    for n, v in enumerate(inp, 2):
        acc += v
    if n == 1:
        return acc

    return acc / n


def find_all_local_maxima(
    image: torch.Tensor, neighbourhood_size: int, minimum_value: float
) -> torch.Tensor:
    """Compute peak_local_max that finds all the local maxima within each neighbourhood.

    May return multiple per neighbourhood.
    """
    # Perform max pooling with the specified neighborhood size
    kernel_size = 2 * neighbourhood_size + 1
    pooled = F.max_pool2d(
        image, kernel_size=kernel_size, stride=1, padding=kernel_size // 2
    )

    # Create a mask for the local maxima
    mask = (pooled == image) * (image >= minimum_value)

    # Apply the mask to the original image to retain only the local maxima values
    local_maxima = image * mask

    return local_maxima


class MedianFilter(nn.Module):
    """Class for Median filtering."""

    def __init__(self, kernel_size: Tuple[int, int]):
        """Initialize the MedianFilter class."""
        from kornia.filters import MedianBlur

        super(MedianFilter, self).__init__()
        self.kernel_size = kernel_size
        self.MedianBlur = MedianBlur(kernel_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.MedianBlur(x)


class InstanSegLoss(nn.Module):
    """InstanSeg Loss class."""

    def __init__(
        self,
        n_sigma: int = 2,
        instance_weight: float = 1.5,
        device: str = "cuda",
        binary_loss_fn_str: str = "lovasz_hinge",
        seed_loss_fn="l1_distance",
        cells_and_nuclei: bool = False,
        to_centre: bool = False,
        multi_centre: bool = True,
        window_size=128,
        feature_engineering_function="0",
        dim_coords=2,
    ):
        """Initialize the InstanSeg Loss class."""
        super().__init__()
        self.n_sigma = n_sigma
        self.instance_weight = instance_weight
        self.device = device
        self.dim_coords = dim_coords

        self.dim_out = self.dim_coords + self.n_sigma + 1
        self.parameters_have_been_updated = False

        if cells_and_nuclei:
            self.dim_out = self.dim_out * 2
        self.cells_and_nuclei = cells_and_nuclei

        self.to_centre = to_centre
        self.multi_centre = multi_centre
        self.window_size = window_size

        self.num_instance_cap = 50
        self.sort_by_eccentricity = False

        xxyy = generate_coordinate_map(
            mode="linear",
            spatial_dim=self.dim_coords,
            height=256,
            width=256,
            device=device,
        )

        self.feature_engineering, self.feature_engineering_width = (
            feature_engineering_generator(feature_engineering_function)
        )
        self.feature_engineering_function = feature_engineering_function

        self.register_buffer("xxyy", xxyy)

        self.update_binary_loss(binary_loss_fn_str)

        self.update_seed_loss(seed_loss_fn)

    def update_binary_loss(self, binary_loss_fn_str):
        """Update the binary loss function."""
        if binary_loss_fn_str == "lovasz_hinge":

            def binary_loss_fn(pred, gt, **kwargs):
                """Binary loss function."""
                # pred = torch.sigmoid_(pred)
                return lovasz_hinge((pred.squeeze(1)), gt, per_image=True)

        elif binary_loss_fn_str == "binary_xloss":
            self.binary_loss_fn = torch.nn.BCEWithLogitsLoss()
        elif binary_loss_fn_str == "dicefocal_loss":
            from monai.losses import DiceFocalLoss

            binary_loss_fn_ = DiceFocalLoss(sigmoid=True)

            def binary_dice_focal_loss_fn(pred, gt, **kwargs):
                """Binary dice focal loss function."""
                loss = binary_loss_fn_(pred[None, :, 0], gt.unsqueeze(0)) * 1.5
                return loss

            self.binary_loss_fn = binary_dice_focal_loss_fn

        elif binary_loss_fn_str == "dice_loss":
            from monai.losses import DiceLoss

            binary_loss_fn_ = DiceLoss(sigmoid=True)

            def binary_dice_loss_fn(pred, gt, **kwargs):
                """Binary dice loss function."""
                loss = binary_loss_fn_(pred[None, :, 0], gt.unsqueeze(0)) * 1.5
                return loss

            self.binary_loss_fn = binary_dice_loss_fn

        elif binary_loss_fn_str == "general_dice_loss":
            from monai.losses import GeneralizedDiceLoss

            def binary_generalized_dice_loss_fn(pred, gt):
                """Binary generalized dice loss function."""
                return GeneralizedDiceLoss(sigmoid=True)(pred, gt.unsqueeze(1))

            self.binary_loss_fn = binary_generalized_dice_loss_fn

        elif binary_loss_fn_str == "cross_entropy":
            from torch.nn import NLLLoss

            assert self.window_size == 256, (
                "Cross entropy loss only works with window size 256"
            )
            assert self.num_instance_cap is None, (
                "Cross entropy loss only works with num_instance_cap = None"
            )

            self.l_fn = NLLLoss()
            self.m = nn.LogSoftmax(dim=1)

            def binary_cross_entropy_loss_fn(pred, gt, sigma):
                """Binary cross entropy loss function."""
                pred = torch.cat([sigma[None, None], pred])

                gt = torch.cat(((gt.sum(0) == 0)[None], gt))
                target = gt.argmax(0)[None]

                pred = pred.squeeze(1).unsqueeze(0)

                pred = self.m(pred)

                return self.l_fn(pred, target.long()) * 7

            self.binary_loss_fn = binary_cross_entropy_loss_fn

        else:
            raise NotImplementedError(
                "Binary loss function", binary_loss_fn, "is not implemented"
            )

    def update_seed_loss(self, seed_loss_fn):
        """Update the seed loss function."""
        if seed_loss_fn in ["binary_xloss"]:
            binary_loss = torch.nn.BCEWithLogitsLoss(reduction="none")

            def seed_loss(x, y, mask=None):
                """Seed loss function."""
                if mask is not None:
                    mask = mask.float()  # Ensure the mask is float for multiplication
                    loss = binary_loss(
                        x, (y > 0).float()
                    )  # Calculate the element-wise binary loss
                    masked_loss = loss * mask  # Apply the mask to the loss
                    return masked_loss.sum() / mask.sum()
                else:
                    return binary_loss(x, (y > 0).float()).mean()

            self.seed_loss = seed_loss

        elif seed_loss_fn in ["l1_distance"]:
            from roche.crisp.utils.instanseg_utils import instance_wise_edt

            distance_loss = torch.nn.L1Loss(reduction="none")

            def seed_loss(x, y, mask=None):
                """Seed loss function."""
                edt = (
                    instance_wise_edt(y.float(), edt_type="edt") - 0.5
                ) * 15  # This is to mimick the range of CELoss
                loss = distance_loss((x), (edt[None]))

                if mask is not None:
                    mask = mask.float()
                    masked_loss = loss * mask
                    return masked_loss.sum() / mask.sum()
                else:
                    return loss.mean()

            self.seed_loss = seed_loss
        else:
            raise NotImplementedError(
                "Seedloss function", seed_loss_fn, "is not implemented"
            )

    def forward(
        self,
        prediction: torch.Tensor,
        instances: torch.Tensor,
        pixel_classifier: torch.nn.Module,
        w_inst: float = 1.5,
        w_seed: float = 1.0,
    ):
        """Forward pass."""
        w_inst = self.instance_weight

        batch_size, height, width = (
            prediction.size(0),
            prediction.size(2),
            prediction.size(3),
        )

        xxyy = self.xxyy[:, 0:height, 0:width].contiguous()  # 2 x h x w

        loss = 0.0

        if self.cells_and_nuclei:
            dim_out = int(self.dim_out / 2)
        else:
            dim_out = self.dim_out

        for mask_channel in range(0, instances.shape[1]):
            if mask_channel == 0:
                prediction_b = prediction[:, 0:dim_out, :, :]
            else:
                prediction_b = prediction[:, dim_out:, :, :]

            instances_batch = instances

            if not self.to_centre:
                spatial_emb_batch = (
                    torch.sigmoid((prediction_b[:, 0 : self.dim_coords])) - 0.5
                ) * 8 + xxyy
            else:
                spatial_emb_batch = (prediction_b[:, 0 : self.dim_coords]) + xxyy
            sigma_batch = prediction_b[
                :, self.dim_coords : self.dim_coords + self.n_sigma
            ]  # n_sigma x h x w
            seed_map_batch = prediction_b[
                :, self.dim_coords + self.n_sigma : self.dim_coords + self.n_sigma + 1
            ]  # 1 x h x w

            for b in range(0, batch_size):
                spatial_emb = spatial_emb_batch[b]
                sigma = sigma_batch[b]
                seed_map = seed_map_batch[b]

                instance_loss = 0
                seed_loss = 0

                instance = instances_batch[b, mask_channel].unsqueeze(0)  # 1 x h x w

                if instance.min() < 0:  # label is sparse
                    mask = instance >= 0
                    instance[instance < 0] = 0
                else:
                    mask = None

                seed_loss_tmp = self.seed_loss(seed_map, instance, mask=mask)

                seed_loss += seed_loss_tmp

                if w_inst == 0:
                    loss += w_seed * seed_loss
                    continue

                instance_ids = instance.unique()
                instance_ids = instance_ids[instance_ids != 0]

                if len(instance_ids) > 0:
                    instance = torch_fastremap(instance)

                    onehot_labels = torch_onehot(instance).squeeze(0)  # C x h x w

                    if (
                        self.num_instance_cap is not None
                    ):  # This is to cap the number of objects to avoid OOM errors.
                        if self.num_instance_cap < onehot_labels.shape[0]:
                            if self.sort_by_eccentricity:
                                eccentricities = eccentricity_batch(
                                    onehot_labels.float()
                                )
                                idx = eccentricities.argsort(descending=True)[
                                    : self.num_instance_cap
                                ]
                            else:
                                idx = torch.randperm(onehot_labels.shape[0])[
                                    : self.num_instance_cap
                                ]
                            onehot_labels = onehot_labels[idx]

                    if self.multi_centre:
                        seed_map_tmp = torch.sigmoid(seed_map)

                        centroids = torch_peak_local_max(
                            seed_map_tmp.squeeze() * onehot_labels.sum(0),
                            neighbourhood_size=3,
                            minimum_value=0.5,
                        ).T

                        if self.to_centre:
                            centres = xxyy[:, centroids[0], centroids[1]].detach().T
                        else:
                            centres = (
                                spatial_emb[:, centroids[0], centroids[1]].detach().T
                            )

                        idx = torch.randperm(centroids.shape[1])[
                            : self.num_instance_cap
                        ]

                        centres = centres[idx]
                        centroids = centroids[:, idx]

                        instance_labels = (
                            onehot_labels[:, centroids[0], centroids[1]]
                            .float()
                            .argmax(0)
                        )
                        onehot_labels = onehot_labels[instance_labels]

                        centroids = centroids.T

                    else:
                        if self.to_centre:
                            seed_map_min = seed_map.min()

                            seed_map_tmp = (seed_map - seed_map.min()).detach()
                            centres = xxyy.flatten(1).T[
                                ((seed_map_tmp * onehot_labels).flatten(1)).argmax(1)
                            ]  # location at max seed (used in postprocessing)
                            seed_map = seed_map_tmp + seed_map_min
                        else:
                            seed_map_tmp = seed_map - seed_map.min()
                            centres = (
                                spatial_emb.flatten(1)
                                .T[
                                    ((seed_map_tmp * onehot_labels).flatten(1)).argmax(
                                        1
                                    )
                                ]
                                .detach()
                            )  # embedding at max seed (used in postprocessing)

                        centroids = (
                            torch.sum(
                                (xxyy[:2] * onehot_labels.unsqueeze(1)).flatten(2),
                                dim=2,
                            )
                            / onehot_labels.flatten(1).sum(1)[:, None]
                        ) * (256 / 64)  # coordinates of centre of mass
                        centroids = torch.stack((centroids[:, 1], centroids[:, 0])).T

                    if len(centroids) == 0:
                        loss += w_seed * seed_loss
                        continue

                    dist, coords = compute_crops(
                        spatial_emb,
                        centres,
                        sigma,
                        centroids,
                        feature_engineering=self.feature_engineering,
                        pixel_classifier=pixel_classifier,
                        window_size=self.window_size,
                    )

                    crop = onehot_labels.squeeze(1)[
                        coords[0], coords[1], coords[2]
                    ].reshape(-1, self.window_size, self.window_size)

                    instance_loss = instance_loss + self.binary_loss_fn(
                        dist, crop.float(), sigma=sigma[0]
                    )

                loss += w_inst * instance_loss + w_seed * seed_loss

        loss = loss / (b + 1)

        if self.cells_and_nuclei:
            loss = loss / 2

        return loss


class InstanSeg_Torchscript(nn.Module):
    """Class to convert InstanSeg model to torchscript format."""

    def __init__(
        self,
        model,
        cells_and_nuclei: bool = False,
        pixel_size: float = 0,
        n_sigma: int = 2,
        dim_coords: int = 2,
        to_centre: bool = True,
        backbone_dim_in: int = 3,
        feature_engineering_function: str = "0",
        params=None,
        mixed_precision: bool = False,
    ):
        """Initialize the InstanSeg_Torchscript model."""
        super(InstanSeg_Torchscript, self).__init__()

        model.eval()

        with torch.amp.autocast("cuda", enabled=mixed_precision):
            with torch.no_grad():
                self.fcn = torch.jit.trace(
                    model, torch.rand(1, backbone_dim_in, 256, 256)
                )

        try:
            self.pixel_classifier = model.pixel_classifier
        except Exception:
            self.pixel_classifier = (
                model.model.pixel_classifier
            )  # I think this is a pytorch version issue between 1.13.1 and 2.0.0
        self.cells_and_nuclei = cells_and_nuclei
        self.pixel_size = pixel_size
        self.dim_coords = dim_coords
        self.n_sigma = n_sigma
        self.to_centre = to_centre
        self.feature_engineering, self.feature_engineering_width = (
            feature_engineering_generator(feature_engineering_function)
        )
        self.params = (params,)

        self.index_dtype = torch.long  # torch.int

    def forward(
        self,
        x: torch.Tensor,
        target_segmentation: torch.Tensor = torch.tensor([1, 1]),  # Nuclei / Cells
        min_size: int = 10,
        mask_threshold: float = 0.53,
        peak_distance: int = 5,
        seed_threshold: float = 0.7,
        overlap_threshold: float = 0.3,
        mean_threshold: float = 0.0,
        window_size: int = 32,
        cleanup_fragments: bool = False,
        resolve_cell_and_nucleus: bool = True,
    ) -> torch.Tensor:
        """Forward pass."""
        torch.clamp_max_(x, 3)  # Safety check, please normalize inputs properly!
        torch.clamp_min_(x, -2)

        x, pad = instanseg_padding(x, extra_pad=0)

        # with torch.autocast(device_type='cuda', dtype=torch.float16):
        with torch.no_grad():
            x_full = self.fcn(x)

            dim_out = x_full.shape[1]

            if self.cells_and_nuclei:
                iterations = torch.tensor([0, 1])[
                    target_segmentation.squeeze().to("cpu") > 0
                ]
                dim_out = int(dim_out / 2)

            else:
                iterations = torch.tensor([0])
                dim_out = dim_out

            output_labels_list = []

            for image_index in range(x_full.shape[0]):
                labels_list = []

                for i in iterations:
                    if i == 0:
                        x = x_full[image_index, 0:dim_out, :, :]
                    else:
                        x = x_full[image_index, dim_out:, :, :]

                    x = recover_padding(x, pad)

                    height, width = x.size(1), x.size(2)

                    xxyy = generate_coordinate_map(
                        mode="linear",
                        spatial_dim=self.dim_coords,
                        height=height,
                        width=width,
                        device=x.device,
                    )

                    if not self.to_centre:
                        fields = (torch.sigmoid(x[0 : self.dim_coords]) - 0.5) * 8
                    else:
                        fields = x[0 : self.dim_coords]

                    sigma = x[self.dim_coords : self.dim_coords + self.n_sigma]
                    mask_map = torch.sigmoid(x[self.dim_coords + self.n_sigma])

                    centroids_idx = torch_peak_local_max(
                        mask_map,
                        neighbourhood_size=peak_distance,
                        minimum_value=seed_threshold,
                        dtype=self.index_dtype,
                    )  # .to(prediction.device)
                    # num_initial_centroids = centroids_idx.shape[0]

                    fields = fields + xxyy

                    if self.to_centre:
                        fields_at_centroids = xxyy[
                            :, centroids_idx[:, 0], centroids_idx[:, 1]
                        ]
                    else:
                        fields_at_centroids = fields[
                            :, centroids_idx[:, 0], centroids_idx[:, 1]
                        ]

                    x = fields
                    c = fields_at_centroids.T
                    h, w = x.shape[-2:]
                    C = c.shape[0]

                    if C == 0:
                        label = torch.zeros(
                            mask_map.shape, dtype=torch.float32, device=mask_map.device
                        ).squeeze()
                        labels_list.append(label)
                        continue

                    window_size = window_size
                    centroids = centroids_idx.clone().cpu()  # C,2
                    centroids[:, 0].clamp_(min=window_size, max=h - window_size)
                    centroids[:, 1].clamp_(min=window_size, max=w - window_size)
                    window_slices = (
                        centroids[:, None].to(x.device)
                        + torch.tensor(
                            [[-1, -1], [1, 1]], device=x.device, dtype=centroids.dtype
                        )
                        * window_size
                    )
                    window_slices = window_slices  # C,2,2

                    slice_size = window_size * 2

                    # Create grids of indices for slice windows
                    grid_x, grid_y = torch.meshgrid(
                        torch.arange(
                            slice_size, device=x.device, dtype=self.index_dtype
                        ),
                        torch.arange(
                            slice_size, device=x.device, dtype=self.index_dtype
                        ),
                        indexing="ij",
                    )
                    mesh = torch.stack((grid_x, grid_y))

                    mesh_grid = mesh.expand(
                        C, 2, slice_size, slice_size
                    )  # C,2,2*window_size,2*window_size
                    mesh_grid_flat = torch.flatten(mesh_grid, 2).permute(
                        1, 0, -1
                    )  # 2,C,2*window_size*2*window_size
                    idx = window_slices[:, 0].permute(1, 0)[:, :, None]
                    mesh_grid_flat = mesh_grid_flat + idx
                    mesh_grid_flat = torch.flatten(
                        mesh_grid_flat, 1
                    )  # 2,C*2*window_size*2*window_size

                    #    x = self.traced_feature_engineering(x, c, sigma,
                    # torch.tensor(window_size).int(), mesh_grid_flat)
                    x = feature_engineering_slow(
                        x, c, sigma, torch.tensor(window_size).int(), mesh_grid_flat
                    )

                    x = torch.sigmoid(self.pixel_classifier(x))

                    x = x.reshape(C, 1, slice_size, slice_size)

                    C = x.shape[0]

                    if C == 0:
                        label = torch.zeros(
                            mask_map.shape, dtype=torch.float32, device=mask_map.device
                        ).squeeze()
                        labels_list.append(label)
                        continue

                    original_device = x.device

                    if x.is_mps:
                        device = "cpu"
                        mesh_grid_flat = mesh_grid_flat.to(device)
                        x = x.to(device)
                        mask_map = mask_map.to(device)

                    coords = mesh_grid_flat.reshape(2, C, slice_size, slice_size)

                    if cleanup_fragments:
                        top_left = window_slices[:, 0, :]
                        shifted_centroid = centroids_idx - top_left
                        cc = connected_components(
                            (x > mask_threshold).float(), num_iterations=64
                        )
                        labels_to_keep = cc[
                            torch.arange(cc.shape[0]),
                            0,
                            shifted_centroid[:, 0],
                            shifted_centroid[:, 1],
                        ]
                        in_mask = cc == labels_to_keep[:, None, None, None]
                        x *= in_mask

                    labels = convert(
                        x, coords, size=(h, w), mask_threshold=mask_threshold
                    )[None]

                    idx = torch.arange(
                        1, C + 1, device=x.device, dtype=self.index_dtype
                    )
                    stack_ID = torch.ones(
                        (C, slice_size, slice_size),
                        device=x.device,
                        dtype=self.index_dtype,
                    )
                    stack_ID = stack_ID * (idx[:, None, None] - 1)

                    iidd = torch.stack(
                        (stack_ID.flatten(), mesh_grid_flat[0] * w + mesh_grid_flat[1])
                    )

                    fg = x.flatten() > mask_threshold
                    x = x.flatten()[fg]
                    sparse_onehot = torch.sparse_coo_tensor(
                        iidd[:, fg],
                        (x.flatten() > mask_threshold).float(),
                        size=(C, h * w),
                        dtype=x.dtype,
                        device=x.device,
                    )

                    object_areas = torch.sparse.sum(
                        sparse_onehot.to(torch.bool).float(), dim=(1,)
                    ).values()
                    sum_mask_value = torch.sparse.sum(
                        (sparse_onehot * mask_map.flatten()[None]), dim=(1,)
                    ).values()
                    mean_mask_value = sum_mask_value / object_areas
                    objects_to_remove = ~torch.logical_and(
                        mean_mask_value > mean_threshold, object_areas > min_size
                    )

                    iou = fast_sparse_iou(sparse_onehot)

                    remapping = find_connected_components(
                        (iou > overlap_threshold).to(self.index_dtype)
                    )

                    labels = remap_values(remapping, labels)

                    labels_to_remove = (
                        torch.arange(
                            0, len(objects_to_remove), device=objects_to_remove.device
                        )
                        + 1
                    )[objects_to_remove]
                    labels[torch.isin(labels, labels_to_remove)] = 0

                    labels_list.append(labels.squeeze().to(original_device))

                if len(labels_list) == 1:
                    lab = labels_list[0][None, None]  # 1,1,H,W
                else:
                    lab = torch.stack(labels_list)[None]

                if lab.shape[1] == 2 and resolve_cell_and_nucleus:  # nuclei and cells
                    lab = resolve_cell_and_nucleus_boundaries(lab)

                output_labels_list.append(lab[0])

            lab = torch.stack(output_labels_list)  # B,C,H,W

            return lab.to(torch.float32)  # B,C,H,W


if __name__ == "__main__":
    import torch
    from instanseg.utils.utils import export_to_torchscript

    model_name = "1804630"

    export_to_torchscript(
        model_name,
        show_example=True,
        mixed_predicision=False,
        model_path="../../models/",
    )
