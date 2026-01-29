import os.path
from typing import Callable


def assert_file_exists(
    path: str,
    exception_supplier: Callable[[], Exception] | None = None,
):
    if not os.path.isfile(path):
        if exception_supplier is None:
            raise ValueError(f"File does not exist: {path}")
        raise exception_supplier()


def assert_dir_exists(
    path: str,
    exception_supplier: Callable[[], Exception] | None = None,
):
    if not os.path.isdir(path):
        if exception_supplier is None:
            raise ValueError(f"Directory does not exist: {path}")
        raise exception_supplier()
