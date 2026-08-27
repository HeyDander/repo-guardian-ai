from __future__ import annotations

from pathlib import Path


class InstallError(RuntimeError):
    """Raised when installing the Skill would overwrite user work."""


def skill_source() -> Path:
    """Locate the repository Skill in editable installs and source checkouts."""
    candidates = [
        Path(__file__).resolve().parents[2] / "SKILL.md",
        Path.cwd() / "SKILL.md",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    packaged = Path(__file__).resolve().parent / "SKILL.md"
    if packaged.is_file():
        return packaged
    raise InstallError("SKILL.md не найден в установленном пакете или исходном репозитории")


def install_skill(repo: str | Path = ".", scope: str = "project", update: bool = False) -> Path:
    """Install the bundled Skill without silently replacing an existing file."""
    root = Path(repo).expanduser().resolve()
    if scope == "user":
        destination = Path.home() / ".claude" / "skills" / "repo-guardian" / "SKILL.md"
    else:
        destination = root / ".claude" / "skills" / "repo-guardian" / "SKILL.md"

    if scope not in {"project", "user"}:
        raise InstallError("scope должен быть project или user")
    if scope == "project" and not root.is_dir():
        raise InstallError(f"репозиторий не найден: {root}")
    if destination.exists() and not update:
        raise InstallError(
            f"файл уже существует: {destination}. Используйте --update только если хотите его заменить"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(skill_source().read_text(encoding="utf-8"), encoding="utf-8")
    return destination
