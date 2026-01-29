"""Structured warning class for MARC lint errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class MarcWarning:
    """A structured warning for a MARC record validation error.

    Attributes:
        field: The MARC field tag (e.g., "020", "245", "LDR" for leader)
        message: The error message
        subfield: Optional subfield code (e.g., "a", "z")
        position: Optional position for repeating fields (0-based index)
        record_id: Optional identifier for the record (e.g., control number from 001,
                   or index position in a batch)
    """

    field: str
    message: str
    subfield: Optional[str] = None
    position: Optional[int] = None
    record_id: Optional[str] = None

    def __str__(self) -> str:
        """Format warning as a string for display.

        Returns a string in the format:
        - "245: Error message" for field-level errors
        - "020: Subfield a error message" for subfield-level errors
        - "245[2]: Error message" for repeating field errors (position shown)
        - "Record 12345: 245: Error message" when record_id is present
        """
        parts = [self.field]

        if self.position is not None:
            parts[0] = f"{self.field}[{self.position + 1}]"

        result = f"{parts[0]}: "

        if self.subfield:
            result += f"Subfield {self.subfield} "

        result += self.message

        if self.record_id:
            result = f"Record {self.record_id}: {result}"

        return result

    def to_dict(self) -> dict:
        """Convert warning to a dictionary for JSON serialization."""
        return {
            "field": self.field,
            "message": self.message,
            "subfield": self.subfield,
            "position": self.position,
            "record_id": self.record_id,
        }
