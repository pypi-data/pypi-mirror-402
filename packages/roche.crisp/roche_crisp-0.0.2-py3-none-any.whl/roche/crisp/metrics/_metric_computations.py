"""Core metric computation module."""

from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from scipy.spatial.distance import cdist
from sklearn.metrics import confusion_matrix

EPSILON = 1e-8


def compute_segmentation_confusion_matrix(
    pred: np.ndarray, target: np.ndarray, num_classes: int
) -> np.ndarray:
    """Calculate confusion matrix for segmentation.

    Supports both binary and multiclass segmentation.

    Adopted from
    https://github.com/kevinzakka/pytorch-goodies/blob/master/metrics.py

    Parameters
    ----------
    pred : numpy.ndarray
        prediction array
    target : numpy.ndarray
        array with ground truth points
    num_classes : int
        number of classes

    Returns
    -------
    numpy.ndarray
        Computed confusion matrix
    """
    mask = (target >= 0) & (target < num_classes)
    cm = np.bincount(
        num_classes * target[mask].astype(int) + pred[mask],
        minlength=num_classes**2,
    ).reshape(num_classes, num_classes)
    return cm


def group_labels_from_confusion_matrix(
    class_map: Dict[int, str],
    label_grouping: List[int],
    label_grouping_name: str,
    matrix: torch.Tensor,
) -> Tuple[Dict[int, str], torch.Tensor]:
    """Merge labels from a confusion matrix.

    Parameters
    ----------
    class_map : Dict[int, str]
        Dictionary mapping indices to class names
    label_grouping : List[int]
        when compute method is called, all labels in this list will be grouped and
        treated as a one class. All other labels will be treated as independent
    label_grouping_name : str
        define a name for the new label for the grouping labels
    matrix : torch.Tensor
        Matrix which performs the manipulation, a new matrix is crea

    Returns
    -------
    Tuple[Dict[int, str], torch.Tensor]
        Returns tuple, where the first element is the new reorganized class map and
        second element is the new matrix with the regrouped labels

    Raises
    ------
    ValueError
        if label_grouping is None
    ValueError
        if label_grouping lenght is <= 1
    ValueError
        if label_grouping is not None but no label_grouping_name is provided
    ValueError
        if a label in label_grouping does not exist in class_map
    """
    if class_map is None:
        raise ValueError("Error, class_map is None")
    if label_grouping is None:
        raise ValueError("Error, label_grouping is None")
    if len(label_grouping) <= 1:
        raise ValueError("Error, label_grouping lenght must be >= 2")
    if label_grouping is not None and label_grouping_name is None:
        raise ValueError(
            "Error, label_grouping is defined, but the label_grouping_name not. "
            "Provide a name"
        )
    if matrix is None:
        raise ValueError("Error, matrix is None")

    matrix_np = matrix.cpu().numpy()
    matrix_label_offset = np.array([0] * matrix.shape[0])
    for label in label_grouping[1:]:
        if label not in class_map:
            raise ValueError(
                f"Error, grouping label {label} not found in class labels: "
                f"{list(class_map.keys())}"
            )

        matrix_np[:, label_grouping[0]] += matrix_np[:, label]
        matrix_np[label_grouping[0], :] += matrix_np[label, :]
        matrix_label_offset[label:] -= 1

    matrix_np = np.delete(matrix_np, label_grouping[1:], axis=1)
    matrix_np = np.delete(matrix_np, label_grouping[1:], axis=0)

    new_class_map = {}
    for label, class_name in class_map.items():
        if label in label_grouping[1:]:
            continue
        if label == label_grouping[0]:
            class_name = label_grouping_name

        new_class_map[label + matrix_label_offset[label]] = class_name

    return new_class_map, torch.tensor(matrix_np)


