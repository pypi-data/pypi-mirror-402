from dataclasses import asdict

from ..exceptions import ValidationError
from ..models import (
    CreateShortUrlRequest,
    CreateShortUrlResponse,
    DeleteShortUrlRequest,
    DeleteShortUrlResponse,
    UpdateShortUrlRequest,
    UpdateShortUrlResponse,
)
from .base import BaseAPI


class ShortUrlAPI(BaseAPI):
    """API methods for Short URL operations."""

    async def create_short_url(
        self, request: CreateShortUrlRequest
    ) -> CreateShortUrlResponse:
        """
        Create a new short URL.

        Args:
            request: The create short URL request containing domain, target URL, and optional parameters

        Returns:
            CreateShortUrlResponse: Response containing the created short URL details

        Raises:
            ValidationError: If target URL is invalid or domain is missing
            APIError: If the API request fails
        """
        # Validate target URL format
        if not request.target_url or not request.target_url.startswith(
            ("http://", "https://")
        ):
            raise ValidationError("Invalid URL: must start with http:// or https://")

        # Validate domain is provided
        if not request.domain:
            raise ValidationError("Domain is required")

        response = await self._http_client.post("/v1/shorten", json=asdict(request))
        return CreateShortUrlResponse.from_dict(response)

    async def update_short_url(
        self, request: UpdateShortUrlRequest
    ) -> UpdateShortUrlResponse:
        """
        Update an existing short URL.

        Args:
            request: The update short URL request containing domain, slug, and fields to update

        Returns:
            UpdateShortUrlResponse: Response indicating the update status

        Raises:
            NotFoundError: If the short URL is not found
            APIError: If the API request fails
        """
        response = await self._http_client.put(
            "/v1/shorten",
            json=asdict(request),
        )
        return UpdateShortUrlResponse.from_dict(response)

    async def delete_short_url(
        self, request: DeleteShortUrlRequest
    ) -> DeleteShortUrlResponse:
        """
        Delete a short URL.

        Args:
            request: The delete short URL request containing domain and slug

        Returns:
            DeleteShortUrlResponse: Response indicating the deletion status

        Raises:
            NotFoundError: If the short URL is not found
            APIError: If the API request fails
        """
        response = await self._http_client.delete("/v1/shorten", json=asdict(request))
        return DeleteShortUrlResponse.from_dict(response)
