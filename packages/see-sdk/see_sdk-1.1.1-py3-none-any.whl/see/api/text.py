from dataclasses import asdict

from ..models import (
    CreateTextRequest,
    CreateTextResponse,
    DeleteTextRequest,
    DeleteTextResponse,
    DomainResponse,
    UpdateTextRequest,
    UpdateTextResponse,
)
from .base import BaseAPI


class TextAPI(BaseAPI):
    """API methods for Text Sharing operations."""

    async def create_text(self, request: CreateTextRequest) -> CreateTextResponse:
        """
        Create a new text sharing entry.

        Args:
            request: The text creation details

        Returns:
            CreateTextResponse: Response containing the created text details

        Raises:
            APIError: If the API request fails
        """
        response = await self._http_client.post("/v1/text", json=asdict(request))
        return CreateTextResponse.from_dict(response)

    async def update_text(self, request: UpdateTextRequest) -> UpdateTextResponse:
        """
        Update an existing text sharing entry.

        Args:
            request: The text update details

        Returns:
            UpdateTextResponse: Response indicating the update status

        Raises:
            APIError: If the API request fails
        """
        response = await self._http_client.put("/v1/text", json=asdict(request))
        return UpdateTextResponse.from_dict(response)

    async def delete_text(self, request: DeleteTextRequest) -> DeleteTextResponse:
        """
        Delete a text sharing entry.

        Args:
            request: The text deletion details

        Returns:
            DeleteTextResponse: Response indicating the deletion status

        Raises:
            APIError: If the API request fails
        """
        # The API documentation says DELETE method but body is used.
        # httpx supports content/json in DELETE.
        response = await self._http_client.delete("/v1/text", json=asdict(request))
        return DeleteTextResponse.from_dict(response)

    async def get_text_domains(self) -> DomainResponse:
        """
        Get available domains for text sharing.

        Returns:
            DomainResponse: Response containing the list of available domains

        Raises:
            APIError: If the API request fails
        """
        response = await self._http_client.get("/v1/text/domains")
        return DomainResponse.from_dict(response)
