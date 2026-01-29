from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..http_client import HttpClient


class BaseAPI:
    """Base class for API mixins providing type hints."""

    _http_client: "HttpClient"
