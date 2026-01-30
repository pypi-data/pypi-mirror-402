import datetime
import ftplib
import logging
import os
import shutil
import time

import humanize

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.utils import LoggingMixin


@register_connector_class("ftp")
class FtpConnector(LoggingMixin):
    def __init__(self, host, user, password, **kwargs):
        self.host = host
        self.username = user
        self.password = password
        self.port = kwargs.pop("port", ftplib.FTP_PORT)

        # The ftplib.FTP is stupid, it doesn't support the port parameter in the constructor
        # so we have to use the connect method to specify the port
        if self.port == ftplib.FTP_PORT:
            self.ftp = ftplib.FTP(host=self.host, user=self.username, passwd=self.password, **kwargs)
        else:
            self.ftp = ftplib.FTP(**kwargs)
            self.ftp.connect(self.host, self.port)
            if user:
                self.ftp.login(user=user, passwd=password, acct=kwargs.get("acct", ""))

    def close(self):
        ftp = self.ftp
        ftp.quit()
        self.ftp = None

    def list_dir(self, path):
        try:
            return self.ftp.nlst(path)
        except ftplib.all_errors:
            return []

    def rename(self, from_name, to_name):
        return self.ftp.rename(from_name, to_name)

    def makedir(self, path):
        self.ftp.mkd(path)

    def rmdir(self, path):
        self.ftp.rmd(path)

    def rm(self, name):
        self.ftp.delete(name)

    def pwd(self):
        return self.ftp.pwd()

    def size(self, name):
        return self.ftp.size(name)

    def is_ftp_dir(self, path):
        original_cwd = self.pwd()
        try:
            self.ftp.cwd(path)
            self.ftp.cwd(original_cwd)
            return True
        except ftplib.all_errors:
            return False

    def download_file(self, src_file, dst_file):
        exists = True
        local_dir = os.path.dirname(dst_file)
        if not os.path.exists(local_dir):
            exists = False
            os.makedirs(local_dir)
        try:
            total_bytes = self.size(src_file)
            with open(dst_file, "wb") as f:
                writer = StatsReaderWriter(f, total_bytes)
                self.ftp.retrbinary(f"RETR {src_file}", writer.write)
            writer.show_stat()
            self.logger.info(f"successfully downloaded {src_file} to {dst_file}")
        except ftplib.all_errors as e:
            os.unlink(dst_file)
            if not exists:
                shutil.rmtree(local_dir)
            self.logger.exception(f"failed to download {src_file}")
            raise e

    def upload_file(self, src_file, dst_file):
        if not os.path.isfile(src_file):
            raise ValueError(f"{src_file} is not a file")
        try:
            total_bytes = os.stat(src_file).st_size
            with open(src_file, "rb") as f:
                reader = StatsReaderWriter(f, total_bytes)
                self.ftp.storbinary(f"STOR {dst_file}", reader)
            reader.show_stat()
            self.logger.info(f"successfully uploaded {src_file} to {dst_file}")
        except ftplib.all_errors as e:
            self.logger.exception(f"failed to upload {src_file}")
            raise e


class StatsReaderWriter(object):
    def __init__(self, fp, total_bytes, show_stats_bytes=1024 * 1024):
        self.fp = fp
        self.total_bytes = total_bytes
        self.show_stats_bytes = show_stats_bytes

        self._transferred_bytes = 0
        self._start_time = time.time()
        self._end_time = 0

    def read(self, n):
        rv = self.fp.read(n)
        self._incr_transferred_bytes(n)
        return rv

    def write(self, data):
        rv = self.fp.write(data)
        self._incr_transferred_bytes(len(data))
        return rv

    def close(self):
        if self.fp.closed:
            if self._end_time == 0:
                self._end_time = time.time()
            return
        try:
            self.fp.close()
        except Exception:
            pass
        self._end_time = time.time()

    def _incr_transferred_bytes(self, n):
        for _ in range(n):
            self._transferred_bytes += 1
            if self._transferred_bytes % self.show_stats_bytes == 0:
                self.show_stat()

    def show_stat(self):
        if self._end_time == 0:
            end_time = time.time()
        else:
            end_time = self._end_time
        duration = end_time - self._start_time
        if duration == 0:
            speed = 0
        else:
            speed = self._transferred_bytes / duration

        if self.total_bytes == 0:
            progress = 0
        else:
            progress = 100 * self._transferred_bytes / self.total_bytes
        logging.info(
            "transferred %s in %s, average speed: %s/s, progress: %.2f%%",
            humanize.naturalsize(self._transferred_bytes, gnu=True),
            datetime.timedelta(seconds=duration),
            humanize.naturalsize(speed, gnu=True),
            progress,
        )
