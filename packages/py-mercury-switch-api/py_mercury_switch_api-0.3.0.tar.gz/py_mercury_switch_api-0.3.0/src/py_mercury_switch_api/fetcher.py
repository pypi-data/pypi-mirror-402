"""HTML page retrieval classes."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests
import requests.cookies
from requests import Response

from .const import URL_REQUEST_TIMEOUT
from .exceptions import (
    MercurySwitchConnectionError,
    NotLoggedInError,
)

_LOGGER = logging.getLogger(__name__)

status_code_ok = requests.codes.ok
status_code_not_found = requests.codes.not_found
status_code_no_response = requests.codes.no_response
status_code_unauthorized = requests.codes.unauthorized


class BaseResponse:
    """Base class for response objects."""

    def __init__(self) -> None:
        """Initialize BaseResponse Object."""
        self.status_code: int = status_code_not_found
        self.content: bytes = b""
        self.text: str = ""
        self.cookies: requests.cookies.RequestsCookieJar = (
            requests.cookies.RequestsCookieJar()
        )

    def __bool__(self) -> bool:
        """Return True if status code is 200."""
        return bool(self.status_code == status_code_ok)


class PageFetcher:
    """Class to fetch html pages from switch (or file)."""

    def __init__(self, host: str) -> None:
        """Initialize PageFetcher Object."""
        self.host = host
        # login cookie
        self._cookie_name: str | None = None
        self._cookie_content: str | None = None

        # offline mode settings
        self.offline_mode = False
        self.offline_path_prefix = ""

    def turn_on_offline_mode(self, path_prefix: str) -> None:
        """Turn on offline mode."""
        self.offline_mode = True
        self.offline_path_prefix = path_prefix

    def turn_on_online_mode(self) -> None:
        """Turn on online mode."""
        self.offline_mode = False

    def get_cookie(self) -> tuple[str | None, str | None]:
        """Get cookie."""
        if self._cookie_name and self._cookie_content:
            return (self._cookie_name, self._cookie_content)
        return (None, None)

    def set_cookie(self, cookie_name: str, cookie_content: str) -> None:
        """Set cookie."""
        self._cookie_name = cookie_name
        self._cookie_content = cookie_content

    def clear_cookie(self) -> None:
        """Clear cookie."""
        self._cookie_name = None
        self._cookie_content = None

    def has_ok_status(self, response: Response | BaseResponse) -> bool:
        """Check if response has OK status."""
        return bool(response.status_code == status_code_ok)

    def request(
        self, method: str, url: str, data: dict[str, Any] | None = None
    ) -> Response:
        """Make HTTP request."""
        cookies: dict[str, str] = {}
        if self._cookie_name and self._cookie_content:
            cookies[self._cookie_name] = self._cookie_content

        try:
            if method.lower() == "post":
                response = requests.post(
                    url, data=data, cookies=cookies, timeout=URL_REQUEST_TIMEOUT
                )
            else:
                response = requests.get(
                    url, cookies=cookies, timeout=URL_REQUEST_TIMEOUT
                )

            # Check if redirected to login page
            if response.status_code == status_code_unauthorized or (
                response.status_code in [301, 302, 303, 307, 308]
                and "logon" in response.url.lower()
            ):
                raise NotLoggedInError("Not logged in")

            return response
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as e:
            raise MercurySwitchConnectionError(f"Connection error: {e}") from e

    def get_page_from_file(self, url: str) -> BaseResponse:
        """Get page from file (offline mode)."""
        response = BaseResponse()
        # Extract filename from URL
        filename = url.split("/")[-1]
        if not filename:
            filename = "index.htm"

        # Construct file path
        file_path = Path(self.offline_path_prefix) / filename

        if file_path.exists():
            response.content = file_path.read_bytes()
            response.text = response.content.decode("utf-8", errors="ignore")
            response.status_code = status_code_ok
        else:
            _LOGGER.warning("File not found: %s", file_path)
            response.status_code = status_code_not_found

        return response
