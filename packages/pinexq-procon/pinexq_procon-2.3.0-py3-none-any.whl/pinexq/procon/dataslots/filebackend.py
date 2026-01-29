import logging
import os
from tempfile import NamedTemporaryFile
from typing import IO, Protocol, Self, runtime_checkable

import httpx
from pydantic import AnyUrl

from ..core.exceptions import ProConDataslotError


LOG = logging.getLogger(__name__)


@runtime_checkable
class FileBackEnd(Protocol):
    """Implements the prototype for the file access behind Slots."""
    uri: AnyUrl
    mode: str

    _file: IO | None = None

    def __init__(self, uri: AnyUrl | str, mode: str = 'r'):
        self.uri = uri
        self.mode = mode

    def __enter__(self) -> Self:
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def file(self) -> IO:
        return self._file

    def open(self):
        if self._file:
            self._file.close()
        self._file = open(str(self.uri), self.mode)

    def close(self):
        self._file.close()

    def push(self):
        pass

    def pull(self):
        pass


class LocalFile(FileBackEnd):
    """Pass-through wrapper for just a local file on disk."""

    def __init__(self, uri: AnyUrl | str, mode: str = 'r'):
        """

        Args:
            uri: Local path of the file.
            mode: File mode to open the file with [rw]b?a?
        """
        super().__init__(uri, mode)


class LocalCachedHttpFile(FileBackEnd):
    """
    Wrapper around a temporary local file with methods to down-/upload it from/to a HTTP server.
    """

    _http_timeout_s: int
    _req_args: dict

    def __init__(self, uri: AnyUrl | str, mode: str = 'r', request_args: dict | None = None):
        """

        Attributes:
            uri: The source/destination uri where the remote data resides.
            mode: File mode for this file [r|w](b)?
            request_args: optional parameters for the HTTP requests
        """
        super().__init__(uri, mode)
        self._req_args = request_args or {}
        self._http_timeout_s = int(os.getenv("PROCON_HTTP_TIMEOUT_S", "60"))

        self._file = NamedTemporaryFile(delete=False)
        self._file.close()

    def open(self):
        if self._file:
            self._file.close()
        self._file = open(self._file.name, self.mode)

    def pull(self):
        """Download the file from the defined source location."""
        try:
            with open(self._file.name, mode='wb') as download_file:
                with httpx.stream("GET", str(self.uri), timeout=self._http_timeout_s, **self._req_args) as response:
                    # total = int(response.headers["Content-Length"])
                    for chunk in response.iter_bytes():
                        download_file.write(chunk)
                    response.raise_for_status()
        except httpx.RequestError as ex:
            raise ProConDataslotError(f"Error in HTTP GET-request for: {ex.request.url}") from ex
        except httpx.HTTPStatusError as ex:
            raise ProConDataslotError(f"Error response {ex.response.status_code} on GET-request for {ex.request.url!r}")
        finally:
            self._file.close()

    def push(self):
        """Upload the file to the defined destination."""
        try:
            with open(self._file.name, 'rb') as f:
                response = httpx.request("PUT", str(self.uri), content=f, timeout=self._http_timeout_s, **self._req_args)
                response.raise_for_status()
        except httpx.RequestError as ex:
            raise ProConDataslotError(f"Error in HTTP PUT-request for: {ex.request.url}") from ex
        except httpx.HTTPStatusError as ex:
            raise ProConDataslotError(f"Error response {ex.response.status_code} on PUT-request for {ex.request.url!r}")

    def __del__(self):
        try:
            if self._file:
                os.unlink(self._file.name)
        except PermissionError:
            LOG.warning(f"Can not delete file '{self._file.name}', as it's still in use!")
