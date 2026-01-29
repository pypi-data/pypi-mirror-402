"""Pre and post processing functions required to generate masks from instanseg model."""

from typing import Tuple, Union

import numpy as np
import torch
import torch.nn.functional as F

from roche.crisp.networks.instanseg_unet import feature_engineering_generator


def convert(
    prob_input: torch.Tensor,
    coords_input: torch.Tensor,
    size: Tuple[int, int],
    mask_threshold: float = 0.5,
) -> torch.Tensor:
    """Convert the probability input to a labeled image."""
    # Create an array of labels for each pixel
    all_labels = torch.arange(
        1, 1 + prob_input.shape[0], dtype=torch.float32, device=prob_input.device
    )
    labels = torch.ones_like(prob_input) * torch.reshape(all_labels, (-1, 1, 1, 1))

    # Get flattened arrays
    labels = labels.flatten()
    prob = prob_input.flatten()
    x = coords_input[0, ...].flatten()
    y = coords_input[1, ...].flatten()

    # Predict image dimensions if we don't have them
    if size is None:
        size = (int(y.max() + 1), int(x.max() + 1))

    # Find indices with above-threshold probability values
    inds_prob = prob >= mask_threshold
    n_thresholded = torch.count_nonzero(inds_prob)
    if n_thresholded == 0:
        return torch.zeros(size, dtype=torch.float32, device=labels.device)

    # Create an array of [linear index, y, x, label], skipping low-probability values
    arr = torch.zeros(
        (int(n_thresholded), 5), dtype=coords_input.dtype, device=labels.device
    )
    arr[:, 1] = y[inds_prob]
    arr[:, 2] = x[inds_prob]
    # NOTE: UNEXPECTED Y,X ORDER!
    arr[:, 0] = arr[:, 2] * size[1] + arr[:, 1]
    arr[:, 3] = labels[inds_prob]

    # Sort first by descending probability
    inds_sorted = prob[inds_prob].argsort(descending=True, stable=True)
    arr = arr[inds_sorted, :]

    # Stable sort by linear indices
    inds_sorted = arr[:, 0].argsort(descending=False, stable=True)
    arr = arr[inds_sorted, :]

    # Find the first occurrence of each linear index - this should correspond to the
    # label that has the highest probability, because they have previously been sorted
    inds_unique = torch.ones_like(arr[:, 0], dtype=torch.bool)
    inds_unique[1:] = arr[1:, 0] != arr[:-1, 0]

    # Create the output
    output = torch.zeros(size, dtype=torch.float32, device=labels.device)
    # NOTE: UNEXPECTED Y,X ORDER!
    output[arr[inds_unique, 2], arr[inds_unique, 1]] = arr[inds_unique, 3].float()

    return output


def find_connected_components(adjacency_matrix: torch.Tensor):
    """Find the connected components of a graph using matrix operations."""
    # https://math.stackexchange.com/questions/1106870/can-i-find-the-connected-components-of-a-graph-using-matrix-operations-on-the-gr
    M = adjacency_matrix + torch.eye(
        adjacency_matrix.shape[0], device=adjacency_matrix.device
    )
    num_iterations = 10
    out = torch.matrix_power(M, num_iterations)
    col = (
        torch.arange(0, out.shape[0], device=out.device)
        .view(-1, 1)
        .expand(out.shape[0], out.shape[0])
    )  # Just a column matrix with numbers from 0 to out.shape[0]
    out_col_idx = ((out > 1).int() - torch.eye(out.shape[0], device=out.device)) * col
    maxes = out_col_idx.argmax(0) * (out_col_idx.max(0)[0] > 0).int()
    maxes = torch.maximum(
        maxes + 1, (torch.arange(0, out.shape[0], device=out.device) + 1)
    )  # recover the diagonal elements that were suppressed
    tentative_remapping = torch.stack(
        ((torch.arange(0, out.shape[0], device=out.device) + 1), maxes)
    )
    # start with two zeros:
    remapping = torch.cat(
        (torch.zeros(2, 1, device=tentative_remapping.device), tentative_remapping),
        dim=1,
    )  # Maybe this can be avoided in the future by thresholding labels

    return remapping


