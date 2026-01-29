"""Module data model."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .lesson import Lesson


@dataclass
class Module:
    """A module containing multiple lessons."""

    id: str
    name: str
    description: str = ""
    order: int = 0
    lesson_files: list[str] = field(default_factory=list)
    lessons: list["Lesson"] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "lesson_count": len(self.lessons),
            "lessons": [lesson.to_dict() for lesson in self.lessons],
        }

    @classmethod
    def from_dict(cls, data: dict, module_id: str = "") -> "Module":
        """Create from dictionary (without lessons - they're loaded separately)."""
        return cls(
            id=module_id or data.get("id", ""),
            name=data.get("name", "Untitled Module"),
            description=data.get("description", ""),
            order=data.get("order", 0),
            lesson_files=data.get("lessons", []),
        )
