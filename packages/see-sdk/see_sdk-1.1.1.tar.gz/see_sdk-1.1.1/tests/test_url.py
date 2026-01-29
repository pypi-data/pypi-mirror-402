"""Tests for Short URL functionality."""

import pytest
from pytest_mock import MockerFixture

from see.client import SeeClient
from see.exceptions import ValidationError
from see.models import (
    CreateShortUrlRequest,
    CreateShortUrlResponse,
    DeleteShortUrlRequest,
    DeleteShortUrlResponse,
    UpdateShortUrlRequest,
    UpdateShortUrlResponse,
)


class TestShortUrl:
    """Tests for Short URL operations."""

    @pytest.mark.asyncio
    async def test_create_short_url(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test creating a short URL with valid request."""
        mock_response = {
            "code": 200,
            "data": {
                "short_url": "https://example.com/abc123",
                "slug": "abc123",
            },
            "message": "Success",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_post = mocker.patch.object(
                client._http_client,
                "post",
                return_value=mock_response,
            )

            request = CreateShortUrlRequest(
                domain="example.com",
                target_url="https://www.google.com",
            )
            result = await client.create_short_url(request)

            assert isinstance(result, CreateShortUrlResponse)
            assert result.code == 200
            assert result.data is not None
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_short_url_with_custom_slug(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test creating a short URL with custom slug and optional fields."""
        mock_response = {
            "code": 200,
            "data": {
                "short_url": "https://example.com/custom",
                "slug": "custom",
            },
            "message": "Success",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mocker.patch.object(
                client._http_client,
                "post",
                return_value=mock_response,
            )

            request = CreateShortUrlRequest(
                domain="example.com",
                target_url="https://www.google.com",
                custom_slug="custom",
                title="Test Link",
                expire_at=1735689599,
                tag_ids=[1, 2],
            )
            result = await client.create_short_url(request)

            assert result.code == 200
            assert result.data["slug"] == "custom"

    @pytest.mark.asyncio
    async def test_create_short_url_invalid_target_url(
        self,
        api_key: str,
        base_url: str,
    ) -> None:
        """Test creating a short URL with invalid target URL raises ValidationError."""
        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            request = CreateShortUrlRequest(
                domain="example.com",
                target_url="not-a-valid-url",
            )

            with pytest.raises(ValidationError, match="Invalid URL"):
                await client.create_short_url(request)

    @pytest.mark.asyncio
    async def test_create_short_url_missing_domain(
        self,
        api_key: str,
        base_url: str,
    ) -> None:
        """Test creating a short URL without domain raises ValidationError."""
        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            request = CreateShortUrlRequest(
                domain="",
                target_url="https://www.google.com",
            )

            with pytest.raises(ValidationError, match="Domain is required"):
                await client.create_short_url(request)

    @pytest.mark.asyncio
    async def test_update_short_url(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test updating a short URL."""
        mock_response = {
            "code": 200,
            "data": None,
            "message": "Updated successfully",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_put = mocker.patch.object(
                client._http_client,
                "put",
                return_value=mock_response,
            )

            request = UpdateShortUrlRequest(
                domain="example.com",
                slug="abc123",
                target_url="https://example.org/new",
                title="Updated Title",
            )
            result = await client.update_short_url(request)

            assert isinstance(result, UpdateShortUrlResponse)
            assert result.code == 200
            assert result.message == "Updated successfully"
            mock_put.assert_called_once_with("/v1/shorten", json=mocker.ANY)

    @pytest.mark.asyncio
    async def test_delete_short_url(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test deleting a short URL."""
        mock_response = {
            "code": 200,
            "data": None,
            "message": "Deleted successfully",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_delete = mocker.patch.object(
                client._http_client,
                "delete",
                return_value=mock_response,
            )

            request = DeleteShortUrlRequest(
                domain="example.com",
                slug="abc123",
            )
            result = await client.delete_short_url(request)

            assert isinstance(result, DeleteShortUrlResponse)
            assert result.code == 200
            assert result.message == "Deleted successfully"
            mock_delete.assert_called_once_with("/v1/shorten", json=mocker.ANY)
