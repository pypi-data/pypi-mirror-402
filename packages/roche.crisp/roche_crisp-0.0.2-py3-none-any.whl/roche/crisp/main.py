"""Entrypoint script to initiate training."""

import logging
import os
import time
from pathlib import Path

import hydra
import lightning
import torch.multiprocessing
import wandb
from omegaconf import DictConfig, OmegaConf

OmegaConf.register_new_resolver("eval", eval)
torch.set_float32_matmul_precision("medium")
torch.multiprocessing.set_sharing_strategy("file_system")


os.environ["HYDRA_FULL_ERROR"] = "1"

output_logger = logging.getLogger(__name__)


def fix_checkpoint_state_dict(state_dict):
    """Fix checkpoint state_dict by removing unwanted keys and adding model prefix.

    Parameters
    ----------
    state_dict : dict
        The original state_dict from checkpoint.

    Returns
    -------
    dict
        Fixed state_dict with proper key names.
    """
    # Keys to remove
    keys_to_remove = ["diam_mean", "diam_labels"]

    # Create new state_dict
    fixed_state_dict = {}

    for key, value in state_dict.items():
        # Skip unwanted keys
        if key in keys_to_remove:
            continue

        # Add "model." prefix if not already present
        if not key.startswith("model."):
            new_key = f"model.{key}"
        else:
            new_key = key

        fixed_state_dict[new_key] = value

    return fixed_state_dict


@hydra.main(
    config_path=f"{os.getcwd()}/configs",
    version_base=None,
    config_name="train_segmentation",
)
def main(cfg: DictConfig) -> None:
    """Load configuration file and initiate training.

    Parameters
    ----------
    cfg : DictConfig
        A configuration dictionary based on hydra that contains input parameters
        for entire training workflow.
    """
    # Set config for logging
    logging_conf = OmegaConf.to_container(
        cfg.logging, resolve=True, throw_on_missing=True
    )
    logging.config.dictConfig(logging_conf)  # type: ignore

    # seed for pseudo-random number generators in pytorch,
    # numpy, python.random etc, for reproducibility
    if cfg.seed is not None:
        lightning.seed_everything(cfg.seed, workers=True)

    # init lightning data module
    dm = hydra.utils.instantiate(cfg.datamodule)

    # init network
    network = hydra.utils.instantiate(
        cfg.network,
    )

    # use pytorch's latest JIT-compiling for faster training
    if cfg.torch_compile:
        network = torch.compile(network)

    # init model
    model = hydra.utils.instantiate(
        cfg.model_engine, cfg=cfg, network=network, _recursive_=False
    )

    if cfg.logger.mode == "online":
        job_id = os.environ.get("LSB_JOBID")
        cfg.logger.name = f"{cfg.logger.name}_{job_id}" if job_id else cfg.logger.name
        os.makedirs(cfg.logger.save_dir, exist_ok=True)

        # init logger
        logger = hydra.utils.instantiate(cfg.logger, _partial_=True)
        conf = OmegaConf.to_container(cfg, resolve=True, throw_on_missing=True)
        logger = logger(
            name=cfg.logger.name, settings=wandb.Settings(code_dir="./"), config=conf
        )

        # log datasets only if enabled in config
        if cfg.get("log_dataset_artifacts", False):
            dataset_types = ["train_data", "val_data"]
            if "test_data" in cfg.datamodule.keys():
                dataset_types.append("test_data")

            dataset_artifact = wandb.Artifact("dataset", type="dataset")
            for dataset_type in dataset_types:
                file_path = getattr(dm, dataset_type)
                dataset_artifact.add_file(file_path, name=dataset_type)

            logger.experiment.log_artifact(dataset_artifact)
    else:
        logger = False

    # init callbacks
    callbacks = hydra.utils.instantiate(cfg.callbacks, _convert_="partial")

    # init trainer
    trainer = hydra.utils.instantiate(
        cfg.trainer,
        logger=logger,
        sync_batchnorm=cfg.trainer.devices > 1,
        use_distributed_sampler=cfg.trainer.devices > 1,
        callbacks=list(callbacks.values()),
    )

    if cfg.pipeline_mode == "train":
        start = time.time()
        if "checkpoint_path" in cfg.keys():
            checkpoint = torch.load(cfg.checkpoint_path)
            load_status = model.load_state_dict(checkpoint["state_dict"], strict=False)
            missing_keys = load_status.missing_keys
            unexpected_keys = load_status.unexpected_keys
            if not missing_keys and not unexpected_keys:
                output_logger.info("All keys successfully loaded!")
            else:
                output_logger.warning(f"Missing keys: {missing_keys}")
                output_logger.warning(f"Unexpected keys: {unexpected_keys}")

        trainer.fit(model, datamodule=dm, ckpt_path=cfg.resume_from_checkpoint_path)
        end = time.time()
        elapsed = end - start
        output_logger.info(f"Time elapsed {elapsed / 60:.2f} min")

        # Get the best checkpoint path from the ModelCheckpoint callback
        best_model_path = callbacks["model_checkpoint"].best_model_path
        output_logger.info(f"Best model path: {best_model_path}")

        if "test_data" in cfg.datamodule.keys():
            trainer.test(model, datamodule=dm, ckpt_path=best_model_path)

    elif cfg.pipeline_mode in ["test", "predict"]:
        if "wandb_model_path" in cfg.keys():
            api = wandb.Api()
            artifact = api.artifact(cfg.wandb_model_path)
            artifact.download()
            wandb_model_name = Path(cfg.wandb_model_path).stem
            checkpoint = torch.load(
                f"artifacts/{wandb_model_name}/model.ckpt", weights_only=False
            )
        elif "checkpoint_path" in cfg.keys():
            checkpoint = torch.load(cfg.checkpoint_path, weights_only=False)
        else:
            raise ValueError(
                f"Either 'wandb_model_path' or 'checkpoint_path' "
                f"must be defined in config yaml for {cfg.pipeline_mode} mode."
            )

        # Fix state_dict keys - for backward compatibility with old checkpoints
        if "state_dict" in checkpoint:
            fixed_state_dict = fix_checkpoint_state_dict(checkpoint["state_dict"])
        else:
            fixed_state_dict = fix_checkpoint_state_dict(checkpoint)

        load_status = model.load_state_dict(fixed_state_dict, strict=False)
        missing_keys = load_status.missing_keys
        unexpected_keys = load_status.unexpected_keys
        if not missing_keys and not unexpected_keys:
            output_logger.info("All keys successfully loaded!")
        else:
            output_logger.warning(f"Missing keys: {missing_keys}")
            output_logger.warning(f"Unexpected keys: {unexpected_keys}")

        if cfg.pipeline_mode == "test":
            # this mode expects ground truth labels in the dataloader
            trainer.test(model, datamodule=dm)
        elif cfg.pipeline_mode == "predict":
            # this mode runs plain inference on the model
            trainer.predict(model, datamodule=dm)
    else:
        raise ValueError(
            f"Invalid pipeline mode: {cfg.pipeline_mode}. "
            "Expected 'train', 'test', or 'predict'."
        )

    if cfg.logger.mode == "online":
        logger.experiment.finish()


if __name__ == "__main__":
    main()
