"""Tests for the main SeeClient."""

import pytest
from pytest_mock import MockerFixture

from see.client import SeeClient
from see.exceptions import ValidationError
from see.models import (
    DomainResponse,
    TagResponse,
)


class TestSeeClient:
    """Tests for SeeClient class."""

    def test_client_initialization(self, api_key: str, base_url: str) -> None:
        """Test client initialization with valid API key."""
        client = SeeClient(api_key=api_key, base_url=base_url)
        assert client is not None
        assert client._http_client is not None

    def test_client_initialization_without_api_key(self) -> None:
        """Test client initialization fails without API key."""
        with pytest.raises(ValidationError, match="API key is required"):
            SeeClient(api_key="")

    @pytest.mark.asyncio
    async def test_get_domains(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test retrieving available domains."""
        mock_response = {
            "code": 200,
            "data": {"domains": ["example.com", "short.link", "my.link"]},
            "message": "Success",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_get = mocker.patch.object(
                client._http_client,
                "get",
                return_value=mock_response,
            )

            result = await client.get_domains()

            assert isinstance(result, DomainResponse)
            assert result.code == 200
            assert "domains" in result.data
            assert len(result.data["domains"]) == 3
            mock_get.assert_called_once_with("/v1/domains")

    @pytest.mark.asyncio
    async def test_get_tags(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test retrieving available tags."""
        mock_response = {
            "code": 200,
            "data": {
                "tags": [
                    {"id": 1, "name": "Marketing"},
                    {"id": 2, "name": "Sales"},
                ]
            },
            "message": "Success",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_get = mocker.patch.object(
                client._http_client,
                "get",
                return_value=mock_response,
            )

            result = await client.get_tags()

            assert isinstance(result, TagResponse)
            assert result.code == 200
            assert "tags" in result.data
            assert len(result.data["tags"]) == 2
            mock_get.assert_called_once_with("/v1/tags")
