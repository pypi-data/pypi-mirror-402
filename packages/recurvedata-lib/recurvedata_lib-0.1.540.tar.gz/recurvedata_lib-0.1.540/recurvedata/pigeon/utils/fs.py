import bz2
import contextlib
import datetime
import glob
import gzip
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from itertools import islice

from recurvedata.pigeon.utils import ensure_list


def new_tempfile(suffix="", prefix=None, dir=None):
    ts = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    suffix = "{}_{}".format(ts, suffix)
    kwargs = {"suffix": suffix, "dir": dir}
    if prefix:
        kwargs["prefix"] = prefix
    _, filename = tempfile.mkstemp(**kwargs)
    return filename


class new_stagefile_factory:
    def __init__(self, directory):
        if not os.path.isabs(directory):
            directory = os.path.join("/tmp", directory)
        self.directory = directory

    def __call__(self, name):
        os.makedirs(self.directory, exist_ok=True)
        return os.path.join(self.directory, name)


def merge_files(files, filename=None, num_skip_lines=0, delete=True):
    """Concat multiple files into one file.

    :param files: source file names
    :param filename: target filename, will create a tempfile if not provided
    :param num_skip_lines: skip n lines before merge into target file
    :param delete: delete source files after been merged
    :return: the target filename
    """
    if filename is None:
        _, filename = tempfile.mkstemp()

    if not num_skip_lines:
        if len(files) == 1 and delete:
            # just rename
            os.rename(files[0], filename)
        else:
            # merge by `cat` for better performance
            cmd = f'cat {" ".join(files)} > {filename}'
            _run_command(cmd)
    else:
        with open(filename, "wb") as fout:
            for f in files:
                with open(f, "rb") as fin:
                    for _ in range(num_skip_lines):
                        fin.readline()
                    shutil.copyfileobj(fin, fout)

    if delete:
        remove_files_safely(files)

    return filename


def skip_lines(infile, lines, inplace=False):
    tmpfile = new_tempfile()
    with open(infile, "rb") as fin, open(tmpfile, "wb") as fout:
        # skip the first n lines
        for _ in range(lines):
            fin.readline()

        # copy the rest to another file
        shutil.copyfileobj(fin, fout)

    if inplace:
        os.rename(tmpfile, infile)
        return infile
    return tmpfile


def read_lines(filename, start_line, lines_num=1):
    with open(filename) as f:
        for line in islice(f, start_line, start_line + lines_num):
            yield line


def is_file_empty(filename):
    """Detect file is empty or not, the non-exists file is considered as empty"""
    try:
        return os.stat(filename).st_size == 0
    except FileNotFoundError:
        return True


def remove_files(files):
    for f in ensure_list(files):
        os.unlink(f)


def remove_files_safely(files):
    with contextlib.suppress(OSError, TypeError, ValueError):
        remove_files(files)


def remove_files_by_pattern(pattern):
    files = glob.glob(pattern)
    logging.info("files to be deleted: %s", str(files))
    remove_files_safely(files)


def remove_folder_safely(folder):
    if not os.path.exists(folder):
        return
    shutil.rmtree(folder, ignore_errors=True)


def gzip_compress(filename, target_filename=None, using_cmd=False):
    """Compress a file using gzip
    :param filename: the path of input file
    :param target_filename: the path of output file, a temporary filename will be made otherwise
    :param using_cmd: use the gzip command line instead of Python GzipFile to speedup
    :return: the target_filename
    """
    if target_filename is None:
        target_filename = new_tempfile(suffix=".gz")

    if using_cmd:
        _run_command(f"gzip {filename} -c > {target_filename}")
        return target_filename

    with open(filename, "rb") as f_in, gzip.GzipFile(target_filename, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return target_filename


def gzip_decompress(filename, target_filename=None, using_cmd=False):
    """Decompress a gzip file
    :param filename: the path of the gzip file
    :param target_filename: the path of output file, a temporary filename will be made otherwise
    :param using_cmd: use the gzip command line instead of Python GzipFile to speedup
    :return: the target_filename
    """
    if target_filename is None:
        target_filename = new_tempfile()

    if using_cmd:
        _run_command(f"gzip -d {filename} -c > {target_filename}")
        return target_filename

    with gzip.GzipFile(filename, "rb") as f_in, open(target_filename, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return target_filename


def bzip2_compress(filename, target_filename=None, using_cmd=False):
    """Compress a file using bzip2
    :param filename: the path of input file
    :param target_filename: the path of output file, a temporary filename will be made otherwise
    :param using_cmd: use the bzip2 command line instead of Python BZ2File to speedup
    :return: the target_filename
    """
    if target_filename is None:
        target_filename = new_tempfile(suffix=".bz2")

    if using_cmd:
        _run_command(f"bzip2 {filename} -c > {target_filename}")
        return target_filename

    with open(filename, "rb") as f_in, bz2.BZ2File(target_filename, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return target_filename


def bzip2_decompress(filename, target_filename=None, using_cmd=False):
    """Decompress a bzip2 file
    :param filename: the path of the bzip2 file
    :param target_filename: the path of output file, a temporary filename will be made otherwise
    :param using_cmd: use the gzip command line instead of Python BZ2File to speedup
    :return: the target_filename
    """
    if target_filename is None:
        target_filename = new_tempfile()

    if using_cmd:
        _run_command(f"bzip2 -d {filename} -c > {target_filename}")
        return target_filename

    with bz2.BZ2File(filename, "rb") as f_in, open(target_filename, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return target_filename


def zip_compress(filename, target_filename=None, using_cmd=False, arcname=None):
    """Compress a file using zip
    :param filename: the path of input file
    :param target_filename: the path of output file, a temporary filename will be made otherwise
    :param using_cmd: use the zip command line instead of Python ZipFile to speedup
    :param arcname: filename in the archive file, only supported with using_cmd=False
    :return: the target_filename
    """
    if target_filename is None:
        target_filename = new_tempfile(suffix=".zip")

    directory, basename = os.path.split(filename.rstrip("/"))

    if using_cmd:
        # 先删除生成的临时文件，只使用生成的文件名，要不然会报错
        # zip warning: missing end signature--probably not a zip file (did you
        # zip warning: remember to use binary mode when you transferred it?)
        # zip warning: (if you are trying to read a damaged archive try -F)
        remove_files_safely(target_filename)
        if arcname is not None:
            logging.warning("arcname is not supported while using cmd")
        _run_command(f"cd {directory} && zip -r {target_filename} {basename}")
        return target_filename

    with zipfile.ZipFile(target_filename, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(filename, arcname=arcname or basename)
    return target_filename


def zip_decompress(filename, target_directory=None, using_cmd=False):
    """Decompress a .zip file
    :param filename: the path of input file
    :param target_directory: the path of output directory, a temporary directory will be made otherwise
    :param using_cmd: use the unzip command line instead of Python ZipFile to speedup
    :return: the output directory
    """
    if not target_directory:
        target_directory = tempfile.mkdtemp()

    if using_cmd:
        _run_command(f"unzip {filename} -d {target_directory}")
        return target_directory

    with zipfile.ZipFile(filename, "r") as zf:
        zf.extractall(target_directory)
    return target_directory


@contextlib.contextmanager
def ensure_remove(filename):
    try:
        yield filename
    finally:
        remove_files_safely(filename)


def schema_filename(base):
    return f"{base}.schema"


def exists(path):
    return os.path.exists(path)


def _run_command(cmd):
    logging.info(cmd)
    subprocess.check_output(cmd, shell=True)
