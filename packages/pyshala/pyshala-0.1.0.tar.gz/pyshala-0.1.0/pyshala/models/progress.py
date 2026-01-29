"""Progress tracking data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Progress:
    """Progress record for a lesson."""

    lesson_id: str
    completed: bool = False
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "lesson_id": self.lesson_id,
            "completed": self.completed,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Progress":
        """Create from dictionary."""
        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        return cls(
            lesson_id=data.get("lesson_id", ""),
            completed=data.get("completed", False),
            completed_at=completed_at,
        )
