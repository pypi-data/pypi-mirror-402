"""Lesson and TestCase data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QuestionOption:
    """A single option for an MCQ question."""

    id: str  # e.g., "a", "b", "c", "d"
    text: str

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {"id": self.id, "text": self.text}

    @classmethod
    def from_dict(cls, data: dict) -> "QuestionOption":
        """Create from dictionary."""
        return cls(id=data.get("id", ""), text=data.get("text", ""))


@dataclass
class Question:
    """A quiz question (MCQ or text)."""

    id: str
    type: str  # "mcq" or "text"
    text: str  # Question text
    options: list[QuestionOption] = field(default_factory=list)  # MCQ options
    multi_select: bool = False  # MCQ: radio vs checkbox
    correct: list[str] = field(default_factory=list)  # Correct answer(s)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "options": [opt.to_dict() for opt in self.options],
            "multi_select": self.multi_select,
            "correct": self.correct,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        """Create from dictionary."""
        options = [QuestionOption.from_dict(opt) for opt in data.get("options", [])]
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "mcq"),
            text=data.get("text", ""),
            options=options,
            multi_select=data.get("multi_select", False),
            correct=data.get("correct", []),
        )


@dataclass
class TestCase:
    """A single test case for a lesson."""

    stdin: str = ""
    expected_output: str = ""
    description: str = ""
    hidden: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "stdin": self.stdin,
            "expected_output": self.expected_output,
            "description": self.description,
            "hidden": self.hidden,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TestCase":
        """Create from dictionary."""
        return cls(
            stdin=data.get("stdin", ""),
            expected_output=data.get("expected_output", ""),
            description=data.get("description", ""),
            hidden=data.get("hidden", False),
        )


@dataclass
class DataFile:
    """A data file associated with a lesson."""

    name: str
    path: str
    content: Optional[bytes] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "path": self.path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataFile":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
        )


@dataclass
class Lesson:
    """A single lesson within a module."""

    id: str
    title: str
    description: str = ""
    instructions: str = ""
    starter_code: str = ""
    order: int = 0
    module_id: str = ""
    lesson_type: str = "code"  # "code" or "quiz"
    test_cases: list[TestCase] = field(default_factory=list)
    data_files: list[DataFile] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)  # For quiz lessons

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "starter_code": self.starter_code,
            "order": self.order,
            "module_id": self.module_id,
            "lesson_type": self.lesson_type,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "data_files": [df.to_dict() for df in self.data_files],
            "questions": [q.to_dict() for q in self.questions],
        }

    @classmethod
    def from_dict(cls, data: dict, module_id: str = "") -> "Lesson":
        """Create from dictionary."""
        test_cases = [
            TestCase.from_dict(tc) for tc in data.get("test_cases", [])
        ]
        data_files = [
            DataFile.from_dict(df) for df in data.get("data_files", [])
        ]
        questions = [
            Question.from_dict(q) for q in data.get("questions", [])
        ]

        return cls(
            id=data.get("id", ""),
            title=data.get("title", "Untitled Lesson"),
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            starter_code=data.get("starter_code", ""),
            order=data.get("order", 0),
            module_id=module_id,
            lesson_type=data.get("type", "code"),
            test_cases=test_cases,
            data_files=data_files,
            questions=questions,
        )
