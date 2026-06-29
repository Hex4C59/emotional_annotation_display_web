"""
将 /lansys 请求反向代理到 Lansys Java 后端，让标注站点和 Java API 共用同一对外域名。
通过环境变量 LANSYS_TOMCAT_URL、LANSYS_PROXY_ENABLED、LANSYS_PROXY_TIMEOUT 控制上游与开关。
"""
import os
from urllib.parse import urlparse

import requests
from flask import Blueprint, Response, abort, request

lansys_proxy_bp = Blueprint("lansys_proxy", __name__, url_prefix="/lansys")

TOMCAT_BASE = os.getenv("LANSYS_TOMCAT_URL", "http://10.10.16.133:8080").rstrip("/")
_PROXY_ON = os.getenv("LANSYS_PROXY_ENABLED", "true").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
_TIMEOUT = int(os.getenv("LANSYS_PROXY_TIMEOUT", "120"))

HOP_BY_HOP = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
    }
)

_SKIP_HEADER_NAMES = frozenset(
    {
        "priority",
        "early-data",
        "upgrade-insecure-requests",
    }
)
_SKIP_HEADER_PREFIXES = ("sec-", "proxy-")

_ALL_METHODS = [
    "GET",
    "HEAD",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]


def _should_skip_header(name_lower: str) -> bool:
    return name_lower in _SKIP_HEADER_NAMES or name_lower.startswith(_SKIP_HEADER_PREFIXES)


def _upstream_url(path: str) -> str:
    suffix = path.lstrip("/")
    url = f"{TOMCAT_BASE}/lansys/{suffix}" if suffix else f"{TOMCAT_BASE}/lansys/"
    if request.query_string:
        url = url + "?" + request.query_string.decode("utf-8", errors="replace")
    return url


def _forward_headers():
    out = {}
    for key, value in request.headers:
        lk = key.lower()
        if lk in HOP_BY_HOP or lk == "host" or _should_skip_header(lk):
            continue
        out[key] = value

    host = urlparse(TOMCAT_BASE).netloc
    out["Host"] = host or "10.10.16.133:8080"

    client = request.remote_addr or ""
    prev = request.headers.get("X-Forwarded-For")
    if prev and client:
        out["X-Forwarded-For"] = f"{prev}, {client}"
    elif prev:
        out["X-Forwarded-For"] = prev
    elif client:
        out["X-Forwarded-For"] = client
    out["X-Forwarded-Proto"] = request.headers.get("X-Forwarded-Proto", request.scheme)
    return out


def _response_headers(r):
    return [(k, v) for k, v in r.headers.items() if k.lower() not in HOP_BY_HOP]


@lansys_proxy_bp.route("/", defaults={"path": ""}, methods=_ALL_METHODS)
@lansys_proxy_bp.route("/<path:path>", methods=_ALL_METHODS)
def forward_to_lansys(path: str):
    if not _PROXY_ON:
        abort(404)

    payload = None if request.method in ("GET", "HEAD", "OPTIONS") else request.get_data()

    try:
        upstream = requests.request(
            method=request.method,
            url=_upstream_url(path),
            headers=_forward_headers(),
            data=payload,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=_TIMEOUT,
        )
    except requests.RequestException:
        abort(502)

    return Response(upstream.content, status=upstream.status_code, headers=_response_headers(upstream))
