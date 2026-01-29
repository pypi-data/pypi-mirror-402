import os
import platform

from dotenv import load_dotenv

dotenv_loaded = False


def load_env():
    global dotenv_loaded
    if not dotenv_loaded:
        load_dotenv()
        dotenv_loaded = True


def get_env(key: str, default: str = None):
    load_env()
    value = os.environ.get(key)
    if value:
        return value

    if default is None:
        raise ValueError(f'Env {key} not found')
    else:
        return default


def get_platform():
    return platform.platform()


def get_system():
    return platform.system()


def is_windows():
    return get_system() == 'Windows'


def get_app_name():
    return get_env('APP_NAME')
