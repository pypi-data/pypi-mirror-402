"""Tests for SeeClient Text functionalities."""

import pytest
from pytest_mock import MockerFixture

from see.client import SeeClient
from see.models import (
    CreateTextRequest,
    CreateTextResponse,
    DeleteTextRequest,
    DeleteTextResponse,
    DomainResponse,
    UpdateTextRequest,
    UpdateTextResponse,
)


class TestSeeClientText:
    """Tests for SeeClient Text functionalities."""

    @pytest.mark.asyncio
    async def test_create_text(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test creating a text sharing entry."""
        mock_response = {
            "code": 0,
            "data": {
                "custom_slug": "slug123",
                "short_url": "https://s.ee/t/slug123",
                "slug": "slug123",
            },
            "message": "success",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_post = mocker.patch.object(
                client._http_client,
                "post",
                return_value=mock_response,
            )

            request = CreateTextRequest(
                content="Hello World",
                title="My Text",
            )
            result = await client.create_text(request)

            assert isinstance(result, CreateTextResponse)
            assert result.code == 0
            assert result.custom_slug == "slug123"
            assert result.short_url == "https://s.ee/t/slug123"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_text(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test updating a text sharing entry."""
        mock_response = {
            "code": 0,
            "data": {"something": "here"},
            "message": "success",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_put = mocker.patch.object(
                client._http_client,
                "put",
                return_value=mock_response,
            )

            request = UpdateTextRequest(
                content="Updated World",
                domain="s.ee",
                slug="slug123",
                title="My Text Updated",
            )
            result = await client.update_text(request)

            assert isinstance(result, UpdateTextResponse)
            assert result.code == 0
            mock_put.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_text(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test deleting a text sharing entry."""
        mock_response = {
            "code": 0,
            "data": {},
            "message": "success",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_delete = mocker.patch.object(
                client._http_client,
                "delete",
                return_value=mock_response,
            )

            request = DeleteTextRequest(
                domain="s.ee",
                slug="slug123",
            )
            result = await client.delete_text(request)

            assert isinstance(result, DeleteTextResponse)
            assert result.code == 0
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_text_domains(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test getting text domains."""
        mock_response = {
            "code": 0,
            "data": {"domains": ["s.ee", "example.com"]},
            "message": "success",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_get = mocker.patch.object(
                client._http_client,
                "get",
                return_value=mock_response,
            )

            result = await client.get_text_domains()

            assert isinstance(result, DomainResponse)
            assert result.code == 0
            assert "s.ee" in result.data["domains"]
            mock_get.assert_called_once()
