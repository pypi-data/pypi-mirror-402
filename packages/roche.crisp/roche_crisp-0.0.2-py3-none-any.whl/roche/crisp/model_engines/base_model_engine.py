"""Pytorch lightning based generic module for training/evaluating any model."""

import logging
from typing import Any, Dict, List, Literal, Tuple, Union

import lightning as L
import torch
from hydra.utils import instantiate
from torch.nn import Module, ModuleDict
from torch.optim import Optimizer
from torch.optim.lr_scheduler import _LRScheduler
from torchmetrics import MetricCollection


class BaseModelEngine(L.LightningModule):
    """Base engine for training/evaluation of any model.

    All other modules should inherit from this class.
    """

    def __init__(self, network: Module, metrics: dict) -> None:
        """Initialize instance of the class.

        Parameters
        ----------
        network : Module
            Pytorch neural network model.
        metrics : dict
            A dictionary of metrics configurations.
        """
        super().__init__()
        self.model = network

        if hasattr(self, "loss_func"):
            self.criterion = instantiate(self.loss_func)

        metrics_collection: MetricCollection = MetricCollection(
            {val: instantiate(cfg) for val, cfg in metrics.items()}  # type: ignore
        )
        self.metrics = ModuleDict(
            {
                "train_metrics": metrics_collection.clone(prefix="train_"),
                "val_metrics": metrics_collection.clone(prefix="val_"),
                "test_metrics": metrics_collection.clone(prefix="test_"),
            }
        )

        self.step_outputs: dict[str, list[dict[str, Any]]] = {
            "train": [],
            "val": [],
            "test": [],
        }

        self.save_hyperparameters(ignore=["network"], logger=False)

        self.output_logger = logging.getLogger(self.__class__.__name__)

    def shared_epoch_end(
        self, mode: Literal["train", "val", "test", "predict"]
    ) -> Dict[str, Any]:
        """Set up common epoch end.

        Parameters
        ----------
        mode : Literal["train", "val", "test", "predict"]
            Specify whether step operation is for train/val/test.

        Returns
        -------
        Dict[str, Any]
            Returns a dictionary with the metrics to log
        """
        raise NotImplementedError("Method to be implemented by inherited class.")

    def shared_step(
        self,
        batch: Union[torch.Tensor, Tuple[torch.Tensor, ...], List[torch.Tensor]],
        mode: Literal["train", "val", "test", "predict"],
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
        raise NotImplementedError("This method must be overridden by a subclass.")

    def training_step(
        self,
        batch: Union[torch.Tensor, Tuple[torch.Tensor, ...], List[torch.Tensor]],
        batch_idx: int,
    ) -> torch.Tensor:
        """Perform forward pass on training data and return loss.

        Also store additional batch outputs for logging.

        Parameters
        ----------
        batch : (torch.Tensor | (torch.Tensor, ...) | [torch.Tensor, ...])
            Output of torch.utils.data.DataLoader class. A tensor, tuple or list
        batch_idx : int
            Integer index of current batch

        Returns
        -------
        torch.Tensor
            loss tensor
        """
        loss, prob, gt = self.shared_step(batch, "train", batch_idx)
        self.metrics["train_metrics"].update(prob, gt)
        self.step_outputs["train"].append(loss)
        return loss

    def validation_step(
        self,
        batch: Union[torch.Tensor, Tuple[torch.Tensor, ...], List[torch.Tensor]],
        batch_idx: int,
    ) -> torch.Tensor:
        """Perform forward pass on validation data and return loss.

        Also store additional batch outputs for logging.

        Parameters
        ----------
        batch : (torch.Tensor | (torch.Tensor, ...) | [torch.Tensor, ...])
            Output of torch.utils.data.DataLoader class. A tensor, tuple or list
        batch_idx : int
            Integer index of current batch

        Returns
        -------
        torch.Tensor
            loss tensor
        """
        loss, prob, gt = self.shared_step(batch, "val", batch_idx)
        self.metrics["val_metrics"].update(prob, gt)
        self.step_outputs["val"].append(loss)
        return loss

    def test_step(
        self,
        batch: Union[torch.Tensor, Tuple[torch.Tensor, ...], List[torch.Tensor]],
        batch_idx: int,
    ) -> torch.Tensor:
        """Perform forward pass on test data and return loss.

        Also store additional batch outputs for logging.

        Parameters
        ----------
        batch : (torch.Tensor | (torch.Tensor, ...) | [torch.Tensor, ...])
            Output of torch.utils.data.DataLoader class. A tensor, tuple or list
        batch_idx : int
            Integer index of current batch

        Returns
        -------
        torch.Tensor
            loss tensor
        """
        _, prob, gt = self.shared_step(batch, "test", batch_idx)
        self.metrics["test_metrics"].update(prob, gt)

    def predict_step(
        self,
        batch: Union[torch.Tensor, Tuple[torch.Tensor, ...], List[torch.Tensor]],
        batch_idx: int,
    ) -> torch.Tensor:
        """Perform forward pass on test data and return loss.

        Also store additional batch outputs for logging.

        Parameters
        ----------
        batch : (torch.Tensor | (torch.Tensor, ...) | [torch.Tensor, ...])
            Output of torch.utils.data.DataLoader class. A tensor, tuple or list
        batch_idx : int
            Integer index of current batch

        Returns
        -------
        torch.Tensor
            loss tensor
        """
        self.shared_step(batch, "predict", batch_idx)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform forward pass on given input x.

        Parameters
        ----------
        x : torch.Tensor
            Input tensor of shape (batch_size, channels, height, width).

        Returns
        -------
        torch.Tensor
            Output tensor of shape (batch_size, num_features).
        """
        return self.model(x)

    def step_logger(self, log_params: dict) -> None:
        """Log common params to the logger after each epoch.

        Parameters
        ----------
        log_params : dict
            Dictionary of parameters to be logged.
        """
        self.log_dict(
            log_params,
            on_step=True,
            on_epoch=True,
            prog_bar=False,
            batch_size=self.cfg.datamodule.batch_size,
            sync_dist=self.trainer.num_devices > 1,
        )

    def epoch_logger(self, log_params: dict) -> None:
        """Perform epoch level operations at the end of train/validation loop.

        e.g. get batch predictions of train/validation step, calculate metrics and log
        them.

        Parameters
        ----------
        log_params : dict
            Dictionary of parameters to be logged.
        """
        self.log_dict(log_params, on_epoch=True, sync_dist=self.trainer.num_devices > 1)

    def on_train_epoch_end(self) -> None:
        """Perform epoch level operations at the end of training loop.

        e.g. get batch predictions of training step, calculate metrics and log them.
        """
        metrics = self.shared_epoch_end("train")

        all_losses = torch.stack([loss for loss in self.step_outputs["train"]])
        all_loss = self.all_gather(all_losses)

        metrics.update({"train_loss": all_loss.mean()})

        self.epoch_logger(metrics)

        self.metrics["train_metrics"].reset()

    def on_validation_epoch_end(self) -> None:
        """Perform epoch level operations at the end of validation loop.

        e.g. get batch predictions of training step, calculate metrics and log them.
        """
        metrics = self.shared_epoch_end("val")

        all_losses = torch.stack([loss for loss in self.step_outputs["val"]])
        all_loss = self.all_gather(all_losses)

        metrics.update({"val_loss": all_loss.mean()})

        self.epoch_logger(metrics)

        self.metrics["val_metrics"].reset()

    def on_test_epoch_end(self) -> None:
        """Perform epoch level operations at the end of test loop.

        e.g. get batch predictions of training step, calculate metrics and log them.
        """
        metrics = self.shared_epoch_end("test")

        self.epoch_logger(metrics)

        self.metrics["test_metrics"].reset()

    def configure_optimizers(
        self,
    ) -> Union[
        Optimizer,
        Tuple[List[Optimizer], List[_LRScheduler]],
        Dict[str, Union[Optimizer, _LRScheduler]],
    ]:
        """Define optimizers and learning-rate schedulers to use in your optimization.

        Returns
        -------
            Any of the below options

            - Single optimizer
            - List or Tuple of optimizers
            - Two lists - The first list has multiple optimizers, and the second has
                multiple LR schedulers
            - Dictionary, with an ``"optimizer"`` key, and (optionally) a
                ``"lr_scheduler"`` key, whose value is a single LR scheduler
        """
        optimizer = instantiate(self.optimizer, params=self.parameters())
        configuration = {"optimizer": optimizer}
        if self.scheduler:
            scheduler = instantiate(self.scheduler, optimizer=optimizer)
            configuration["lr_scheduler"] = scheduler

        return configuration