def merge_sparse_predictions(
    x: torch.Tensor,
    coords: torch.Tensor,
    mask_map: torch.Tensor,
    size: Tuple[int, int, int],
    mask_threshold: float = 0.5,
    window_size=128,
    min_size=10,
    overlap_threshold=0.5,
    mean_threshold=0.5,
):
    """Merge sparse predictions."""
    labels = convert(x, coords, size=(size[1], size[2]), mask_threshold=mask_threshold)[
        None
    ]

    idx = torch.arange(1, size[0] + 1, device=x.device, dtype=coords.dtype)
    stack_ID = torch.ones(
        (size[0], window_size, window_size), device=x.device, dtype=coords.dtype
    )
    stack_ID = stack_ID * (idx[:, None, None] - 1)

    coords = torch.stack((stack_ID.flatten(), coords[0] * size[2] + coords[1])).to(
        coords.dtype
    )

    fg = x.flatten() > mask_threshold
    x = x.flatten()[fg]
    coords = coords[:, fg]

    using_mps = False
    if x.is_mps:
        using_mps = True
        device = "cpu"
        x = x.to(device)
        mask_map = mask_map.to(device)

    sparse_onehot = torch.sparse_coo_tensor(
        coords,
        x.flatten() > mask_threshold,
        size=(size[0], size[1] * size[2]),
        dtype=x.dtype,
        device=x.device,
        requires_grad=False,
    )

    object_areas = torch.sparse.sum(sparse_onehot, dim=1).values()

    sum_mask_value = torch.sparse.sum(
        (sparse_onehot * mask_map.flatten()[None]), dim=1
    ).values()
    mean_mask_value = sum_mask_value / object_areas
    objects_to_remove = ~torch.logical_and(
        mean_mask_value > mean_threshold, object_areas > min_size
    )

    if window_size**2 * sparse_onehot.shape[0] == sparse_onehot.sum():
        # This can happen at the start of training.
        # This can cause OOM errors and is never a good sign - may aswell abort.
        return labels

    iou = fast_sparse_iou(sparse_onehot)

    remapping = find_connected_components((iou > overlap_threshold).float())

    if using_mps:
        device = "mps"
        remapping = remapping.to(device)
        labels = labels.to(device)

    labels = remap_values(remapping, labels)

    labels_to_remove = (
        torch.arange(
            0,
            len(objects_to_remove),
            device=objects_to_remove.device,
            dtype=coords.dtype,
        )
        + 1
    )[objects_to_remove]

    labels[torch.isin(labels, labels_to_remove)] = 0

    return labels


def generate_coordinate_map(
    mode: str = "linear",
    spatial_dim: int = 2,
    height: int = 256,
    width: int = 256,
    device: torch.device = torch.device(type="cuda"),
):
    """Generate a coordinate map.

    The coordinate map is a tensor of shape (spatial_dim, height, width) that contains
    the coordinates of the pixels in the image.
    """
    if mode == "linear":
        if spatial_dim == 2:
            xx = (
                torch.linspace(0, width * 64 / 256, width, device=device)
                .view(1, 1, -1)
                .expand(1, height, width)
            )
            yy = (
                torch.linspace(0, height * 64 / 256, height, device=device)
                .view(1, -1, 1)
                .expand(1, height, width)
            )
            xxyy = torch.cat((xx, yy), 0)

        elif spatial_dim >= 3:
            xx = (
                torch.linspace(0, width * 64 / 256, width, device=device)
                .view(1, 1, -1)
                .expand(1, height, width)
            )
            yy = (
                torch.linspace(0, height * 64 / 256, height, device=device)
                .view(1, -1, 1)
                .expand(1, height, width)
            )
            zz = torch.zeros_like(xx).expand(spatial_dim - 2, -1, -1)
            xxyy = torch.cat((xx, yy, zz), 0)
        else:
            xxyy = torch.zeros(
                (spatial_dim, height, width), device=device
            )  # NOT IMPLEMENTED - THIS IS JUST A DUMMY VALUE

    else:
        xxyy = torch.zeros(
            (spatial_dim, height, width), device=device
        )  # NOT IMPLEMENTED - THIS IS JUST A DUMMY VALUE

    return xxyy


def torch_peak_local_max(
    image: torch.Tensor,
    neighbourhood_size: int,
    minimum_value: float,
    return_map: bool = False,
    dtype: torch.dtype = torch.int,
) -> torch.Tensor:
    """Find the local maxima of an image.

    UPDATED FOR PERFORMANCE TESTING - NOT IDENTICAL, AS USES *FIRST* MAX,
    NOT FURTHEST FROM ORIGIN
    """
    h, w = image.shape
    image = image.view(1, 1, h, w)
    device = image.device

    kernel_size = 2 * neighbourhood_size + 1
    pooled, max_inds = F.max_pool2d(
        image,
        kernel_size=kernel_size,
        stride=1,
        padding=neighbourhood_size,
        return_indices=True,
    )

    inds = torch.arange(0, image.numel(), device=device, dtype=dtype).reshape(
        image.shape
    )

    peak_local_max = (max_inds == inds) * (pooled > minimum_value)

    if return_map:
        return peak_local_max

    # Non-zero causes host-device synchronization, which is a bottleneck
    return torch.nonzero(peak_local_max.squeeze()).to(dtype)


