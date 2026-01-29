"""Module containing utility functions for processing output of multi-task model."""

import numpy as np
import scipy.ndimage.filters as filters
from scipy.ndimage import binary_fill_holes
from skimage.measure import label
from skimage.morphology import remove_small_objects
from skimage.segmentation import clear_border, watershed


def post_process_mask(mask: np.ndarray, det_prob: np.ndarray) -> np.ndarray:
    """Perform post processing to generate semantic mask.

    Requires segmented mask and detection probabilities.

    Parameters
    ----------
    mask : numpy.ndarray
        Segmented mask.
    det_prob : numpy.ndarray
        Detection probabilities.

    Returns
    -------
    numpy.ndarray
        Generated semantic mask.
    """
    seg_mask = mask.copy()
    seg_mask[seg_mask == 1] = 0  # remove boundary class
    seg_mask[seg_mask == 2] = 1  # binarize

    processed_mask = remove_small_objects(
        seg_mask.astype("bool"), min_size=96, connectivity=4
    )
    region_mask = binary_fill_holes(processed_mask).astype("uint8")
    final_seg_mask = clear_border(region_mask)

    dets = det_prob.copy()
    # remove spurious detections outside nuclei mask
    for i in range(1, len(dets)):
        dets[i][final_seg_mask != 1] = 0

    det_points = non_max_suppression_multi_class(dets)
    labels = watershed(
        image=final_seg_mask,
        markers=label(det_points),
        mask=final_seg_mask,
        watershed_line=True,
        connectivity=1,
        compactness=0,
    )
    return labels, det_points


def get_local_max_2s_arr(
    detection_mask_softmax: np.ndarray,
    neighborhood_size: int = 10,
    threshold: float = 0.7,
) -> np.ndarray:
    """Detect local maxima in a 2D array of softmax predictions.

    Parameters
    ----------
    detection_mask_softmax : numpy.ndarray
        Array of detection softmax predictions.
    neighborhood_size : int, optional
        Size of neighborhood used for max-min filtering, by default 10.
    threshold : float, optional
        Threshold for difference betwen max-min values, by default 0.7.

    Returns
    -------
    numpy.ndarray
        Array with values indicating the positions of local maxima.
    """
    data_max = filters.maximum_filter(detection_mask_softmax, neighborhood_size)
    maxima = detection_mask_softmax == data_max
    data_min = filters.minimum_filter(detection_mask_softmax, neighborhood_size)
    diff = (data_max - data_min) > threshold
    maxima[diff == 0] = 0
    return maxima


def non_max_suppression_multi_class(softmax_predictions: np.ndarray) -> np.ndarray:
    """Perform NMS for multi-class predictions.

    Parameters
    ----------
    softmax_predictions : numpy.ndarray
        Model predictions post softmax. Has the shape (h,w,c)

    Returns
    -------
    numpy.ndarray
        Output containing classified predictions. Has the shape (h,w)
    """
    # input HxWxC
    # Output HxW
    THRESHOLD = 0.0005
    NEIGHB_SIZE = 15
    softmax_predictions = np.moveaxis(softmax_predictions, 0, -1)
    H, W, C = np.shape(softmax_predictions)

    all_classes_nms = np.zeros([H, W, C], dtype="uint8")
    for i in range(1, C):
        input = 1 - softmax_predictions[..., 0]
        local_maxima_bg = get_local_max_2s_arr(
            input, neighborhood_size=NEIGHB_SIZE, threshold=THRESHOLD
        )
        all_classes_nms[:, :, i] = local_maxima_bg

    out_softmax_nms = softmax_predictions * all_classes_nms
    return np.argmax(out_softmax_nms, axis=2)
