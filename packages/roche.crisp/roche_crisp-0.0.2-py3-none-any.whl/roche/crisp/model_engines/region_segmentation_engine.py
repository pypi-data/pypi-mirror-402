"""Module for training/evaluating region segmentation model."""

from typing import Any, Dict, List, Literal, Tuple, Union

import torch
from torch import nn

from roche.crisp.model_engines import BaseModelEngine


class RegionSegmentationEngine(BaseModelEngine):
    """Training/evaluation engine for region segmentation model."""

    def __init__(self, network: nn.Module, metrics: dict, **kwargs) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        network : nn.Module
            Pytorch neural network model
        metrics : dict
            A dictionary of metrics configurations
        """
        for k, v in kwargs.items():
            setattr(self, k, v)
        super().__init__(network, metrics)

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
        return self.metrics[f"{mode}_metrics"].compute()

    def shared_step(
        self,
        batch: Union[torch.Tensor, Tuple[torch.Tensor, ...], List[torch.Tensor]],
        mode: Literal["train", "val", "test"],
        batch_idx: int,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Set up common forward pass and loss operations.

        Parameters
        ----------
        batch : Union[torch.Tensor, Tuple[torch.Tensor, ...], List[torch.Tensor]]
            Output of torch.utils.data.DataLoader class. A tensor, tuple or list
        mode : Literal["train", "val", "test"]
            Specify whether step operation is for train/val/test..
        batch_idx : int
            Integer index of current batch

        Returns
        -------
        Tuple of torch.Tensor
            loss tensor, prediction and ground truth
        """
        _, input_data, masks, _ = batch

        out = self.forward(input_data)

        loss = self.criterion(out, masks.long())

        pred_sgm_masks = torch.argmax(out, dim=1, keepdim=True).squeeze(dim=1)
        return loss, pred_sgm_masks, masks
