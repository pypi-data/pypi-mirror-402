import logging
import subprocess
from typing import Optional

_logger = logging.getLogger(__name__)


def run(cmd: str, logger: Optional[logging.Logger] = _logger) -> None:
    logger.debug("Running command: %s", cmd)
    subprocess.check_call(cmd, shell=True)


def run_output(cmd: str, logger: Optional[logging.Logger] = _logger) -> str:
    logger.debug("Running command: %s", cmd)
    return subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
