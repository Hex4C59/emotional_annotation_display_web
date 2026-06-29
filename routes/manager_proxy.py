"""
Proxy /manager requests to the Django lansys-manager backend.

The Django app runs at its own root path, while the public Flask site exposes it
under /manager. Redirect responses from Django are rewritten back under that
prefix so login and form flows stay on the public URL.
"""
import os
import re
from urllib.parse import urlparse

import requests
from flask import Blueprint, Response, abort, request

manager_proxy_bp = Blueprint("manager_proxy", __name__, url_prefix="/manager")

MANAGER_BASE = os.getenv("LANSYS_MANAGER_URL", "http://10.10.16.133:8000").rstrip("/")
PUBLIC_PREFIX = "/manager"
_PROXY_ON = os.getenv("LANSYS_MANAGER_PROXY_ENABLED", "true").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
_TIMEOUT = int(os.getenv("LANSYS_MANAGER_PROXY_TIMEOUT", "120"))

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

_ABSOLUTE_ATTR_RE = re.compile(
    r"(?P<prefix>\b(?:href|src|action)=)(?P<quote>[\"']?)(?P<url>/(?!/)(?!manager(?:/|$))[^\"'\s>]*)"
    r"(?P=quote)"
)
_CSS_URL_RE = re.compile(
    r"url\((?P<quote>[\"']?)(?P<url>/(?!/)(?!manager(?:/|$))[^\"')\s]*)(?P=quote)\)"
)


def _should_skip_header(name_lower: str) -> bool:
    return name_lower in _SKIP_HEADER_NAMES or name_lower.startswith(_SKIP_HEADER_PREFIXES)


def _upstream_url(path: str) -> str:
    suffix = path.lstrip("/")
    url = f"{MANAGER_BASE}/{suffix}" if suffix else f"{MANAGER_BASE}/"
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

    host = urlparse(MANAGER_BASE).netloc
    out["Host"] = host or "10.10.16.133:8000"

    client = request.remote_addr or ""
    prev = request.headers.get("X-Forwarded-For")
    if prev and client:
        out["X-Forwarded-For"] = f"{prev}, {client}"
    elif prev:
        out["X-Forwarded-For"] = prev
    elif client:
        out["X-Forwarded-For"] = client

    out["X-Forwarded-Host"] = request.host
    out["X-Forwarded-Proto"] = request.headers.get("X-Forwarded-Proto", request.scheme)
    out["X-Script-Name"] = PUBLIC_PREFIX
    return out


def _rewrite_location(value: str) -> str:
    if not value:
        return value
    if value.startswith(PUBLIC_PREFIX + "/") or value == PUBLIC_PREFIX:
        return value

    parsed_base = urlparse(MANAGER_BASE)
    base_origin = f"{parsed_base.scheme}://{parsed_base.netloc}"
    if value.startswith(base_origin):
        value = value[len(base_origin):] or "/"

    if value.startswith("/"):
        return PUBLIC_PREFIX + value
    return value


def _response_headers(r):
    headers = []
    for key, value in r.headers.items():
        lk = key.lower()
        if lk in HOP_BY_HOP or lk == "set-cookie":
            continue
        if lk == "location":
            value = _rewrite_location(value)
        headers.append((key, value))

    raw_headers = getattr(getattr(r, "raw", None), "headers", None)
    if raw_headers is not None and hasattr(raw_headers, "getlist"):
        cookie_values = raw_headers.getlist("Set-Cookie")
    elif "Set-Cookie" in r.headers:
        cookie_values = [r.headers["Set-Cookie"]]
    else:
        cookie_values = []

    for value in cookie_values:
        headers.append(("Set-Cookie", value))
    return headers


def _rewrite_html(body: bytes, content_type: str) -> bytes:
    if "text/html" not in content_type.lower():
        return body

    encoding = "utf-8"
    match = re.search(r"charset=([^;\s]+)", content_type, re.IGNORECASE)
    if match:
        encoding = match.group(1)

    try:
        text = body.decode(encoding)
    except UnicodeDecodeError:
        text = body.decode("utf-8", errors="replace")
        encoding = "utf-8"

    def attr_repl(match_obj):
        return (
            f"{match_obj.group('prefix')}{match_obj.group('quote')}"
            f"{PUBLIC_PREFIX}{match_obj.group('url')}{match_obj.group('quote')}"
        )

    def css_repl(match_obj):
        quote = match_obj.group("quote")
        return f"url({quote}{PUBLIC_PREFIX}{match_obj.group('url')}{quote})"

    text = _ABSOLUTE_ATTR_RE.sub(attr_repl, text)
    text = _CSS_URL_RE.sub(css_repl, text)
    return text.encode(encoding)


@manager_proxy_bp.route("/", defaults={"path": ""}, methods=_ALL_METHODS)
@manager_proxy_bp.route("/<path:path>", methods=_ALL_METHODS)
def forward_to_manager(path: str):
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

    body = _rewrite_html(upstream.content, upstream.headers.get("Content-Type", ""))
    return Response(body, status=upstream.status_code, headers=_response_headers(upstream))
