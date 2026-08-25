from __future__ import annotations

import argparse
import json
from .audit import audit
from .repository import Repository


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="repo-guardian", description="Доказательный аудит репозитория")
    p.add_argument("mode", nargs="?", default="full", choices=["doctor", "map", "bugs", "tests", "security", "dependencies", "performance", "architecture", "refactor", "review", "docs", "release", "context", "full", "fix"])
    p.add_argument("--repo", default=".", help="путь к проверяемому репозиторию")
    p.add_argument("--json", action="store_true", help="машиночитаемый отчёт")
    p.add_argument("--all", action="store_true", help="показать все findings, а не только top 5")
    return p


def render(result, show_all: bool = False) -> str:
    lines = ["Repo Guardian", f"Стек: {', '.join(result.stacks) or 'не определён'}", f"Overall: {result.overall}/100", "", "Оценки:"]
    lines += [f"  {s.category:<20} {s.value:>3}/100  ({'; '.join(s.reasons)})" for s in result.scores]
    findings = result.findings if show_all else result.findings[:5]
    lines += ["", f"Top findings ({len(findings)} из {len(result.findings)}):"]
    if not findings: lines.append("  ✓ Подтверждённых проблем не найдено")
    for f in findings:
        evidence = ", ".join(f.evidence[:2])
        lines.append(f"  [{f.severity.value}/{f.confidence.value}] {f.id}: {f.title} — {evidence}")
    lines += ["", "Правило: LOW confidence не повышается автоматически и требует ручной проверки."]
    return "\n".join(lines)


def render_map(repo_root: str) -> str:
    repo = Repository(repo_root)
    files = repo.files()
    entrypoints = [p for p in files if p.name in {"main.py", "app.py", "server.py", "main.go", "index.js", "index.ts", "manage.py"}]
    configs = [p for p in files if p.name in {"pyproject.toml", "package.json", "Dockerfile", "docker-compose.yml", "go.mod", "Cargo.toml"}]
    return "\n".join(["Repo Guardian: карта codebase", f"Файлов: {len(files)}", f"Entry points: {', '.join(str(p.relative_to(repo.root)) for p in entrypoints) or 'не найдены'}", f"Конфигурация: {', '.join(p.name for p in configs) or 'не найдена'}", "", "Critical flows требуют подтверждения по фактическим imports/calls; эта базовая карта не выдумывает связи."])


def render_context(repo_root: str) -> str:
    repo = Repository(repo_root)
    state = repo.git_state()
    return "\n".join(["# Repo Guardian context", f"Root: {repo.root}", "", "## Стек", ", ".join(audit(repo_root, "docs").stacks) or "не определён", "", "## Git", f"Branch: {state['branch']}", "", "## Правило агента", "Сначала читай evidence и существующие инструкции; risky changes только после подтверждения."])


def render_fix(result) -> str:
    safe = [f for f in result.findings if f.category in {"Documentation", "Testing"}]
    risky = [f for f in result.findings if f not in safe]
    lines = ["Repo Guardian: план fix", "", "SAFE FIXES (можно подготовить после обычного подтверждения):"]
    lines += [f"  - {f.id}: {f.suggested_fix or f.recommendation}" for f in safe] or ["  - нет"]
    lines += ["", "REQUIRES CONFIRMATION:"]
    lines += [f"  - {f.id}: {f.suggested_fix or f.recommendation}" for f in risky] or ["  - нет"]
    lines += ["", "Ни один файл не изменён."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.mode == "map":
        print(render_map(args.repo)); return 0
    if args.mode == "context":
        print(render_context(args.repo)); return 0
    result = audit(args.repo, args.mode)
    if args.mode == "fix":
        print(render_fix(result)); return 0
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) if args.json else render(result, args.all))
    return 1 if any(f.severity.value in {"CRITICAL", "HIGH"} and f.confidence.value == "HIGH" for f in result.findings) else 0
