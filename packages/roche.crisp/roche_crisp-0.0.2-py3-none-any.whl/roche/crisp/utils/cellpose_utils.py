"""Pre and Post processing functions required to generate masks from cellpose model."""

import logging
import os
from glob import glob
from pathlib import Path
from typing import Optional, Tuple

import click
import cv2
import fastremap
import imageio
import numpy as np
import pandas as pd
import scipy.ndimage
import tifffile
import torch
from numba import njit
from scipy.ndimage import maximum_filter1d, mean
from tqdm import tqdm

from roche.crisp.utils import common_utils, transforms

LOG = logging.getLogger(__name__)


@click.group()
def cli():
    """Utilities for cellpose training."""
    pass


@njit("(float64[:], int32[:], int32[:], int32, int32, int32, int32)", nogil=True)
def _extend_centers(
    T: np.ndarray[float],
    y: np.ndarray[int],
    x: np.ndarray[int],
    ymed: int,
    xmed: int,
    Lx: int,
    niter: int,
) -> np.ndarray:
    """Run diffusion from center of mask (ymed, xmed) on mask pixels (y, x).

    Parameters
    ----------
    T : np.ndarray[float]
        _ x Lx array that diffusion is run in
    y : np.ndarray[int]
        pixels in y inside mask
    x : np.ndarray[int]
        pixels in x inside mask
    ymed : int
        center of mask in y
    xmed : int
        center of mask in x
    Lx : int
        size of x-dimension of masks
    niter : int
        number of iterations to run diffusion

    Returns
    -------
    T : np.ndarray
        amount of diffused particles at each pixel
    """
    for t in range(niter):
        T[ymed * Lx + xmed] += 1
        T[y * Lx + x] = (
            1
            / 9.0
            * (
                T[y * Lx + x]
                + T[(y - 1) * Lx + x]
                + T[(y + 1) * Lx + x]
                + T[y * Lx + x - 1]
                + T[y * Lx + x + 1]
                + T[(y - 1) * Lx + x - 1]
                + T[(y - 1) * Lx + x + 1]
                + T[(y + 1) * Lx + x - 1]
                + T[(y + 1) * Lx + x + 1]
            )
        )
    return T


def _extend_centers_gpu(
    neighbors: torch.Tensor,
    centers: torch.Tensor,
    isneighbor: torch.Tensor,
    Ly: int,
    Lx: int,
    n_iter: int = 200,
    device: torch.device = torch.device("cuda"),
) -> torch.Tensor:
    """Run diffusion on GPU to generate flows for training images or quality control.

    neighbors is 9 x pixels in masks, centers are mask centers, isneighbor is valid
    neighbor boolean 9 x pixels

    Parameters
    ----------
    neighbors : torch.Tensor
        9 x pixels in masks
    centers : torch.Tensor
        mask centers
    isneighbor : torch.Tensor
        valid neighbor boolean 9 x pixels
    Ly : int
        size of y-dimension of masks
    Lx : int
        size of x-dimension of masks
    n_iter : int
        number of iterations to run diffusion
    device : torch.device
        Device to be used for computation, by default uses gpu.
    """
    nimg = neighbors.shape[0] // 9
    pt = torch.from_numpy(neighbors).to(device)

    T = torch.zeros((nimg, Ly, Lx), dtype=torch.double, device=device)
    meds = torch.from_numpy(centers.astype(int)).to(device).long()
    isneigh = torch.from_numpy(isneighbor).to(device)
    for i in range(n_iter):
        T[:, meds[:, 0], meds[:, 1]] += 1
        Tneigh = T[:, pt[:, :, 0], pt[:, :, 1]]
        Tneigh *= isneigh
        T[:, pt[0, :, 0], pt[0, :, 1]] = Tneigh.mean(axis=1)
    del meds, isneigh, Tneigh
    T = torch.log(1.0 + T)
    # gradient positions
    grads = T[:, pt[[2, 1, 4, 3], :, 0], pt[[2, 1, 4, 3], :, 1]]
    del pt
    dy = grads[:, 0] - grads[:, 1]
    dx = grads[:, 2] - grads[:, 3]
    del grads
    mu_torch = np.stack((dy.cpu().squeeze(), dx.cpu().squeeze()), axis=-2)
    return mu_torch


def masks_to_flows_gpu(
    masks: np.ndarray, device: torch.device = torch.device("cuda")
) -> tuple[np.ndarray, np.ndarray]:
    """Convert masks to flows.

    Using diffusion from center pixel Center of masks where
    diffusion starts is defined using COM.

    Parameters
    ----------
    masks : int, 2D or 3D array
        labelled masks 0=NO masks; 1,2,...=mask labels
    device : torch.device
        Device to be used for computation, by default uses gpu.

    Returns
    -------
    mu : float, 3D or 4D array
        flows in Y = mu[-2], flows in X = mu[-1].
        if masks are 3D, flows in Z = mu[0].
    mu_c : float, 2D or 3D array
        for each pixel, the distance to the center of the mask
        in which it resides
    """
    Ly0, Lx0 = masks.shape
    Ly, Lx = Ly0 + 2, Lx0 + 2

    masks_padded = np.zeros((Ly, Lx), np.int64)
    masks_padded[1:-1, 1:-1] = masks

    # get mask pixel neighbors
    y, x = np.nonzero(masks_padded)
    neighborsY = np.stack((y, y - 1, y + 1, y, y, y - 1, y - 1, y + 1, y + 1), axis=0)
    neighborsX = np.stack((x, x, x, x - 1, x + 1, x - 1, x + 1, x - 1, x + 1), axis=0)
    neighbors = np.stack((neighborsY, neighborsX), axis=-1)

    # get mask centers
    slices = scipy.ndimage.find_objects(masks)

    centers = np.zeros((masks.max(), 2), "int")
    for i, si in enumerate(slices):
        if si is not None:
            sr, sc = si
            # ly, lx = sr.stop - sr.start + 1, sc.stop - sc.start + 1
            yi, xi = np.nonzero(masks[sr, sc] == (i + 1))
            yi = yi.astype(np.int32) + 1  # add padding
            xi = xi.astype(np.int32) + 1  # add padding
            ymed = np.median(yi)
            xmed = np.median(xi)
            imin = np.argmin((xi - xmed) ** 2 + (yi - ymed) ** 2)
            xmed = xi[imin]
            ymed = yi[imin]
            centers[i, 0] = ymed + sr.start
            centers[i, 1] = xmed + sc.start

    # get neighbor validator (not all neighbors are in same mask)
    neighbor_masks = masks_padded[neighbors[:, :, 0], neighbors[:, :, 1]]
    isneighbor = neighbor_masks == neighbor_masks[0]
    ext = np.array(
        [[sr.stop - sr.start + 1, sc.stop - sc.start + 1] for sr, sc in slices]
    )
    n_iter = 2 * (ext.sum(axis=1)).max()
    # run diffusion
    mu = _extend_centers_gpu(
        neighbors, centers, isneighbor, Ly, Lx, n_iter=n_iter, device=device
    )

    # normalize
    mu /= 1e-20 + (mu**2).sum(axis=0) ** 0.5

    # put into original image
    mu0 = np.zeros((2, Ly0, Lx0))
    mu0[:, y - 1, x - 1] = mu
    mu_c = np.zeros_like(mu0)
    return mu0, mu_c