def compute_detection_confusion_matrix(
    pred: np.ndarray,
    gt: np.ndarray,
    radius: int,
    class_map: dict,
    noncell_label: int = 0,
    ignore_label: Optional[Union[int, List[int]]] = None,
    undeterminedcell_label: Optional[int] = None,
) -> np.ndarray:
    """Compute confusion matrix for given prediction.

    Parameters
    ----------
        pred : numpy.ndarray
            Array with prediction
        gt : numpy.ndarray
            Array with ground truth
        radius : int
            Acceptable shift comparing ground truth
        class_map : dict
            The mapping from indices to class names
        noncell_label : int
            Label for non-cell regions, default is 0
        ignore_label : int or list of int, optional
            Label or list of labels to be ignored during evaluation,
            default is None
        undeterminedcell_label : int, optional
            Label for undetermined cells, default is None
            They are only present in the ground truth.

    Returns
    -------
        numpy.ndarray
            confusion matrix
        list
            sorted classes used for confusion matrix

    Notes
    -----
        As an example this is a 5x5 confusion matrix that shows the truth value
        vs. the predicted value for each class (Cell 1, Cell 2, Cell 3, Cell 4,
        Non-Cell). UD-Cell is the undetermined cell class.

        The confusion matrix organizes these elements as follows:

                     | Cell 1 | Cell 2 | Cell 3 | Cell 4 | Non-Cell | UD-Cell |
                     |--------|--------|--------|--------|----------|---------|
            | Cell 1 | TP1    | E12    | E13    | E14    | E15      | 0       |
            | Cell 2 | E21    | TP2    | E23    | E24    | E25      | 0       |
            | Cell 3 | E31    | E32    | TP3    | E34    | E35      | 0       |
            | Cell 4 | E41    | E42    | E43    | TP4    | E45      | 0       |
            |Non-Cell| E51    | E52    | E53    | E54    | 0        | 0       |
            |UD-Cell | E61    | E62    | E63    | E64    | E65      | 0       |

        The matrix is arranged based on the sorted keys for class_map with the
        'Non-Cell' class at the end. The element E55 is always 0.

        If the 'Undetermined-Cell' class is present, it is placed at the end of
        the matrix. Note that this class is only present in the ground truth
        and never predicted by the model, so the values in the last column are
        always 0.

        Undetermined cells have defined locations but lack a consensus class
        established by human annotators.
    """
    # Ensure pred and gt are numpy arrays
    pred, gt = (np.array(x) if not isinstance(x, np.ndarray) else x for x in (pred, gt))

    # If there are classes to ignore, mask those classes in gt and pred, and set
    # them to 0
    if ignore_label is not None:
        mask = np.isin(gt, np.array(ignore_label))
        gt[mask], pred[mask] = noncell_label, noncell_label

    # Find the coordinates of cells in pred and gt
    pred_cell_coords, gt_cell_coords = (
        np.argwhere(pred != noncell_label),
        np.argwhere(gt != noncell_label),
    )

    # Compute a distance matrix between gt and pred coordinates
    distmat = cdist(gt_cell_coords, pred_cell_coords)
    # Flatten the distance matrix
    flatdists = distmat.ravel()

    # Find the indices of distances that are less than or equal to the radius
    possible_indx = np.nonzero(flatdists <= radius)[0]
    # Sort these indices
    sorted_dists_indx = np.argsort(flatdists[possible_indx])

    # Unravel the sorted indices into a 2D array
    sorted_ij = np.transpose(
        np.unravel_index(possible_indx[sorted_dists_indx], distmat.shape)
    )

    # Create sets of remaining indices to be checked in gt and pred
    rem_i = set(range(gt_cell_coords.shape[0]))
    rem_j = set(range(pred_cell_coords.shape[0]))

    # Initialize a list to store pairs of indices corresponding to global
    # minimum values
    global_min_pairs = []
    # Iterate over the sorted indices
    for i, j in sorted_ij:
        # If there are no remaining indices, break the loop
        if len(rem_i) + len(rem_j) == 0:
            break

        # If both indices are in the remaining sets, remove them from the
        # sets and add the pair to global_min_pairs
        if (i in rem_i) and (j in rem_j):
            rem_i.remove(i)
            rem_j.remove(j)
            global_min_pairs.append((i, j))

    # Convert global_min_pairs to a numpy array
    global_min_pairs = np.array(global_min_pairs)

    # Initialize lists to store gt and pred cell labels
    gt_cell_labels = []
    pred_cell_labels = []
    # If there are any global minimum pairs
    if len(global_min_pairs) > 0:
        # Select the corresponding gt and pred coordinates
        selected_gt_cell_coords = gt_cell_coords[global_min_pairs[:, 0]]  # type: ignore
        selected_pred_cell_coords = pred_cell_coords[
            global_min_pairs[:, 1]  # type: ignore
        ]

        # Get the corresponding gt and pred labels
        gt_cell_labels = list(
            gt[
                selected_gt_cell_coords[:, 0],
                selected_gt_cell_coords[:, 1],  # type: ignore
            ]
        )
        pred_cell_labels = list(
            pred[selected_pred_cell_coords[:, 0], selected_pred_cell_coords[:, 1]]
        )

    # Select the remaining gt and pred coordinates
    selected_gt_cell_coords = gt_cell_coords[list(rem_i)]
    selected_pred_cell_coords = pred_cell_coords[list(rem_j)]
    # Get the remaining gt and pred labels
    gt_cell_labels_rem = gt[
        selected_gt_cell_coords[:, 0], selected_gt_cell_coords[:, 1]
    ]
    pred_cell_labels_rem = pred[
        selected_pred_cell_coords[:, 0], selected_pred_cell_coords[:, 1]
    ]

    # Concatenate the selected and remaining labels, padding with zeros as
    # necessary to make the lengths match
    gt_cell_labels += list(gt_cell_labels_rem) + [noncell_label] * len(rem_j)
    pred_cell_labels += [noncell_label] * len(rem_i) + list(pred_cell_labels_rem)

    # Sort classes, place noncell_label and undeterminedcell_label at the end
    sorted_classes = sort_classes(
        class_map, noncell_label, ignore_label, undeterminedcell_label
    )

    # Compute a confusion matrix from the gt and pred labels
    confmat = confusion_matrix(gt_cell_labels, pred_cell_labels, labels=sorted_classes)

    return confmat, sorted_classes


