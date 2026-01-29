"""Module for training/evaluating cell detection & classification model."""

from typing import Any, Dict, List, Literal, Tuple, Union

import torch
import torch.nn.functional as F
import wandb
from torch.nn import Module

from roche.crisp.model_engines import BaseModelEngine
from roche.crisp.utils.common_utils import get_effective_sample_based_classweights
from roche.crisp.utils.visualization import plot_confusion_matrix


class CellDetectionEngine(BaseModelEngine):
    """Training/evaluation engine for cell detection & classification model."""

    def __init__(self, network: Module, **kwargs) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        network : Module
            Pytorch neural network model
        """
        for k, v in kwargs.items():
            setattr(self, k, v)
        super().__init__(network, self.metrics)

    def shared_epoch_end(self, mode: Literal["train", "val", "test"]) -> Dict[str, Any]:
        """Set up common epoch end.

        Parameters
        ----------
        mode : Literal["train", "val", "test"]
            Specify whether step operation is for train/val/test.

        Returns
        -------
        Dict[str, Any]
            Returns a dictionary with the metrics to log
        """
        if mode != "train":
            conf_mat_fig = plot_confusion_matrix(
                confusion_matrix=self.metrics[f"{mode}_metrics"]
                .detection_stats.conf_mat.cpu()
                .numpy(),
                class_names=self.metrics[
                    f"{mode}_metrics"
                ].detection_stats.class_labels,
            )
            wandb.log({f"{mode} confusion_matrix": wandb.Image(conf_mat_fig)})

        return self.metrics[f"{mode}_metrics"].compute()

    def shared_step(
        self,
        batch: Union[torch.Tensor, Tuple[torch.Tensor, ...], List[torch.Tensor]],
        mode: Literal["train", "val", "test"],
        batch_idx: int,
    ) -> Tuple[torch.Tensor, ...]:
        """Set up common forward pass and loss operations.

        Parameters
        ----------
        batch : Union[torch.Tensor, Tuple[torch.Tensor, ...], List[torch.Tensor]]
            Output of torch.utils.data.DataLoader class. A tensor, tuple or list
        mode : Literal["train", "val", "test"]
            Specify whether step operation is for train/val/test.
        batch_idx : int
            Integer index of current batch

        Returns
        -------
        Tuple[torch.Tensor, ...]
            Tuple containing loss, predictions and groundtruth mask
        """
        input_data, masks = batch
        gt_mask = masks[0]
        derived_masks = masks[1:]
        derived_masks[0] = derived_masks[0].permute(0, 3, 1, 2)

        out = self.forward(input_data)

        class_weights = None

        if self.class_weights:
            class_weights = get_effective_sample_based_classweights(
                gt_mask,
                beta=self.beta,
                total_classes=self.num_classes,
                ignore_label=self.metrics[
                    f"{mode}_metrics"
                ].detection_stats.ignore_label,
            )
            class_weights = class_weights.to("cuda")
        sh1, sh2, sh3, sh4 = out.shape
        weights = (
            class_weights.view(1, sh2, 1, 1).expand(sh1, -1, sh3, sh4)
            if class_weights is not None
            else torch.ones_like(out)
        )

        # set the weight to 0 for ignore labels (2) in the background channel
        # of the gaussian mask
        mask = derived_masks[0][:, 0] == 2
        mask = mask.unsqueeze(1).repeat(1, self.num_classes, 1, 1)

        weights = weights.clone()
        weights[mask] = 0
        loss = F.binary_cross_entropy_with_logits(
            input=out,
            target=derived_masks[0],
            weight=weights,
            reduction="mean",
        )

        prob = F.softmax(out, dim=1)

        return loss, prob, gt_mask
