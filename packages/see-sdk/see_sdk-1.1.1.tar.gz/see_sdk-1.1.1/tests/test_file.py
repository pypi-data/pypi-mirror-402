"""Tests for SeeClient File functionalities."""

import pytest
from pytest_mock import MockerFixture

from see.client import SeeClient
from see.models import (
    DeleteFileResponse,
    DomainResponse,
    UploadFileResponse,
)


class TestSeeClientFile:
    """Tests for SeeClient File functionalities."""

    @pytest.mark.asyncio
    async def test_upload_file(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
        tmp_path,
    ) -> None:
        """Test uploading a file."""
        mock_response = {
            "code": 0,
            "data": {
                "file_id": 123,
                "filename": "test.txt",
                "hash": "hash123",
                "url": "https://s.ee/f/hash123",
                "delete": "https://s.ee/del/...",
                "page": "https://s.ee/p/...",
                "width": 0,
                "height": 0,
                "size": 100,
            },
            "message": "success",
        }

        # Create a temporary file
        d = tmp_path / "subdir"
        d.mkdir()
        p = d / "test.txt"
        p.write_text("content")

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_post = mocker.patch.object(
                client._http_client,
                "post",
                return_value=mock_response,
            )

            result = await client.upload_file(str(p))

            assert isinstance(result, UploadFileResponse)
            assert result.code == 0
            assert result.file_id == 123
            assert result.hash == "hash123"
            mock_post.assert_called_once()

            # Verify called kwargs
            _args, kwargs = mock_post.call_args
            assert "files" in kwargs

    @pytest.mark.asyncio
    async def test_delete_file(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test deleting a file."""
        mock_response = {
            "code": "success",
            "message": "deleted",
            "success": True,
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_get = mocker.patch.object(
                client._http_client,
                "get",
                return_value=mock_response,
            )

            result = await client.delete_file("hash123")

            assert isinstance(result, DeleteFileResponse)
            assert result.success is True
            mock_get.assert_called_once_with("/v1/file/delete/hash123")

    @pytest.mark.asyncio
    async def test_get_file_domains(
        self,
        api_key: str,
        base_url: str,
        mocker: MockerFixture,
    ) -> None:
        """Test getting file domains."""
        mock_response = {
            "code": 0,
            "data": {"domains": ["f.see", "files.com"]},
            "message": "success",
        }

        async with SeeClient(api_key=api_key, base_url=base_url) as client:
            mock_get = mocker.patch.object(
                client._http_client,
                "get",
                return_value=mock_response,
            )

            result = await client.get_file_domains()

            assert isinstance(result, DomainResponse)
            assert result.code == 0
            assert "f.see" in result.data["domains"]
            mock_get.assert_called_once()
