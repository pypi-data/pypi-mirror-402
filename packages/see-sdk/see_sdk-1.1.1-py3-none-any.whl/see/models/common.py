"""Common data models for SEE URL SDK."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DomainResponse:
    """Represents a response payload containing available domains."""

    code: int
    data: dict[str, list[str]]
    message: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainResponse":
        """Create a DomainResponse instance from a dictionary."""
        return cls(
            code=data.get("code", 0),
            data=data.get("data", {}),
            message=data.get("message", ""),
        )


@dataclass(frozen=True)
class Tag:
    """Represents a tag model."""

    id: int
    name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tag":
        """Create a Tag instance from a dictionary."""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
        )


@dataclass(frozen=True)
class TagResponse:
    """Represents a response payload containing tags."""

    code: int
    data: dict[str, list[dict[str, Any]]]
    message: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TagResponse":
        """Create a TagResponse instance from a dictionary."""
        return cls(
            code=data.get("code", 0),
            data=data.get("data", {}),
            message=data.get("message", ""),
        )
