"""Base model class for Redfish API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self


@dataclass
class BaseModel:
    """Base class for all API response models.

    Provides common functionality:
    - _is_valid tracking for graceful degradation
    - from_dict factory method pattern

    Models should set _is_valid = True only when meaningful data
    was successfully parsed from the API response.
    """

    _is_valid: bool = field(default=False, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create instance from API response dictionary.

        Override in subclasses for custom parsing.

        Args:
            data: Raw API response dictionary

        Returns:
            Model instance
        """
        raise NotImplementedError

    @property
    def is_valid(self) -> bool:
        """Check if data was successfully retrieved from API.

        Returns:
            True if meaningful data was parsed
        """
        return self._is_valid
