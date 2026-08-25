from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


IGNORED = {".git", ".venv", "venv", "node_modules", "target", "dist", "build", "__pycache__"}


@dataclass
class CommandResult:
    command: str
    returncode: int
    stdout: str = ""
    stderr: str = ""
    skipped: bool = False


class Repository:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def files(self) -> list[Path]:
        return [p for p in self.root.rglob("*") if p.is_file() and not any(part in IGNORED for part in p.parts)]

    def exists(self, name: str) -> bool:
        return (self.root / name).exists()

    def read(self, path: Path, limit: int = 200_000) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace")[:limit]
        except OSError:
            return ""

    def line(self, path: Path, number: int) -> str:
        lines = self.read(path).splitlines()
        return lines[number - 1].strip() if 0 < number <= len(lines) else ""

    def git(self, *args: str) -> CommandResult:
        proc = subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, timeout=15)
        return CommandResult("git " + " ".join(args), proc.returncode, proc.stdout.strip(), proc.stderr.strip())

    def safe_command(self, command: list[str], timeout: int = 30) -> CommandResult:
        """Run only an explicitly supplied, non-shell command; never mutates by itself."""
        if not command or any(token in {"rm", "reset", "clean", "push", "--force"} for token in command):
            return CommandResult(" ".join(command), 2, skipped=True, stderr="command blocked by safety policy")
        try:
            proc = subprocess.run(command, cwd=self.root, text=True, capture_output=True, timeout=timeout)
            return CommandResult(" ".join(command), proc.returncode, proc.stdout[-4000:], proc.stderr[-4000:])
        except (OSError, subprocess.TimeoutExpired) as exc:
            return CommandResult(" ".join(command), 124, skipped=True, stderr=str(exc))

    def git_state(self) -> dict[str, str]:
        branch = self.git("branch", "--show-current")
        status = self.git("status", "--short")
        return {"branch": branch.stdout or "(detached/unknown)", "status": status.stdout}


def json_dump(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)

