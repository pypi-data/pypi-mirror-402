"""Module for training/evaluating cell segmentation model."""

from typing import Any, Dict, List, Literal, Tuple, Union

import torch
from hydra.utils import instantiate
from torch.nn import Module

from roche.crisp.model_engines import BaseModelEngine
from roche.crisp.networks.instanseg_unet import initialize_pixel_classifier
from roche.crisp.utils.instanseg_utils import (
    postprocessing,
)


class InstanSegEngine(BaseModelEngine):
    """Training/evaluation engine for cell instance segmentation model."""

    def __init__(self, network: Module, **kwargs) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        network : nn.Module
            Pytorch neural network model
        **kwargs
            Keyword arguments passed through configs/model_engine
            yaml.
        """
        for k, v in kwargs.items():
            setattr(self, k, v)
        super().__init__(network, self.metrics)
        self.loss_fn = instantiate(self.criterion)

        self.loss_fn.update_seed_loss("binary_xloss")
        self.loss_fn.update_binary_loss("dice_loss")
        self.update_loss_fn = True

        self.model: torch.nn.Module = initialize_pixel_classifier(
            self.model, MLP_width=5
        )
        self.pixel_classifier = self.model.pixel_classifier

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        """Perform forward pass on given input x.

        Parameters
        ----------
        x : torch.Tensor
            Input to model

        Returns
        -------
        torch.Tensor
            Model output
        """
        return self.model(x)

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
            Specify whether step operation is for train/val/test.
        batch_idx : int
            Integer index of current batch

        Returns
        -------
        Tuple[torch.Tensor, ...]
            Tuple containing loss, predictions and groundtruth mask
        """
        input_data, labels = batch
        output = self.forward(input_data)

        if mode != "test":
            loss = self.compute_loss(labels, output)
        else:
            loss = 0.0

        predicted_labels = torch.stack(
            [
                postprocessing(
                    out, device=self.device, classifier=self.pixel_classifier
                )
                for out in output
            ]
        )
        return loss, predicted_labels, labels.unsqueeze(1)

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

    def on_train_epoch_end(self) -> None:
        """Update loss functions after training for 10 epochs."""
        super().on_train_epoch_end()
        if self.update_loss_fn and self.current_epoch > 10:
            self.loss_fn.update_seed_loss("l1_distance")
            self.loss_fn.update_binary_loss("lovasz_hinge")
            self.update_loss_fn = False  # Only update loss functions once

    def compute_loss(self, labels: torch.Tensor, predictions: torch.Tensor) -> float:
        """Compute the loss function between true labels and predictions.

        Parameters
        ----------
        labels : torch.Tensor
            True labels
        predictions : torch.Tensor
            Predicted labels

        Returns
        -------
        float
            Loss value
        """
        return self.loss_fn.forward(
            predictions, labels.unsqueeze(1), self.pixel_classifier
        )
