"""Module containing utility functions for I/O functionalities."""

import argparse
import getpass
import glob
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def save_input_arguments(args: argparse.Namespace, filename: str) -> None:
    """Save input `args` to a YAML file located in a folder named 'argument_history'.

    The folder is located in the user's directory path.
    If the folder does not exist, it ll be created.

    Parameters
    ----------
        args : argparse.Namespace
            Any input arguments to be saved
        filename : str
            The name of the file to save the arguments into
    """
    argument_history_path = f"/home/{getpass.getuser()}/argument_history/"
    os.makedirs(argument_history_path, exist_ok=True)
    slurm_job_id = os.getenv("SLURM_JOB_ID")
    timestamp = datetime.now().strftime("%d_%b_%Y_%H_%M_%S_%f")
    argument_dir = os.path.join(
        argument_history_path,
        f"{slurm_job_id}_{timestamp}" if slurm_job_id else timestamp,
    )
    os.makedirs(argument_dir, exist_ok=True)
    with open(f"{argument_dir}/arguments_{filename}", "w") as f:
        f.write(json.dumps(vars(args)))


def _get_git_dir():
    """Get the Git directory."""
    current_dir = Path(os.path.abspath(__file__)).parent
    while current_dir != Path("/"):
        if (current_dir / ".git").exists():
            return current_dir
        current_dir = current_dir.parent
    return None


def _get_current_commit_info():
    """Get the current commit info."""
    main_dir = _get_git_dir()
    git_status_output = subprocess.check_output(["git", "status"], cwd=main_dir)
    git_log_output = subprocess.check_output(["git", "log"], cwd=main_dir)
    branch_name = git_status_output.decode().split("\n")[0].split(" ")[-1]
    commit_hash = git_log_output.decode().split(" ")[1].split("\n")[0]
    return branch_name, commit_hash


def _copy_tree(source, target, include_pattern="*.py", include_folders=[]):
    """Copy the code tree."""
    source_path = Path(source)
    target_path = Path(target)

    if not target_path.exists():
        target_path.mkdir(parents=True)

    for item in source_path.glob("*"):
        src_item = source_path / item.name
        dest_item = target_path / item.name

        # Handle directories
        if src_item.is_dir():
            # If the directory path is in the list of folders to be exclusively included
            if src_item.name in include_folders:
                # Copy the entire directory tree
                shutil.copytree(src_item, dest_item)

        # Handle files
        elif src_item.is_file():
            # Check if the file matches the include pattern
            if glob.fnmatch.fnmatch(src_item.name, include_pattern):
                shutil.copy2(src_item, dest_item)


def create_snapshot(output_path: str, args: argparse.Namespace) -> None:
    """Create a snapshot in time of the current codebase.

    It creates a snapshot of the current codebase by copying all Python files
    in the 'scripts' and 'src' directories to the specified output path. It also saves
    information about the current Git branch and commit hash to a 'commit.txt' file,
    and the command line arguments to a 'command.txt' file.
    If the 'args' parameter is not None,
    it also saves the arguments to an 'args.txt' file in JSON format.

    Parameters
    ----------
    output_path : str
        The path to save the snapshot to.
    args : argparse.Namespace
        The command line arguments passed to the script, by default None.

    Returns
    -------
    None
    """
    branch_name, commit_hash = None, None
    try:
        branch_name, commit_hash = _get_current_commit_info()
        with open(os.path.join(output_path, "commit.txt"), "w") as f:
            f.write("branch_name: " + branch_name + os.linesep)
            f.write("commit_hash: " + commit_hash)
    except Exception as e:
        print(f"could not get GIT INFO!: {e}")

    snapshot_dir = os.path.join(output_path, "snapshot")
    main_dir = Path(_get_git_dir())
    print(f"Making snapshot from {main_dir}")
    # If the snapshot directory already exists,
    # In the case the session was re-run, don't create it.
    if not os.path.isdir(snapshot_dir):
        _copy_tree(
            main_dir,
            snapshot_dir,
            include_pattern="*.py",
            include_folders=["scripts", "src"],
        )
        print(f"Created a snapshot at {output_path}")

    # capture command line
    if sys.argv:
        with open(os.path.join(output_path, "command.txt"), "w") as f:
            f.write(" ".join(sys.argv))

    if args is not None:
        with open(os.path.join(output_path, "args.txt"), "w") as f:
            json.dump(args.__dict__, f, indent=2)


def check_prefix_file_exist(image_path, output_dir, prefix):
    """Check if file with `prefix` exist for a given image path.

    Return `image_path` if corresponding file doesn't exist.

    Parameters
    ----------
    image_path : pathlib.Path
        Image path for checking corresponding file with prefix
    output_dir : str
        Output directory where the file with prefix is/will be stored
    prefix : str
        prefix to be added to the image file for check

    Returns
    -------
    str
        `image_path` for which file with prefix does not exist
    """
    img_path = Path(image_path)
    slide = img_path.parent.name
    if not Path.exists(Path(output_dir, slide, prefix + img_path.name)):
        return image_path
