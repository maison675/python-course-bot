"""SQLite для прогресса пользователя."""
from __future__ import annotations

from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent.parent / "data" / "progress.db"


async def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS solved (
                user_id   INTEGER NOT NULL,
                task_id   TEXT    NOT NULL,
                solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, task_id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS state (
                user_id        INTEGER PRIMARY KEY,
                current_task   TEXT
            )
            """
        )
        await db.commit()


async def mark_solved(user_id: int, task_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO solved (user_id, task_id) VALUES (?, ?)",
            (user_id, task_id),
        )
        await db.commit()


async def is_solved(user_id: int, task_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM solved WHERE user_id = ? AND task_id = ?",
            (user_id, task_id),
        ) as cur:
            return (await cur.fetchone()) is not None


async def solved_in_topic(user_id: int, topic_id: str) -> set[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT task_id FROM solved WHERE user_id = ? AND task_id LIKE ?",
            (user_id, f"{topic_id}-%"),
        ) as cur:
            rows = await cur.fetchall()
    return {r[0] for r in rows}


async def total_solved(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM solved WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else 0


async def set_current(user_id: int, task_id: str | None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO state (user_id, current_task) VALUES (?, ?) "
            "ON CONFLICT (user_id) DO UPDATE SET current_task = excluded.current_task",
            (user_id, task_id),
        )
        await db.commit()


async def get_current(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT current_task FROM state WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row and row[0] else None
