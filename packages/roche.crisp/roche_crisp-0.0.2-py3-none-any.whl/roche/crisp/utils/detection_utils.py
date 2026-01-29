"""Utility functions for postprocessing of detection predictions."""

from typing import Tuple

import numpy as np
import scipy.ndimage.filters as filters


class DetectionUtils:
    """Utility functions for postprocessing of detection predictions."""

    @staticmethod
    def __get_local_max_2s_arr(
        detection_mask_softmax: np.ndarray,
        neighborhood_size: int = 10,
        threshold: float = 0.7,
    ) -> np.ndarray:
        """Get local maxima from given array.

        Parameters
        ----------
        detection_mask_softmax : numpy.ndarray
            array with mask to calculate local maximum
        neighborhood_size : int, optional
            distance from each maximum, by default 10
        threshold : float, optional
            threshold of values to ignore, by default 0.7

        Returns
        -------
        numpy.ndarray
            array of local maximas
        """
        data_max = filters.maximum_filter(detection_mask_softmax, neighborhood_size)
        maxima = detection_mask_softmax == data_max
        data_min = filters.minimum_filter(detection_mask_softmax, neighborhood_size)
        diff = (data_max - data_min) > threshold
        maxima[diff == 0] = 0
        return maxima

    @staticmethod
    def non_max_suppression_multi_class(
        softmax_predictions: np.ndarray, neighb: int = 10, threshold: float = 0.7
    ) -> Tuple[np.ndarray, ...]:
        """Perform non-max supression.

        Helps find non-overlapping cells.

        Parameters
        ----------
        softmax_predictions : numpy.ndarray
            array with prediction
        neighb : int, optional
            distance from each maximum, by default 10
        threshold : float, optional
            threshold of values to ignore, by default 0.7

        Returns
        -------
        Tuple[numpy.ndarray,...]
            return tupple of arrays: predicted cell max, local maximas
        """
        softmax_predictions = np.moveaxis(softmax_predictions, 0, -1)
        C = softmax_predictions.shape[2]
        softmax_predictions = np.asarray(softmax_predictions)
        input = 1 - softmax_predictions[..., 0]
        local_maxima_bg = DetectionUtils.__get_local_max_2s_arr(
            input, neighborhood_size=neighb, threshold=threshold
        )

        all_classes_nms = np.repeat(local_maxima_bg[:, :, np.newaxis], C, axis=2)
        out_softmax_nms = softmax_predictions * all_classes_nms

        pred_cell_mask = np.argmax(out_softmax_nms, axis=2)
        max_prob = np.amax(out_softmax_nms, axis=2)
        return pred_cell_mask, max_prob
