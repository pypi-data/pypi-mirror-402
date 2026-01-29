"""Module for training/evaluating cell segmentation model."""

from typing import Any, Dict, List, Literal, Tuple, Union

import torch
import torch.nn as nn
from torch.nn import Module

from roche.crisp.model_engines import BaseModelEngine
from roche.crisp.utils import common_utils, transforms
from roche.crisp.utils.cellpose_utils import postprocess
from roche.crisp.utils.velox_postprocessing import velox_post_process


class CellSegmentationEngine(BaseModelEngine):
    """Training/evaluation engine for cell segmentation model."""

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
        batch: Union[
            torch.Tensor,
            Dict[str, torch.Tensor],
            Tuple[torch.Tensor, ...],
            List[torch.Tensor],
        ],
        mode: Literal["train", "val", "test", "predict"],
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
        input_data = batch["image"]  # type: ignore
        if mode in ["train", "val"]:
            input_label = batch["flows"]  # type: ignore
        if mode == "test":
            input_label = batch["instance_label"]  # type: ignore

        if self.resample:
            resampled_width = int(
                (input_data.shape[-2] + 1) / (self.diam_mean / self.diameter)
            )
            resampled_height = int(
                (input_data.shape[-1] + 1) / (self.diam_mean / self.diameter)
            )

        input_data, ysub_pad, xsub_pad = common_utils.pad_image(input_data)
        output = self.forward(input_data)[0]
        output = common_utils.remove_padding(output, ysub_pad, xsub_pad)

        if self.resample:
            output = transforms.resize_image_gpu(
                output, resampled_width, resampled_height
            )
            if mode in ["train", "val", "test"]:
                input_label = transforms.resize_image_gpu(
                    input_label, resampled_width, resampled_height
                )

        if mode not in ["predict", "test"]:
            loss, gradient_loss, class_loss = self.compute_loss(input_label, output)
            input_label = input_label[:, 0, :, :]
            self.log(f"{mode}_loss", loss)
            self.log(f"{mode}_mse_vert_horz_grad_loss", gradient_loss)
            self.log(f"{mode}_cross_entropy_loss", class_loss)
        else:
            loss = 0

        with torch.no_grad():
            if self.postprocess_backend == "cellpose":
                masks = postprocess(
                    output,
                    vectorized=True,
                    segmentation_type=self.segmentation_type,
                    cellprob_threshold=self.cellprob_threshold,
                    flow_threshold=self.flow_threshold,
                )
            else:
                gradients = output[:, :2]
                sem_logits = output[:, 2:]
                sem_output_softmax = nn.softmax(sem_logits, dim=1)

                cellprobs = 1 - sem_output_softmax[:, 0]

                masks = velox_post_process(
                    cellprobs,
                    gradients,
                    cellprob_threshold=self.cellprob_threshold,
                )

        if self.segmentation_type == "semantic":
            # convert to binary mask for metrics computation
            masks = masks.to(torch.int16)
            masks[masks > 0] = 1
            if mode != "predict":
                input_label = batch["binary_label"]  # type: ignore

        if mode not in ["predict"]:
            return loss, masks, input_label
        else:
            return loss, masks, None

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

    def compute_loss(
        self, labels: torch.Tensor, predictions: torch.Tensor
    ) -> Tuple[torch.Tensor, ...]:
        """Compute the loss function between true labels and predictions.

        Parameters
        ----------
        labels : torch.Tensor
            True labels
        predictions : torch.Tensor
            Predicted labels

        Returns
        -------
        Tuple[torch.Tensor, ...]
            Tuple containing the total_loss, gradient_loss, class_loss
        """
        # MSE loss for the predicted horizontal and vertical gradients
        mean_squared_error_loss = nn.MSELoss(reduction="mean")
        true_gradients = 5.0 * labels[:, 1:, :]
        predicted_gradients = predictions[:, :2, :]

        gradient_loss = mean_squared_error_loss(predicted_gradients, true_gradients)
        gradient_loss /= 2.0

        predicted_classes = predictions[:, 2:, :]

        if self.segmentation_type == "instance":
            # update labels to be binary and convert to float
            true_classes = labels[:, :1, :] > 0.5
            true_classes = true_classes.type(torch.FloatTensor).to(
                predicted_classes.device
            )
        else:
            # convert labels to long
            true_classes = labels[:, :1, :].long()

        class_loss = self.criterion(
            predicted_classes,
            true_classes,
        )

        total_loss = gradient_loss + class_loss

        return total_loss, gradient_loss, class_loss
