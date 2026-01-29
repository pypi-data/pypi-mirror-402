"""Metrics for detection and segmentation evaluation."""

import numpy as np
import scipy
import torch
import torch.nn.functional as F
from scipy.spatial.distance import cdist

EPS = 1e-10


def compute_detection_accuracy(pred, gt, radius):
    """Compute detection accuracy metrics.

    Parameters
    ----------
    pred : array_like or int
        Predicted values. If not already an ndarray, it will be converted to one.
    gt : array_like or int
        Ground truth values. If not already an ndarray, it will be converted to one.
    radius : float
        Radius within which a predicted point is considered a true positive.

    Returns
    -------
    TP : float
        True positives.
    FP : float
        False positives.
    FN : float
        False negatives.
    Ng : int
        Number of ground truth points.
    """
    if not isinstance(pred, np.ndarray):
        pred = np.array(pred)
    if not isinstance(gt, np.ndarray):
        gt = np.array(gt)

    pred_points = np.argwhere(pred != 0)
    Np = pred_points.shape[0]
    gt_points = np.argwhere(gt != 0)
    Ng = gt_points.shape[0]

    TP = 0.0
    FN = 0.0
    for i in range(Ng):  # for each gt point, find the nearest pred point
        if np.size(pred_points) == 0:
            FN += 1
            continue
        gt_point = gt_points[i, :]
        dist = np.linalg.norm(pred_points - gt_point, axis=1)
        if (
            np.min(dist) < radius
        ):  # the nearest pred point is in the radius of the gt point
            pred_idx = np.argmin(dist)
            pred_points = np.delete(pred_points, pred_idx, axis=0)  # delete the TP
            TP += 1
        else:  # the nearest pred point is not in the radius
            FN += 1

    FP = Np - TP

    return TP, FP, FN, Ng


def get_confusion_matrix(pred, target, num_classes):
    """Compute the confusion matrix.

    Parameters
    ----------
    pred : array_like
        Predicted values.
    target : array_like
        Target values.
    num_classes : int
        Number of classes.

    Returns
    -------
    cm : ndarray
        Confusion matrix of shape (num_classes, num_classes).
    """
    mask = (target >= 0) & (target < num_classes)
    cm = np.bincount(
        num_classes * target[mask].astype(int) + pred[mask],
        minlength=num_classes**2,
    ).reshape(num_classes, num_classes)
    return cm


def evaluate(cm):
    """Evaluate performance metrics based on the confusion matrix.

    Parameters
    ----------
    cm : array_like
        Confusion matrix.

    Returns
    -------
    mean_iou : float
        Mean Intersection over Union (IoU) score.
    mean_dice : float
        Mean Dice coefficient.
    pixel_acc : float
        Pixel accuracy.
    """
    tp = np.diag(cm)
    tp_fp = cm.sum(axis=1)
    tp_fn = cm.sum(axis=0)

    dice_score = (2 * tp) / (tp_fp + tp_fn)
    mean_dice = np.nanmean(dice_score)
    # we use nanmean rather than mean inorder to ignore any nan values in the dice
    iou = tp / (tp_fp + tp_fn - tp)  # Jaccard Index
    mean_iou = np.nanmean(iou)

    pixel_acc = tp.sum() / cm.sum()

    return mean_iou, mean_dice, pixel_acc


def AJI_fast(gt, pred_arr):
    """Calculate the Aggregated Jaccard Index (AJI) score.

    Parameters
    ----------
    gt : array_like
        Ground truth values.
    pred_arr : array_like
        Predicted values.

    Returns
    -------
    aji : float
        Aggregated Jaccard Index (AJI) score.
    """
    gs, g_areas = np.unique(gt, return_counts=True)
    assert np.all(gs == np.arange(len(gs)))
    ss, s_areas = np.unique(pred_arr, return_counts=True)
    assert np.all(ss == np.arange(len(ss)))

    i_idx, i_cnt = np.unique(
        np.concatenate([gt.reshape(1, -1), pred_arr.reshape(1, -1)]),
        return_counts=True,
        axis=1,
    )
    i_arr = np.zeros(shape=(len(gs), len(ss)), dtype=np.int)
    i_arr[i_idx[0], i_idx[1]] += i_cnt
    u_arr = g_areas.reshape(-1, 1) + s_areas.reshape(1, -1) - i_arr
    iou_arr = 1.0 * i_arr / u_arr

    i_arr = i_arr[1:, 1:]
    u_arr = u_arr[1:, 1:]
    iou_arr = iou_arr[1:, 1:]

    if iou_arr.shape[1] == 0:
        return 0

    j = np.argmax(iou_arr, axis=1)

    c = np.sum(i_arr[np.arange(len(gs) - 1), j])
    u = np.sum(u_arr[np.arange(len(gs) - 1), j])
    used = np.zeros(shape=(len(ss) - 1), dtype=np.int)
    used[j] = 1
    u += np.sum(s_areas[1:] * (1 - used))
    return 1.0 * c / u


