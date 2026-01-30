import os
import re
from urllib.parse import quote


class EnvContextManager:
    def __init__(self, env_vars: dict):
        self.env_vars = env_vars
        self.old_env_vars = {}

    def __enter__(self):
        for key, value in self.env_vars.items():
            self.old_env_vars[key] = os.environ.get(key)
            os.environ[key] = value

    def __exit__(self, exc_type, exc_value, traceback):
        for key, value in self.old_env_vars.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value


def juice_sync_process_special_character_within_secret(secret_part: str) -> str:
    """
    `When you get "/" in ACCESS_KEY or SECRET_KEY strings,you need to replace "/" with "%2F".`
    :return:
    """
    if "/" in secret_part:
        secret_part = secret_part.replace("/", "%2F")
    return secret_part


def juice_sync_process_special_character_within_path(path: str) -> str:
    """
    1. 冒号需要在 juice sync 里处理两遍，第一遍转成 %3A, 第二遍再把 %3A quote 一下，用于 juice sync
    2. 有些路径需要加引号
    """
    if not path:
        return path
    colon_quote = quote(":")
    if colon_quote in path:
        path = path.replace(colon_quote, quote(colon_quote))

    if re.search("[ &]", path):
        path = f'"{path}"'
    return path
