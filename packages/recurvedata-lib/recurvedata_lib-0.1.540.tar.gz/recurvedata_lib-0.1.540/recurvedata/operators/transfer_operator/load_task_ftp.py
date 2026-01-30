import logging

from recurvedata.operators.transfer_operator.load_task_sftp import SFTPLoadTask

logger = logging.getLogger(__name__)


class FTPLoadTask(SFTPLoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("ftp",)

    @staticmethod
    def ensure_directory_exists(ds, conf):
        ftp = ds.connector
        try:
            ftp.list_dir(conf["directory"])
        except OSError:
            logger.warning("failed to list directory %s, maybe not exists, try to make it", conf["directory"])
            ftp.makedir(conf["directory"])
