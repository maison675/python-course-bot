"""Конвертирует задачи и решения из python_course/ в YAML с автотестами.

Запуск:
    python content/build_tasks.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
SOURCE = Path("/home/ubuntu/python_course")
PRACTICE = SOURCE / "practice"
CODE = SOURCE / "solutions_code"
OUT = ROOT / "tasks"
OUT.mkdir(exist_ok=True)


# Темы → метаданные. stdin_per_task: для тех задач, где нужно подать ввод.
# function_per_task: где нужно проверять функцию вместо stdout.
TOPIC_OVERRIDES: dict[str, dict] = {
    "05_io": {
        "stdin": {
            1: "Алиса\n",
            2: "7\n13\n",
            3: "9\n",
            4: "5\n10\n15\n",
            5: "4\n7\n10\n",
            6: "5\n",
            7: "7 13\n",
            8: "5\n",
            9: "Иван\nПетров\n",
            10: "12\n*\n4\n",
        },
    },
}


def parse_tasks_md(path: Path) -> dict[int, str]:
    """Разбить *_tasks.md на отдельные задачи по заголовкам '## Задача N. ...'."""
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^##\s+Задача\s+(\d+)\.?\s*", text, flags=re.MULTILINE)
    # parts[0] — заголовок файла, дальше пары (номер, тело)
    out: dict[int, str] = {}
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1].strip()
        # Убрать разделители --- и хвост
        body = re.split(r"^---\s*$", body, flags=re.MULTILINE)[0].strip()
        # Восстановим заголовок задачи
        title_line, _, rest = body.partition("\n")
        out[num] = f"### Задача {num}. {title_line.strip()}\n\n{rest.strip()}"
    return out


def run_reference(py_file: Path, stdin: str = "") -> str:
    """Выполнить эталонный .py и вернуть stdout."""
    res = subprocess.run(
        [sys.executable, py_file.name],
        cwd=py_file.parent,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if res.returncode != 0:
        raise RuntimeError(f"{py_file}: {res.stderr}")
    return res.stdout


def build_topic_yaml(topic_id: str) -> Path:
    tasks_md = PRACTICE / f"{topic_id}_tasks.md"
    code_dir = CODE / topic_id
    overrides = TOPIC_OVERRIDES.get(topic_id, {})
    stdin_map = overrides.get("stdin", {})

    statements = parse_tasks_md(tasks_md)
    out_tasks: list[dict] = []

    for n in range(1, 11):
        py = code_dir / f"task_{n:02d}.py"
        ref_code = py.read_text(encoding="utf-8")
        stdin = stdin_map.get(n, "")
        expected = run_reference(py, stdin=stdin)

        statement = statements.get(n, f"### Задача {n}\n\n(не найдено)")
        # Краткий заголовок задачи — первая строка statement без префикса
        m = re.match(r"###\s+Задача\s+\d+\.?\s*(.+)", statement)
        title = m.group(1).strip() if m else f"Задача {n}"

        task = {
            "id": f"{topic_id}-{n:02d}",
            "topic_id": topic_id,
            "index": n,
            "title": title,
            "statement": statement,
            "reference": ref_code,
            "check": {
                "kind": "stdout",
                "expected_stdout": expected,
            },
        }
        if stdin:
            task["check"]["stdin"] = stdin
            task["needs_stdin"] = True

        out_tasks.append(task)

    out_path = OUT / f"{topic_id}.yaml"
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            {"topic_id": topic_id, "tasks": out_tasks},
            f,
            allow_unicode=True,
            sort_keys=False,
            width=10000,
        )
    return out_path


def main() -> int:
    topics_yaml = yaml.safe_load((ROOT / "topics.yaml").read_text(encoding="utf-8"))
    for topic in topics_yaml["topics"]:
        topic_id = topic["id"]
        out = build_topic_yaml(topic_id)
        print(f"  {topic_id}: {out.name}")
    print("Готово.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
