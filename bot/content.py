"""Загрузка тем и задач из YAML."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import yaml

CONTENT_DIR = Path(__file__).parent.parent / "content"
COURSE_THEORY = CONTENT_DIR / "theory.md"


@dataclass
class Topic:
    id: str
    title: str
    emoji: str
    summary: str


@dataclass
class Task:
    id: str
    topic_id: str
    index: int
    title: str
    statement: str
    reference: str
    check: dict[str, Any]
    needs_stdin: bool = False


@cache
def load_topics() -> list[Topic]:
    data = yaml.safe_load((CONTENT_DIR / "topics.yaml").read_text(encoding="utf-8"))
    return [Topic(**t) for t in data["topics"]]


@cache
def load_tasks(topic_id: str) -> list[Task]:
    path = CONTENT_DIR / "tasks" / f"{topic_id}.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        Task(
            id=t["id"],
            topic_id=t["topic_id"],
            index=t["index"],
            title=t["title"],
            statement=t["statement"],
            reference=t["reference"],
            check=t["check"],
            needs_stdin=t.get("needs_stdin", False),
        )
        for t in data["tasks"]
    ]


def get_task(task_id: str) -> Task | None:
    topic_id = task_id.rsplit("-", 1)[0]
    for t in load_tasks(topic_id):
        if t.id == task_id:
            return t
    return None


def get_topic(topic_id: str) -> Topic | None:
    for t in load_topics():
        if t.id == topic_id:
            return t
    return None


# === Теория: разрезаем учебник на разделы по тем ===

# Соответствие topic_id → номера разделов учебника, которые относятся к теме.
THEORY_SECTIONS: dict[str, list[int]] = {
    "01_hello": [1, 2],
    "02_variables": [4],
    "03_strings": [6],
    "04_operators": [5],
    "05_io": [7],
    "06_conditions": [8],
    "07_loops": [9],
    "08_lists": [10],
    "09_dicts": [10],
    "10_sets": [10],
    "11_functions": [11, 12],
    "12_recursion": [11],
    "13_files": [14],
    "14_exceptions": [15],
    "15_oop": [16, 17, 18],
    "16_comprehensions": [21, 22],
}


@cache
def _theory_sections() -> dict[int, tuple[str, str]]:
    """Парсит учебник, разбивает на разделы вида '## N. Title'.

    Возвращает {номер: (заголовок, тело)}.
    """
    import re

    text = COURSE_THEORY.read_text(encoding="utf-8")
    pattern = re.compile(r"^##\s+(\d+)\.\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: dict[int, tuple[str, str]] = {}
    for i, m in enumerate(matches):
        num = int(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections[num] = (title, body)
    return sections


def get_theory(topic_id: str) -> str:
    sec_nums = THEORY_SECTIONS.get(topic_id, [])
    sections = _theory_sections()
    parts: list[str] = []
    for n in sec_nums:
        if n in sections:
            title, body = sections[n]
            parts.append(f"## {n}. {title}\n\n{body}")
    if not parts:
        return "_Теория для этой темы пока не размечена._"
    return "\n\n---\n\n".join(parts)


if __name__ == "__main__":
    for t in load_topics():
        tasks = load_tasks(t.id)
        theory = get_theory(t.id)
        print(f"{t.emoji} {t.title}: {len(tasks)} задач, теория {len(theory)} симв.")