def dice_score(logits, targets, thresh):
    """Compute the Dice score for binary segmentation.

    Parameters
    ----------
    logits : torch.Tensor
        Logits predicted by the model.
    targets : torch.Tensor
        Target ground truth.
    thresh : float
        Threshold for binarizing the logits.

    Returns
    -------
    dice : float
        Dice score.
    """
    hard_preds = (F.sigmoid(logits) > thresh).float()
    m1 = hard_preds.view(-1)  # Flatten
    m2 = targets.view(-1)  # Flatten
    intersection = (m1 * m2).sum()
    return (2.0 * intersection) / (m1.sum() + m2.sum() + 1e-6)


def dice_coeff(pred, target, smooth=0):
    """Compute the Dice coefficient for binary or multi-class segmentation.

    Parameters
    ----------
    pred : torch.Tensor
        Predicted segmentation.
    target : torch.Tensor
        Target ground truth.
    smooth : float, optional
        Smoothing factor to prevent division by zero, by default 0.

    Returns
    -------
    dice : float
        Dice coefficient.
    """
    num = pred.size(0)
    m1 = pred.view(num, -1)  # Flatten
    m2 = target.view(num, -1)  # Flatten
    intersection = (m1 * m2).sum()

    return (2.0 * intersection + smooth) / (m1.sum() + m2.sum() + smooth + 1e-10)


def closest_point(pt, others):
    """Find the closest point and its distance to a given point.

    Parameters
    ----------
    pt : array_like
        Coordinates of the reference point.
    others : array_like
        Coordinates of other points.

    Returns
    -------
    distance : float
        Distance between the reference point and the closest point.
    index : int
        Index of the closest point.
    """
    distances = cdist(pt, others)
    return distances.min(), distances.argmin()


def compute_cell_detection_accuracy(pred_mask, gt_mask, max_dist):
    """Compute cell detection accuracy metrics.

    Parameters
    ----------
    pred_mask : np.ndarray
        Predicted binary mask of cell locations.
    gt_mask : np.ndarray
        Ground truth binary mask of cell locations.
    max_dist : float
        Maximum distance threshold for matching a predicted cell with a ground truth
        cell.

    Returns
    -------
    TP : int
        Number of true positive cell detections.
    FP : int
        Number of false positive cell detections.
    num_gt_pts : int
        Number of ground truth cell locations.
    """
    pred_cell_coords = np.transpose(np.nonzero(pred_mask))
    gt_cell_coords = np.nonzero(gt_mask)
    Np = len(pred_cell_coords)
    num_gt_pts = len(gt_cell_coords)
    TP = 0
    FN = 0
    for iPoint in range(len(pred_cell_coords)):
        if len(gt_cell_coords) > 0:
            point = pred_cell_coords[iPoint]
            dist, min_idx = closest_point(
                np.array([[point[0], point[1]]]), np.array(gt_cell_coords)
            )
            if dist <= max_dist:
                TP += 1
                gt_cell_coords = np.delete(gt_cell_coords, min_idx, axis=0)
            else:
                FN += 1
    FP = Np - TP
    # if num_gt_pts > 0:
    #     TP = TP / num_gt_pts
    return TP, FP, num_gt_pts


def compute_class_agnostic_detection_accuracy(pred_mask, gt_mask, max_dist):
    """Compute class-agnostic cell detection accuracy.

    Parameters
    ----------
    pred_mask : np.ndarray
        Predicted binary mask of cell locations.
    gt_mask : np.ndarray
        Ground truth binary mask of cell locations.
    max_dist : float
        Maximum distance threshold for matching a predicted cell with a ground truth
        cell.

    Returns
    -------
    accuracy : float
        Class-agnostic cell detection accuracy.
    """
    total_matched_pts, num_gt_pts = compute_cell_detection_accuracy(
        pred_mask > 0, gt_mask > 0, max_dist
    )
    return total_matched_pts / num_gt_pts


def compute_per_class_detection_accuracy(pred_mask, gt_mask, max_dist, num_classes=4):
    """Compute per-class cell detection accuracy.

    Parameters
    ----------
    pred_mask : np.ndarray
        Predicted mask of cell classes.
    gt_mask : np.ndarray
        Ground truth mask of cell classes.
    max_dist : float
        Maximum distance threshold for matching a predicted cell with a ground truth
        cell.
    num_classes : int, optional
        Number of classes, by default 4.

    Returns
    -------
    confmat : np.ndarray
        Confusion matrix representing per-class detection accuracy.
    """
    confmat = np.zeros([num_classes, num_classes], dtype="float32")
    for c in range(num_classes):
        if c == 0:
            pass
        else:
            tp, fp, fn, num_gt_pts = compute_detection_accuracy(
                pred_mask == c, gt_mask == c, max_dist
            )
            confmat[c, c] = tp
    # confmat = confmat[1:, 1:]
    return confmat


