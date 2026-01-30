import collections
import contextlib
import csv
import datetime
import fcntl
import glob
import hashlib
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import IO, Any, Sequence, Union

from recurvedata.utils import helpers, shell

logger = logging.getLogger(__name__)
PathLike = Union[str, os.PathLike]

_csv_dialect_options = {
    "delimiter": ",",
    "quoting": csv.QUOTE_ALL,
    "lineterminator": "\r\n",
}


def new_tempfile(suffix: str = "", prefix: str = None, dir: str = None) -> str:
    """Create a tempfile with a random filename.

    Args:
        suffix: suffix of the filename
        prefix: prefix of the filename
        dir: directory to store the file

    Returns:
        the filename
    """
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    kwargs = {"suffix": f"{ts}_{suffix}", "dir": dir}
    if prefix:
        kwargs["prefix"] = prefix
    _, filename = tempfile.mkstemp(**kwargs)
    return filename


def new_tempdir(suffix: str = "", prefix: str = None, dir: str = None) -> str:
    """Create a tempdir with a random filename.

    Args:
        suffix: suffix of the filename
        prefix: prefix of the filename
        dir: directory to store the file

    Returns:
        the filename
    """
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    kwargs = {"suffix": f"{ts}_{suffix}", "dir": dir}
    if prefix:
        kwargs["prefix"] = prefix
    return tempfile.mkdtemp(**kwargs)


def merge_files(
    files: Sequence[PathLike],
    filename: str = None,
    num_skip_lines: int = 0,
    delete: bool = True,
) -> str:
    """Concat multiple files into one.

    Args:
        files: source file names
        filename: target filename, will create a tempfile if not provided
        num_skip_lines: skip n lines before merge into target file
        delete: delete source files after being merged

    Returns:
        the target filename
    """
    if filename is None:
        _, filename = tempfile.mkstemp()

    if num_skip_lines:
        with open(filename, "wb") as fout:
            for f in files:
                with open(f, "rb") as fin:
                    for _ in range(num_skip_lines):
                        fin.readline()
                    shutil.copyfileobj(fin, fout)

    else:
        if len(files) == 1 and delete:
            os.rename(files[0], filename)
        else:
            # merge by `cat` for better performance
            shell.run(f'cat {" ".join(files)} > {filename}', logger)

    if delete:
        remove_files_safely(files)

    return filename


def remove_lines_from_start(filename: PathLike, lines: int, inplace: bool = False) -> str:
    """Skip the first n lines of a file.

    Args:
        filename: source file name
        lines: number of lines to be skipped
        inplace: modify the file in-place or not

    Returns:
        the filename, will be the same as the source file if inplace is True
    """
    tmp_file = new_tempfile()
    with open(filename, "rb") as f_in, open(tmp_file, "wb") as f_out:
        # skip the first n lines
        for _ in range(lines):
            next(f_in, None)

        # copy the rest to another file
        shutil.copyfileobj(f_in, f_out)

    return replace_file_with_temp(tmp_file, filename, inplace)


def is_file_empty(filename: PathLike) -> bool:
    """Detect file is empty or not, the non-exists file is considered as empty"""
    try:
        return os.stat(filename).st_size == 0
    except FileNotFoundError:
        return True


def remove_files(files: Sequence[PathLike]) -> None:
    """Remove files."""
    file_list: list[PathLike] = helpers.ensure_list(files)
    for f in file_list:
        os.unlink(f)


def remove_files_safely(files: Sequence[PathLike]) -> None:
    """Remove files safely. Ignore the errors."""
    with contextlib.suppress(OSError, TypeError, ValueError):
        remove_files(files)


def remove_files_by_pattern(pattern: str) -> None:
    """Remove files by pattern. Ignore the errors."""
    files = glob.glob(pattern)
    logger.info("files to be deleted: %s", str(files))
    remove_files_safely(files)


def remove_folder_safely(folder: str) -> None:
    """Remove folder safely. Ignore the errors."""
    if not os.path.exists(folder):
        return
    shutil.rmtree(folder, ignore_errors=True)


@contextlib.contextmanager
def ensure_remove(filename: PathLike):
    """Remove file safely after using."""
    try:
        yield filename
    finally:
        remove_files_safely(filename)


def convert_excel_to_csv(
    src_file: PathLike,
    dst_file: PathLike = None,
    skiprows: int = 0,
    inplace: bool = True,
) -> str:
    """Convert an Excel file to a CSV file

    Args:
        src_file: the path of the Excel file
        dst_file: the path of output file, a temporary filename will be made otherwise
        skiprows: skip the first N rows
        inplace: replace the original file if True

    Returns:
        the target_filename
    """
    import pandas as pd

    if not dst_file:
        dst_file = new_tempfile(dir=os.path.dirname(src_file))

    df = pd.read_excel(src_file, skiprows=skiprows)
    df.to_csv(dst_file, line_terminator="\r\n", header=False, index=False)

    return replace_file_with_temp(dst_file, src_file, inplace)


