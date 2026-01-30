import os
import signal
from typing import ContextManager

from recurvedata.exceptions import TimeoutException


class timeout(ContextManager):
    """Timeout context manager

    Example:
        with timeout(seconds=1):
            do_something()
    """

    def __init__(self, seconds: float = 1.0, error_message: str = "Timeout"):
        self.seconds = seconds
        self.error_message = error_message + ", PID: " + str(os.getpid())

    def handle_timeout(self, signum, frame):
        raise TimeoutException(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.setitimer(signal.ITIMER_REAL, self.seconds)

    def __exit__(self, type_, value, traceback):
        signal.setitimer(signal.ITIMER_REAL, 0)