def compute_per_class_detection_confmat(
    pred_mask, gt_mask, confmat, max_dist=10, num_classes=4, ignore_classes=[]
):
    """Compute per class detection confusion matrix.

    Loops over all gt cells and identifies closest predicted cell of same class.

    Parameters
    ----------
    pred_mask : np.ndarray
        Predicted mask.
    gt_mask : np.ndarray
        Ground truth mask.
    confmat : np.ndarray
        Confusion matrix to update.
    max_dist : int, optional
        Maximum distance threshold for matching points, by default 10.
    num_classes : int, optional
        Number of classes, by default 4.
    ignore_classes : list, optional
        List of classes to ignore in the confusion matrix, by default [].

    Returns
    -------
    confmat : np.ndarray
        Updated confusion matrix.

    Notes
    -----
                 ----- GT -------
                 BG  C1  C2  C3
         P|BG    x   FN  FN  FN
         R|C1    x   TP  FP  FP
         E|C2    x   FP  TP  FP
         D|C3    x   FP  FP  TP
    """
    pred_cell_coords = np.argwhere(pred_mask != 0)
    gt_cell_coords = np.argwhere(gt_mask != 0)
    num_gt_pts = gt_cell_coords.shape[0]
    tmp_pred_cell_coords = pred_cell_coords

    # if num_gt_pts == 0 and num_pred_pts != 0:
    #     ''' there were bg pixels predicted as cells '''
    #     for iPoint in range(num_pred_pts):
    #         point = pred_cell_coords[iPoint]
    #         point_lbl = pred_mask[point[0], point[1]]
    #         confmat[point_lbl, 0] += 1
    # else:
    """ there exist non-bg only cells in ground truth """
    for iPoint in range(num_gt_pts):
        # for each point in GT mask, find closest point in prediction mask
        point = gt_cell_coords[iPoint]
        point_lbl = gt_mask[point[0], point[1]]
        if len(tmp_pred_cell_coords) > 0:
            # dist, min_idx = closest_point(np.array([[point[0], point[1]]]),
            #                               np.array(tmp_pred_cell_coords))
            dist = np.linalg.norm(tmp_pred_cell_coords - point, axis=1)
            if np.min(dist) < max_dist:
                # if gt point has matching prediction, compute confmat for
                # corresponding classes
                pred_idx = np.argmin(dist)
                pred_pt = tmp_pred_cell_coords[pred_idx]
                confmat[pred_mask[pred_pt[0], pred_pt[1]], point_lbl] += 1
                # if point is matched, delete from list of prediction points
                tmp_pred_cell_coords = np.delete(tmp_pred_cell_coords, pred_idx, axis=0)
            else:
                # if point is not matched then consider as missed prediction i.e.
                # false negative
                confmat[0, point_lbl] += 1

    # if any point is left in the prediction there are false positives
    if tmp_pred_cell_coords.any():
        num_fp_pts = tmp_pred_cell_coords.shape[0]
        for iFP in range(num_fp_pts):
            point = tmp_pred_cell_coords[iFP]
            confmat[pred_mask[point[0], point[1]], 0] += 1
    # excluding background from the confusion matrix by starting from 1
    # temp_ignore_classes = ignore_classes.copy()
    # temp_ignore_classes.append(0)

    # confmat = np.delete(confmat, temp_ignore_classes, 0)
    # confmat = np.delete(confmat, temp_ignore_classes, 1)
    return confmat


def nanmean(x):
    """Compute the arithmetic mean ignoring any NaNs.

    Parameters
    ----------
    x : torch.Tensor
        Input tensor.

    Returns
    -------
    mean : torch.Tensor
        Arithmetic mean of the input tensor, ignoring NaN values.
    """
    return torch.mean(x[x == x])


def _fast_hist(true, pred, num_classes):
    """Compute a fast confusion matrix.

    Parameters
    ----------
    true : torch.Tensor
        True labels.
    pred : torch.Tensor
        Predicted labels.
    num_classes : int
        Number of classes.

    Returns
    -------
    hist : torch.Tensor
        Confusion matrix of shape (num_classes, num_classes) representing class-wise
        predictions.
    """
    mask = (true >= 0) & (true < num_classes)
    hist = (
        torch.bincount(
            num_classes * true[mask] + pred[mask],
            minlength=num_classes**2,
        )
        .reshape(num_classes, num_classes)
        .float()
    )
    return hist


