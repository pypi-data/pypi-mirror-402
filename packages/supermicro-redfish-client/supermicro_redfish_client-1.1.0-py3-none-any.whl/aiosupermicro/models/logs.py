"""Log-related models for /redfish/v1/Managers/1/LogServices."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel


@dataclass(kw_only=True)
class LogEntryOem:
    """OEM (Supermicro-specific) log entry information."""

    interface: str = ""
    user: str = ""
    source: str = ""
    category: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LogEntryOem:
        """Parse from Oem.Supermicro object."""
        supermicro = data.get("Supermicro", {})
        return cls(
            interface=supermicro.get("Interface", ""),
            user=supermicro.get("User", ""),
            source=supermicro.get("Source", ""),
            category=supermicro.get("Category", ""),
        )


@dataclass(kw_only=True)
class LogEntry(BaseModel):
    """Log entry from /redfish/v1/Managers/1/LogServices/x/Entries/y."""

    id: str = ""
    name: str = ""
    entry_type: str = ""
    severity: str = ""
    created: str = ""
    message: str = ""
    message_id: str = ""
    oem_record_format: str = ""

    # OEM data
    oem: LogEntryOem = field(default_factory=LogEntryOem)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LogEntry:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            entry_type=data.get("EntryType", ""),
            severity=data.get("Severity", ""),
            created=data.get("Created", ""),
            message=data.get("Message", ""),
            message_id=data.get("MessageId", ""),
            oem_record_format=data.get("OemRecordFormat", ""),
            oem=LogEntryOem.from_dict(data.get("Oem", {})),
        )

        # Valid if we have message
        instance._is_valid = bool(instance.message)
        return instance

    @property
    def is_error(self) -> bool:
        """Check if this is an error entry."""
        return self.severity in ("Critical", "Warning")

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical entry."""
        return self.severity == "Critical"
