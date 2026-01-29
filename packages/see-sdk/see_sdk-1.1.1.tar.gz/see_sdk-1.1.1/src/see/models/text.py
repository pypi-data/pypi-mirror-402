"""Data models for Text Sharing operations."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CreateTextRequest:
    """Represents a request payload to create a text sharing."""

    content: str
    title: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CreateTextRequest":
        return cls(
            content=data.get("content", ""),
            title=data.get("title", ""),
        )


@dataclass(frozen=True)
class CreateTextResponse:
    """Represents a response payload from creating a text sharing."""

    code: int
    custom_slug: str
    short_url: str
    slug: str
    message: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CreateTextResponse":
        inner_data = data.get("data", {})
        return cls(
            code=data.get("code", 0),
            custom_slug=inner_data.get("custom_slug", ""),
            short_url=inner_data.get("short_url", ""),
            slug=inner_data.get("slug", ""),
            message=data.get("message", ""),
        )


@dataclass(frozen=True)
class UpdateTextRequest:
    """Represents a request payload to update a text sharing."""

    content: str
    domain: str
    slug: str
    title: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UpdateTextRequest":
        return cls(
            content=data.get("content", ""),
            domain=data.get("domain", ""),
            slug=data.get("slug", ""),
            title=data.get("title", ""),
        )


@dataclass(frozen=True)
class UpdateTextResponse:
    """Represents a response payload from updating a text sharing."""

    code: int
    message: str
    data: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UpdateTextResponse":
        return cls(
            code=data.get("code", 0),
            message=data.get("message", ""),
            data=data.get("data", {}),
        )


@dataclass(frozen=True)
class DeleteTextRequest:
    """Represents a request payload to delete a text sharing."""

    domain: str
    slug: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeleteTextRequest":
        return cls(
            domain=data.get("domain", ""),
            slug=data.get("slug", ""),
        )


@dataclass(frozen=True)
class DeleteTextResponse:
    """Represents a response payload from deleting a text sharing."""

    code: int
    message: str
    data: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeleteTextResponse":
        return cls(
            code=data.get("code", 0),
            message=data.get("message", ""),
            data=data.get("data", {}),
        )