def centre_crop(
    centroids: torch.Tensor, window_size: int, h: int, w: int
) -> torch.Tensor:
    """Centres the crop around the centroid.

    Ensures that the crop does not exceed the image dimensions.
    """
    C = centroids.shape[0]
    centroids = centroids.clone()  # C,2
    centroids[:, 0] = centroids[:, 0].clamp(
        min=window_size // 2, max=h - window_size // 2
    )
    centroids[:, 1] = centroids[:, 1].clamp(
        min=window_size // 2, max=w - window_size // 2
    )
    window_slices = centroids[:, None] + torch.tensor(
        [[-1, -1], [1, 1]], device=centroids.device
    ) * (window_size // 2)

    grid_x, grid_y = torch.meshgrid(
        torch.arange(window_size, device=centroids.device, dtype=centroids.dtype),
        torch.arange(window_size, device=centroids.device, dtype=centroids.dtype),
        indexing="ij",
    )

    mesh = torch.stack((grid_x, grid_y))

    mesh_grid = mesh.expand(
        C, 2, window_size, window_size
    )  # C,2,2*window_size,2*window_size
    mesh_grid_flat = torch.flatten(mesh_grid, 2).permute(
        1, 0, -1
    )  # 2,C,2*window_size*2*window_size
    idx = window_slices[:, 0].permute(1, 0)[:, :, None]
    mesh_grid_flat = mesh_grid_flat + idx
    mesh_grid_flat = torch.flatten(mesh_grid_flat, 1)  # 2,C*2*window_size*2*window_size

    return mesh_grid_flat


def compute_crops(
    x: torch.Tensor,
    c: torch.Tensor,
    sigma: torch.Tensor,
    centroids_idx: torch.Tensor,
    feature_engineering,
    pixel_classifier,
    window_size: int = 128,
):
    """Compute the crops.

    This function computes the crops from the input tensor.
    """
    h, w = x.shape[-2:]
    C = c.shape[0]

    mesh_grid_flat = centre_crop(centroids_idx, window_size, h, w)

    x = feature_engineering(x, c, sigma, window_size // 2, mesh_grid_flat)

    x = pixel_classifier(x)  # C*H*W,1

    x = x.view(C, 1, window_size, window_size)

    idx = torch.arange(1, C + 1, device=x.device, dtype=mesh_grid_flat.dtype)

    rep = torch.ones(
        (C, window_size, window_size), device=x.device, dtype=mesh_grid_flat.dtype
    )
    rep = rep * (idx[:, None, None] - 1)

    iidd = torch.cat((rep.flatten()[None,], mesh_grid_flat)).to(mesh_grid_flat.dtype)

    return x, iidd


def postprocessing(
    prediction: Union[torch.Tensor, np.ndarray],
    mask_threshold: float = 0.53,
    peak_distance: int = 5,
    seed_threshold: float = 0.8,
    overlap_threshold: float = 0.3,
    mean_threshold: float = 0.1,
    window_size: int = 128,
    min_size: int = 10,
    n_sigma: int = 2,
    dim_coords: int = 2,
    device=None,
    classifier: torch.nn.Module = None,
    to_centre: bool = True,
    cells_and_nuclei: bool = False,
    feature_engineering_function="0",
    max_seeds: int = 2000,
    return_intermediate_objects: bool = False,
    precomputed_crops: torch.Tensor = None,
    precomputed_seeds: torch.Tensor = None,
):
    """Postprocess the prediction.

    This function postprocesses the prediction to remove small objects and merge
    overlapping objects.
    """
    if isinstance(prediction, np.ndarray):
        prediction = torch.tensor(prediction, device=device)

    feature_engineering, _ = feature_engineering_generator(feature_engineering_function)

    dim_out = dim_coords + n_sigma + 1
    if cells_and_nuclei:
        iterations = 2
        dim_out = int(dim_out / 2)
    else:
        iterations = 1
        dim_out = dim_out

    labels = []

    for i in range(iterations):
        if precomputed_crops is None:
            if i == 0:
                prediction_i = prediction[0:dim_out, :, :]
            else:
                prediction_i = prediction[dim_out:, :, :]

            height, width = prediction_i.size(1), prediction_i.size(2)

            ##torch.cuda.synchronize()

            xxyy = generate_coordinate_map(
                mode="linear",
                spatial_dim=dim_coords,
                height=height,
                width=width,
                device=device,
            )

            # torch.cuda.synchronize()

            if not to_centre:
                fields = (torch.sigmoid(prediction_i[0:dim_coords]) - 0.5) * 8
            else:
                fields = prediction_i[0:dim_coords]

            sigma = prediction_i[dim_coords : dim_coords + n_sigma]
            mask_map = torch.sigmoid(prediction_i[dim_coords + n_sigma])

            if (mask_map > mask_threshold).max() == 0:  # no foreground pixels
                label = torch.zeros(
                    mask_map.shape, dtype=int, device=mask_map.device
                ).squeeze()
                labels.append(label)
                continue

            # torch.cuda.synchronize()

            if precomputed_seeds is None:
                local_centroids_idx = torch_peak_local_max(
                    mask_map,
                    neighbourhood_size=int(peak_distance),
                    minimum_value=seed_threshold,
                )
            else:
                local_centroids_idx = precomputed_seeds

            # torch.cuda.synchronize()

            fields = fields + xxyy
            if to_centre:
                fields_at_centroids = xxyy[
                    :, local_centroids_idx[:, 0], local_centroids_idx[:, 1]
                ]
            else:
                fields_at_centroids = fields[
                    :, local_centroids_idx[:, 0], local_centroids_idx[:, 1]
                ]

            if local_centroids_idx.shape[0] > max_seeds:
                print("Too many seeds, skipping", local_centroids_idx.shape[0])
                label = torch.zeros(
                    mask_map.shape, dtype=int, device=mask_map.device
                ).squeeze()
                labels.append(label)
                continue

            C = fields_at_centroids.shape[0]

            h, w = mask_map.shape[-2:]
            window_size = min(window_size, h, w)
            window_size = window_size - window_size % 2

            if C == 0:
                label = torch.zeros(
                    mask_map.shape, dtype=int, device=mask_map.device
                ).squeeze()
                labels.append(label)
                continue

            # torch.cuda.synchronize()
            crops, coords = compute_crops(
                fields,
                fields_at_centroids.T,
                sigma,
                local_centroids_idx.int(),
                feature_engineering=feature_engineering,
                pixel_classifier=classifier,
                window_size=window_size,
            )  # about 65% of the time
            # torch.cuda.synchronize()
            coords = coords[
                1:
            ]  # The first channel are just channel indices, not required here.

            if return_intermediate_objects:
                return crops, coords, mask_map

            C = crops.shape[0]
            if C == 0:
                label = torch.zeros(
                    mask_map.shape, dtype=int, device=mask_map.device
                ).squeeze()
                labels.append(label)
                continue

        else:
            crops, coords, mask_map = precomputed_crops
            C = crops.shape[0]

        h, w = mask_map.shape[-2:]

        label = merge_sparse_predictions(
            crops,
            coords,
            mask_map,
            size=(C, h, w),
            mask_threshold=mask_threshold,
            window_size=window_size,
            min_size=min_size,
            overlap_threshold=overlap_threshold,
            mean_threshold=mean_threshold,
        ).int()  # about 30% of the time

        labels.append(label.squeeze())

    if len(labels) == 1:
        return labels[0][None]  # 1,H,W
    else:
        return torch.stack(labels)  # 2,H,W


def instanseg_padding(
    img: torch.Tensor,
    extra_pad: int = 0,
    min_dim: int = 16,
    ensure_square: bool = False,
):
    """Pad the image.

    This function pads the image to ensure that it is square and has a minimum
    dimension.
    """
    is_square = img.shape[-2] == img.shape[-1]
    original_shape = img.shape[-2:]
    bigger_dim = max(img.shape[-2], img.shape[-1])

    if ensure_square and not is_square:
        img = torch.functional.F.pad(
            img,
            [0, bigger_dim - img.shape[-1], 0, bigger_dim - img.shape[-2]],
            mode="constant",
        )

    padx = (
        min_dim * torch.ceil(torch.tensor((img.shape[-2] / min_dim))).int()
        - img.shape[-2]
        + extra_pad * 2
    )
    pady = (
        min_dim * torch.ceil(torch.tensor((img.shape[-1] / min_dim))).int()
        - img.shape[-1]
        + extra_pad * 2
    )

    if padx > img.shape[-2]:
        padx = padx - extra_pad
    if pady > img.shape[-1]:
        pady = pady - extra_pad
    img = torch.functional.F.pad(img, [0, int(pady), 0, int(padx)], mode="reflect")

    if ensure_square and not is_square:
        pady = pady + bigger_dim - original_shape[-1]
        padx = padx + bigger_dim - img.shape[-2]
        print(padx, pady)

    return img, torch.stack((padx, pady))


def get_intersection_over_nucleus_area(
    label: torch.Tensor, return_lab: bool = False
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Return the intersection over nucleus area in a 2 channel labeled image.

    label must be a 1,2,H,W tensor where the first channel is nuclei and the second is
    whole cell
    """
    label = torch.stack((torch_fastremap(label[0, 0]), torch_fastremap(label[0, 1])))[
        None
    ]
    nuclei_onehot = torch_sparse_onehot(label[0, 0], flatten=True)[0]
    cell_onehot = torch_sparse_onehot(label[0, 1], flatten=True)[0]
    intersection = torch.sparse.mm(nuclei_onehot, cell_onehot.T).to_dense()
    sparse_sum1 = torch.sparse.sum(nuclei_onehot, dim=(1,))[None].to_dense()
    nuclei_area = sparse_sum1.T

    if return_lab:
        return (intersection / nuclei_area), label

    return (intersection / nuclei_area), nuclei_area


def keep_only_largest_nucleus_per_cell(
    labels: torch.Tensor, return_lab: bool = True
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Keep only the largest nucleus per cell.

    Parameters
    ----------
    labels : torch.Tensor
        Tensor of shape 1,2,H,W containing nucleus and cell labels respectively
    return_lab : bool, optional
        If True, returns the labels with only the largest nucleus per cell,
        and only cells that have a nucleus.

    Returns
    -------
    Tuple[torch.Tensor, torch.Tensor]
        Tuple containing:
        - nuclei_ids : torch.Tensor
            Tensor of shape N containing the largest nucleus per cell
        - labels : torch.Tensor
            Tensor of shape 1,2,H,W containing nucleus and cell labels respectively
    """
    labels = torch_fastremap(labels)
    iou, nuclei_area = get_intersection_over_nucleus_area(labels)
    iou_biggest_area = ((iou > 0.5).float() * nuclei_area) == (
        ((iou > 0.5).float() * nuclei_area).max(0)[0]
    )
    iou_biggest_area = (iou_biggest_area.float() * iou) > 0.5
    nuclei_ids = torch.unique(labels[0, 0][labels[0, 0] > 0])
    cell_ids = torch.unique(labels[0, 1][labels[0, 1] > 0])
    largest_nucleus = (iou_biggest_area.sum(1)) == 1
    nucleated_cells = ((iou > 0.5).float().sum(0)) >= 1
    if return_lab:
        return nuclei_ids[largest_nucleus], torch.stack(
            (
                labels[0, 0] * torch.isin(labels[0, 0], nuclei_ids[largest_nucleus]),
                labels[0, 1] * torch.isin(labels[0, 1], cell_ids[nucleated_cells]),
            )
        ).unsqueeze(0)
    return (
        nuclei_ids[largest_nucleus],
        nuclei_ids[largest_nucleus],
    )  # the duplication is to keep torchscript happy


def resolve_cell_and_nucleus_boundaries(
    lab: torch.Tensor, allow_unnucleated_cells: bool = True
) -> torch.Tensor:
    """Resolve the boundaries between cells and nuclei.

    It will first match the labels of the largest nucleus and its cell.
    It will then erase from the cell masks all the nuclei pixels.
    This resolves nuclei "just" overlapping adjacent cell.
    It will then recover the nuclei pixels that were erased by adding
    them back to the cell masks.

    Parameters
    ----------
    lab : torch.Tensor
        Tensor of shape 1,2,H,W containing nucleus and cell labels respectively
    allow_unnucleated_cells : bool, optional
        If False, this will remove all cells that don't have nucleus.

    Returns
    -------
    torch.Tensor
        Tensor of the same shape as lab

    Notes
    -----
    This function will return a tensor of the same shape as lab.
    The first channel will be the nuclei labels and the second channel will be the cell
    labels.
    """
    if lab[0, 0].max() == 0:  # No nuclei
        if lab[0, 1].max() == 0 or not allow_unnucleated_cells:  # No cells
            return torch.zeros_like(lab)
        else:
            return lab
    elif lab[0, 1].max() == 0:
        return torch.stack((lab[0, 0], lab[0, 0])).unsqueeze(
            0
        )  # Nuclei but no cells, just duplicate the nuclei.

    lab = torch.stack(
        (torch_fastremap(lab[0, 0]), torch_fastremap(lab[0, 1]))
    ).unsqueeze(0)  # just relabel the nuclei and cells from 1 to N

    original_nuclei_labels = lab[0, 0].clone()
    original_cell_labels = lab[0, 1].clone()

    _, lab = keep_only_largest_nucleus_per_cell(
        lab, return_lab=True
    )  # There will now be as many cells as there are nuclei.
    # But the labels are not yet matched

    lab = torch.stack(
        (torch_fastremap(lab[0, 0]), torch_fastremap(lab[0, 1]))
    ).unsqueeze(0)

    if lab[0, 0].max() == 0:  # No nuclei
        if lab[0, 1].max() == 0 or not allow_unnucleated_cells:  # No cells
            return torch.zeros_like(lab)
        else:
            return lab
    elif lab[0, 1].max() == 0:
        return torch.stack((lab[0, 0], lab[0, 0])).unsqueeze(
            0
        )  # Nuclei but no cells, just duplicate the nuclei.

    clean_lab = lab

    iou, _ = get_intersection_over_nucleus_area(clean_lab)
    onehot_remapping = (torch.nonzero(iou > 0.5).T + 1).flip(0)
    remapping = torch.cat(
        (torch.zeros(2, 1, device=onehot_remapping.device), onehot_remapping), dim=1
    )
    clean_lab[0, 1] = remap_values(
        remapping, clean_lab[0, 1]
    ).int()  # Every matching cell and nucleus now have the same label.

    nuclei_labels = clean_lab[0, 0]
    cell_labels = clean_lab[0, 1]

    original_nuclei_labels[nuclei_labels > 0] = 0
    original_nuclei_labels = torch_fastremap(original_nuclei_labels)
    original_nuclei_labels[original_nuclei_labels > 0] += nuclei_labels.max()
    nuclei_labels += original_nuclei_labels

    cell_labels[nuclei_labels > 0] = 0
    cell_labels += nuclei_labels

    if allow_unnucleated_cells:
        cell_labels[cell_labels == 0] = (
            original_cell_labels[cell_labels == 0] + cell_labels.max()
        ) * (original_cell_labels > 0)[
            cell_labels == 0
        ].float()  # this step can create small fragments.
        # This is not a bug - but may have to be cleaned up in the future.

    return torch.stack((nuclei_labels, cell_labels)).unsqueeze(0)


def recover_padding(x: torch.Tensor, pad: torch.Tensor):
    """Recover the padding from the padded image."""
    # x must be 1,C,H,W or C,H,W
    squeeze = False
    if x.ndim == 3:
        x = x.unsqueeze(0)
        squeeze = True

    if pad[0] == 0:
        pad[0] = -x.shape[2]
    if pad[1] == 0:
        pad[1] = -x.shape[3]

    if squeeze:
        return x[:, :, : -pad[0], : -pad[1]].squeeze(0)
    else:
        return x[:, :, : -pad[0], : -pad[1]]


def remap_values(remapping: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
    """Remap the values in x according to the pairs in the remapping tensor.

    Make sure the remapping is 1 to 1, and there are no loops (i.e. 1->2, 2->3, 3->1).
    Loops can be removed using graph based connected components algorithms. (see
    instanseg postprocessing for an example)
    """
    sorted_remapping = remapping[:, remapping[0].argsort()]
    index = torch.bucketize(x.ravel(), sorted_remapping[0])
    return sorted_remapping[1][index].reshape(x.shape)


def torch_fastremap(x: torch.Tensor) -> torch.Tensor:
    """Remap the values in x to a new set of values."""
    if x.max() == 0:
        return x
    unique_values = torch.unique(x, sorted=True)
    new_values = torch.arange(len(unique_values), dtype=x.dtype, device=x.device)
    remapping = torch.stack((unique_values, new_values))
    return remap_values(remapping, x)


def torch_onehot(x: torch.Tensor) -> torch.Tensor:
    """Convert a labeled image to a onehot encoded tensor.

    x is a labeled image of shape _,_,H,W returns a onehot encoding of shape 1,C,H,W
    """
    if x.max() == 0:
        return torch.zeros_like(x).reshape(1, 0, *x.shape[-2:])
    H, W = x.shape[-2:]
    x = x.view(-1, 1, H, W)
    x = x.squeeze().view(1, 1, H, W)
    unique = torch.unique(x[x > 0])
    x = x.repeat(1, len(unique), 1, 1)
    return x == unique.unsqueeze(-1).unsqueeze(-1)


def fast_iou(onehot: torch.Tensor, threshold: float = 0.5) -> torch.Tensor:
    """Return the intersection over union between two dense onehot encoded tensors."""
    # onehot is C,H,W
    if onehot.ndim == 3:
        onehot = onehot.flatten(1)
    onehot = (onehot > threshold).float()
    intersection = onehot @ onehot.T
    union = onehot.sum(1)[None].T + onehot.sum(1)[None] - intersection
    return intersection / union


def fast_sparse_iou(sparse_onehot: torch.Tensor) -> torch.Tensor:
    """Return the intersection over union between two sparse onehot encoded tensors."""
    intersection = torch.sparse.mm(sparse_onehot, sparse_onehot.T).to_dense()
    sparse_sum = torch.sparse.sum(sparse_onehot, dim=(1,))[None].to_dense()
    union = sparse_sum.T + sparse_sum - intersection
    return intersection / union


def instance_wise_edt(x: torch.Tensor, edt_type: str = "auto") -> torch.Tensor:
    """Create instance-normalized distance map from a labeled image.

    Each pixel within an instance gives the distance to the closed background pixel,
    divided by the maximum distance (so that the maximum within an instance is 1).

    The calculation of the Euclidean Distance Transform can use the 'edt' or 'monai'
    packages. 'edt' is faster for CPU computation, while 'monai' can use cucim for GPU
    acceleration where CUDA is available. Use 'auto' to decide automatically.
    """
    if x.max() == 0:
        return torch.zeros_like(x).squeeze()
    is_mps = x.is_mps
    if is_mps:
        # Need to convert to CPU for MPS, because distance transform gives float64
        # result and Monai's internal attempt to convert type will fail
        x = x.to("cpu")

    use_edt = edt_type == "edt" or (edt_type != "monai" and not x.is_cuda)
    if use_edt:
        import edt

        xedt = torch.from_numpy(edt.edt(x[0].cpu().numpy(), black_border=False))
        x = torch_onehot(x)[0] * xedt.to(x.device)
    else:
        import monai

        x = torch_onehot(x)
        x = monai.transforms.utils.distance_transform_edt(x[0])

    # Normalize instance distances to have max 1
    x = x / (x.flatten(1).max(1)[0]).view(-1, 1, 1)
    x = x.sum(0)

    if is_mps:
        x = x.type(torch.FloatTensor).to("mps")
    return x


def fast_dual_iou(onehot1: torch.Tensor, onehot2: torch.Tensor) -> torch.Tensor:
    """Return the intersection over union between two dense onehot encoded tensors."""
    # onehot1 and onehot2 are C1,H,W and C2,H,W

    C1 = onehot1.shape[0]
    C2 = onehot2.shape[0]

    max_C = max(C1, C2)

    onehot1 = torch.cat((onehot1, torch.zeros((max_C - C1, *onehot1.shape[1:]))), dim=0)
    onehot2 = torch.cat((onehot2, torch.zeros((max_C - C2, *onehot2.shape[1:]))), dim=0)

    onehot1 = onehot1.flatten(1)
    onehot1 = (onehot1 > 0.5).float()  # onehot should be binary

    onehot2 = onehot2.flatten(1)
    onehot2 = (onehot2 > 0.5).float()

    intersection = onehot1 @ onehot2.T
    union = (onehot1).sum(1)[None].T + (onehot2).sum(1)[None] - intersection

    return (intersection / union)[:C1, :C2]


def torch_sparse_onehot(
    x: torch.Tensor, flatten: bool = False
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Convert the labeled image to a sparse onehot encoded tensor."""
    # x is a labeled image of shape _,_,H,W returns a sparse tensor of shape C,H,W
    unique_values = torch.unique(x, sorted=True)
    x = torch_fastremap(x)

    H, W = x.shape[-2], x.shape[-1]

    if flatten:
        if x.max() == 0:
            return torch.zeros_like(x).reshape(1, 1, H * W)[:, :0], unique_values

        x = x.reshape(H * W)
        xxyy = torch.nonzero(x > 0).squeeze(1)
        zz = x[xxyy] - 1
        C = x.max().int().item()

        # print(C, H, W, type(C), type(H), type(W))
        sparse_onehot = torch.sparse_coo_tensor(
            torch.stack((zz, xxyy)).long(),
            (torch.ones_like(xxyy).float()),
            size=(int(C), int(H * W)),
            dtype=torch.float32,
        )

    else:
        if x.max() == 0:
            return torch.zeros_like(x).reshape(1, 0, H, W), unique_values

        x = x.squeeze().view(H, W)
        x_temp = torch.nonzero(x > 0).T
        zz = x[x_temp[0], x_temp[1]] - 1
        C = x.max().int().item()
        sparse_onehot = torch.sparse_coo_tensor(
            torch.stack((zz, x_temp[0], x_temp[1])).long(),
            (torch.ones_like(x_temp[0]).float()),
            size=(int(C), int(H), int(W)),
            dtype=torch.float32,
        )

    return sparse_onehot, unique_values


def fast_sparse_dual_iou(onehot1: torch.Tensor, onehot2: torch.Tensor) -> torch.Tensor:
    """Return the intersection over union between two sparse onehot encoded tensors."""
    # onehot1 and onehot2 are C1,H*W and C2,H*W

    intersection = torch.sparse.mm(onehot1, onehot2.T).to_dense()
    sparse_sum1 = torch.sparse.sum(onehot1, dim=(1,))[None].to_dense()
    sparse_sum2 = torch.sparse.sum(onehot2, dim=(1,))[None].to_dense()
    union = sparse_sum1.T + sparse_sum2 - intersection

    return intersection / union


def iou_test():
    """Test for the fast dual iou functions."""
    out = torch.randint(0, 50, (1, 2, 124, 256), dtype=torch.float32)
    onehot1 = torch_onehot(out[0, 0])[0]
    onehot2 = torch_onehot(out[0, 1])[0]
    iou_dense = fast_dual_iou(onehot1, onehot2)

    onehot1 = torch_sparse_onehot(out[0, 0], flatten=True)[0]
    onehot2 = torch_sparse_onehot(out[0, 1], flatten=True)[0]
    iou_sparse = fast_sparse_dual_iou(onehot1, onehot2)

    assert torch.allclose(iou_dense, iou_sparse)


def match_labels(
    tile_1: torch.Tensor, tile_2: torch.Tensor, threshold: float = 0.5, strict=False
):
    """Take two labeled tiles, and match overlapping labels.

    If strict is set to True, the function will discard non matching objects.
    """
    if tile_1.max() == 0 or tile_2.max() == 0:
        if not strict:
            return tile_1, tile_2
        else:
            return torch.zeros_like(tile_1), torch.zeros_like(tile_2)

    old_problematic_onehot, old_unique_values = torch_sparse_onehot(
        tile_1, flatten=True
    )
    new_problematic_onehot, new_unique_values = torch_sparse_onehot(
        tile_2, flatten=True
    )

    iou = fast_sparse_dual_iou(old_problematic_onehot, new_problematic_onehot)

    onehot_remapping = torch.nonzero(iou > threshold).T  # + 1

    if old_unique_values.min() == 0:
        old_unique_values = old_unique_values[old_unique_values > 0]
    if new_unique_values.min() == 0:
        new_unique_values = new_unique_values[new_unique_values > 0]

    if onehot_remapping.shape[1] > 0:
        onehot_remapping = torch.stack(
            (
                new_unique_values[onehot_remapping[1]],
                old_unique_values[onehot_remapping[0]],
            )
        )

        if not strict:
            mask = torch.isin(tile_2, onehot_remapping[0])
            tile_2[mask] = remap_values(onehot_remapping, tile_2[mask])

            return tile_1, tile_2
        else:
            tile_1 = tile_1 * torch.isin(tile_1, onehot_remapping[1]).int()
            tile_2 = tile_2 * torch.isin(tile_2, onehot_remapping[0]).int()

            tile_2[tile_2 > 0] = remap_values(onehot_remapping, tile_2[tile_2 > 0])

            return tile_1, tile_2

    else:
        if not strict:
            return tile_1, tile_2
        else:
            return torch.zeros_like(tile_1), torch.zeros_like(tile_2)


def connected_components(x: torch.Tensor, num_iterations: int = 32) -> torch.Tensor:
    """Take a binary image and return the connected components."""
    mask = x == 1

    B, _, H, W = x.shape
    out = torch.arange(B * W * H, device=x.device, dtype=x.dtype).reshape((B, 1, H, W))
    out[~mask] = 0

    for _ in range(num_iterations):
        out[mask] = F.max_pool2d(out, kernel_size=3, stride=1, padding=1)[mask]

    return out


def iou_heatmap(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Take two labeled images and return the intersection over union heatmap."""
    if x.max() == 0 or y.max() == 0:
        return torch.zeros_like(x)

    x = torch_fastremap(x)
    y = torch_fastremap(y)

    x_onehot, _ = torch_sparse_onehot(x, flatten=True)
    y_onehot, _ = torch_sparse_onehot(y, flatten=True)

    iou = fast_sparse_dual_iou(x_onehot, y_onehot)
    predicted_iou = iou.sum(1)
    onehot = torch_onehot(x)
    onehot = onehot.float() * predicted_iou[:, None, None]
    map = onehot.max(1)[0]

    return map


def eccentricity_batch(mask_tensor):
    """Calculate the eccentricity of a batch of binary masks.

    B,H,W -> returns B.
    """
    # Get dimensions
    batch_size, m, n = mask_tensor.shape

    # Create indices grid
    y_indices, x_indices = torch.meshgrid(
        torch.arange(m), torch.arange(n), indexing="ij"
    )
    y_indices = y_indices.unsqueeze(0).to(mask_tensor.device).expand(batch_size, m, n)
    x_indices = x_indices.unsqueeze(0).to(mask_tensor.device).expand(batch_size, m, n)

    # Find total mass and centroid
    total_mass = mask_tensor.sum(dim=(1, 2))
    centroid_y = (y_indices * mask_tensor).sum(dim=(1, 2)) / total_mass
    centroid_x = (x_indices * mask_tensor).sum(dim=(1, 2)) / total_mass

    # Calculate second-order moments
    y_diff = y_indices - centroid_y.view(batch_size, 1, 1)
    x_diff = x_indices - centroid_x.view(batch_size, 1, 1)
    M_yy = torch.sum(y_diff**2 * mask_tensor, dim=(1, 2))
    M_xx = torch.sum(x_diff**2 * mask_tensor, dim=(1, 2))
    M_xy = torch.sum(x_diff * y_diff * mask_tensor, dim=(1, 2))

    # Construct second-order moments tensor
    moments_tensor = torch.stack(
        [torch.stack([M_xx, M_xy]), torch.stack([M_xy, M_yy])]
    ).permute(2, 0, 1)

    # Compute eigenvalues
    eigenvalues = torch.linalg.eigvals(moments_tensor)

    # Get maximum eigenvalue
    lambda1 = torch.max(eigenvalues.real, dim=1).values
    # Get minimum eigenvalue
    lambda2 = torch.min(eigenvalues.real, dim=1).values

    # Calculate eccentricity
    eccentricity = torch.sqrt(1 - (lambda2 / lambda1))

    return eccentricity.squeeze(1, 2)
