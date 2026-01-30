import concurrent.futures
import logging
import os
import shutil

from pywebhdfs.webhdfs import PyWebHdfsClient

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.utils import extract_dict, mp


@register_connector_class('hdfs')
class HDFSConnector(object):
    def __init__(self, host, port, username=None, user_name=None, **kwargs):
        self.host = host
        self.port = port
        self.user_name = username or user_name
        extra_opts = extract_dict(kwargs, ['path_to_hosts', 'timeout', 'base_uri_pattern', 'request_extra_opts'])
        self.hdfs = PyWebHdfsClient(host=self.host, port=self.port, user_name=self.user_name, **extra_opts)

    def list_dir(self, path):
        return self.hdfs.list_dir(path)

    def make_dir(self, path, **kwargs):
        return self.hdfs.make_dir(path, **kwargs)

    def delete_file(self, path, recursive=False):
        return self.hdfs.delete_file_dir(path, recursive=recursive)

    def upload_file(self, local_path, hdfs_path=None, overwrite=True):
        if not hdfs_path:
            hdfs_path = os.path.basename(local_path)

        if not os.path.dirname(hdfs_path):
            hdfs_path = os.path.join('/tmp', hdfs_path)

        self.delete_file(hdfs_path)

        with open(local_path, 'rb') as data:
            self.hdfs.create_file(hdfs_path, data, overwrite=overwrite)
        return hdfs_path

    def upload_files(self, local_paths, hdfs_folder, num_threads=2):
        """num_threads is currently not used"""
        for lf in local_paths:
            hdfs_filename = os.path.join(hdfs_folder, os.path.basename(lf))
            self.upload_file(lf, hdfs_filename, overwrite=True)
            logging.info(f'uploaded {lf} to {hdfs_filename}')


class HDFSCliConnector(HDFSConnector):
    def __init__(self, hdfs_cli=None, **kwargs):
        if not hdfs_cli:
            hdfs_cli = shutil.which('hdfs')
        if not hdfs_cli:
            raise ValueError('could not locate hdfs command line')
        self.hdfs_cli = hdfs_cli

    def list_dir(self, path):
        raise NotImplementedError

    def make_dir(self, path, **kwargs):
        self._run_cmd(f'-mkdir {path}')

    def delete_file(self, path, recursive=False):
        self._run_cmd(f'-rm {"-r" if recursive else ""} -f {path}')

    def upload_file(self, local_path, hdfs_path=None, overwrite=True):
        if not hdfs_path:
            hdfs_path = os.path.basename(local_path)

        if not os.path.dirname(hdfs_path):
            hdfs_path = os.path.join('/tmp', hdfs_path)
        self._run_cmd(f'-put {"-f" if overwrite else ""} {local_path} {hdfs_path}')
        return hdfs_path

    def upload_files(self, local_paths, hdfs_folder, num_threads=2):
        local_path_groups = partition_files_equally(local_paths, num_threads)
        sub_cmds = [f'-put {" ".join(x)} {hdfs_folder}' for x in local_path_groups]
        pool_size = min(num_threads, len(local_path_groups))
        with concurrent.futures.ThreadPoolExecutor(max_workers=pool_size) as executor:
            for _ in executor.map(self._run_cmd, sub_cmds):
                # exhaust the iterator returned by executor.map
                # if any task raises an exception, other tasks will be canceled by executor
                pass

    def _run_cmd(self, sub_cmd):
        cmd = f'{self.hdfs_cli} dfs {sub_cmd}'
        logging.info(cmd)
        output = mp.run_subprocess(cmd, return_output=True, shell=True)
        if 'NotReplicatedYetException' in output:
            raise IOError('Incomplete copying from /data/oneflow to /tmp/oneflow/ !')
        return output


def partition_files_equally(local_paths, num_groups: int):
    groups = _do_partition_files_equally([(f, os.stat(f).st_size) for f in local_paths], num_groups)
    return [[x[0] for x in g] for g in groups if g]