def masks_to_flows_cpu(
    masks: np.ndarray, device: Optional[torch.device] = None
) -> tuple[np.ndarray, np.ndarray]:
    """Convert masks to flows.

    Using diffusion from center pixel Center of masks where
    diffusion starts is defined to be the closest pixel to the median of all pixels that
    is inside the mask. Result of diffusion is converted into flows by computing the
    gradients of the diffusion density map.

    Parameters
    ----------
    masks : numpy.ndarray
        labelled masks 0=NO masks; 1,2,...=mask labels
    device : torch.device
        Device to be used for computation, by default uses cpu.

    Returns
    -------
    mu : numpy.ndarray
        flows in Y = mu[-2], flows in X = mu[-1].
        if masks are 3D, flows in Z = mu[0].
    mu_c : numpy.ndarray
        for each pixel, the distance to the center of the mask
        in which it resides
    """
    Ly, Lx = masks.shape
    mu = np.zeros((2, Ly, Lx), np.float64)
    mu_c = np.zeros((Ly, Lx), np.float64)

    # nmask = masks.max()
    slices = scipy.ndimage.find_objects(masks)
    dia = common_utils.get_diameters(masks)[0]
    s2 = (0.15 * dia) ** 2
    for i, si in enumerate(slices):
        if si is not None:
            sr, sc = si
            ly, lx = sr.stop - sr.start + 1, sc.stop - sc.start + 1
            y, x = np.nonzero(masks[sr, sc] == (i + 1))
            y = y.astype(np.int32) + 1
            x = x.astype(np.int32) + 1
            ymed = np.median(y)
            xmed = np.median(x)
            imin = np.argmin((x - xmed) ** 2 + (y - ymed) ** 2)
            xmed = x[imin]
            ymed = y[imin]

            d2 = (x - xmed) ** 2 + (y - ymed) ** 2
            mu_c[sr.start + y - 1, sc.start + x - 1] = np.exp(-d2 / s2)

            niter = 2 * np.int32(np.ptp(x) + np.ptp(y))
            T = np.zeros((ly + 2) * (lx + 2), np.float64)
            T = _extend_centers(T, y, x, ymed, xmed, np.int32(lx), np.int32(niter))
            T[(y + 1) * lx + x + 1] = np.log(1.0 + T[(y + 1) * lx + x + 1])

            dy = T[(y + 1) * lx + x] - T[(y - 1) * lx + x]
            dx = T[y * lx + x + 1] - T[y * lx + x - 1]
            mu[:, sr.start + y - 1, sc.start + x - 1] = np.stack((dy, dx))

    mu /= 1e-20 + (mu**2).sum(axis=0) ** 0.5

    return mu, mu_c


def masks_to_flows(masks: np.ndarray, use_gpu: bool = False) -> np.ndarray:
    """Convert masks to flows using diffusion from center pixel.

    Center of masks where diffusion starts is defined to be the
    closest pixel to the median of all pixels that is inside the
    mask. Result of diffusion is converted into flows by computing
    the gradients of the diffusion density map.

    Parameters
    ----------
    masks : numpy.ndarray
        labelled masks 0=NO masks; 1,2,...=mask labels
    use_gpu : bool
        use GPU to run interpolated dynamics (faster than CPU)

    Returns
    -------
    mu : numpy.ndarray
        flows in Y = mu[-2], flows in X = mu[-1].
        if masks are 3D, flows in Z = mu[0].

    mu_c : numpy.ndarray
        for each pixel, the distance to the center of the mask
        in which it resides
    """
    if masks.max() == 0:
        LOG.warning("empty masks!")
        return np.zeros((2, *masks.shape), "float32")

    if use_gpu:
        device = torch.device("cuda")
        masks_to_flows_device = masks_to_flows_gpu
    else:
        device = None
        masks_to_flows_device = masks_to_flows_cpu

    if masks.ndim == 3:
        Lz, Ly, Lx = masks.shape
        mu = np.zeros((3, Lz, Ly, Lx), np.float32)
        for z in range(Lz):
            mu0 = masks_to_flows_device(masks[z], device=device)[0]
            mu[[1, 2], z] += mu0
        for y in range(Ly):
            mu0 = masks_to_flows_device(masks[:, y], device=device)[0]
            mu[[0, 2], :, y] += mu0
        for x in range(Lx):
            mu0 = masks_to_flows_device(masks[:, :, x], device=device)[0]
            mu[[0, 1], :, :, x] += mu0
        return mu
    elif masks.ndim == 2:
        mu, mu_c = masks_to_flows_device(masks, device=device)
        return mu

    else:
        raise ValueError("masks_to_flows only takes 2D or 3D arrays")


def labels_to_flows(
    labels: list[np.ndarray],
    files: list[str],
    use_gpu: bool = False,
) -> None:
    """Convert labels (list of binary masks or instance masks) to flows.

    Flows are saved to the same directory as the labels in .tif format.

    Parameters
    ----------
    labels : list[numpy.ndarray]
        labels[k] can be 2D or 3D, if [3 x Ly x Lx] then it is assumed that flows were
        precomputed.
        Otherwise labels[k][0] or labels[k] (if 2D) is used to create flows and cell
        probabilities.
    files : list[str]
        files[k] is the file name to save flows to,
    use_gpu : bool, optional
        use GPU to run interpolated dynamics (faster than CPU), by default False

    Returns
    -------
    None
    """
    nimg = len(labels)
    if labels[0].ndim < 3:
        labels = [labels[n][np.newaxis, :, :] for n in range(nimg)]

    if labels[0].shape[0] == 1 or labels[0].ndim < 3:
        LOG.info("computing flows for labels")

        # compute flows; labels are fixed here to be unique, so they need to be passed
        # back make sure labels are unique!
        labels = [fastremap.renumber(label, in_place=True)[0] for label in labels]
        veci = [masks_to_flows(labels[n][0], use_gpu=use_gpu) for n in range(nimg)]

        # concatenate labels, distance transform, vector flows, heat (boundary and mask
        # are computed in augmentations)
        flows = [
            np.concatenate((labels[n], veci[n]), axis=0).astype(np.float32)
            for n in range(nimg)
        ]
        flows_dir = Path(files[0]).parent
        for flow, file in zip(flows, files):
            file_name = Path(file).stem.replace("mask", "flows")
            tifffile.imwrite(str(flows_dir / (file_name + ".tif")), flow)
    else:
        raise ValueError(
            f"Expected labels to be instance or binary masks of shape (height, width) "
            f"or (1, height, width). Got shape: {labels[0].shape}"
        )


