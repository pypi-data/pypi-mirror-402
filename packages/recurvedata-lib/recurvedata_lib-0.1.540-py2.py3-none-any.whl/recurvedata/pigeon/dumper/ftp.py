import os

import humanize

from recurvedata.pigeon.connector.ftp import FtpConnector
from recurvedata.pigeon.meta import DumperMeta
from recurvedata.pigeon.utils import LoggingMixin


class FtpDumperMeta(DumperMeta):
    def __init__(self):
        super().__init__()
        self.total_size = 0
        self.dumped_files = []

    def to_dict(self):
        speed = self.total_size / self.duration.total_seconds()
        return {
            "time_start": self.time_start,
            "time_finish": self.time_finish,
            "time_duration": self.duration,
            "total_size": self.total_size,
            "total_size_human": humanize.naturalsize(self.total_size, gnu=True),
            "download_speed": f"{humanize.naturalsize(speed, gnu=True)}/s",
            "num_dumped_files": len(self.dumped_files),
            "dumped_files": self.dumped_files,
        }


class FtpDumper(LoggingMixin):
    def __init__(self, connector, src, dst):
        assert isinstance(connector, FtpConnector)
        self.connector = connector
        self.src = src
        self.dst = dst
        self.meta = FtpDumperMeta()

    def execute(self):
        self.meta.mark_start()
        self.execute_impl()
        self.meta.mark_finish()
        self.logger.info(f"dumper meta: {self.meta.to_json(indent=2)}")
        return self.meta

    def execute_impl(self):
        if self.connector.is_ftp_dir(self.src):
            for item in self.connector.list_dir(self.src):
                if self.connector.is_ftp_dir(item):
                    self.logger.warning(f"{item} may be a directory. Skip")
                else:
                    _, remote_file = os.path.split(item)
                    dst = os.path.join(self.dst, remote_file)
                    self.connector.download_file(item, dst)
                    self.collect_meta(dst)
        else:
            self.connector.download_file(self.src, self.dst)
            self.collect_meta(self.dst)

    def collect_meta(self, filepath):
        if not os.path.exists(filepath):
            return None
        file_size = os.stat(filepath).st_size
        self.meta.dumped_files.append({"filepath": filepath, "size": file_size})
        self.meta.total_size += file_size
