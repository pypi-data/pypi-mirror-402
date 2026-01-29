"""SQLite-based progress tracking service."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

from ..models.progress import Progress


class ProgressDB:
    """Service to track lesson completion progress in SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the progress database.

        Args:
            db_path: Path to the SQLite database file.
                    Defaults to DATABASE_PATH env var or ./data/progress.db
        """
        self.db_path = Path(
            db_path or os.getenv("DATABASE_PATH", "./data/progress.db")
        )
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database and create tables if needed."""
        if self._initialized:
            return

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_id TEXT UNIQUE NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    completed_at TEXT
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_lesson_id
                ON progress (lesson_id)
            """)
            await db.commit()

        self._initialized = True

    async def mark_completed(self, lesson_id: str) -> Progress:
        """Mark a lesson as completed.

        Args:
            lesson_id: The lesson identifier (format: module_id/lesson_id).

        Returns:
            Updated Progress record.
        """
        await self.initialize()

        completed_at = datetime.utcnow()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO progress (lesson_id, completed, completed_at)
                VALUES (?, 1, ?)
                ON CONFLICT(lesson_id) DO UPDATE SET
                    completed = 1,
                    completed_at = ?
                """,
                (lesson_id, completed_at.isoformat(), completed_at.isoformat()),
            )
            await db.commit()

        return Progress(
            lesson_id=lesson_id,
            completed=True,
            completed_at=completed_at,
        )

    async def mark_incomplete(self, lesson_id: str) -> Progress:
        """Mark a lesson as incomplete.

        Args:
            lesson_id: The lesson identifier.

        Returns:
            Updated Progress record.
        """
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO progress (lesson_id, completed, completed_at)
                VALUES (?, 0, NULL)
                ON CONFLICT(lesson_id) DO UPDATE SET
                    completed = 0,
                    completed_at = NULL
                """,
                (lesson_id,),
            )
            await db.commit()

        return Progress(lesson_id=lesson_id, completed=False)

    async def get_progress(self, lesson_id: str) -> Progress:
        """Get progress for a specific lesson.

        Args:
            lesson_id: The lesson identifier.

        Returns:
            Progress record (may be incomplete if not found).
        """
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM progress WHERE lesson_id = ?",
                (lesson_id,),
            ) as cursor:
                row = await cursor.fetchone()

        if not row:
            return Progress(lesson_id=lesson_id, completed=False)

        completed_at = None
        if row["completed_at"]:
            completed_at = datetime.fromisoformat(row["completed_at"])

        return Progress(
            lesson_id=lesson_id,
            completed=bool(row["completed"]),
            completed_at=completed_at,
        )

    async def get_all_progress(self) -> dict[str, Progress]:
        """Get all progress records.

        Returns:
            Dictionary mapping lesson_id to Progress records.
        """
        await self.initialize()

        progress_map = {}

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM progress") as cursor:
                async for row in cursor:
                    completed_at = None
                    if row["completed_at"]:
                        completed_at = datetime.fromisoformat(
                            row["completed_at"]
                        )

                    progress_map[row["lesson_id"]] = Progress(
                        lesson_id=row["lesson_id"],
                        completed=bool(row["completed"]),
                        completed_at=completed_at,
                    )

        return progress_map

    async def get_completed_lessons(self) -> set[str]:
        """Get the set of completed lesson IDs.

        Returns:
            Set of completed lesson identifiers.
        """
        await self.initialize()

        completed = set()

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT lesson_id FROM progress WHERE completed = 1"
            ) as cursor:
                async for row in cursor:
                    completed.add(row[0])

        return completed

    async def get_module_progress(
        self, module_id: str, lesson_ids: list[str]
    ) -> tuple[int, int]:
        """Get progress statistics for a module.

        Args:
            module_id: The module identifier.
            lesson_ids: List of lesson IDs in the module.

        Returns:
            Tuple of (completed_count, total_count).
        """
        await self.initialize()

        full_ids = [f"{module_id}/{lid}" for lid in lesson_ids]
        completed = await self.get_completed_lessons()

        completed_count = sum(1 for lid in full_ids if lid in completed)

        return completed_count, len(lesson_ids)

    async def reset_progress(self) -> None:
        """Reset all progress (for testing/development)."""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM progress")
            await db.commit()


# Global instance
_db: Optional[ProgressDB] = None


def get_progress_db() -> ProgressDB:
    """Get the global progress database instance."""
    global _db
    if _db is None:
        _db = ProgressDB()
    return _db
