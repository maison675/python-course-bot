"""Клавиатуры и форматирование сообщений."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.content import Task, Topic, load_tasks, load_topics

TG_MAX = 4000  # с запасом до лимита 4096


def main_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📚 Темы курса", callback_data="topics")
    b.button(text="📊 Мой прогресс", callback_data="progress")
    b.button(text="ℹ️ Как пользоваться", callback_data="help")
    b.adjust(1)
    return b.as_markup()


def topics_menu(solved_per_topic: dict[str, int]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for t in load_topics():
        solved = solved_per_topic.get(t.id, 0)
        suffix = f" ({solved}/10)" if solved else ""
        b.button(text=f"{t.emoji} {t.title}{suffix}", callback_data=f"t:{t.id}")
    b.button(text="« В меню", callback_data="main")
    b.adjust(1)
    return b.as_markup()


def topic_menu(topic: Topic, solved: set[str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📖 Теория", callback_data=f"y:{topic.id}")
    n_solved = len(solved)
    b.button(
        text=f"🎯 Полигон ({n_solved}/10 решено)",
        callback_data=f"p:{topic.id}",
    )
    b.button(text="« К темам", callback_data="topics")
    b.adjust(1)
    return b.as_markup()


def practice_menu(topic: Topic, solved: set[str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for task in load_tasks(topic.id):
        mark = "✅" if task.id in solved else "⬜"
        b.button(
            text=f"{mark} {task.index}. {task.title[:40]}",
            callback_data=f"q:{task.id}",
        )
    b.button(text="« К теме", callback_data=f"t:{topic.id}")
    b.adjust(1)
    return b.as_markup()


def task_menu(task: Task, *, solved: bool, has_next: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Показать решение", callback_data=f"s:{task.id}")
    if has_next:
        b.button(text="➡️ Следующая задача", callback_data=f"n:{task.id}")
    b.button(text="« К списку задач", callback_data=f"p:{task.topic_id}")
    b.adjust(1)
    return b.as_markup()


def chunk_text(text: str, limit: int = TG_MAX) -> list[str]:
    """Разбить длинный текст на куски, стараясь резать по абзацам."""
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    cur = ""
    for paragraph in text.split("\n\n"):
        if len(cur) + len(paragraph) + 2 > limit:
            if cur:
                parts.append(cur.rstrip())
                cur = ""
            # параграф сам слишком большой?
            while len(paragraph) > limit:
                parts.append(paragraph[:limit])
                paragraph = paragraph[limit:]
        cur += paragraph + "\n\n"
    if cur.strip():
        parts.append(cur.rstrip())
    return parts


def task_intro(task: Task, *, solved: bool) -> str:
    head = f"{'✅' if solved else '🎯'} *Задача {task.index}*\n\n"
    body = task.statement
    tail = "\n\n💡 Напиши решение в чат — я проверю автоматически."
    if task.needs_stdin:
        tail += "\n\nДля этой задачи я подам нужный ввод сам, можешь использовать `input()`."
    return head + body + tail
