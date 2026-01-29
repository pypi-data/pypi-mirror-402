"""Lesson loader service for parsing YAML lesson files."""

import os
from pathlib import Path
from typing import Optional

import yaml

from ..models.lesson import DataFile, Lesson, TestCase
from ..models.module import Module


class LessonLoader:
    """Service to load and cache lessons from YAML files."""

    def __init__(self, lessons_path: Optional[str] = None):
        """Initialize the lesson loader.

        Args:
            lessons_path: Path to the lessons directory.
                         Defaults to LESSONS_PATH env var or ./lessons
        """
        self.lessons_path = Path(
            lessons_path or os.getenv("LESSONS_PATH", "./lessons")
        )
        self._modules_cache: dict[str, Module] = {}
        self._lessons_cache: dict[str, Lesson] = {}

    def load_all(self) -> list[Module]:
        """Load all modules and lessons from the lessons directory.

        Returns:
            List of Module objects with their lessons populated.
        """
        self._modules_cache.clear()
        self._lessons_cache.clear()

        modules = []

        if not self.lessons_path.exists():
            return modules

        # Each subdirectory is a module
        for module_dir in sorted(self.lessons_path.iterdir()):
            if not module_dir.is_dir():
                continue
            if module_dir.name.startswith("."):
                continue

            module = self._load_module(module_dir)
            if module:
                modules.append(module)
                self._modules_cache[module.id] = module

        # Sort modules by order
        modules.sort(key=lambda m: m.order)

        return modules

    def _load_module(self, module_dir: Path) -> Optional[Module]:
        """Load a single module from a directory.

        Args:
            module_dir: Path to the module directory.

        Returns:
            Module object or None if invalid.
        """
        module_file = module_dir / "module.yaml"
        module_id = module_dir.name

        if module_file.exists():
            with open(module_file) as f:
                data = yaml.safe_load(f) or {}
            module = Module.from_dict(data, module_id=module_id)
        else:
            # Create module from directory name
            module = Module(
                id=module_id,
                name=module_id.replace("_", " ").replace("-", " ").title(),
            )

        # Load lessons
        module.lessons = self._load_module_lessons(module_dir, module)

        return module

    def _load_module_lessons(
        self, module_dir: Path, module: Module
    ) -> list[Lesson]:
        """Load all lessons for a module.

        Args:
            module_dir: Path to the module directory.
            module: The parent module.

        Returns:
            List of Lesson objects.
        """
        lessons = []

        # If module.yaml specifies lesson files, use that order
        if module.lesson_files:
            for i, filename in enumerate(module.lesson_files):
                lesson_path = module_dir / filename
                if lesson_path.exists():
                    lesson = self._load_lesson(lesson_path, module.id, order=i)
                    if lesson:
                        lessons.append(lesson)
                        self._lessons_cache[f"{module.id}/{lesson.id}"] = lesson
        else:
            # Auto-discover YAML files (excluding module.yaml)
            yaml_files = sorted(
                [
                    f
                    for f in module_dir.glob("*.yaml")
                    if f.name != "module.yaml"
                ]
            )
            for i, lesson_path in enumerate(yaml_files):
                lesson = self._load_lesson(lesson_path, module.id, order=i)
                if lesson:
                    lessons.append(lesson)
                    self._lessons_cache[f"{module.id}/{lesson.id}"] = lesson

        # Sort by order
        lessons.sort(key=lambda l: l.order)

        return lessons

    def _load_lesson(
        self, lesson_path: Path, module_id: str, order: int = 0
    ) -> Optional[Lesson]:
        """Load a single lesson from a YAML file.

        Args:
            lesson_path: Path to the lesson YAML file.
            module_id: ID of the parent module.
            order: Default order if not specified in YAML.

        Returns:
            Lesson object or None if invalid.
        """
        try:
            with open(lesson_path) as f:
                data = yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError) as e:
            print(f"Error loading lesson {lesson_path}: {e}")
            return None

        # Generate lesson ID from filename
        lesson_id = lesson_path.stem

        # Parse test cases
        test_cases = []
        for tc_data in data.get("test_cases", []):
            test_cases.append(TestCase.from_dict(tc_data))

        # Parse data files
        data_files = []
        for df_data in data.get("data_files", []):
            df = DataFile.from_dict(df_data)
            # Load file content
            file_path = lesson_path.parent / df.path
            if file_path.exists():
                try:
                    with open(file_path, "rb") as f:
                        df.content = f.read()
                except OSError:
                    pass
            data_files.append(df)

        # Check for external instructions file
        instructions = data.get("instructions", "")
        instructions_file = data.get("instructions_file")
        if instructions_file:
            instructions_path = lesson_path.parent / instructions_file
            if instructions_path.exists():
                try:
                    with open(instructions_path) as f:
                        instructions = f.read()
                except OSError:
                    pass

        lesson = Lesson(
            id=lesson_id,
            title=data.get("title", lesson_id.replace("_", " ").title()),
            description=data.get("description", ""),
            instructions=instructions,
            starter_code=data.get("starter_code", ""),
            order=data.get("order", order),
            module_id=module_id,
            test_cases=test_cases,
            data_files=data_files,
        )

        return lesson

    def get_module(self, module_id: str) -> Optional[Module]:
        """Get a module by ID.

        Args:
            module_id: The module identifier.

        Returns:
            Module object or None if not found.
        """
        if not self._modules_cache:
            self.load_all()
        return self._modules_cache.get(module_id)

    def get_lesson(self, module_id: str, lesson_id: str) -> Optional[Lesson]:
        """Get a lesson by module and lesson ID.

        Args:
            module_id: The module identifier.
            lesson_id: The lesson identifier.

        Returns:
            Lesson object or None if not found.
        """
        if not self._lessons_cache:
            self.load_all()
        return self._lessons_cache.get(f"{module_id}/{lesson_id}")

    def get_all_modules(self) -> list[Module]:
        """Get all loaded modules.

        Returns:
            List of Module objects.
        """
        if not self._modules_cache:
            self.load_all()
        return list(self._modules_cache.values())

    def get_next_lesson(
        self, module_id: str, lesson_id: str
    ) -> Optional[Lesson]:
        """Get the next lesson after the given one.

        Args:
            module_id: Current module ID.
            lesson_id: Current lesson ID.

        Returns:
            Next Lesson object or None if at the end.
        """
        module = self.get_module(module_id)
        if not module:
            return None

        current_idx = None
        for i, lesson in enumerate(module.lessons):
            if lesson.id == lesson_id:
                current_idx = i
                break

        if current_idx is None or current_idx >= len(module.lessons) - 1:
            return None

        return module.lessons[current_idx + 1]

    def get_previous_lesson(
        self, module_id: str, lesson_id: str
    ) -> Optional[Lesson]:
        """Get the previous lesson before the given one.

        Args:
            module_id: Current module ID.
            lesson_id: Current lesson ID.

        Returns:
            Previous Lesson object or None if at the beginning.
        """
        module = self.get_module(module_id)
        if not module:
            return None

        current_idx = None
        for i, lesson in enumerate(module.lessons):
            if lesson.id == lesson_id:
                current_idx = i
                break

        if current_idx is None or current_idx <= 0:
            return None

        return module.lessons[current_idx - 1]


# Global instance
_loader: Optional[LessonLoader] = None


def get_lesson_loader() -> LessonLoader:
    """Get the global lesson loader instance."""
    global _loader
    if _loader is None:
        _loader = LessonLoader()
        _loader.load_all()
    return _loader
