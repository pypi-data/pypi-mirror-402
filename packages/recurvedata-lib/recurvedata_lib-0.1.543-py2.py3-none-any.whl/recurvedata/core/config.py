import os
import pathlib


class Config:
    CONFIG_FOLDER_ENV_NAME = "RECURVE_CONFIG_FOLDER"
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self, folder: str = None):
        folder = folder or os.environ.get(self.CONFIG_FOLDER_ENV_NAME, "~/.recurve")
        if not folder:
            raise ValueError(f"config folder is required, got {repr(folder)}")

        self._folder = pathlib.Path(folder).expanduser()
        self._folder.mkdir(mode=0o755, parents=True, exist_ok=True)
        self._config_file = self._folder / "config"

        self.__defaults = self.load_defaults()

    def load_defaults(self) -> dict:
        """load default config from env file or environment variables

        file format:
        RECURVE_HOST = https://abc.test.domain.com
        RECURVE_USERNAME = foo
        RECURVE_PASSWORD = pwd123
        """
        from dotenv import dotenv_values

        # failed to install dotenv in 3.11  todo
        return {
            **dotenv_values(self._config_file),
            **os.environ,
        }

    def get_or_default(self, value: str, env_key: str) -> str:
        if value:
            return value
        if env_key not in self.__defaults:
            raise ValueError("value is required")
        return self.__defaults[env_key]
