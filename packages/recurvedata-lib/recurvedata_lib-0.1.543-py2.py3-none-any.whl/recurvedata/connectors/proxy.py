import socket
import urllib.parse

from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.connectors.utils import EnvContextManager
from recurvedata.core.translation import _l
from recurvedata.utils.log import LoggingMixin

logger = LoggingMixin.logger()

HTTP_PROXY_CONFIG_SCHEMA = {
    "proxies": {
        "type": "object",
        "title": _l("HTTP/HTTPS Proxy Settings"),
        "description": _l("Configure proxy servers for HTTP and HTTPS connections"),
        "properties": {
            "https": {
                "type": "string",
                "title": _l("HTTPS Proxy"),
                "description": _l("HTTPS proxy URL in format https://host:port, or http://host:port"),
            },
            "http": {
                "type": "string",
                "title": _l("HTTP Proxy"),
                "description": _l("HTTP proxy URL in format http://host:port"),
            },
        },
        "order": ["https", "http"],
    },
}


class ProxyEnvContextManager(EnvContextManager):
    def __init__(self, proxy: str = None, http_proxy: str = None, https_proxy: str = None):
        env_vars = {}
        if http_proxy or proxy:
            env_vars["http_proxy"] = http_proxy or proxy
        if https_proxy or proxy:
            env_vars["https_proxy"] = https_proxy or proxy
        super().__init__(env_vars)


class ProxyMixinBase:
    pass


class HttpProxyMixin(ProxyMixinBase):
    @classmethod
    def format_config_schema(cls):
        config_schema = super(HttpProxyMixin, cls).format_config_schema()
        return add_http_proxy_to_config_schema(config_schema)

    def _init_proxy_manager(self):
        proxies = self.proxies or {}
        return ProxyEnvContextManager(http_proxy=proxies.get("http"), https_proxy=proxies.get("https"))

    @classmethod
    def preprocess_conf(cls, data: dict) -> dict:
        data = RecurveConnectorBase.preprocess_conf(data)
        proxies = data.get("proxies")
        if proxies and not cls.check_proxy(proxies):
            logger.warning(f"proxies {proxies} is not available, use direct connect")
            data["proxies"] = None
        return data

    @classmethod
    def check_proxy(cls, proxies: dict, timeout=10):
        """
        检查 proxy 是否可用
        proxies example: {'http': 'http://proxy_host:proxy_port', 'https': 'https://proxy_host:proxy_port'}
        """
        if not proxies:
            return False
        return cls._check_proxy_connection(proxies.get("http"), timeout) or cls._check_proxy_connection(
            proxies.get("https"), timeout
        )

    @classmethod
    def _check_proxy_connection(cls, proxy_url, timeout):
        parsed_url = urllib.parse.urlparse(proxy_url)
        if not parsed_url.scheme:
            proxy_url = f"http://{proxy_url}"
            parsed_url = urllib.parse.urlparse(proxy_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

        try:
            with socket.create_connection((hostname, port), timeout=timeout):
                return True
        except socket.timeout:
            logger.info(f"Connection timed out while connecting to {hostname}:{port}")
            return False
        except socket.error as e:
            logger.info(f"Error connecting to {hostname}:{port}: {e}")
            return False


def add_http_proxy_to_config_schema(config_schema: dict) -> dict:
    if "proxies" in config_schema["properties"]:
        return config_schema

    config_schema["properties"].update(HTTP_PROXY_CONFIG_SCHEMA)
    config_schema["order"].append("proxies")
    return config_schema
