import os

from recurvedata.operators.utils.fs import get_exist_path


class Config(object):  # todo: move to somewhere else
    DATA_ROOT = "/opt/recurve/worker_data"

    PYENV_BASE_BIN_PATH = os.path.join(
        get_exist_path([os.environ.get("RECURVE__WORKER__PYENV__BASE"), "~/.pyenv"]) or "/opt/pyenv",
        "versions/{pyenv}/bin",
    )
    PYENV_PYTHON_PATH = os.path.join(PYENV_BASE_BIN_PATH, "python")

    RECURVE_EXECUTOR_PYENV_BIN_PATH = PYENV_BASE_BIN_PATH.format(pyenv="recurve_executor")

    REDIS_URL = "redis://localhost:6381/13"


# CONF 是一个全局对象，用于获取配置项。
CONF = Config()
