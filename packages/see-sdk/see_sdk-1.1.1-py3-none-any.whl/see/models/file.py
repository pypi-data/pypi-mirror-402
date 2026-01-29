"""Data models for File Sharing operations."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UploadFileResponse:
    """Represents a response payload from uploading a file."""

    code: int
    file_id: int
    filename: str
    hash: str
    url: str
    message: str
    delete_url: str = ""
    page_url: str = ""
    width: int = 0
    height: int = 0
    size: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UploadFileResponse":
        inner = data.get("data", {})
        return cls(
            code=data.get("code", 0),
            message=data.get("message", ""),
            file_id=inner.get("file_id", 0),
            filename=inner.get("filename", ""),
            hash=inner.get("hash", ""),
            url=inner.get("url", ""),
            delete_url=inner.get("delete", ""),
            page_url=inner.get("page", ""),
            width=inner.get("width", 0),
            height=inner.get("height", 0),
            size=inner.get("size", 0),
        )


@dataclass(frozen=True)
class DeleteFileResponse:
    """Represents a response payload from deleting a file."""

    code: str
    message: str
    success: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeleteFileResponse":
        return cls(
            code=str(data.get("code", "")),
            message=data.get("message", ""),
            success=data.get("success", False),
        )
