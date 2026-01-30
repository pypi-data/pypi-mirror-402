import os
import shutil

import paramiko

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.utils import LoggingMixin
from recurvedata.pigeon.utils.timing import DisplayProgress


@register_connector_class('sftp')
class SFtpConnector(LoggingMixin):
    def __init__(self, host, port, username, password, rsa_private_key_file: str = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        client = paramiko.Transport((self.host, self.port))
        if rsa_private_key_file and password:
            private_key = paramiko.RSAKey.from_private_key_file(rsa_private_key_file)
            client.start_client(event=None, timeout=15)
            client.get_remote_server_key()
            client.auth_publickey(self.username, private_key, event=None)
            client.auth_password(self.username, self.password, event=None)
        elif rsa_private_key_file:
            private_key = paramiko.RSAKey.from_private_key_file(rsa_private_key_file)
            client.connect(username=self.username, pkey=private_key)
        else:
            client.connect(username=self.username, password=self.password)
        self.sftp = paramiko.SFTPClient.from_transport(client)

    def close(self):
        self.sftp.close()

    def rename(self, from_name, to_name):
        self.sftp.rename(from_name, to_name)

    def makedir(self, path):
        self.sftp.mkdir(path)

    def rmdir(self, path):
        self.sftp.rmdir(path)

    def rm(self, name):
        self.sftp.remove(name)

    def pwd(self):
        return self.sftp.getcwd()

    def size(self, name):
        return self.sftp.stat(name).st_size

    def download_file(self, src_file, dst_file):
        exists = True
        local_dir = os.path.dirname(dst_file)
        if not os.path.exists(local_dir):
            exists = False
            os.makedirs(local_dir)
        try:
            size = self.size(src_file)
            self.sftp.get(src_file, dst_file, callback=DisplayProgress(size, stream=False))
            self.logger.info(f'successfully downloaded {src_file} to {dst_file}')
        except Exception as e:
            os.unlink(dst_file)
            if not exists:
                shutil.rmtree(local_dir)

            self.logger.exception(f'failed to download {src_file}, reason:{e}')
            raise e

    def upload_file(self, src_file, dst_file):
        self.sftp.put(src_file, dst_file, callback=DisplayProgress(stream=False))
        self.logger.info(f'successfully uploaded {src_file} to {dst_file}')