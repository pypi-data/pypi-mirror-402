"""Utility functions for post processing of instance masks using PyTorch."""

import torch
import torch.nn.functional as F


def remove_small_masks_(instance_masks, min_pixels=32):
    """Remove small masks from a batch of instance masks in-place.

    Parameters
    ----------
    instance_masks : torch.Tensor
        A tensor of shape (B, H, W) containing instance segmentation masks,
        where B is the batch size, H is the height, and W is the width.
        The masks should be integer-encoded, where each unique positive
        integer represents a different object instance.
    min_pixels : int, optional
        The minimum number of pixels an object must have to be retained.
        Objects with fewer pixels than this threshold will be removed (set to 0).
        Default is 32.

    Returns
    -------
    None
        This function modifies the `instance_masks` tensor in-place.
    """
    device = instance_masks.device
    bs = instance_masks.shape[0]
    top_instance_label = instance_masks.max()
    cell_vals = torch.arange(1, top_instance_label + 1, device=instance_masks.device)
    bin_masks = (
        instance_masks[:, None, :] == cell_vals[None, :, None, None]
    )  # (bs, ninstances, h, w)
    npixels_per_instance = bin_masks.sum(dim=(2, 3))
    invalid_mask_mask = npixels_per_instance < min_pixels  # shape: (bs, top_label)

    # Because bin mask indexing starts at 0 and mask labels at one we need to
    # shift this one to the right.
    false_col = torch.zeros((bs, 1), dtype=torch.bool, device=device)
    invalid_mask_mask = torch.cat([false_col, invalid_mask_mask], dim=1)

    # Broadcast the invalid_mask_mask to the shape of instance_masks.
    # The shape of the index tensors defines the output shape!
    # Equally to the following iteration:
    # for i in range(bs):
    #   for j in range(h):
    #     for k in range(w):
    #       mask[i, j, k] = lookup[i, values[i, j, k]]
    batch_indices = torch.arange(bs, device=device)[:, None, None]
    replacement_mask = invalid_mask_mask[batch_indices, instance_masks]

    instance_masks[replacement_mask] = 0


