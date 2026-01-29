from pathlib import Path

from ..models import (
    DeleteFileResponse,
    DomainResponse,
    UploadFileResponse,
)
from .base import BaseAPI


class FileAPI(BaseAPI):
    """API methods for File Sharing operations."""

    async def upload_file(self, file_path: str) -> UploadFileResponse:
        """
        Upload a file.

        Args:
            file_path: Path to the file to upload

        Returns:
            UploadFileResponse: Response containing the uploaded file details

        Raises:
            APIError: If the API request fails
            IOError: If the file cannot be read
        """
        path = Path(file_path)
        filename = path.name

        with path.open("rb") as f:
            # httpx will handle the multipart encoding by providing `files`.
            files = {"file": (filename, f)}

            response = await self._http_client.post(
                "/v1/file/upload",
                files=files,
            )
            return UploadFileResponse.from_dict(response)

    async def delete_file(self, hash_str: str) -> DeleteFileResponse:
        """
        Delete a file.

        Args:
            hash_str: The hash of the file to delete

        Returns:
            DeleteFileResponse: Response indicating the deletion status

        Raises:
            APIError: If the API request fails
        """
        # The doc says /delete/string, likely /delete/{hash}
        response = await self._http_client.get(f"/v1/file/delete/{hash_str}")
        return DeleteFileResponse.from_dict(response)

    async def get_file_domains(self) -> DomainResponse:
        """
        Get available domains for file sharing.

        Returns:
            DomainResponse: Response containing the list of available domains

        Raises:
            APIError: If the API request fails
        """
        response = await self._http_client.get("/v1/file/domains")
        return DomainResponse.from_dict(response)