def overall_pixel_accuracy(hist):
    """Compute the overall pixel accuracy.

    Parameters
    ----------
    hist : torch.Tensor
        Confusion matrix of shape (num_classes, num_classes) representing class-wise
        predictions.

    Returns
    -------
    overall_acc : float
        Overall pixel accuracy.
    """
    correct = torch.diag(hist).sum()
    total = hist.sum()
    overall_acc = correct / (total + EPS)
    return overall_acc


def per_class_pixel_accuracy(hist):
    """Compute the average per-class pixel accuracy.

    The per-class pixel accuracy is a more fine-grained
    version of the overall pixel accuracy. A model could
    score a relatively high overall pixel accuracy by
    correctly predicting the dominant labels or areas
    in the image whilst incorrectly predicting the
    possibly more important/rare labels. Such a model
    will score a low per-class pixel accuracy.

    Parameters
    ----------
    hist : torch.Tensor
        Confusion matrix of shape (num_classes, num_classes) representing class-wise
        predictions.

    Returns
    -------
    avg_per_class_acc : float
        Average per-class pixel accuracy.
    per_class_acc : torch.Tensor
        Per-class pixel accuracy for each class.
    """
    correct_per_class = torch.diag(hist)
    total_per_class = hist.sum(dim=1)
    per_class_acc = correct_per_class / (total_per_class + EPS)
    avg_per_class_acc = nanmean(per_class_acc)
    return avg_per_class_acc, per_class_acc


def jaccard_index(hist):
    """Compute the Jaccard index for each class.

    Parameters
    ----------
    hist : torch.Tensor
        Confusion matrix of shape (num_classes, num_classes).

    Returns
    -------
    avg_jacc : torch.Tensor
        Average Jaccard index across all classes.
    """
    A_inter_B = torch.diag(hist)
    A = hist.sum(dim=1)
    B = hist.sum(dim=0)
    jaccard = A_inter_B / (A + B - A_inter_B + EPS)
    avg_jacc = nanmean(jaccard)
    return avg_jacc


def dice_coefficient(hist):
    """Compute the Dice coefficient for each class.

    Parameters
    ----------
    hist : torch.Tensor
        Confusion matrix of shape (num_classes, num_classes).

    Returns
    -------
    avg_dice : torch.Tensor
        Average Dice coefficient across all classes.
    """
    A_inter_B = torch.diag(hist)
    A = hist.sum(dim=1)
    B = hist.sum(dim=0)
    dice = (2 * A_inter_B) / (A + B + EPS)
    avg_dice = nanmean(dice)
    return avg_dice


def eval_metrics(true, pred, num_classes):
    """Compute evaluation metrics for semantic segmentation.

    Parameters
    ----------
    true : list or array-like
        List of ground truth segmentation masks.
    pred : list or array-like
        List of predicted segmentation masks.
    num_classes : int
        Number of classes in the segmentation task.

    Returns
    -------
    overall_acc : float
        Overall pixel accuracy.
    avg_per_class_acc : float
        Average per-class pixel accuracy.
    avg_jacc : float
        Average Jaccard index.
    avg_dice : float
        Average Dice coefficient.
    per_class_acc : array-like
        Per-class pixel accuracy for each class.
    """
    hist = torch.zeros((num_classes, num_classes))
    for t, p in zip(true, pred):
        hist += _fast_hist(t.flatten(), p.flatten(), num_classes)
    overall_acc = overall_pixel_accuracy(hist)
    avg_per_class_acc, per_class_acc = per_class_pixel_accuracy(hist)
    avg_jacc = jaccard_index(hist)
    avg_dice = dice_coefficient(hist)
    return overall_acc, avg_per_class_acc, avg_jacc, avg_dice, per_class_acc


def detect_touching_cells(point_mask, seg_pred_mask):
    """Detect touching cells in a segmentation mask.

    Parameters
    ----------
    point_mask : ndarray
        Binary mask indicating the location of cells.
    seg_pred_mask : ndarray
        Segmentation mask.

    Returns
    -------
    unique : ndarray
        Array of unique counts of touching cells.
    counts : ndarray
        Array of corresponding counts for each unique count of touching cells.
    """
    labels, no_of_objects = scipy.ndimage.label(seg_pred_mask)
    point_true_mask = point_mask > 0
    touching_cells_count_list = []
    for i in range(1, no_of_objects + 1):
        labels_bool = labels == i
        touching_cells_count = sum(sum((np.logical_and(labels_bool, point_true_mask))))
        touching_cells_count_list.append(touching_cells_count)
    touching_cells_count_npy = np.array(touching_cells_count_list)
    unique, counts = np.unique(touching_cells_count_npy, return_counts=True)
    return unique, counts