def convert_jsonlines_to_csv(
    src_file: PathLike,
    dst_file: PathLike = None,
    skiprows: int = 0,
    src_encoding: str = "utf8",
    inplace: bool = True,
) -> str:
    """Convert a JSON Lines file to a CSV file

    Args:
        src_file: the path of the JSON Lines file
        dst_file: the path of output file, a temporary filename will be made otherwise
        skiprows: skip the first N rows
        src_encoding: the encoding of the JSON Lines file
        inplace: replace the original file if True

    Returns:
        the target_filename
    """
    if not dst_file:
        dst_file = new_tempfile(dir=os.path.dirname(src_file))

    decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
    with open(src_file, "r", encoding=src_encoding) as f_in, open(dst_file, "w") as f_out:
        _skip_header_rows(f_in, skiprows)

        line = f_in.readline()
        row = decoder.decode(line)
        writer = csv.DictWriter(f_out, fieldnames=list(row.keys()), **_csv_dialect_options)
        writer.writerow(row)

        for line in f_in:
            writer.writerow(decoder.decode(line))

    return replace_file_with_temp(dst_file, src_file, inplace)


def convert_encoding(
    filename: PathLike,
    src_encoding: str,
    dst_encoding: str = "utf8",
    skiprows: int = 0,
    inplace: bool = True,
) -> str:
    """Convert the encoding of a file

    Args:
        filename: the path of the file
        src_encoding: the encoding of the file
        dst_encoding: the encoding to convert to
        skiprows: skip the first N rows
        inplace: replace the original file if True

    Returns:
        the target_filename
    """
    if src_encoding == dst_encoding:
        return filename

    target = new_tempfile(dir=os.path.dirname(filename))
    with open(filename, "r", encoding=src_encoding) as f_in, open(target, "w", encoding=dst_encoding) as f_out:
        _skip_header_rows(f_in, skiprows)
        shutil.copyfileobj(f_in, f_out)

    return replace_file_with_temp(target, filename, inplace)


def convert_csv_dialect(
    filename: PathLike,
    src_dialect_options: dict[str, Any],
    dst_dialect_options: dict[str, Any] = None,
    skiprows: int = 0,
    src_encoding: str = "utf8",
    inplace: bool = True,
):
    """Convert the dialect of a CSV file

    Args:
        filename: the path of the CSV file
        src_dialect_options: the dialect of the file
        dst_dialect_options: the dialect to convert to
        skiprows: skip the first N rows
        src_encoding: the encoding of the file
        inplace: replace the original file if True

    Returns:
        the target_filename
    """
    if dst_dialect_options is None:
        dst_dialect_options = _csv_dialect_options.copy()

    if _same_dict(src_dialect_options, dst_dialect_options):
        if src_encoding != "utf8":
            convert_encoding(filename, src_encoding=src_encoding, skiprows=skiprows, inplace=True)
        return filename

    dst_file = new_tempfile(dir=os.path.dirname(filename))
    with open(filename, "r", encoding=src_encoding) as f_in, open(dst_file, "w") as f_out:
        _skip_header_rows(f_in, skiprows)

        reader = csv.reader(f_in, **src_dialect_options)
        writer = csv.writer(f_out, **dst_dialect_options)
        for row in reader:
            writer.writerow(row)

    return replace_file_with_temp(dst_file, filename, inplace)


def replace_file_with_temp(tmp_file: PathLike, target_file: PathLike, inplace: bool = False) -> PathLike:
    """Determine the filename of the converted file, and rename it if inplace is True"""
    if inplace:
        os.rename(tmp_file, target_file)
        return target_file
    return tmp_file


def _skip_header_rows(f: IO, n: int = 0):
    for _ in range(n):
        f.readline()


def _same_dict(a: dict, b: dict) -> bool:
    if len(a) != len(b):
        return False
    for k in a:
        if k not in b or a[k] != b[k]:
            return False
    return True


def calculate_md5(filepath: Path | str) -> str:
    md5_hash = hashlib.md5()
    chunk_size = 1024 * 1024
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


class FileLock:
    """A file lock using fcntl.
    copy from recurve web
    """

    def __init__(self, lock_file_path: str | Path):
        self.lock_file_path = Path(lock_file_path)
        self.fd = None

    def acquire(self):
        try:
            self.fd = self.lock_file_path.open("w")
            # Acquire an exclusive lock, this will block until the lock is acquired
            fcntl.flock(self.fd, fcntl.LOCK_EX)
        except Exception as e:
            self._reset()
            raise e  # Propagate unexpected exceptions

    def release(self):
        if not self.fd:
            return
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        except Exception as e:
            raise e  # Propagate unexpected exceptions
        finally:
            self._reset()

    def _reset(self):
        if self.fd:
            self.fd.close()
            self.fd = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def __del__(self):
        try:
            self.release()
        except Exception:
            # Suppress exceptions in __del__, as we've done our best
            pass
