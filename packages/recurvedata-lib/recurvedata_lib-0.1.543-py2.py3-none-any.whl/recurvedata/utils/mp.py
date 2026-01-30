import logging
import subprocess
import sys
import time
from multiprocessing import Process
from multiprocessing.queues import Queue
from queue import Empty, Full
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


def get_qsize(queue: Queue) -> Optional[int]:
    if sys.platform.lower() == "darwin":
        # queue.qsize() Raises NotImplementedError on Mac OSX because of broken sem_getvalue()
        return None
    return queue.qsize()


def safe_join_subprocesses(workers: list[Process], result_queue: Queue) -> list[Any]:
    result = []
    live_workers = list(workers)
    while live_workers:
        try:
            while 1:
                result.append(result_queue.get(False))
        except Empty:
            pass

        time.sleep(0.5)  # Give tasks a chance to put more data in
        if not result_queue.empty():
            continue
        live_workers = [p for p in live_workers if p.is_alive()]
    return result


def has_process_fail(workers: list[Process], log: bool = True) -> bool:
    for p in workers:
        if p.is_alive():
            continue
        if p.exitcode != 0:
            if log:
                logger.info(f"found process {p.pid} fail, exitcode {p.exitcode}")
            return True
    return False


def terminate_processes(workers: list[Process]):
    for p in workers:
        if p.is_alive():
            logger.info(f"start terminate process {p.pid}")
            p.terminate()
            logger.info(f"finish terminate process {p.pid}")


def master_safe_put_queue(
    queue: Queue,
    obj: Any,
    workers: list[Process],
    block: bool = True,
    timeout: Optional[int] = None,
) -> Optional[bool]:
    """
    A scenario where queue.put is called involves the master putting data into the queue, while workers consume the data.
     Under the default settings of timeout=None and block=True,
     if queue.maxsize is small and workers encounter errors that prevent them from consuming data promptly,
     this can cause the master to become stuck when calling queue.put.
    This master_safe_put_queue function can address this issue.
    When operating under timeout=None and block=True,
     it uses a small timeout (10 seconds) and continuously attempts queue.put(timeout=10) in a loop.
     If queue.put becomes stuck for 10 seconds, it raises a queue.Full error.

    Args:
        queue: multiprocessing.Queue
        obj: the object to be placed into the queue
        workers: subprocesses
        block: whether to block when the queue has no free slots
        timeout: the timeout for queue.put

    Returns:
        If there are any worker processes that have exited abnormally, it returns True,
        indicating that an abnormal worker exit caused the master's queue.put to become stuck.
        If all workers are functioning normally, it indicates that the workers are simply consuming data slowly,
        and it will continue to call queue.put(timeout=10) in a loop.
        In other cases, it behaves the same as queue.put.
    """
    if timeout is None and block:
        while True:
            try:
                return queue.put(obj, timeout=10)
            except Full:
                if has_process_fail(workers):
                    return True
    else:
        return queue.put(obj, block=block, timeout=timeout)


def safe_join_subprocesses_early_stop(workers: list[Process], result_queue: Queue) -> tuple[list, bool]:
    """
    wait and read the sub workers' result from result_queue,
    exit when
        1) one sub worker fail, or
        2) all sub workers success

    Args:
        workers: sub progresses
        result_queue: queue which sub progresses put result into

    Returns:
        result got from sub workers, and early_stop flag
    """
    result = []
    early_stop = False
    live_workers = list(workers)
    last_check_early_stop_time = time.time()
    while live_workers:
        try:
            while 1:
                result.append(result_queue.get(False))

                if time.time() - last_check_early_stop_time > 10:
                    if has_process_fail(live_workers):
                        early_stop = True
                        return result, early_stop
                    last_check_early_stop_time = time.time()

        except Empty:
            pass

        time.sleep(0.5)  # Give tasks a chance to put more data in
        if not result_queue.empty():
            continue

        if has_process_fail(live_workers):
            early_stop = True
            return result, early_stop
        last_check_early_stop_time = time.time()
        live_workers = [p for p in live_workers if p.is_alive()]
    return result, early_stop


def run_subprocess(
    cmd: Union[str, list],
    return_output=False,
    _logger: logging.Logger = logger,
    **kwargs,
) -> Optional[str]:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, **kwargs)
    logger.info(f"started sub process: {cmd}, pid: {p.pid}")
    lines: list[str] = []
    for raw_line in iter(p.stdout.readline, ""):
        line = raw_line.rstrip()
        _logger.info(line)
        if return_output:
            lines.append(line)
    p.wait()
    logger.info("sub process exited with return code %s", p.returncode)
    if p.returncode:
        raise subprocess.CalledProcessError(p.returncode, p.args)
    return "\n".join(lines)


def robust_run_subprocess(
    cmd: Union[str, list],
    _logger: logging.Logger = logger,
    **kwargs,
) -> tuple[str, int]:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, **kwargs)
    logger.info(f"started sub process: {cmd}, pid: {p.pid}")
    lines: list[str] = []
    for raw_line in iter(p.stdout.readline, ""):
        line = raw_line.rstrip()
        _logger.info(line)
        lines.append(line)
    p.wait()
    logger.info("sub process exited with return code %s", p.returncode)
    output = "\n".join(lines)
    return output, p.returncode
