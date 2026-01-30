import bz2
import gzip
import logging
import os
import shutil
import struct
import tarfile
import tempfile
import zipfile
import zlib
from typing import Callable, NamedTuple, Optional

from recurvedata.utils import files, shell

logger = logging.getLogger(__name__)


class _Config(NamedTuple):
    opener: Callable
    ext: str
    compress_cmd: str
    decompress_cmd: str


_gzip_cfg = _Config(gzip.open, "gz", "gzip", "gzip -d")
_bzip2_cfg = _Config(bz2.open, "bz2", "bzip2", "bzip2 -d")


def gzip_compress(src_file: str, dst_file: str = None, using_cmd: bool = False, inplace: bool = False) -> str:
    """Compress a file using gzip

    Args:
        src_file: the path of input file
        dst_file: the path of output file, a temporary filename will be made otherwise
        using_cmd: use the gzip command line instead of Python gzip to speedup
        inplace: replace the src_file with dst_file if True

    Returns:
        the dst_file if inplace is False, otherwise the src_file
    """
    return _compress_file(_gzip_cfg, src_file, dst_file, using_cmd, inplace)


def gzip_decompress(src_file: str, dst_file: str = None, using_cmd: bool = False, inplace: bool = False) -> str:
    """Decompress a .gz file

    Args:
        src_file: the path of input file
        dst_file: the path of output file, a temporary filename will be made otherwise
        using_cmd: use the gzip command line instead of Python gzip to speedup
        inplace: replace the filename with target_filename if True

    Returns:
        the dst_file if inplace is False, otherwise the src_file
    """
    return _decompress_file(_gzip_cfg, src_file, dst_file, using_cmd, inplace)


def bzip2_compress(src_file: str, dst_file: str = None, using_cmd: bool = False, inplace: bool = False) -> str:
    """Compress a file using bzip2

    Args:
        src_file: the path of input file
        dst_file: the path of output file, a temporary filename will be made otherwise
        using_cmd: use the bzip2 command line instead of Python bzip2 to speedup
        inplace: replace the filename with target_filename if True

    Returns:
        the dst_file if inplace is False, otherwise the src_file
    """
    return _compress_file(_bzip2_cfg, src_file, dst_file, using_cmd, inplace)


def bzip2_decompress(src_file: str, dst_file: str = None, using_cmd: bool = False) -> str:
    """Decompress a .bz2 file

    Args:
        src_file: the path of input file
        dst_file: the path of output file, a temporary filename will be made otherwise
        using_cmd: use the bzip2 command line instead of Python bzip2 to speedup

    Returns:
        the dst_file if inplace is False, otherwise the src_file
    """
    return _decompress_file(_bzip2_cfg, src_file, dst_file, using_cmd, False)


def _compress_file(
    cfg: _Config, src_file: str, dst_file: str = None, using_cmd: bool = False, inplace: bool = False
) -> str:
    if dst_file is None:
        dst_file = files.new_tempfile(suffix=f".{cfg.ext}")

    if using_cmd:
        shell.run(f"{cfg.compress_cmd} {src_file} -c > {dst_file}", logger)
    else:
        with open(src_file, "rb") as f_in, cfg.opener(dst_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    return files.replace_file_with_temp(dst_file, src_file, inplace)


def _decompress_file(
    cfg: _Config, src_file: str, dst_file: str = None, using_cmd: bool = False, inplace: bool = False
) -> str:
    if dst_file is None:
        dst_file = files.new_tempfile()

    if using_cmd:
        shell.run(f"{cfg.decompress_cmd} {src_file} -c > {dst_file}", logger)
    else:
        with cfg.opener(src_file, "rb") as f_in, open(dst_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    return files.replace_file_with_temp(dst_file, src_file, inplace)


def zip_compress(src_file: str, dst_file: str = None, using_cmd: bool = False, arcname: str = None) -> str:
    """Compress a file using zip

    Args:
        src_file: the path of input file
        dst_file: the path of output file, a temporary filename will be made otherwise
        using_cmd: use the zip command line instead of Python ZipFile to speedup
        arcname: filename in the archive file, only supported with using_cmd=False

    Returns:
        the target_filename
    """
    if dst_file is None:
        dst_file = files.new_tempfile(suffix=".zip")

    directory, basename = os.path.split(src_file.rstrip("/"))

    if using_cmd:
        # 先删除生成的临时文件，只使用生成的文件名，要不然会报错
        # zip warning: missing end signature--probably not a zip file (did you
        # zip warning: remember to use binary mode when you transferred it?)
        # zip warning: (if you are trying to read a damaged archive try -F)
        files.remove_files_safely(dst_file)
        if arcname is not None:
            logger.warning("arcname is not supported while using cmd")
        shell.run(f"cd {directory} && zip -r {dst_file} {basename}", logger)
        return dst_file

    with zipfile.ZipFile(dst_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(src_file, arcname=arcname or basename)
    return dst_file


def zip_decompress(src_file: str, target_directory: str = None, using_cmd: bool = False) -> str:
    """Decompress a .zip file into a directory

    Args:
        src_file: the path of input file
        target_directory: the path of output directory, a temporary directory will be made otherwise
        using_cmd: use the unzip command line instead of Python ZipFile to speedup

    Returns:
        the output directory
    """
    if not target_directory:
        target_directory = tempfile.mkdtemp()

    if using_cmd:
        shell.run(f"unzip {src_file} -d {target_directory}", logger)
        return target_directory

    with zipfile.ZipFile(src_file, "r") as zf:
        zf.extractall(target_directory)
    return target_directory


def mysql_compress(value: bytes) -> Optional[bytes]:
    """A Python implementation of COMPRESS function of MySQL."""
    if value is None:
        return None
    if value == b"":
        return b""
    size: bytes = struct.pack("I", len(value))
    data: bytes = zlib.compress(value)
    return size + data


def mysql_uncompress(value: bytes) -> bytes:
    """A Python implementation of UNCOMPRESS function of MySQL.

    Used to decompress result of COMPRESS function.

    https://dev.mysql.com/doc/refman/5.7/en/encryption-functions.html#function_compress
    """
    size_byte: int = 4
    if not value or len(value) < size_byte:
        return value

    return zlib.decompress(value[size_byte:])


def tar_gzip_uncompress(tar_gz_path, extract_path):
    logger.info(f"extract tar.gz {tar_gz_path} to {extract_path}")
    os.makedirs(extract_path, exist_ok=True)
    with tarfile.open(tar_gz_path, "r:gz") as tar:
        tar.extractall(path=extract_path)
