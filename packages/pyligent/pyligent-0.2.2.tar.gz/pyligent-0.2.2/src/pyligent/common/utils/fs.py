import shutil
from pathlib import Path


def remove_dir(path: Path):
    """Removes directory recursively

    Args:
        path (str): path to directory
    """
    shutil.rmtree(path, ignore_errors=True)
