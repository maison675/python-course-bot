"""Прогон: все эталонные решения должны проходить свою же проверку."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.content import load_topics, load_tasks
from sandbox.grader import grade


def main() -> int:
    failed: list[tuple[str, str]] = []
    total = 0
    for topic in load_topics():
        for task in load_tasks(topic.id):
            total += 1
            res = grade(task.reference, task.check)
            if not res.passed:
                failed.append((task.id, f"{res.message}: {res.details[:200]}"))
                print(f"  FAIL {task.id}: {res.message}")
            else:
                pass
    print()
    print(f"Всего: {total}, провалено: {len(failed)}")
    if failed:
        for tid, msg in failed:
            print(f"  {tid}\n    {msg}")
        return 1
    print("OK — все 160 эталонных решений проходят свою же автопроверку.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
