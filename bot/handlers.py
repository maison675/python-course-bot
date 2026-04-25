"""Обработчики команд и callback-запросов."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot import progress
from bot.content import (
    Task,
    Topic,
    get_task,
    get_topic,
    get_theory,
    load_tasks,
    load_topics,
)
from bot.ui import (
    chunk_text,
    main_menu,
    practice_menu,
    task_intro,
    task_menu,
    topic_menu,
    topics_menu,
)
from sandbox.grader import grade

log = logging.getLogger(__name__)
router = Router()

OWNER_ID = int(os.getenv("OWNER_TG_ID", "0"))


@router.message(F.from_user.id != OWNER_ID)
async def reject_others(msg: Message) -> None:
    if OWNER_ID == 0:
        return
    await msg.answer(
        "Этот бот личный. Если ты хочешь свой такой — напиши Devin :)"
    )


@router.message(CommandStart())
async def cmd_start(msg: Message) -> None:
    await progress.set_current(msg.from_user.id, None)
    await msg.answer(
        "Привет! Я твой персональный тренажёр по Python.\n\n"
        "Здесь 16 тем, в каждой 10 задач. Я буду проверять решения автоматически.\n\n"
        "Выбирай тему, читай теорию, решай задачи. Удачи!",
        reply_markup=main_menu(),
    )


@router.message(Command("menu"))
async def cmd_menu(msg: Message) -> None:
    await msg.answer("Меню", reply_markup=main_menu())


@router.message(Command("topics"))
async def cmd_topics(msg: Message) -> None:
    await _show_topics(msg)


@router.message(Command("progress"))
async def cmd_progress(msg: Message) -> None:
    await _show_progress(msg)


# === Кнопки главного меню ===


@router.callback_query(F.data == "main")
async def cb_main(cb: CallbackQuery) -> None:
    await cb.message.edit_text("Меню", reply_markup=main_menu())
    await cb.answer()


@router.callback_query(F.data == "topics")
async def cb_topics(cb: CallbackQuery) -> None:
    await _show_topics(cb.message, edit=True, user_id=cb.from_user.id)
    await cb.answer()


@router.callback_query(F.data == "progress")
async def cb_progress(cb: CallbackQuery) -> None:
    await _show_progress(cb.message, user_id=cb.from_user.id, edit=True)
    await cb.answer()


@router.callback_query(F.data == "help")
async def cb_help(cb: CallbackQuery) -> None:
    text = (
        "*Как пользоваться ботом*\n\n"
        "1. Заходишь в любую тему.\n"
        "2. Читаешь теорию (кнопка 📖).\n"
        "3. Открываешь полигон (🎯), выбираешь задачу.\n"
        "4. Пишешь решение прямо в чат — я запускаю его в песочнице "
        "и сравниваю вывод с эталоном.\n"
        "5. Если получилось — задача отмечается ✅. Если нет — покажу разницу.\n\n"
        "Команды:\n"
        "/menu — главное меню\n"
        "/topics — список тем\n"
        "/progress — статистика"
    )
    await cb.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await cb.answer()


# === Темы ===


async def _show_topics(target: Message, *, edit: bool = False, user_id: int | None = None) -> None:
    user_id = user_id or target.from_user.id
    counts: dict[str, int] = {}
    for t in load_topics():
        solved = await progress.solved_in_topic(user_id, t.id)
        counts[t.id] = len(solved)
    kb = topics_menu(counts)
    text = "📚 Выбери тему:"
    if edit:
        await target.edit_text(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("t:"))
async def cb_topic(cb: CallbackQuery) -> None:
    topic_id = cb.data[2:]
    topic = get_topic(topic_id)
    if topic is None:
        await cb.answer("Тема не найдена")
        return
    solved = await progress.solved_in_topic(cb.from_user.id, topic_id)
    text = f"{topic.emoji} *{topic.title}*\n\n{topic.summary}"
    await cb.message.edit_text(
        text, reply_markup=topic_menu(topic, solved), parse_mode="Markdown"
    )
    await cb.answer()


# === Теория ===


@router.callback_query(F.data.startswith("y:"))
async def cb_theory(cb: CallbackQuery) -> None:
    topic_id = cb.data[2:]
    topic = get_topic(topic_id)
    theory = get_theory(topic_id)
    chunks = chunk_text(theory)

    # Первое сообщение — редактируем текущее (на ходу меняем заголовок),
    # остальные — добавляем новыми сообщениями.
    await cb.message.edit_text(f"📖 *Теория: {topic.title}*", parse_mode="Markdown")
    for i, ch in enumerate(chunks):
        try:
            await cb.message.answer(ch, parse_mode="Markdown")
        except Exception:
            # Если Markdown ломается на каком-то спецсимволе — слать без разметки
            await cb.message.answer(ch)
    solved = await progress.solved_in_topic(cb.from_user.id, topic_id)
    await cb.message.answer("Готов решать?", reply_markup=topic_menu(topic, solved))
    await cb.answer()


# === Полигон ===


@router.callback_query(F.data.startswith("p:"))
async def cb_practice(cb: CallbackQuery) -> None:
    topic_id = cb.data[2:]
    topic = get_topic(topic_id)
    solved = await progress.solved_in_topic(cb.from_user.id, topic_id)
    text = f"🎯 *Полигон: {topic.title}*\n\nВыбери задачу:"
    await cb.message.edit_text(
        text, reply_markup=practice_menu(topic, solved), parse_mode="Markdown"
    )
    await cb.answer()


@router.callback_query(F.data.startswith("q:"))
async def cb_task(cb: CallbackQuery) -> None:
    task_id = cb.data[2:]
    task = get_task(task_id)
    if task is None:
        await cb.answer("Задача не найдена")
        return
    await progress.set_current(cb.from_user.id, task_id)
    solved = await progress.is_solved(cb.from_user.id, task_id)
    has_next = task.index < 10
    await cb.message.answer(
        task_intro(task, solved=solved),
        reply_markup=task_menu(task, solved=solved, has_next=has_next),
        parse_mode="Markdown",
    )
    await cb.answer()


@router.callback_query(F.data.startswith("s:"))
async def cb_solution(cb: CallbackQuery) -> None:
    task_id = cb.data[2:]
    task = get_task(task_id)
    if task is None:
        await cb.answer("Задача не найдена")
        return
    msg = (
        f"📝 *Эталонное решение*\n\n```python\n{task.reference}```\n\n"
        f"Это лишь _один из_ способов — твоё решение тоже принимается, "
        f"если выводит то же самое."
    )
    await cb.message.answer(msg, parse_mode="Markdown")
    await cb.answer()


@router.callback_query(F.data.startswith("n:"))
async def cb_next(cb: CallbackQuery) -> None:
    cur_id = cb.data[2:]
    cur = get_task(cur_id)
    if cur is None:
        await cb.answer("Не найдено")
        return
    next_index = cur.index + 1
    next_id = f"{cur.topic_id}-{next_index:02d}"
    nxt = get_task(next_id)
    if nxt is None:
        await cb.answer("Это была последняя задача темы!", show_alert=True)
        return
    await progress.set_current(cb.from_user.id, next_id)
    solved = await progress.is_solved(cb.from_user.id, next_id)
    has_next = nxt.index < 10
    await cb.message.answer(
        task_intro(nxt, solved=solved),
        reply_markup=task_menu(nxt, solved=solved, has_next=has_next),
        parse_mode="Markdown",
    )
    await cb.answer()


# === Прогресс ===


async def _show_progress(target: Message, *, user_id: int | None = None, edit: bool = False) -> None:
    user_id = user_id or target.from_user.id
    total = await progress.total_solved(user_id)
    lines = [f"📊 *Твой прогресс*\n\nРешено всего: *{total}/160*\n"]
    for t in load_topics():
        n = len(await progress.solved_in_topic(user_id, t.id))
        bar_len = 10
        filled = "▰" * n + "▱" * (bar_len - n)
        lines.append(f"{t.emoji} {t.title}\n   {filled}  {n}/10")
    text = "\n".join(lines)
    if edit:
        await target.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await target.answer(text, reply_markup=main_menu(), parse_mode="Markdown")


# === Решение задачи: пользователь шлёт код ===


def _looks_like_code(text: str) -> bool:
    if not text:
        return False
    return any(
        kw in text
        for kw in (
            "print(", "input(", "def ", "for ", "while ", "if ", "import ",
            "class ", "lambda", "return", "=", "[", "{",
        )
    )


def _strip_code_fence(text: str) -> str:
    """Убрать ```python ... ``` обёртку, если есть."""
    t = text.strip()
    if t.startswith("```"):
        # отрезать первую строку после ```
        first_nl = t.find("\n")
        if first_nl > 0:
            t = t[first_nl + 1:]
        if t.endswith("```"):
            t = t[:-3].rstrip()
    return t


@router.message(F.text)
async def handle_solution(msg: Message) -> None:
    if msg.from_user.id != OWNER_ID and OWNER_ID != 0:
        return
    cur = await progress.get_current(msg.from_user.id)
    if not cur:
        await msg.answer(
            "Сначала выбери задачу через /topics или /menu.", reply_markup=main_menu()
        )
        return

    task = get_task(cur)
    if task is None:
        await msg.answer("Текущая задача потерялась, выбери заново.", reply_markup=main_menu())
        return

    code = _strip_code_fence(msg.text)
    if not _looks_like_code(code):
        await msg.answer(
            "Не похоже на код. Напиши решение Python — например `print('Hi')`.",
            parse_mode="Markdown",
        )
        return

    notice = await msg.answer("⏳ Запускаю...")
    try:
        result = await asyncio.to_thread(grade, code, task.check)
    except Exception as e:
        log.exception("grade failed")
        await notice.edit_text(f"💥 Внутренняя ошибка: {e!r}")
        return

    text = result.message
    if result.details:
        # ограничим объём
        details = result.details
        if len(details) > 1500:
            details = details[:1500] + "\n…(обрезано)"
        text += f"\n\n```\n{details}\n```"

    if result.passed:
        await progress.mark_solved(msg.from_user.id, task.id)
        next_index = task.index + 1
        next_id = f"{task.topic_id}-{next_index:02d}"
        nxt = get_task(next_id)
        if nxt:
            await notice.edit_text(text, parse_mode="Markdown")
            await progress.set_current(msg.from_user.id, next_id)
            solved = await progress.is_solved(msg.from_user.id, next_id)
            await msg.answer(
                task_intro(nxt, solved=solved),
                reply_markup=task_menu(nxt, solved=solved, has_next=nxt.index < 10),
                parse_mode="Markdown",
            )
        else:
            await notice.edit_text(text + "\n\n🏁 Это была последняя задача темы!", parse_mode="Markdown")
            await msg.answer("Возвращайся в меню за следующей темой.", reply_markup=main_menu())
            await progress.set_current(msg.from_user.id, None)
    else:
        try:
            await notice.edit_text(text, parse_mode="Markdown")
        except Exception:
            await notice.edit_text(text)
