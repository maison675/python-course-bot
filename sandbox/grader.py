"""Проверка решений: сравнение со stdout-эталоном или функциональные тесты."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from sandbox.runner import run_code, run_with_helper


@dataclass
class GradeResult:
    passed: bool
    message: str
    details: str = ""


def _normalize(s: str) -> str:
    """Сравнение без хвостовых пробелов и пустых строк в конце."""
    return "\n".join(line.rstrip() for line in s.rstrip().splitlines())


def grade_stdout(
    code: str,
    expected: str,
    *,
    stdin: str = "",
    timeout: float = 5.0,
    extra_files: dict[str, str] | None = None,
) -> GradeResult:
    res = run_code(code, stdin=stdin, timeout=timeout, extra_files=extra_files)
    if res.timed_out:
        return GradeResult(False, "⏱ Слишком долго работает", res.stderr)
    if res.exit_code != 0:
        return GradeResult(False, "❌ Ошибка выполнения", res.stderr or res.stdout)

    actual = _normalize(res.stdout)
    expected_norm = _normalize(expected)
    if actual == expected_norm:
        return GradeResult(True, "✅ Верно!", "")

    # Несовпадение — покажем разницу
    return GradeResult(
        False,
        "❌ Вывод не совпал с ожидаемым",
        f"Ожидалось:\n{expected_norm}\n\nПолучено:\n{actual}",
    )


def grade_function(
    code: str,
    *,
    function_name: str,
    cases: list[dict[str, Any]],
    timeout: float = 5.0,
) -> GradeResult:
    """Прогнать функцию из user_code на наборе тестов.

    cases — список словарей вида:
        {"args": [1, 2], "expected": 3}
        {"args": ["abc"], "kwargs": {}, "expected": "ABC"}
    """
    import json

    helper = f"""
import json
import sys
sys.path.insert(0, ".")
try:
    import solution_user as _sol
except Exception as e:
    print(json.dumps({{"loaderror": repr(e)}}))
    sys.exit(0)

if not hasattr(_sol, {function_name!r}):
    print(json.dumps({{"missing": {function_name!r}}}))
    sys.exit(0)

_func = getattr(_sol, {function_name!r})
_cases = {json.dumps(cases, ensure_ascii=False)}
_results = []
for _c in _cases:
    try:
        _r = _func(*_c.get("args", []), **_c.get("kwargs", {{}}))
        _results.append({{"ok": _r == _c["expected"], "got": repr(_r), "exp": repr(_c["expected"]), "case": _c}})
    except Exception as _e:
        _results.append({{"ok": False, "error": repr(_e), "case": _c}})

print(json.dumps(_results, ensure_ascii=False))
"""
    res = run_with_helper(code, helper, timeout=timeout)
    if res.timed_out:
        return GradeResult(False, "⏱ Слишком долго работает", res.stderr)
    if res.exit_code != 0:
        return GradeResult(False, "❌ Ошибка запуска тестов", res.stderr or res.stdout)

    try:
        data = json.loads(res.stdout.strip().splitlines()[-1])
    except Exception:
        return GradeResult(
            False, "❌ Не удалось разобрать результат", res.stdout[-500:]
        )

    if isinstance(data, dict) and "loaderror" in data:
        return GradeResult(
            False, "❌ Ошибка при загрузке решения", str(data["loaderror"])
        )
    if isinstance(data, dict) and "missing" in data:
        return GradeResult(
            False,
            f"❌ Не найдена функция `{data['missing']}`",
            "Убедись, что определил функцию с таким именем.",
        )

    failed = [r for r in data if not r["ok"]]
    total = len(data)
    if not failed:
        return GradeResult(True, f"✅ Все тесты пройдены ({total}/{total})", "")

    sample = failed[0]
    args = sample["case"].get("args", [])
    if "error" in sample:
        msg = f"При вызове {function_name}({', '.join(map(repr, args))}) — ошибка: {sample['error']}"
    else:
        msg = (
            f"Не сработало для {function_name}({', '.join(map(repr, args))}):\n"
            f"  ожидалось: {sample['exp']}\n"
            f"  получено:  {sample['got']}"
        )
    return GradeResult(
        False,
        f"❌ Провалено {len(failed)} из {total} тестов",
        msg,
    )


# Универсальная функция-диспатчер
GradeKind = Literal["stdout", "function"]


def grade(
    code: str,
    spec: dict,
) -> GradeResult:
    kind = spec.get("kind", "stdout")
    if kind == "stdout":
        return grade_stdout(
            code,
            expected=spec["expected_stdout"],
            stdin=spec.get("stdin", ""),
            timeout=spec.get("timeout", 5.0),
            extra_files=spec.get("extra_files"),
        )
    if kind == "function":
        return grade_function(
            code,
            function_name=spec["function"],
            cases=spec["cases"],
            timeout=spec.get("timeout", 5.0),
        )
    return GradeResult(False, f"Неизвестный тип проверки: {kind}", "")


if __name__ == "__main__":
    # Самопроверка
    r = grade('print("Hello, World!")', {"kind": "stdout", "expected_stdout": "Hello, World!"})
    print("stdout/match:", r)

    r = grade('print("Hi")', {"kind": "stdout", "expected_stdout": "Hello"})
    print("stdout/mismatch:", r)

    r = grade(
        "def add(a, b): return a + b",
        {"kind": "function", "function": "add", "cases": [
            {"args": [2, 3], "expected": 5},
            {"args": [10, -7], "expected": 3},
        ]},
    )
    print("function/pass:", r)

    r = grade(
        "def add(a, b): return a - b",
        {"kind": "function", "function": "add", "cases": [
            {"args": [2, 3], "expected": 5},
        ]},
    )
    print("function/fail:", r)