def _steps2D_interp(
    p: np.ndarray, dP: np.ndarray, niter: int, device=torch.device("cpu")
) -> np.ndarray:
    """Interpolate 2D steps based on displacement field.

    Parameters
    ----------
    p : numpy.ndarray
        Array of shape (n_points, 2) representing the initial pixel locations.
    dP : numpy.ndarray or torch.Tensor
        Array or tensor of shape (2, Ly, Lx) representing the displacement field.
    niter : int
        Number of iterations for stepping.
    device : torch.device or str, optional
        Device to be used when `use_gpu` is True. If None, a default GPU device will be
        used.

    Returns
    -------
    numpy.ndarray
        Array of shape (n_points, 2) representing the final pixel locations after
        interpolation.
    """
    shape = dP.shape[1:]
    shape = (
        np.array(shape)[[1, 0]].astype("float") - 1
    )  # Y and X dimensions (dP is 2.Ly.Lx), flipped X-1, Y-1
    pt = (
        torch.from_numpy(p[[1, 0]].T).float().to(device).unsqueeze(0).unsqueeze(0)
    )  # p is n_points by 2, so pt is [1 1 2 n_points]
    im = (
        torch.from_numpy(dP[[1, 0]]).float().to(device).unsqueeze(0)
    )  # convert flow numpy array to tensor on GPU, add dimension
    # normalize pt between  0 and  1, normalize the flow
    for k in range(2):
        im[:, k, :, :] *= 2.0 / shape[k]
        pt[:, :, :, k] /= shape[k]

    # normalize to between -1 and 1
    pt = pt * 2 - 1

    # here is where the stepping happens
    for t in range(niter):
        # align_corners default is False, just added to suppress warning
        dPt = torch.nn.functional.grid_sample(im, pt, align_corners=False)

        for k in range(2):  # clamp the final pixel locations
            pt[:, :, :, k] = torch.clamp(pt[:, :, :, k] + dPt[:, k, :, :], -1.0, 1.0)

    # undo the normalization from before, reverse order of operations
    pt = (pt + 1) * 0.5
    for k in range(2):
        pt[:, :, :, k] *= shape[k]

    p = pt[:, :, :, [1, 0]].cpu().numpy().squeeze().T
    return p


def _steps2D_interp_gpu(
    p: torch.Tensor, dP: torch.Tensor, niter: int, device=torch.device("cpu")
) -> np.ndarray:
    """Interpolate 2D steps based on displacement field.

    Supports computation on GPU as well as CPU.

    Parameters
    ----------
    p : torch.Tensor
        Tensor of shape (2, n_points) representing the initial pixel locations.
    dP : torch.Tensor
        Tensor of shape (2, Ly, Lx) representing the displacement field.
    niter : int
        Number of iterations for stepping.
    device : torch.device, optional
        Device to be used for computation, by default uses cpu.

    Returns
    -------
    numpy.ndarray
        Array of shape (n_points, 2) representing the final pixel locations after
        interpolation.
    """
    # dP:torch.Size([2, 1024, 1024]) p:torch.Size([2, 407679]) niter:torch.Size([])
    shape = dP.shape[1:]  # torch.Size([1024, 1024])

    shape = (
        np.array(shape)[[1, 0]].astype("float") - 1
    )  # Y and X dimensions (dP is 2.Ly.Lx), flipped X-1, Y-1
    pt = (
        p[[1, 0]].T.float().to(device).unsqueeze(0).unsqueeze(0)
    )  # p is n_points by 2, so pt is [1 1 2 n_points]
    im = (
        dP[[1, 0]].float().to(device).unsqueeze(0)
    )  # convert flow numpy array to tensor on GPU, add dimension
    # normalize pt between  0 and  1, normalize the flow
    for k in range(2):
        im[:, k, :, :] *= 2.0 / shape[k]
        pt[:, :, :, k] /= shape[k]

    # normalize to between -1 and 1
    pt = pt * 2 - 1

    # here is where the stepping happens
    for t in range(niter):
        # align_corners default is False, just added to suppress warning
        dPt = torch.nn.functional.grid_sample(
            im, pt, align_corners=False
        )  # im: torch.Size([1, 2, 1024, 1024]) pt: torch.Size([1, 1, n, 2])
        # dPt: torch.Size([1, 2, 1, 387550])
        for k in range(2):  # clamp the final pixel locations
            pt[:, :, :, k] = torch.clamp(pt[:, :, :, k] + dPt[:, k, :, :], -1.0, 1.0)

    # undo the normalization from before, reverse order of operations
    pt = (pt + 1) * 0.5
    for k in range(2):
        pt[:, :, :, k] *= shape[k]

    p = pt[:, :, :, [1, 0]].squeeze().T
    return p


@njit("(float32[:,:,:], float32[:,:,:], int32[:,:], int32)", nogil=True)
def _steps2D(p: np.ndarray, dP: np.ndarray, inds: np.ndarray, niter: int) -> np.ndarray:
    """Run dynamics of pixels to recover masks in 2D.

    Euler integration of dynamics dP for niter steps

    Parameters
    ----------
    p : numpy.ndarray
        pixel locations [axis x Ly x Lx] (start at initial meshgrid)

    dP : numpy.ndarray
        flows [axis x Ly x Lx]

    inds : numpy.ndarray
        non-zero pixels to run dynamics on [npixels x 2]

    niter : int
        number of iterations of dynamics to run

    Returns
    -------
    p : numpy.ndarray
        final locations of each pixel after dynamics
    """
    shape = p.shape[1:]
    for t in range(niter):
        for j in range(inds.shape[0]):
            # starting coordinates
            y = inds[j, 0]
            x = inds[j, 1]
            p0, p1 = int(p[0, y, x]), int(p[1, y, x])
            step = dP[:, p0, p1]
            for k in range(p.shape[0]):
                p[k, y, x] = min(shape[k] - 1, max(0, p[k, y, x] + step[k]))
    return p