def _do_partition_files_equally(filename_size_pairs, num_groups: int):
    """把文件划分为若干个总大小相当的分组
    抄了这个算法: https://cloud.tencent.com/developer/article/1659134，以下文字来自该文章

    这个问题是典型的动态规划的问题，理论上是无法找到最优解的，但是本次只是为了解决实际生产中的问题，而不是要AC，所以我们只需要找到一个相对合理的算法，使得partition的分配相对均衡就好了。

    输入：int数组，分组数divisionNum
    1. 对数组倒序排序
    2. 计算数组的平均值 avg
    3. 遍历数组。
        * 如果第一个数大于等于avg，将这个数单独作为一组，因为再加下一个数也不会使得求和更接近avg；
          然后将剩下的数重新求平均，表示需要让剩下的数分配得更加平均，这样可以避免极值的影响，然后重新开始下一轮计算
        * 如果第一个数num小于avg，我们将这个数加入到数组中，然后我们需要找到一（或若干）个数，使得其和更接近delta = avg-num，
            - 继续遍历数组，若发现某个数k==delta，将k加入到数组，结束本轮寻找
            - 若发现a > delta > b；此时要继续判断，如果(delta - b) > (a - delta)，将b加入到数组，delta = delta - b，然后继续遍历；
              如果(delta - b) < (a - delta)，保存distance = delta - b，然后将a将入到数组中，继续往下遍历，
              判断能否找到距离 < distance的，如果有则选择距离更小的这组，否则选择将b加入数组。

    :param filename_size_pairs: 文件路径和大小的组合，格式 [(name1, size1), (name2, size2)...]
    :param num_groups: 分组数量
    """
    filename_size_pairs = sorted(filename_size_pairs, key=lambda x: x[1], reverse=True)
    total_size = sum(x[1] for x in filename_size_pairs)
    avg = total_size / num_groups
    groups = []
    for idx in range(num_groups):
        if idx == num_groups - 1:
            # 最后一个分组，把剩余的全部放一起
            groups.append(filename_size_pairs)
            break

        if filename_size_pairs and filename_size_pairs[0][1] >= avg:
            sub_group = [filename_size_pairs[0]]
            total_size -= filename_size_pairs[0][1]
            avg = total_size / (num_groups - len(groups))
        else:
            sub_group, _ = __get_list(filename_size_pairs, avg, abs(avg))
        groups.append(sub_group)
        for item in sub_group:
            filename_size_pairs.remove(item)
    return groups


def __get_list(filename_size_pairs, delta: float, distance: float):
    result = []
    if not filename_size_pairs:
        return result, -1

    for idx, (filename, size) in enumerate(filename_size_pairs):
        if delta < size:
            continue
        if delta == size:
            result.append((filename, size))
            return result, 0
        else:
            if idx == 0:
                result.append((filename, size))
                delta -= size
                distance = abs(delta)
                tmp, d = __get_list(filename_size_pairs[idx + 1:], delta, distance)
                result.extend(tmp)
                return result, d
            else:
                dis1 = abs(filename_size_pairs[idx - 1][1] - delta)
                dis2 = abs(delta - size)
                if dis1 > dis2:
                    result.append((filename, size))
                    delta -= size
                    tmp, d = __get_list(filename_size_pairs[idx + 1:], delta, dis2)
                    result.extend(tmp)
                    return result, d
                else:
                    tmp, d = __get_list(filename_size_pairs[idx:], delta, dis2)
                    if dis1 > d:
                        result.extend(tmp)
                        return result, d
                    result.append(filename_size_pairs[idx - 1])
                    return result, dis1

    dis = abs(delta - filename_size_pairs[-1][1])
    if dis < distance:
        return filename_size_pairs[-1:], dis
    return [], -1


if __name__ == '__main__':
    data = [('233dafd9b1d0b03e6e784987fe748be5.5', 400275118),
            ('233dafd9b1d0b03e6e784987fe748be5.2', 1147688439),
            ('233dafd9b1d0b03e6e784987fe748be5.4', 1232810556),
            ('233dafd9b1d0b03e6e784987fe748be5.3', 1318304652),
            ('233dafd9b1d0b03e6e784987fe748be5.0', 1392554705),
            ('233dafd9b1d0b03e6e784987fe748be5.8', 1440314997),
            ('233dafd9b1d0b03e6e784987fe748be5.7', 1453587946),
            ('233dafd9b1d0b03e6e784987fe748be5.6', 1470806585),
            ('233dafd9b1d0b03e6e784987fe748be5.1', 1509157699),
            ('233dafd9b1d0b03e6e784987fe748be5.9', 1546082238)]
    groups = _do_partition_files_equally(data, 5)
    for g in groups:
        print(g, sum(x[1] for x in g))
    # [('233dafd9b1d0b03e6e784987fe748be5.9', 1546082238), ('233dafd9b1d0b03e6e784987fe748be5.5', 400275118)] 1946357356
    # [('233dafd9b1d0b03e6e784987fe748be5.1', 1509157699), ('233dafd9b1d0b03e6e784987fe748be5.2', 1147688439)] 2656846138
    # [('233dafd9b1d0b03e6e784987fe748be5.6', 1470806585), ('233dafd9b1d0b03e6e784987fe748be5.4', 1232810556)] 2703617141
    # [('233dafd9b1d0b03e6e784987fe748be5.7', 1453587946), ('233dafd9b1d0b03e6e784987fe748be5.3', 1318304652)] 2771892598
    # [('233dafd9b1d0b03e6e784987fe748be5.8', 1440314997), ('233dafd9b1d0b03e6e784987fe748be5.0', 1392554705)] 2832869702
