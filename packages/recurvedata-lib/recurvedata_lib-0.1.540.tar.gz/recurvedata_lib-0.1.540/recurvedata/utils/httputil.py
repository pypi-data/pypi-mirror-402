import json
import os
import re
import shutil
import urllib.parse
from typing import Optional

import httpx
import requests
import requests.adapters
from urllib3.util.retry import Retry


def new_retry_session(
    max_retries=3,
    backoff_factor=0.3,
    method_whitelist=None,
    status_forcelist=(429, 500, 502, 503, 504),
    session=None,
):
    if not method_whitelist:
        method_whitelist = Retry.DEFAULT_ALLOWED_METHODS
    session = session or requests.Session()
    retry = Retry(
        total=max_retries,
        read=max_retries,
        connect=max_retries,
        allowed_methods=method_whitelist,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def download_file(url: str, filepath: str, **kwargs) -> str:
    if os.path.isdir(filepath):
        filename = url.split("/")[-1]
        filepath = os.path.join(filepath, filename)

    with requests.get(url, stream=True, **kwargs) as r:
        with open(filepath, "wb") as f:
            shutil.copyfileobj(r.raw, f)

    return filepath


FQDN_RE = re.compile(r"^((?!-)[-A-Z\d]{1,62}(?<!-)\.)+[A-Z]{1,62}\.?$", re.IGNORECASE)


def is_valid_domain(host: str) -> bool:
    if len(host) > 253:
        return False
    return bool(FQDN_RE.match(host))


def fill_scheme_to_url(url: str, scheme="https") -> str:
    p = urllib.parse.urlparse(url)
    # 有 scheme，不需要处理
    if p.scheme != "":
        return url

    netloc = p.netloc or p.path
    if "/" in netloc:
        if netloc.startswith("://"):
            return f"{scheme}{url}"

        domain = netloc[: netloc.index("/")]
        if not is_valid_domain(domain):
            return url
    path = p.path if p.netloc else ""
    p = urllib.parse.ParseResult(scheme, netloc, path, *p[3:])
    return p.geturl()


def ensure_url_list(s: str, fix_scheme=True) -> Optional[list[str]]:
    if not s:
        return None

    try:
        urls = json.loads(s)
    except json.JSONDecodeError:
        # try use comma as seperator
        urls = s.split(",")
    if fix_scheme:
        urls = [fill_scheme_to_url(x) for x in urls]
    return urls


async def forward(_request, endpoint: str):
    """
    Forward a request to another server (received via FastAPI) and return the response.
    We create a common method to use in multiple places.
    """
    from fastapi import Request
    from fastapi.responses import Response

    request: Request = _request
    method = request.method
    headers = dict(request.headers)
    params = request.query_params
    body = await request.body()

    async with httpx.AsyncClient() as client:
        # Forward the request
        response = await client.request(
            method=method,
            url=endpoint,
            headers=headers,
            params=params,
            content=body,
        )

    # Return the response from the target server
    return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
