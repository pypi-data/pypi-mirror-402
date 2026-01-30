import collections
import csv
import json
import os
import shutil
import time

from recurvedata.pigeon.utils import fs

_csv_dialect_options = {
    "delimiter": ",",
    "quoting": csv.QUOTE_ALL,
    "lineterminator": "\r\n",
}


def gzip_decompress(src_file, dst_file=None, inplace=True):
    if not dst_file:
        dst_file = fs.new_tempfile(dir=os.path.dirname(src_file))
    fs.gzip_decompress(src_file, dst_file)

    if inplace:
        os.rename(dst_file, src_file)
        return src_file
    return dst_file


def zip_decompress(src_file, dst_file=None, inplace=True):
    if not dst_file:
        # Create a temporary directory for extraction
        dst_dir = os.path.join(os.path.dirname(src_file), f"tmp_zip_{os.path.basename(src_file)}_{int(time.time())}")
        os.makedirs(dst_dir, exist_ok=True)
        dst_file = dst_dir

    # Ensure the target directory exists
    if not os.path.exists(dst_file):
        os.makedirs(dst_file, exist_ok=True)

    fs.zip_decompress(src_file, dst_file)

    if inplace:
        # For inplace replacement, we need to:
        # 1. Remove the original zip file
        # 2. Move the extracted content to the original location
        extracted_files = os.listdir(dst_file)
        if len(extracted_files) == 1:
            # If there's only one file, move it to replace the original
            extracted_file = os.path.join(dst_file, extracted_files[0])
            os.remove(src_file)  # Remove original zip
            os.rename(extracted_file, src_file)  # Move extracted file to original location
            os.rmdir(dst_file)  # Clean up empty temp dir
        else:
            # If multiple files, keep them in the directory
            os.remove(src_file)  # Remove original zip
            return dst_file  # Return the directory containing extracted files
        return src_file
    return dst_file


def convert_excel_to_csv(src_file, dst_file=None, skiprows=0, inplace=True, lineterminator="\r\n"):
    import pandas as pd

    if not dst_file:
        dst_file = fs.new_tempfile(dir=os.path.dirname(src_file))

    df = pd.read_excel(src_file, skiprows=skiprows)
    df.to_csv(dst_file, lineterminator=lineterminator, header=False, index=False)
    if inplace:
        os.rename(dst_file, src_file)
        return src_file
    return dst_file


def convert_jsonlines_to_csv(src_file, dst_file=None, skiprows=0, src_encoding="utf8", inplace=True):
    """把 JSONLines 格式文件转换成 CSV，JSONLines 文件的每一行都是一个 JSON object"""
    if not dst_file:
        dst_file = fs.new_tempfile(dir=os.path.dirname(src_file))

    decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
    with open(src_file, "r", encoding=src_encoding) as f_in, open(dst_file, "w") as f_out:
        _skip_header_rows(f_in, skiprows)

        line = f_in.readline()
        row = decoder.decode(line)
        writer = csv.DictWriter(f_out, fieldnames=list(row.keys()), **_csv_dialect_options)
        writer.writerow(row)

        for line in f_in:
            writer.writerow(decoder.decode(line))

    if inplace:
        os.rename(dst_file, src_file)
        return src_file
    return dst_file


def convert_encoding(filename, src_encoding, dst_encoding="utf8", skiprows=0, inplace=True):
    if src_encoding == dst_encoding:
        return filename

    target = fs.new_tempfile(dir=os.path.dirname(filename))
    with open(filename, "r", encoding=src_encoding) as f_in, open(target, "w", encoding=dst_encoding) as f_out:
        _skip_header_rows(f_in, skiprows)

        shutil.copyfileobj(f_in, f_out)

    if inplace:
        os.rename(target, filename)
        return filename
    return target


def convert_csv_dialect(
    filename, src_dialect_options, dst_dialect_options=None, skiprows=0, src_encoding="utf8", inplace=True
):
    if dst_dialect_options is None:
        dst_dialect_options = _csv_dialect_options.copy()

    if _same_dict(src_dialect_options, dst_dialect_options):
        if src_encoding != "utf8":
            convert_encoding(filename, src_encoding=src_encoding, skiprows=skiprows, inplace=True)
        return filename

    dst_file = fs.new_tempfile(dir=os.path.dirname(filename))
    with open(filename, "r", encoding=src_encoding) as f_in, open(dst_file, "w") as f_out:
        _skip_header_rows(f_in, skiprows)

        reader = csv.reader(f_in, **src_dialect_options)
        writer = csv.writer(f_out, **dst_dialect_options)
        for row in reader:
            writer.writerow(row)

    if inplace:
        os.rename(dst_file, filename)
        return filename
    return dst_file


def _skip_header_rows(f, n=0):
    for _ in range(n):
        f.readline()


def _same_dict(a: dict, b: dict):
    if len(a) != len(b):
        return False
    for k in a:
        if k not in b or a[k] != b[k]:
            return False
    return True
