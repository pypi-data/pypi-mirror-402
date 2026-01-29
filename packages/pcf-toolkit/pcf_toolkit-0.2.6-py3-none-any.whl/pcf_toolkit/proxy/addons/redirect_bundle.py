"""Mitmproxy addon that redirects PCF webresource requests to localhost."""

from __future__ import annotations

import os
import re

from mitmproxy import http

PCF_NAME = os.getenv("PCF_COMPONENT_NAME")
PCF_EXPECTED_PATH = os.getenv("PCF_EXPECTED_PATH", "/webresources/{PCF_NAME}/")
HTTP_SERVER_PORT = int(os.getenv("HTTP_SERVER_PORT", "8082"))
HTTP_SERVER_HOST = os.getenv("HTTP_SERVER_HOST", "localhost")


def _matches_expected_path(request_url: str, request_path: str) -> tuple[bool, str]:
    """Checks if request matches expected PCF webresource path.

    Args:
      request_url: Full request URL.
      request_path: Request path component.

    Returns:
      Tuple of (matches, remainder) where remainder is the path after the
      expected base.
    """
    if not PCF_NAME:
        return False, ""
    expected_base = PCF_EXPECTED_PATH.replace("{PCF_NAME}", PCF_NAME)
    if expected_base in request_path:
        target = request_path
    elif expected_base in request_url:
        target = request_url
    else:
        return False, ""
    pattern = re.escape(expected_base) + r"(.*)"
    match = re.search(pattern, target)
    if not match:
        return False, ""
    return True, match.group(1)


def request(flow: http.HTTPFlow) -> None:
    """Mitmproxy request hook that redirects PCF webresource requests.

    Intercepts requests matching the expected PCF webresource path and redirects
    them to the local HTTP server.

    Args:
      flow: HTTP flow object from mitmproxy.
    """
    if not PCF_NAME:
        return

    matches, remainder = _matches_expected_path(flow.request.url, flow.request.path)
    if not matches:
        return

    dynamic_path = remainder.lstrip("/")
    if dynamic_path:
        redirect_path = f"/{dynamic_path}"
    else:
        redirect_path = "/"

    flow.request.host = HTTP_SERVER_HOST
    flow.request.port = HTTP_SERVER_PORT
    flow.request.scheme = "http"
    flow.request.path = redirect_path
    flow.request.headers["if-none-match"] = ""
    flow.request.headers["cache-control"] = "no-cache"
