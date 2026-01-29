import os.path
import shutil
from io import TextIOWrapper

from edi_core.utils.assertions import assert_file_exists
from edi_core.utils.env import get_env


def dir_exists(path: str) -> bool:
    return os.path.isdir(path)


def file_exists(path: str) -> bool:
    return os.path.isfile(path)


def path_exists(path: str) -> bool:
    return os.path.exists(path)


def move(src, dest):
    shutil.move(src, dest)


def delete_file(path: str):
    if file_exists(path):
        os.remove(path)


def get_file_name_without_extension(path: str) -> str:
    base_name = os.path.basename(path)
    name_without_extension, _ = os.path.splitext(base_name)
    return name_without_extension


def get_file_name_with_extension(path: str) -> str:
    return os.path.basename(path)


def get_output_dir():
    return os.path.expanduser(get_env("OUTPUT_DIR"))


def get_input_dir():
    return os.path.expanduser(get_env("INPUT_DIR"))


def to_output_path(relative_path: str):
    return os.path.join(get_output_dir(), relative_path)


def to_input_path(relative_path: str):
    return os.path.join(get_input_dir(), relative_path)


def ensure_parent_dir_exists(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def save_str_to_output_dir(relative_path: str, content: str) -> str:
    output_path = to_output_path(relative_path)
    ensure_parent_dir_exists(output_path)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(content)
    return output_path


def save_bytes_to_output_dir(relative_path: str, content: bytes) -> str:
    output_path = to_output_path(relative_path)
    ensure_parent_dir_exists(output_path)
    with open(output_path, 'wb') as file:
        file.write(content)
    return output_path


def open_file_in_output_for_write(relative_path: str) -> TextIOWrapper:
    output_path = to_output_path(relative_path)
    ensure_parent_dir_exists(output_path)
    return open(output_path, 'w', encoding='utf-8')


def open_file_in_input_for_read(relative_path: str) -> TextIOWrapper:
    input_path = to_input_path(relative_path)
    return open(input_path, 'r', encoding='utf-8')


def read_file(path: str) -> str:
    assert_file_exists(path)
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()


def get_app_dir():
    return os.path.expanduser(get_env("APP_DIR"))


def get_path_from_app_dir(relative_path: str) -> str:
    return os.path.join(get_app_dir(), relative_path)