def compute_detection_metrics(
    conf_mat: np.ndarray,
    class_map: dict,
    class_labels: list,
    undeterminedcell_label: Optional[int] = None,
) -> dict:
    """Compute the final metric values from the confusion matrix.

    Parameters
    ----------
    conf_mat : numpy.ndarray
        The confusion matrix.
    class_map : dict
        The mapping from indices to class names.
    class_labels : list
        The list of class labels ordered according to the confusion matrix.
        It expects the noncell_label to be at the end of the list.
    undeterminedcell_label : int, optional
        Label for undetermined cells, default is None.

    Returns
    -------
    dict
        The computed metrics as a dictionary.
    """
    if undeterminedcell_label is not None:
        inner_conf_mat = conf_mat[:-1, :-1]
        tp = inner_conf_mat.diag()
        fp = inner_conf_mat.sum(dim=0) - tp
        fn = inner_conf_mat.sum(dim=1) - tp
    else:
        tp = conf_mat.diag()
        fp = conf_mat.sum(dim=0) - tp
        fn = conf_mat.sum(dim=1) - tp

    # Calculate precision, recall and F1 score for each class
    precision = tp / (tp + fp + EPSILON)
    recall = tp / (tp + fn + EPSILON)
    f1 = 2 * ((precision * recall) / (precision + recall + EPSILON))

    # Calculate false positive rate and false negative rate for each class
    fp_rate = fp / (fp + tp + EPSILON)
    fn_rate = fn / (fn + tp + EPSILON)

    # Calculate false positive rate (missed cell detection) and false negative
    # rate (false cell detection)
    if undeterminedcell_label is not None:
        fnr = conf_mat[:, -2].sum() / (
            conf_mat[:-2, :].sum() + conf_mat[-1, :].sum() + EPSILON
        )
        fpr = conf_mat[-2, :].sum() / (
            conf_mat[:-2, :].sum() + conf_mat[-1, :].sum() + EPSILON
        )
    else:
        fnr = conf_mat[:-1, -1].sum() / (conf_mat[:-1, :].sum() + EPSILON)
        fpr = conf_mat[-1, :-1].sum() / (conf_mat[:-1, :].sum() + EPSILON)

    # Calculate micro precision, recall and F1 score
    # for micro averaging, precision and recall are equal
    micro_precision = tp.sum() / (tp.sum() + fp.sum() + EPSILON)
    micro_recall = tp.sum() / (tp.sum() + fn.sum() + EPSILON)
    micro_f1 = 2 * (
        (micro_precision * micro_recall) / (micro_precision + micro_recall + EPSILON)
    )

    # Calculate macro precision, recall and F1 score
    macro_precision = precision.mean()
    macro_recall = recall.mean()
    macro_f1 = f1.mean()

    metrics = {
        **{
            f"{class_map[class_labels[i]]}_{metric}": value.item()
            for i in range(len(class_labels) - 1)
            for metric, value in zip(
                ["precision", "recall", "f1", "fp_rate", "fn_rate"],
                [precision[i], recall[i], f1[i], fp_rate[i], fn_rate[i]],
            )
        },
        "micro_precision": micro_precision.item(),
        "micro_recall": micro_recall.item(),
        "micro_f1": micro_f1.item(),
        "macro_precision": macro_precision.item(),
        "macro_recall": macro_recall.item(),
        "macro_f1": macro_f1.item(),
        "fnr": fnr.item(),
        "fpr": fpr.item(),
    }

    return metrics


def sort_classes(
    class_map: dict,
    noncell_label: int = 0,
    ignore_label: Optional[Union[int, List[int]]] = None,
    undeterminedcell_label: Optional[int] = None,
) -> list:
    """Sort the classes in the class_map.

    noncell and undeterminedcell classes appear at the end.
    """
    ignore_label = (
        [ignore_label] if isinstance(ignore_label, int) else ignore_label or []
    )
    ignore_set = set(ignore_label + [noncell_label, undeterminedcell_label])

    sorted_classes = sorted(key for key in class_map.keys() if key not in ignore_set)

    sorted_classes.append(noncell_label)
    if undeterminedcell_label is not None:
        sorted_classes.append(undeterminedcell_label)

    return sorted_classes
