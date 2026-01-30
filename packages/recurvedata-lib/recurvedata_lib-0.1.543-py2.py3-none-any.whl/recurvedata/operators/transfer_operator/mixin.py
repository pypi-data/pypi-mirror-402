import csv
import logging
import os

try:
    from recurvedata.pigeon.handler.csv_handler import HiveCSVFileHandler
except ImportError:
    pass
logger = logging.getLogger(__name__)


class HiveTextfileConverterMixin(object):
    def convert_csv_to_hive_text_if_needed(self):
        """把 CSV 文件转换成 Hive 的文本文件"""
        if not self.handler_options.get("hive"):
            return

        if not os.path.exists(self.filename):
            logger.warning("%s is not exists", self.filename)
            return

        new_name = f"{self.filename}.hive"
        handler = HiveCSVFileHandler(filename=new_name)
        with open(self.filename, newline="") as inf:
            reader = csv.reader(inf)
            for row in reader:
                handler.handle(tuple(row))
        handler.close()

        if os.path.exists(new_name):
            os.rename(new_name, self.filename)