def follow_flows(
    dP: np.ndarray,
    niter: int = 200,
    interp: bool = True,
    use_gpu: bool = True,
    device: torch.device = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Define pixels and run dynamics to recover masks in 2D.

    Pixels are meshgrid. Only pixels with non-zero cell-probability
    are used (as defined by inds)

    Parameters
    ----------
    dP : numpy.ndarray
        flows [axis x Ly x Lx] or [axis x Lz x Ly x Lx]

    niter : int (optional, default 200)
        number of iterations of dynamics to run

    interp : bool (optional, default True)
        interpolate during 2D dynamics (not available in 3D)
        (in previous versions + paper it was False)

    use_gpu : bool (optional, default False)
        use GPU to run interpolated dynamics (faster than CPU)

    device : torch.device, optional
        Device to be used for computation, by default uses cpu.

    Returns
    -------
    p : numpy.ndarray
        final locations of each pixel after dynamics; [axis x Ly x Lx] or
        [axis x Lz x Ly x Lx]

    inds : numpy.ndarray
        indices of pixels used for dynamics; [axis x Ly x Lx] or [axis x Lz x Ly x Lx]
    """
    shape = np.array(dP.shape[1:]).astype(np.int32)
    niter = np.uint32(niter)

    p = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), indexing="ij")
    p = np.array(p).astype(np.float32)

    inds = np.array(np.nonzero(np.abs(dP[0]) > 1e-3)).astype(np.int32).T
    if inds.ndim < 2 or inds.shape[0] < 5:
        LOG.warning("WARNING: no mask pixels found")
        return p, None

    if not interp:
        p = _steps2D(p, dP.astype(np.float32), inds, niter)

    else:
        p_interp = _steps2D_interp(
            p[:, inds[:, 0], inds[:, 1]],
            dP,
            niter,
            device=device,
        )
        p[:, inds[:, 0], inds[:, 1]] = p_interp
    return p, inds


def follow_flows_gpu(
    dP: torch.Tensor,
    niter: int = 200,
    interp: bool = True,
    use_gpu: bool = True,
    device: torch.device = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Define pixels and run dynamics to recover masks in 2D.

    Pixels are meshgrid. Only pixels with non-zero cell-probability
    are used (as defined by inds)

    Parameters
    ----------
    dP : torch.Tensor
        flows [axis x Ly x Lx] or [axis x Lz x Ly x Lx]

    niter : int
        number of iterations of dynamics to run

    interp : bool
        interpolate during 2D dynamics (not available in 3D)
        (in previous versions + paper it was False)

    use_gpu : bool
        use GPU to run interpolated dynamics (faster than CPU)

    device : torch.device
        Device to be used for computation, by default uses cpu.

    Returns
    -------
    p : torch.device
        final locations of each pixel after dynamics; [axis x Ly x Lx] or
        [axis x Lz x Ly x Lx]

    inds : torch.device
        indices of pixels used for dynamics; [axis x Ly x Lx] or [axis x Lz x Ly x Lx]
    """
    shape = torch.tensor(dP.shape[1:], dtype=torch.int32)
    niter = torch.tensor(niter, dtype=torch.int32)
    plist = [torch.arange(s, dtype=torch.float32) for s in shape]
    p = torch.meshgrid(plist)
    p = torch.stack(p).type(torch.long)
    inds = (torch.abs(dP[0]) > 1e-3).nonzero().to(torch.long)
    if inds.ndim < 2 or inds.shape[0] < 5:
        LOG.warning("WARNING: no mask pixels found")
        return p, None

    if not interp:
        p = _steps2D(p, dP.astype(np.float32), inds, niter)

    else:
        p = p.to(device).long()
        p_interp = _steps2D_interp_gpu(
            p[:, inds[:, 0], inds[:, 1]],
            dP,
            niter,
            device=device,
        )
        # p: torch.Size([2, 1024, 1024]) inds: torch.Size([n, 2])
        # p_interp:torch.Size([2, n])
        inds = inds.long()
        p_interp = p_interp.long()
        p[:, inds[:, 0], inds[:, 1]] = p_interp
    return p, inds


def remove_bad_flow_masks(masks, flows, threshold=0.4, use_gpu=False):
    """Remove masks which have inconsistent flows.

    Uses flow_error to compute flows from predicted masks
    and compare flows to predicted flows from network. Discards
    masks with flow errors greater than the threshold.

    Parameters
    ----------
    masks : numpy.ndarray
        labelled masks, 0=NO masks; 1,2,...=mask labels,
        size [Ly x Lx] or [Lz x Ly x Lx]
    flows : numpy.ndarray
        flows [axis x Ly x Lx] or [axis x Lz x Ly x Lx]
    threshold : float (optional, default 0.4)
        masks with flow error greater than threshold are discarded.
    use_gpu : bool (optional, default False)
        use GPU to run interpolated dynamics (faster than CPU)

    Returns
    -------
    masks : numpy.ndarray
        masks with inconsistent flow masks removed,
        0=NO masks; 1,2,...=mask labels,
        size [Ly x Lx] or [Lz x Ly x Lx]
    """
    merrors, _ = flow_error(masks, flows, use_gpu)
    badi = 1 + (merrors > threshold).nonzero()[0]
    masks[np.isin(masks, badi)] = 0
    return masks


def flow_error(
    maski: np.ndarray,
    dP_net: np.ndarray,
    use_gpu: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Error in flows from predicted masks vs flows predicted by network run on image.

    This function serves to benchmark the quality of masks, it works as follows
    1. The predicted masks are used to create a flow diagram
    2. The mask-flows are compared to the flows that the network predicted

    If there is a discrepancy between the flows, it suggests that the mask is incorrect.
    Masks with flow_errors greater than 0.4 are discarded by default. Setting can be
    changed in Cellpose.eval or CellposeModel.eval.

    Parameters
    ----------
    maski : numpy.ndarray
        masks produced from running dynamics on dP_net,
        where 0=NO masks; 1,2... are mask labels
    dP_net : numpy.ndarray
        ND flows where dP_net.shape[1:] = maski.shape
    use_gpu : bool
        use GPU to run interpolated dynamics (faster than CPU), by default False

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        Tuple of mean squared error between predicted flows and flows from masks,
        and ND flows produced from the predicted masks

    Raises
    ------
    ValueError
        If dP_net.shape[1:] != maski.shape
    """
    if dP_net.shape[1:] != maski.shape:
        raise ValueError("Net flow is not same size as predicted masks")

    # flows predicted from estimated masks
    dP_masks = masks_to_flows(maski, use_gpu=use_gpu)
    # difference between predicted flows vs mask flows
    flow_errors = np.zeros(maski.max())
    for i in range(dP_masks.shape[0]):
        flow_errors += mean(
            (dP_masks[i] - dP_net[i].detach().cpu().numpy() / 5.0) ** 2,
            maski,
            index=np.arange(1, maski.max() + 1),
        )

    return flow_errors, dP_masks


def get_masks(p: np.ndarray, iscell: np.ndarray = None, rpad: int = 20) -> np.ndarray:
    """Create masks using pixel convergence after running dynamics.

    Makes a histogram of final pixel locations p, initializes masks
    at peaks of histogram and extends the masks from the peaks so that
    they include all pixels with more than 2 final pixels p. Discards
    masks with flow errors greater than the threshold.

    Parameters
    ----------
    p : numpy.ndarray
        final locations of each pixel after dynamics,
        size [axis x Ly x Lx] or [axis x Lz x Ly x Lx].
    iscell : numpy.ndarray
        if iscell is not None, set pixels that are
        iscell False to stay in their original location.
    rpad : int (optional, default 20)
        histogram edge padding

    Returns
    -------
    numpy.ndarray
        masks with inconsistent flow masks removed,
        0=NO masks; 1,2,...=mask labels,
        size [Ly x Lx] or [Lz x Ly x Lx]
    """
    pflows = []
    edges = []
    shape0 = p.shape[1:]
    dims = len(p)
    if iscell is not None:
        if dims == 3:
            inds = np.meshgrid(
                np.arange(shape0[0]),
                np.arange(shape0[1]),
                np.arange(shape0[2]),
                indexing="ij",
            )
        elif dims == 2:
            inds = np.meshgrid(
                np.arange(shape0[0]), np.arange(shape0[1]), indexing="ij"
            )
        for i in range(dims):
            p[i, ~iscell] = inds[i][~iscell]

    for i in range(dims):
        pflows.append(p[i].flatten().astype("int32"))
        edges.append(np.arange(-0.5 - rpad, shape0[i] + 0.5 + rpad, 1))

    h, _ = np.histogramdd(tuple(pflows), bins=edges)
    hmax = h.copy()
    for i in range(dims):
        hmax = maximum_filter1d(hmax, 5, axis=i)

    seeds = np.nonzero(np.logical_and(h - hmax > -1e-6, h > 10))
    Nmax = h[seeds]
    isort = np.argsort(Nmax)[::-1]
    for s in seeds:
        s = s[isort]

    pix = list(np.array(seeds).T)

    shape = h.shape
    if dims == 3:
        expand = np.nonzero(np.ones((3, 3, 3)))
    else:
        expand = np.nonzero(np.ones((3, 3)))
    for e in expand:
        e = np.expand_dims(e, 1)

    for iter in range(5):
        for k in range(len(pix)):
            if iter == 0:
                pix[k] = list(pix[k])
            npix = []
            niin = []
            for i, e in enumerate(expand):
                epix = e[:, np.newaxis] + np.expand_dims(pix[k][i], 0) - 1
                epix = epix.flatten()
                niin.append(np.logical_and(epix >= 0, epix < shape[i]))
                npix.append(epix)
            iin = np.all(tuple(niin), axis=0)
            for p in npix:
                p = p[iin]
            newpix = tuple(npix)
            igood = h[newpix] > 2
            for i in range(dims):
                pix[k][i] = newpix[i][igood]
            if iter == 4:
                pix[k] = tuple(pix[k])

    M = np.zeros(h.shape, np.uint32)
    for k in range(len(pix)):
        M[pix[k]] = 1 + k

    for i in range(dims):
        pflows[i] = pflows[i] + rpad
    M0 = M[tuple(pflows)]

    # remove big masks
    uniq, counts = fastremap.unique(M0, return_counts=True)
    big = np.prod(shape0) * 0.4
    bigc = uniq[counts > big]
    if len(bigc) > 0 and (len(bigc) > 1 or bigc[0] != 0):
        M0 = fastremap.mask(M0, bigc)
    fastremap.renumber(M0, in_place=True)  # convenient to guarantee non-skipped labels
    M0 = np.reshape(M0, shape0)
    return M0


def compute_masks(
    dP: np.ndarray,
    cellprob: np.ndarray,
    p: np.ndarray = None,
    niter: int = 200,
    cellprob_threshold: float = 0.0,
    flow_threshold: float = 0.4,
    interp: bool = True,
    do_3D: bool = False,
    min_size: int = 15,
    resize: tuple[int, int] = None,
    use_gpu: bool = False,
    device: torch.device = None,
):
    """Compute cell masks based on displacement field and cell probabilities.

    Parameters
    ----------
    dP : numpy.ndarray
        Array of shape (2, Ly, Lx) representing the displacement field.
    cellprob : numpy.ndarray
        Array of shape (Ly, Lx) representing the cell probabilities.
    p : numpy.ndarray or None, optional
        Array of shape (len(shape), Ly, Lx) representing the initial pixel locations.
        If None, the initial pixel locations will be determined by following flows.
        Defaults to None.
    niter : int, optional
        Number of iterations for stepping. Defaults to 200.
    cellprob_threshold : float, optional
        Threshold value for cell probabilities. Pixels with values higher than this
        threshold
        will be considered as cell clusters. Defaults to 0.0.
    flow_threshold : float or None, optional
        Threshold value for flow. If not None and greater than 0, labels will be
        filtered
        based on the flow magnitude. Defaults to 0.4.
    interp : bool, optional
        Flag indicating whether to interpolate flows during stepping. Defaults to True.
    do_3D : bool, optional
        Flag indicating whether to perform 3D computations. Defaults to False.
    min_size : int, optional
        Minimum size of masks. Masks smaller than this size will be removed. Defaults
        to 15.
    resize : tuple[int, int], optional
        Tuple of (Ly, Lx) representing the desired output size. If None, no resizing
        will be performed.
        Defaults to None.
    use_gpu : bool, optional
        Flag indicating whether to use GPU acceleration. Defaults to False.
    device : torch.device or str, optional
        Device to be used when `use_gpu` is True. If None, a default GPU device will be
        used.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        Tuple of array representing the computed cell masks and
        array representing the final pixel locations after stepping.
    """
    cp_mask = cellprob > cellprob_threshold
    if np.any(cp_mask):  # mask at this point is a cell cluster binary map, not labels
        # follow flows
        if p is None:
            p, inds = follow_flows(
                dP * cp_mask / 5.0,
                niter=niter,
                interp=interp,
                use_gpu=use_gpu,
                device=device,
            )
            if inds is None:
                LOG.info("No cell pixels found.")
                shape = resize if resize is not None else cellprob.shape
                mask = np.zeros(shape, np.uint16)
                p = np.zeros((len(shape), *shape), np.uint16)
                return mask, p

        # calculate masks
        mask = get_masks(p, iscell=cp_mask)

        # flow thresholding factored out of get_masks
        if not do_3D:
            # shape0 = p.shape[1:]
            if mask.max() > 0 and flow_threshold is not None and flow_threshold > 0:
                # make sure labels are unique at output of get_masks
                mask = remove_bad_flow_masks(
                    mask, dP, threshold=flow_threshold, use_gpu=use_gpu
                )

        if resize is not None:
            # if verbose:
            #    dynamics_logger.info(f'resizing output with resize = {resize}')
            if mask.max() > 2**16 - 1:
                recast = True
                mask = mask.astype(np.float32)
            else:
                recast = False
                mask = mask.astype(np.uint16)
            mask = transforms.resize_image(
                mask, resize[0], resize[1], interpolation=cv2.INTER_NEAREST
            )
            if recast:
                mask = mask.astype(np.uint32)
            Ly, Lx = mask.shape
        elif mask.max() < 2**16:
            mask = mask.astype(np.uint16)

    else:  # nothing to compute, just make it compatible
        LOG.info("No cell pixels found.")
        shape = resize if resize is not None else cellprob.shape
        mask = np.zeros(shape, np.uint16)
        p = np.zeros((len(shape), *shape), np.uint16)
        return mask, p
    # moving the cleanup to the end helps avoid some bugs arising from scaling...
    # maybe better would be to rescale the min_size and hole_size parameters to do the
    mask = common_utils.fill_holes_and_remove_small_masks(mask, min_size=min_size)

    if mask.dtype == np.uint32:
        LOG.warning("more than 65535 masks in image, masks returned as np.uint32")

    return mask, p


def compute_masks_flow(
    dP: torch.Tensor,
    cellprob: torch.Tensor,
    p: torch.Tensor = None,
    niter: int = 200,
    cellprob_threshold: float = 0.0,
    flow_threshold: float = 0.4,
    interp: bool = True,
    do_3D: bool = False,
    min_size: int = 15,
    resize: tuple[int, int] = None,
    use_gpu: bool = False,
    device: torch.device = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute cell masks.

    Based on displacement field and cell probabilities using GPU
    acceleration.

    Parameters
    ----------
    dP : torch.Tensor
        Tensor of shape (2, Ly, Lx) representing the displacement field.
    cellprob : torch.Tensor
        Tensor of shape (Ly, Lx) representing the cell probabilities.
    p : torch.Tensor or None, optional
        Tensor of shape (len(shape), Ly, Lx) representing the initial pixel locations.
        If None, the initial pixel locations will be determined by following flows.
        Defaults to None.
    niter : int, optional
        Number of iterations for stepping. Defaults to 200.
    cellprob_threshold : float, optional
        Threshold value for cell probabilities. Pixels with values higher than thi
        threshold
        will be considered as cell clusters. Defaults to 0.0.
    flow_threshold : float, optional
        Threshold value for flow. If not None and greater than 0, labels will be
        filtered based on the flow magnitude. Defaults to 0.4.
    interp : bool, optional
        Flag indicating whether to interpolate flows during stepping. Defaults to True.
    do_3D : bool, optional
        Flag indicating whether to perform 3D computations. Defaults to False.
    min_size : int, optional
        Minimum size of masks. Masks smaller than this size will be removed. Default
        to 15.
    resize : tuple[int, int], optional
        Tuple of (Ly, Lx) representing the desired output size. If None, no resizing
        will be performed. Defaults to None.
    use_gpu : bool, optional
        Flag indicating whether to use GPU acceleration. Defaults to False.
    device : torch.device or str, optional
        Device to be used when `use_gpu` is True. If None, a default GPU device will b
        used.

    Returns
    -------
    numpy.ndarray
        Array of shape (len(shape), Ly, Lx) representing the final pixel location
        after stepping.
    numpy.ndarray
        Array of shape (Ly, Lx) representing the computed cell masks.
    """
    cp_mask = cellprob > cellprob_threshold
    # cp_mask_flag = 0
    if torch.any(
        cp_mask
    ):  # mask at this point is a cell cluster binary map, not labels
        # cp_mask_flag = 1
        # follow flows
        if p is None:
            p, inds = follow_flows_gpu(
                dP * cp_mask / 5.0,
                niter=niter,
                interp=interp,
                use_gpu=use_gpu,
                device=device,
            )
            if inds is None:
                LOG.info("No cell pixels found.")
                shape = resize if resize is not None else cellprob.shape
                mask = np.zeros(shape, dtype=bool)
                p = np.zeros((len(shape), *shape), dtype=bool)
                return p, mask

        # calculate masks
        p = p.cpu().numpy()
        cp_mask = cp_mask.cpu().numpy()
        return p, cp_mask

    else:  # nothing to compute, just make it compatible
        LOG.info("No cell pixels found.")
        shape = resize if resize is not None else cellprob.shape
        mask = np.zeros(shape, dtype=bool)
        p = np.zeros((len(shape), *shape), dtype=bool)
        return p, mask


def steps2D_interp_gpu_vectorized(p, dP, niter, device=torch.device("cpu")):
    """Interpolate 2D steps based on displacement field.

    Vectorized version. Supports computation on GPU as well as CPU.

    Parameters
    ----------
    p : torch.Tensor
        Tensor of shape (2, n_points) representing the initial pixel locations.
    dP : torch.Tensor
        Tensor of shape (2, Ly, Lx) representing the displacement field.
    niter : int
        Number of iterations for stepping.
    device : torch.device, optional
        Device to be used for computation, by default uses cpu.

    Returns
    -------
    numpy.ndarray
        Array of shape (n_points, 2) representing the final pixel locations after
        interpolation.
    """
    shape = dP.shape[-2:]
    # swap X and Y dims and remove batch dim
    factor = (shape[-1] - 1, shape[-2] - 1)
    pt = torch.permute(p[:, [1, 0]], (0, 2, 1)).unsqueeze(1).float().to(device)
    im = dP[:, [1, 0]].float().to(device)

    # normalize pt between  0 and  1, normalize the flow
    for k in range(2):
        im[:, k, :, :] *= 2.0 / factor[k]
        pt[:, :, :, k] /= factor[k]

    # normalize to between -1 and 1
    pt = pt * 2 - 1

    # here is where the stepping happens
    for t in range(niter):
        # align_corners default is False, just added to suppress warning
        dPt = torch.nn.functional.grid_sample(
            im, pt, align_corners=False
        )  # im: torch.Size([1, 2, 1024, 1024]) pt: torch.Size([1, 1, n, 2])
        # dPt: torch.Size([1, 2, 1, 387550])
        for k in range(2):  # clamp the final pixel locations
            pt[:, :, :, k] = torch.clamp(pt[:, :, :, k] + dPt[:, k, :, :], -1.0, 1.0)

    # undo the normalization from before, reverse order of operations
    pt = (pt + 1) * 0.5

    for k in range(2):
        pt[:, :, :, k] *= factor[k]

    p = torch.permute(pt[:, :, :, [1, 0]].squeeze(1), (0, 2, 1))

    return p


def follow_flows_gpu_vectorized(
    dP: torch.Tensor,
    niter: int = 200,
    interp: bool = True,
    use_gpu: bool = True,
    device: torch.device = torch.device("cpu"),
) -> tuple[torch.Tensor, torch.Tensor]:
    """Define pixels and run dynamics to recover masks in 2D.

    Vectorized version.

    Pixels are meshgrid. Only pixels with non-zero cell-probability
    are used (as defined by inds)

    Parameters
    ----------
    dP : float32, 3D or 4D array
        flows [batch x axis x Ly x Lx]

    niter : int (optional, default 200)
        number of iterations of dynamics to run

    interp : bool (optional, default True)
        interpolate during 2D dynamics (not available in 3D)
        (in previous versions + paper it was False)

    use_gpu : bool (optional, default False)
        use GPU to run interpolated dynamics (faster than CPU)

    device : torch.device
        Device to be used for computation, by default uses cpu.

    Returns
    -------
    p : float32, 3D array
        final locations of each pixel after dynamics; [batch x axis x Ly x Lx]

    inds : int32, 3D array
        list of indices of pixels used for dynamics; List[[axis x Ly x Lx]]
        len(inds) = batch_size
    """
    # NOTE: shape should be the same for all tiles
    batch_size = dP.shape[0]
    shape = torch.tensor(dP.shape[-2:], dtype=torch.int32)
    niter = torch.tensor(niter, dtype=torch.int32)
    p = [torch.arange(s, dtype=torch.float32, device=device) for s in shape]
    p = torch.meshgrid(p)
    p = torch.stack(p).type(torch.long)

    p_prelim_list = []
    inds = []
    for b in range(batch_size):
        ind = (torch.abs(dP[b, 0, ...]) > 1e-3).nonzero().to(torch.long)
        p_prelim_list.append(p[:, ind[:, 0], ind[:, 1]])  # type: ignore
        inds.append(ind)

    # Need to fixed the max value for the vectorized p-value that gets
    # sent to steps2D_interp_gpu_vectorized
    # This will ensure a fixed-size input for p
    max_size = -1
    for x in p_prelim_list:
        max_size = max(max_size, x.shape[1])
    p_vec_initial = torch.zeros((len(p_prelim_list), 2, max_size))
    for i, _ in enumerate(p_prelim_list):
        length = p_prelim_list[i].shape[1]
        p_vec_initial[i, :, :length] = p_prelim_list[i]

    p_interp = steps2D_interp_gpu_vectorized(
        p_vec_initial,
        dP,
        niter,
        device=device,
    )
    p_interp = p_interp.long().cpu()
    p_vec_final = torch.zeros((batch_size, 2, shape[0], shape[1])).long()
    for b in range(batch_size):
        ind = inds[b].long()
        length = ind.shape[0]
        p_vec_final[b, ...] = p
        p_vec_final[b, :, ind[:, 0], ind[:, 1]] = p_interp[b, :, :length]
    return p_vec_final, inds


def compute_masks_flow_vectorized(
    dP,
    cellprob,
    p=None,
    niter=200,
    cellprob_threshold=0.0,
    flow_threshold=0.4,
    interp=True,
    do_3D=False,
    min_size=15,
    resize=None,
    use_gpu=False,
    device=None,
):
    """Compute cell masks.

    Based on displacement field and cell probabilities using GPU
    acceleration.

    Parameters
    ----------
    dP : torch.Tensor
        Tensor of shape (2, Ly, Lx) representing the displacement field.
    cellprob : torch.Tensor
        Tensor of shape (Ly, Lx) representing the cell probabilities.
    p : torch.Tensor or None, optional
        Tensor of shape (len(shape), Ly, Lx) representing the initial pixel locations.
        If None, the initial pixel locations will be determined by following flows.
        Defaults to None.
    niter : int, optional
        Number of iterations for stepping. Defaults to 200.
    cellprob_threshold : float, optional
        Threshold value for cell probabilities. Pixels with values higher than thi
        threshold
        will be considered as cell clusters. Defaults to 0.0.
    flow_threshold : float, optional
        Threshold value for flow. If not None and greater than 0, labels will be
        filtered based on the flow magnitude. Defaults to 0.4.
    interp : bool, optional
        Flag indicating whether to interpolate flows during stepping. Defaults to True.
    do_3D : bool, optional
        Flag indicating whether to perform 3D computations. Defaults to False.
    min_size : int, optional
        Minimum size of masks. Masks smaller than this size will be removed. Default
        to 15.
    resize : tuple or None, optional
        Tuple of (Ly, Lx) representing the desired output size. If None, no resizing
        will be performed. Defaults to None.
    use_gpu : bool, optional
        Flag indicating whether to use GPU acceleration. Defaults to False.
    device : torch.device or str, optional
        Device to be used when `use_gpu` is True. If None, a default GPU device will b
        used.

    Returns
    -------
    numpy.ndarray
        Array of shape (len(shape), Ly, Lx) representing the final pixel location
        after stepping.
    numpy.ndarray
        Array of shape (Ly, Lx) representing the computed cell masks.
    """
    cp_mask = cellprob > cellprob_threshold
    # cp_mask_flag = 0
    if torch.any(
        cp_mask
    ):  # mask at this point is a cell cluster binary map, not labels
        # cp_mask_flag = 1
        # follow flows
        if p is None:
            p, inds = follow_flows_gpu_vectorized(
                dP * cp_mask.unsqueeze(1) / 5.0,
                niter=niter,
                interp=interp,
                use_gpu=use_gpu,
                device=device,
            )
            if inds is None:
                LOG.info("No cell pixels found.")
                shape = resize if resize is not None else cellprob.shape
                mask = np.zeros(shape, np.uint16)
                p = np.zeros((len(shape), *shape), np.uint16)
                return mask, p

        # calculate masks
        p = p.cpu().numpy()
        cp_mask = cp_mask.cpu().numpy()
        dP = dP.cpu().numpy()
        return p, cp_mask
    else:
        LOG.info("No cell pixels found.")
        shape = resize if resize is not None else cellprob.shape
        cp_mask = np.zeros(shape, dtype=bool)
        p = np.zeros(
            (len(cellprob), 2, cellprob.shape[1], cellprob.shape[2]), dtype=bool
        )
        return p, cp_mask


def compute_masks_rm_flow(
    mask: np.ndarray,
    dP: np.ndarray,
    p: np.ndarray,
    flow_threshold: float,
    use_gpu: bool,
    device: str,
    do_3D: bool,
) -> np.ndarray:
    """Apply flow-based post-processing to the input mask.

    Parameters
    ----------
    mask : numpy.ndarray
        The input mask array.
    dP : numpy.ndarray
        The dynamics array.
    p : numpy.ndarray
        The flow array.
    flow_threshold : float or None
        The threshold value for flow-based post-processing. If None, no post-processin
        is performed.
    use_gpu : bool
        A flag indicating whether to use GPU acceleration for post-processing.
    device : str or None
        The device identifier for GPU acceleration.
    do_3D : bool
        A flag indicating whether to perform 3D post-processing.

    Returns
    -------
    numpy.ndarray
        The mask array after applying flow-based post-processing.
    """
    if not do_3D:
        # shape0 = p.shape[1:]
        if mask.max() > 0 and flow_threshold is not None and flow_threshold > 0:
            # make sure labels are unique at output of get_masks
            mask = remove_bad_flow_masks(
                mask,
                dP,
                threshold=flow_threshold,
                use_gpu=use_gpu,
            )

    return mask


def compute_masks_fl_rm(
    mask: np.ndarray, resize: tuple[int, int], min_size: int
) -> np.ndarray:
    """Compute masks and perform post-processing operations.

    Parameters
    ----------
    mask : numpy.ndarray
        The input mask array.
    resize : tuple[int, int]
        The desired shape for resizing the mask. If None, no resizing is performed.
    min_size : int
        The minimum size threshold for removing small masks.

    Returns
    -------
    numpy.ndarray
        The computed and processed mask array.
    """
    if resize is not None:
        if mask.max() > 2**16 - 1:
            recast = True
            mask = mask.astype(np.float32)
        else:
            recast = False
            mask = mask.astype(np.uint16)
        mask = transforms.resize_image(
            mask, resize[0], resize[1], interpolation=cv2.INTER_NEAREST
        )
        if recast:
            mask = mask.astype(np.uint32)
        Ly, Lx = mask.shape
    elif mask.max() < 2**16:
        mask = mask.astype(np.uint16)

    # moving the cleanup to the end helps avoid some bugs arising from scaling...
    # maybe better would be to rescale the min_size and hole_size parameters to do the
    # cleanup at the prediction scale, or switch depending on which one is bigger...
    mask = common_utils.fill_holes_and_remove_small_masks(mask, min_size=min_size)

    # if mask.dtype==np.uint32:
    #     dynamics_logger.warning('more than 65535 masks in image, \
    #     masks returned as np.uint32')

    return mask


def postprocess(
    model_output,
    vectorized=True,
    segmentation_type="instance",
    cellprob_threshold=0.2,
    flow_threshold=0.55,
):
    """Compute final masks from the model output.

    Parameters
    ----------
    model_output : np.ndarray
        Ouput from the model.

    Returns
    -------
    List
        Phenotype masks.
    """
    yf = model_output
    if segmentation_type == "semantic":
        softmax = torch.nn.Softmax(dim=1)
        sem_output_softmax = softmax(yf[:, 2:, :, :])
        cellprob = 1 - sem_output_softmax[:, 0, :, :]
    else:
        cellprob = yf[:, 2, :, :]

    dP = yf[:, :2, :, :]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not vectorized:
        # Process each sample individually
        results = [
            compute_masks_flow(
                dp,
                cp,
                niter=200,
                cellprob_threshold=cellprob_threshold,
                flow_threshold=flow_threshold,
                interp=True,
                resize=None,
                use_gpu=True,
                device=device,
            )
            for dp, cp in zip(dP, cellprob)
        ]
        ip, imask = zip(*results)
    else:
        p, cp_mask = compute_masks_flow_vectorized(
            dP,
            cellprob,
            niter=200,
            cellprob_threshold=cellprob_threshold,
            flow_threshold=flow_threshold,
            interp=True,
            resize=None,
            use_gpu=True,
            device=device,
        )
        ip = [p[i, ...] for i in range(dP.shape[0])]
        imask = [cp_mask[i, ...] for i in range(dP.shape[0])]

    final_masks = []
    for p, mask, dp in zip(ip, imask, dP):
        maski = get_masks(p, iscell=mask)
        cleaned_mask = compute_masks_rm_flow(maski, dp, p, 0.5, True, device, False)
        final_mask = compute_masks_fl_rm(cleaned_mask, None, 15)
        final_masks.append(final_mask)

    # phenotype_masks = []
    # for mask, sem in zip(final_masks, sem_output_max):
    #     phenotype_mask = create_panoptic_mask_from_instance_and_semantic_masks(
    #         mask, sem
    #     )
    #     phenotype_masks.append(phenotype_mask)

    return torch.from_numpy(np.stack(final_masks))


def get_dataset_celldiam_stats(dataset_path: str) -> Tuple[np.array, np.float64]:
    """Generate cell diameter statistics for the dataset.

    Parameters
    ----------
    dataset_path : str
        Path to the dataset.

    Returns
    -------
    tuple
        Mean of median diameters of cells in images in the dataset,
        median diameters of cells in images
    """
    label_paths = glob(os.path.join(dataset_path, "*.tif"))
    diam_meds = []
    for label_path in tqdm(label_paths):
        label = tifffile.imread(label_path)
        binary_mask = label[0]
        diam = common_utils.get_diameters(binary_mask)
        diam_meds.append(diam)
    diam_meds = np.array(diam_meds)
    diam_meds[diam_meds < 5] = 5.0  # type: ignore
    diam_mean = np.mean(diam_meds)
    return diam_mean, diam_meds


@cli.command()
@click.argument("dataset_path", type=click.Path(exists=True))
@click.option("--use-gpu/--no-gpu", default=True, help="Use GPU for flow computation")
def create_flows(dataset_path: str, use_gpu: bool):
    """Generate flow labels for the dataset.

    Parameters
    ----------
    dataset_path : str
        Path to the directory containing PNG mask files
    use_gpu : bool
        Use GPU for flow computation

    Examples
    --------
        python cellpose_utils.py create-flows /path/to/masks/directory
        python cellpose_utils.py create-flows /path/to/masks/directory --no-gpu
    """
    click.echo(f"Generating flows for masks in {dataset_path}")
    tile_paths = glob(os.path.join(dataset_path, "*.png"))
    for file_path in tqdm(tile_paths):
        mask = imageio.v3.imread(file_path)
        labels_to_flows(
            [mask],
            files=[file_path],
            use_gpu=use_gpu,
        )
    click.echo("Flow generation complete!")


@cli.command()
@click.argument("dataset_path", type=click.Path(exists=True))
def get_celldiam_stats(dataset_path: str):
    """Generate cell diameter statistics for the dataset.

    Parameters
    ----------
    dataset_path : str
        Path to the directory containing TIF flow files

    Examples
    --------
        python cellpose_utils.py get-celldiam-stats /path/to/flows/directory
    """
    click.echo(f"Computing cell diameter statistics for {dataset_path}")
    diam_mean, diam_meds = get_dataset_celldiam_stats(dataset_path)
    click.echo(f"Mean of median diameters: {diam_mean:.2f}")
    click.echo(f"Median of median diameters: {np.median(diam_meds):.2f}")


@cli.command()
@click.argument("data_path", type=click.Path(exists=True))
@click.option(
    "--split",
    type=click.Choice(["train", "val", "test"]),
    default="val",
    help="Dataset split to process",
)
def create_csv(data_path: str, split: str):
    """Create CSV file mapping images to their corresponding flow masks.

    This assumes that the dataset is organized in a specific structure:
    <dataset_path>/<split>/fovs/*.png
    <dataset_path>/<split>/labels/flows_*.tif

    Parameters
    ----------
    data_path : str
        Base path to the dataset directory
    split : str
        Dataset split to process (train/val/test)

    Examples
    --------
        python cellpose_utils.py create-csv /path/to/dataset --split val
    """
    click.echo(f"Creating CSV for {split} split in {data_path}")

    image_path = glob(os.path.join(data_path, f"{split}/fovs/*.png"))
    mask_path = []

    for img in tqdm(image_path, desc="Processing images"):
        img_name = Path(img).stem
        mask_file = os.path.join(
            str(Path(img).parent.parent),
            "labels",
            f"flows_{img_name.split('img_')[1]}.tif",
        )
        mask_path.append(str(mask_file))

    df = pd.DataFrame(list(zip(image_path, mask_path)), columns=["image", "mask"])
    output_path = os.path.join(data_path, f"{split}.csv")
    df.to_csv(output_path, index=False)
    click.echo(f"CSV file created at {output_path}")


if __name__ == "__main__":
    cli()
