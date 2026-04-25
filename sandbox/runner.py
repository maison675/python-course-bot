"""Безопасный запуск пользовательского кода в подпроцессе с лимитами.

Защита:
- лимит CPU времени (signal SIGXCPU при превышении);
- лимит памяти (RLIMIT_AS);
- общий timeout (subprocess wait);
- запрет fork/exec на уровне rlimit (RLIMIT_NPROC);
- запуск без сети — на хосте полагаемся на firewall / контейнер.
- отдельная рабочая директория, удаляется по завершении.
"""
from __future__ import annotations

import os
import resource
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def _set_limits(cpu_seconds: int, memory_mb: int) -> None:
    """Применяется в child-процессе перед exec."""
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    bytes_limit = memory_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))
    # Ограничим количество дочерних процессов
    resource.setrlimit(resource.RLIMIT_NPROC, (16, 16))
    # Запретим запись больших файлов
    resource.setrlimit(resource.RLIMIT_FSIZE, (5 * 1024 * 1024, 5 * 1024 * 1024))


def run_code(
    code: str,
    *,
    stdin: str = "",
    timeout: float = 5.0,
    cpu_seconds: int = 4,
    memory_mb: int = 128,
    extra_files: dict[str, str] | None = None,
) -> RunResult:
    """Запустить пользовательский код, вернуть stdout/stderr."""
    workdir = Path(tempfile.mkdtemp(prefix="usercode_"))
    try:
        script = workdir / "solution.py"
        script.write_text(code, encoding="utf-8")
        if extra_files:
            for name, content in extra_files.items():
                (workdir / name).write_text(content, encoding="utf-8")

        env = {
            "PATH": "/usr/bin:/bin",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LANG": "C.UTF-8",
            "HOME": str(workdir),
        }

        try:
            proc = subprocess.run(
                [sys.executable, "-I", "solution.py"],
                cwd=workdir,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                preexec_fn=lambda: _set_limits(cpu_seconds, memory_mb),
            )
        except subprocess.TimeoutExpired as e:
            return RunResult(
                stdout=(e.stdout or "")[:8000] if isinstance(e.stdout, str) else "",
                stderr=f"⏱ Превышено время выполнения ({timeout} сек)",
                exit_code=-1,
                timed_out=True,
            )

        return RunResult(
            stdout=proc.stdout[-8000:],
            stderr=proc.stderr[-4000:],
            exit_code=proc.returncode,
            timed_out=False,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def run_with_helper(
    user_code: str,
    helper_code: str,
    *,
    timeout: float = 5.0,
    cpu_seconds: int = 4,
    memory_mb: int = 128,
) -> RunResult:
    """Запустить helper_code, который импортирует user_code как модуль `solution`.

    Используется для function-tests: helper делает `import solution` и
    вызывает `solution.func(...)` с проверкой результата.
    """
    return run_code(
        helper_code,
        timeout=timeout,
        cpu_seconds=cpu_seconds,
        memory_mb=memory_mb,
        extra_files={"solution_user.py": user_code},
    )


if __name__ == "__main__":
    # Самопроверка
    r = run_code('print("hello")')
    print("ok:", r.ok, "stdout:", repr(r.stdout))

    r = run_code("while True: pass", timeout=1.0, cpu_seconds=1)
    print("infinite loop handled:", r.timed_out, r.stderr[:100])

    r = run_code("import sys; sys.stdout.write(input().upper())", stdin="hello")
    print("stdin works:", repr(r.stdout))
