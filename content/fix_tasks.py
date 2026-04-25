"""Точечные правки YAML после автогенерации:
- 10_sets: сделать вывод детерминированным через sorted();
- 13_files: задачам 02-09 нужны исходные файлы (notes.txt, user.json) в sandbox.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

CONTENT = Path(__file__).parent
TASKS = CONTENT / "tasks"


def _run(code: str, *, cwd: Path | None = None) -> str:
    if cwd is None:
        import tempfile
        cwd = Path(tempfile.mkdtemp(prefix="ref_"))
        (cwd / "solution.py").write_text(code, encoding="utf-8")
    res = subprocess.run(
        [sys.executable, "solution.py"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if res.returncode != 0:
        raise RuntimeError(res.stderr)
    return res.stdout


# Контент файлов, которые нужны для задач темы 13
NOTES_TXT = "Первая строка\nВторая строка\nТретья строка\n"
USER_JSON = (
    '{"name": "Алиса", "age": 25, "hobbies": ["читать", "бегать"], "active": true}\n'
)


def fix_sets() -> None:
    path = TASKS / "10_sets.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    # Задача 01: print(fruits) → print(sorted(fruits)); добавим в задание уточнение
    t1 = data["tasks"][0]
    t1["reference"] = (
        '"""Задача 1. Создать множество и добавить/удалить элементы."""\n'
        'fruits = {"яблоко", "банан"}\n'
        'fruits.add("вишня")\n'
        'fruits.add("яблоко")     # дубликат — игнорируется\n'
        'fruits.discard("банан")  # удалить\n'
        "print(sorted(fruits))\n"
        "print(len(fruits))\n"
    )
    t1["statement"] = (
        "### Задача 1. Множество фруктов\n\n"
        "Создай множество с двумя фруктами: `яблоко` и `банан`. Добавь в него `вишня`,\n"
        "попробуй добавить `яблоко` повторно (что произойдёт?), удали `банан`.\n\n"
        "Выведи отсортированный список оставшихся фруктов и их количество.\n\n"
        "Подсказка: используй `print(sorted(s))`, чтобы вывод был детерминированным."
    )
    t1["check"]["expected_stdout"] = _run(t1["reference"])

    # Задача 03: print двух множеств → sorted
    t3 = data["tasks"][2]
    if "{3, 4, 5}" in t3["check"]["expected_stdout"]:
        t3["reference"] = (
            '"""Задача 3. Пересечение множеств."""\n'
            "a = {1, 2, 3, 4, 5}\n"
            "b = {3, 4, 5, 6, 7}\n"
            "print(sorted(a & b))\n"
            "print(sorted(a.intersection(b)))\n"
        )
        t3["statement"] = (
            "### Задача 3. Пересечение множеств\n\n"
            "Найди пересечение двух множеств `{1, 2, 3, 4, 5}` и `{3, 4, 5, 6, 7}`\n"
            "двумя способами: оператором `&` и методом `.intersection()`.\n\n"
            "Выведи оба результата в виде отсортированного списка."
        )
        t3["check"]["expected_stdout"] = _run(t3["reference"])

    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=10000),
        encoding="utf-8",
    )
    print("  10_sets fixed")


def fix_files() -> None:
    path = TASKS / "13_files.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    # Задачи 2..9 могут читать notes.txt; задача 8 — user.json (создаёт сама в задаче 7).
    needs_notes = [2, 3, 4, 5, 6, 9, 10]
    needs_user_json = [8]

    for t in data["tasks"]:
        idx = t["index"]
        extras: dict[str, str] = {}
        if idx in needs_notes:
            extras["notes.txt"] = NOTES_TXT
        if idx in needs_user_json:
            extras["user.json"] = USER_JSON
        if extras:
            t["check"]["extra_files"] = extras

    # Перегенерим expected_stdout для задач, где он зависит от файлов
    import tempfile
    for t in data["tasks"]:
        extras = t["check"].get("extra_files", {})
        if not extras:
            continue
        cwd = Path(tempfile.mkdtemp(prefix="reffix_"))
        for name, content in extras.items():
            (cwd / name).write_text(content, encoding="utf-8")
        (cwd / "solution.py").write_text(t["reference"], encoding="utf-8")
        try:
            t["check"]["expected_stdout"] = _run(t["reference"], cwd=cwd)
        except Exception as e:
            print(f"  WARN {t['id']}: {e}")

    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=10000),
        encoding="utf-8",
    )
    print("  13_files fixed")


if __name__ == "__main__":
    fix_sets()
    fix_files()
