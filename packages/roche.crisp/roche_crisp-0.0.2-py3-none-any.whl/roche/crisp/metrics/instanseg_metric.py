"""Module for InstanSeg metrics."""

from typing import Union

import numpy as np
import pandas as pd
from stardist import matching
from tqdm import tqdm


def _robust_f1_mean_calculator(nan_list: Union[list, np.ndarray]):
    """Calculate the robust F1 mean."""
    nan_list = np.array(nan_list)
    if len(nan_list) == 0:
        return np.nan
    elif np.isnan(nan_list).all():
        return np.nan
    else:
        return np.nanmean(nan_list)


def robust_average_precision(labels, predicted, threshold):
    """Compute the robust average precision.

    Parameters
    ----------
    labels : list
        List of ground truth masks.
    predicted : list
        List of predicted masks.
    threshold : float
        Threshold for the average precision.

    Returns
    -------
    float
        Robust average precision.
    """
    for i in range(len(labels)):
        if labels[i].min() < 0 and not (labels[i] < 0).all():
            labels[i][labels[i] < 0] = 0  # sparse labels
            predicted[i][labels[i] < 0] = 0

    y_true = [
        labels[i].astype(np.int32)
        for i, lbl in enumerate(labels)
        if labels[i].min() >= 0 and labels[i].max() > 0
    ]
    y_pred = [
        predicted[i].astype(np.int32)
        for i, lbl in enumerate(labels)
        if labels[i].min() >= 0 and labels[i].max() > 0
    ]

    if len(y_true) == 0:
        return np.nan

    stats = matching.matching_dataset(
        y_true,
        y_pred,
        thresh=threshold,
        show_progress=False,
    )
    if isinstance(threshold, float) and threshold == 0.5:
        return stats.f1

    f1i = [stat.f1 for stat in stats]
    return np.nanmean(f1i)


def compute_and_export_metrics(
    gt_masks,
    pred_masks,
    output_path,
    target,
    return_metrics=False,
    show_progress=False,
    verbose=True,
):
    """Compute and export metrics for InstanSeg.

    Parameters
    ----------
    gt_masks : list
        List of ground truth masks.
    """
    taus = [0.5, 0.6, 0.7, 0.8, 0.9]
    stats = [
        matching.matching_dataset(
            gt_masks, pred_masks, thresh=t, show_progress=False, by_image=False
        )
        for t in tqdm(taus, disable=not show_progress)
    ]
    df_list = []

    for stat in stats:
        df_list.append(pd.DataFrame([stat]))
    df = pd.concat(df_list, ignore_index=True)

    mean_f1 = df[["thresh", "f1"]].iloc[:].mean()["f1"]
    mean_panoptic_quality = (
        df[["thresh", "panoptic_quality"]].iloc[:].mean()["panoptic_quality"]
    )
    panoptic_quality_05 = df[["thresh", "panoptic_quality"]].iloc[0]["panoptic_quality"]
    f1_05 = df[["thresh", "f1"]].iloc[0]["f1"]

    df["mean_f1"] = mean_f1
    df["f1_05"] = f1_05
    df["mean_PQ"] = mean_panoptic_quality
    df["SQ"] = panoptic_quality_05 / f1_05

    if verbose:
        print("Target:", target)
        print("Mean f1 score: ", mean_f1)
        print("f1 score at 0.5: ", f1_05)
        print("SQ: ", panoptic_quality_05 / f1_05)

    if return_metrics:
        return mean_f1, f1_05, panoptic_quality_05 / f1_05

    if output_path is not None:
        df.to_csv(output_path / str(target + "_matching_metrics.csv"))
