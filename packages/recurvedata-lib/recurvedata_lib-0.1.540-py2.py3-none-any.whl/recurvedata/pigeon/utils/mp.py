import logging
import threading
import time
from multiprocessing import Process
from multiprocessing.queues import Queue
from queue import Empty, Full
from subprocess import PIPE, STDOUT, CalledProcessError, Popen
from typing import Any, List, Optional, Tuple, Union


def safe_join_subprocesses(workers, result_queue):
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


def has_process_fail(workers: List[Process], log=True):
    for p in workers:
        if p.is_alive():
            continue
        if p.exitcode != 0:
            if log:
                logging.info(f"found process {p.pid} fail, exitcode {p.exitcode}")
            return True
    return False


def terminate_processes(workers: List[Process]):
    for p in workers:
        if p.is_alive():
            logging.info(f"start terminate process {p.pid}")
            p.terminate()
            logging.info(f"finish terminate process {p.pid}")


def master_safe_put_queue(
    queue: Queue, obj: Any, workers: List[Process], block=True, timeout: Optional[int] = None
) -> Optional[bool]:
    """
    一种调用 queue.put 的场景，是 master put 数据，worker 消费数据.
    在默认的 timeout=None, block=True 下，
    如果 queue.maxsize 较小，且 workers 遇到了报错，没法及时消费，
    就会导致 master 在调用 queue.put 的时候卡住。
    master_safe_put_queue 可以解决这个问题，
    当 timeout=None, block=True 的情况下，
    会用一个较小的 timeout（10s），死循环不断尝试 queue.put(timeout=10)，
    当 queue.put 卡住达到 10s 的时候，会报错 queue.Full，
    这时候检查 workers 是否有异常退出的进程，
        如果 workers 有异常退出的进程，则返回 True, 表示 worker 有异常退出导致 master queue.put 卡住;
        如果 workers 都正常，则表示确实是 worker 消费速度较慢，重新调用 queue.put(timeout=10) 继续死循环

    其他情况下与 queue.put 一致

    :param queue: queue
    :param obj: the obj to put into queue
    :param workers: sub processes
    :param block: should block when queue has no free slot
    :param timeout: queue.put's timeout
    :return: True 表示 workers 有异常退出导致 master queue.put 卡住；否则返回 None
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


def safe_join_subprocesses_early_stop(workers: List[Process], result_queue: Queue) -> Tuple[List, bool]:
    """
    this function wait and read the sub workers' result from result_queue,
    exit when
        1) one sub worker fail
        or
        2) all sub workers success
    :param workers: sub progresses
    :param result_queue: queue which sub progresses put result into
    :return: result got from sub workers, and early_stop flag
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


def run_subprocess(cmd: Union[str, List], stdout=PIPE, stderr=STDOUT, return_output=False, **kwargs) -> Optional[str]:
    p = Popen(cmd, stdout=stdout, stderr=stderr, **kwargs)
    logging.info(f"started sub process: {cmd}, pid: {p.pid}")
    lines: List[str] = []
    for raw_line in iter(p.stdout.readline, b""):
        line = raw_line.decode("utf8").rstrip()
        logging.info(line)
        if return_output:
            lines.append(line)
    p.wait()
    logging.info("sub process exited with return code %s", p.returncode)
    if p.returncode:
        raise CalledProcessError(p.returncode, p.args)
    return "\n".join(lines)


class PropagatingThread(threading.Thread):
    def run(self):
        self.exc = None
        try:
            if hasattr(self, "_Thread__target"):
                # Thread uses name mangling prior to Python 3.
                self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            else:
                self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        super().join(timeout)
        if self.exc:
            raise self.exc
        return self.ret