def bin_dilation(bin_masks):
    """Perform binary dilation on a batch of binary masks.

    This function applies a 3x3 cross-shaped kernel to dilate the binary masks.

    Parameters
    ----------
    bin_masks : torch.Tensor
        A tensor of shape (B, H, W) containing binary masks, where B is the
        batch size, H is the height, and W is the width.

    Returns
    -------
    torch.Tensor
        A tensor of the same shape and dtype as `bin_masks` containing the
        dilated masks.
    """
    device = bin_masks.device
    kernel = torch.tensor(
        [[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=torch.float32, device=device
    )
    input_type = bin_masks.dtype
    float_masks = bin_masks[:, None, :].float()
    dilated = F.conv2d(float_masks, kernel[None, None, :], padding=1)
    return dilated.type(input_type).squeeze()


def bin_erosion(bin_masks):
    """Perform binary erosion on a batch of binary masks.

    This function applies a 3x3 cross-shaped kernel to erode the binary masks.

    Parameters
    ----------
    bin_masks : torch.Tensor
        A tensor of shape (B, H, W) containing binary masks, where B is the
        batch size, H is the height, and W is the width.

    Returns
    -------
    torch.Tensor
        A tensor of the same shape and dtype as `bin_masks` containing the
        eroded masks.
    """
    device = bin_masks.device
    kernel = torch.tensor(
        [[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=torch.float32, device=device
    )

    input_type = bin_masks.dtype
    float_masks = bin_masks[:, None, :].float()
    neg_masks = -float_masks
    padded_input = F.pad(neg_masks, (1, 1, 1, 1), mode="constant", value=float("-inf"))
    result = -F.conv2d(padded_input, kernel[None, None, :]) / 5  # sum of the kernel
    return (result.squeeze() >= 1).type(input_type)


def bin_closing(bin_masks):
    """Perform binary closing on a batch of binary masks.

    Closing is a dilation followed by an erosion, using a 3x3 cross-shaped kernel.
    It is useful for filling small holes in objects.

    Parameters
    ----------
    bin_masks : torch.Tensor
        A tensor of shape (B, H, W) containing binary masks, where B is the
        batch size, H is the height, and W is the width.

    Returns
    -------
    torch.Tensor
        A tensor of the same shape and dtype as `bin_masks` containing the
        closed masks.
    """
    device = bin_masks.device
    kernel = torch.tensor(
        [[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=torch.float32, device=device
    )
    input_type = bin_masks.dtype

    # opening
    float_masks = bin_masks[:, None, :].float()
    dilated = (F.conv2d(float_masks, kernel[None, None, :], padding=1) > 0).float()

    # closing
    dilated *= -1
    dilated = F.pad(dilated, (1, 1, 1, 1), mode="constant", value=-1)
    result = -F.conv2d(dilated, kernel[None, None, :]) / 5  # sum of the kernel

    return (result.squeeze() >= 1).type(input_type)


def binarize_remove_small_objects_and_fill_holes(instance_masks, min_pixels=32):
    """Binarize instance masks, remove small objects, and fill holes.

    This function converts instance masks to binary masks, removes objects smaller
    than a specified pixel threshold, and fills holes using binary dilation.

    Parameters
    ----------
    instance_masks : torch.Tensor
        A tensor of shape (B, H, W) containing instance segmentation masks.
    min_pixels : int, optional
        The minimum number of pixels for an object to be retained, by default 32.

    Returns
    -------
    valid_bin_masks : torch.Tensor
        A tensor of shape (N, H, W) containing the processed binary masks, where N
        is the total number of valid masks across the batch.
    num_masks_per_tile : torch.Tensor
        A 1D tensor of shape (B,) containing the number of valid masks for each
        image in the batch.
    """
    device = instance_masks.device
    top_instance_label = instance_masks.max()
    cell_vals = torch.arange(1, top_instance_label + 1, device=device)
    bin_masks = (
        instance_masks[:, None, :] == cell_vals[None, :, None, None]
    )  # (bs, top_label, h, w)
    npixels_per_instance = bin_masks.sum(dim=(2, 3))

    # Do this before dilation to be consistant with what cellpose does.
    valid_masks_mask = npixels_per_instance >= min_pixels  # shape: (bs, top_label)

    old_shape = bin_masks.shape
    sz = old_shape[-1]
    bin_masks = bin_dilation(bin_masks.view(-1, sz, sz))
    bin_masks = bin_masks.view(old_shape)
    valid_bin_masks = bin_masks[valid_masks_mask]

    return valid_bin_masks, valid_masks_mask.sum(1)


def remove_small_objects_and_fill_holes(instance_masks, min_pixels=32):
    """Remove small objects and fill holes in instance masks.

    This function removes objects smaller than `min_pixels`, fills holes in the
    remaining objects using a closing operation, and returns the processed
    instance masks.

    Parameters
    ----------
    instance_masks : torch.Tensor
        A tensor of shape (B, H, W) containing instance segmentation masks.
    min_pixels : int, optional
        The minimum number of pixels for an object to be retained, by default 32.

    Returns
    -------
    torch.Tensor
        A tensor of shape (B, H, W) with small objects removed and holes filled.
    """
    device = instance_masks.device
    top_instance_label = instance_masks.max()
    cell_vals = torch.arange(1, top_instance_label + 1, device=device)
    bin_masks = (
        instance_masks[:, None, :] == cell_vals[None, :, None, None]
    )  # (bs, top_label, h, w)
    npixels_per_instance = bin_masks.sum(dim=(2, 3))

    # Do this before dilation to be consistant with what cellpose does.
    valid_masks_mask = npixels_per_instance >= min_pixels  # shape: (bs, top_label)

    old_shape = bin_masks.shape
    sz = old_shape[-1]
    bin_masks = bin_closing(bin_masks.view(-1, sz, sz))
    bin_masks = bin_masks.view(old_shape)

    bin_masks = torch.where(valid_masks_mask[..., None, None], bin_masks, 0)
    bin_masks *= cell_vals[None, :, None, None]

    # Not using sum here. Because of the previous dilation masks
    # could overlap by at max two pixels.
    new_instance_masks = bin_masks.max(1)[0]

    return new_instance_masks
