"""Загрузка тем и задач из YAML."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import yaml

CONTENT_DIR = Path(__file__).parent.parent / "content"
LEGACY_THEORY = CONTENT_DIR / "theory.md"
THEORY_DIR = CONTENT_DIR / "theory"


@dataclass
class Track:
    id: str  # "beginner" | "advanced"
    title: str
    description: str
    topic_ids: list[str]


@dataclass
class Topic:
    id: str
    title: str
    emoji: str
    summary: str
    track_id: str


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
def _raw() -> dict:
    return yaml.safe_load((CONTENT_DIR / "topics.yaml").read_text(encoding="utf-8"))


@cache
def load_tracks() -> list[Track]:
    data = _raw()
    out: list[Track] = []
    for tid, t in data["tracks"].items():
        out.append(
            Track(
                id=tid,
                title=t["title"],
                description=t["description"].strip(),
                topic_ids=[topic["id"] for topic in t["topics"]],
            )
        )
    return out


@cache
def get_track(track_id: str) -> Track | None:
    for t in load_tracks():
        if t.id == track_id:
            return t
    return None


@cache
def load_topics(track_id: str | None = None) -> list[Topic]:
    """Список тем. Если track_id указан — только из этого трека."""
    data = _raw()
    out: list[Topic] = []
    for tid, track in data["tracks"].items():
        if track_id and tid != track_id:
            continue
        for topic in track["topics"]:
            out.append(
                Topic(
                    id=topic["id"],
                    title=topic["title"],
                    emoji=topic["emoji"],
                    summary=topic["summary"],
                    track_id=tid,
                )
            )
    return out


@cache
def get_topic(topic_id: str) -> Topic | None:
    for t in load_topics():
        if t.id == topic_id:
            return t
    return None


@cache
def load_tasks(topic_id: str) -> list[Task]:
    path = CONTENT_DIR / "tasks" / f"{topic_id}.yaml"
    if not path.exists():
        return []
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


# === Теория ===
#
# Теория хранится в двух источниках:
# 1. `content/theory/<track>/<topic_id>.md` — расширенная теория, пишется
#    вручную для каждой темы. Если файл есть — используем его.
# 2. `content/theory.md` — общий учебник 25 разделов, режется по секциям.
#    Используется как fallback.

LEGACY_SECTIONS: dict[str, list[int]] = {
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
def _legacy_sections() -> dict[int, tuple[str, str]]:
    import re

    if not LEGACY_THEORY.exists():
        return {}
    text = LEGACY_THEORY.read_text(encoding="utf-8")
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
    topic = get_topic(topic_id)
    if topic is None:
        return "_Тема не найдена._"
    # 1) Свой файл
    custom = THEORY_DIR / topic.track_id / f"{topic_id}.md"
    if custom.exists():
        return custom.read_text(encoding="utf-8").strip()

    # 2) Legacy fallback из общего учебника
    sec_nums = LEGACY_SECTIONS.get(topic_id, [])
    sections = _legacy_sections()
    parts: list[str] = []
    for n in sec_nums:
        if n in sections:
            title, body = sections[n]
            parts.append(f"## {n}. {title}\n\n{body}")
    if parts:
        return "\n\n---\n\n".join(parts)
    return "_Теория для этой темы пока в работе._"


def has_custom_theory(topic_id: str) -> bool:
    topic = get_topic(topic_id)
    if topic is None:
        return False
    return (THEORY_DIR / topic.track_id / f"{topic_id}.md").exists()


if __name__ == "__main__":
    for tr in load_tracks():
        print(f"\n{tr.title}")
        print(f"  {tr.description[:80]}…")
        for t in load_topics(tr.id):
            tasks = load_tasks(t.id)
            theory_kind = "custom" if has_custom_theory(t.id) else "legacy"
            print(
                f"  {t.emoji} {t.title}: {len(tasks)} задач, "
                f"теория ({theory_kind}) {len(get_theory(t.id))} симв."
            )
