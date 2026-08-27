from __future__ import annotations

import argparse
import json
from pathlib import Path
from .audit import audit
from .repository import Repository
from .tui import run_ui
from .installer import InstallError, install_skill


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="repo-guardian", description="Доказательный аудит репозитория")
    p.add_argument("mode", nargs="?", default="full", choices=["doctor", "map", "bugs", "tests", "security", "dependencies", "performance", "architecture", "refactor", "review", "docs", "release", "context", "full", "fix", "ui", "init"])
    p.add_argument("--repo", default=".", help="путь к проверяемому репозиторию")
    p.add_argument("--json", action="store_true", help="машиночитаемый отчёт")
    p.add_argument("--all", action="store_true", help="показать все findings, а не только top 5")
    p.add_argument("--fail-on", choices=["critical", "high", "medium", "low", "never"], default="high", help="код выхода для CI при findings этой серьёзности")
    p.add_argument("--symptom", help="симптом для bug investigation; агент использует его как контекст")
    p.add_argument("--scope", choices=["project", "user"], default="project", help="куда установить Skill в режиме init")
    p.add_argument("--update", action="store_true", help="разрешить замену существующего Skill в режиме init")
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
    entrypoints = [p for p in files if p.name in {"main.py", "app.py", "server.py", "main.go", "index.js", "index.ts", "manage.py"} and not any(part in {"tests", "fixtures"} for part in p.relative_to(repo.root).parts)]
    configs = [p for p in files if p.name in {"pyproject.toml", "package.json", "Dockerfile", "docker-compose.yml", "go.mod", "Cargo.toml"}]
    extensions: dict[str, int] = {}
    for path in files: extensions[path.suffix or "[без расширения]"] = extensions.get(path.suffix or "[без расширения]", 0) + 1
    tests = [p for p in files if "test" in p.name.lower() or "spec" in p.name.lower()]
    commands = repo.project_commands()
    return "\n".join(["Repo Guardian: карта codebase", f"Файлов: {len(files)}", f"Entry points: {', '.join(str(p.relative_to(repo.root)) for p in entrypoints) or 'не найдены'}", f"Тесты: {len(tests)} файлов", f"Конфигурация: {', '.join(p.name for p in configs) or 'не найдена'}", f"Команды (не запускались): {', '.join(c['command'] for c in commands) or 'не обнаружены'}", f"Типы файлов: {', '.join(f'{key}={value}' for key, value in sorted(extensions.items(), key=lambda item: -item[1])[:8])}", "", "Critical flows требуют подтверждения по фактическим imports/calls; эта базовая карта не выдумывает связи."])


def render_context(repo_root: str) -> str:
    repo = Repository(repo_root)
    state = repo.git_state()
    result = audit(repo_root, "docs")
    commands = repo.project_commands()
    return "\n".join(["# Repo Guardian context", f"Root: {repo.root}", "", "## Стек", ", ".join(result.stacks) or "не определён", "", "## Key files", *(f"- {path}" for path in repo.key_files()), "", "## Commands (not run)", *(f"- `{item['command']}` from {item['source']}" for item in commands), "", "## Git", f"Branch: {state['branch']}", f"Last commit: {state['last_commit']}", "", "## Правило агента", "Сначала читай evidence и существующие инструкции; risky changes только после подтверждения."])


def render_fix(result) -> str:
    safe = [f for f in result.findings if f.category in {"Documentation", "Testing"}]
    risky = [f for f in result.findings if f not in safe]
    lines = ["Repo Guardian: план fix", "", "SAFE FIXES (можно подготовить после обычного подтверждения):"]
    lines += [f"  - {f.id}: {f.suggested_fix or f.recommendation}" for f in safe] or ["  - нет"]
    lines += ["", "REQUIRES CONFIRMATION:"]
    lines += [f"  - {f.id}: {f.suggested_fix or f.recommendation}" for f in risky] or ["  - нет"]
    lines += ["", "Ни один файл не изменён."]
    return "\n".join(lines)


def render_refactor() -> str:
    return "\n".join(["Repo Guardian: безопасный refactor workflow", "", "1. UNDERSTAND  собрать map, imports, tests и Git scope", "2. PLAN        описать маленькие обратимые шаги", "3. CONFIRM     получить подтверждение на risky изменения", "4. IMPLEMENT   менять только согласованный scope", "5. TEST        запустить релевантные проверки", "6. REVIEW      повторить diff и health-check", "", "Ни один файл не изменён."])


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.mode == "map":
        print(render_map(args.repo)); return 0
    if args.mode == "ui":
        target = Path(args.repo).expanduser().resolve()
        if not target.is_dir():
            print(f"Ошибка: репозиторий не найден: {target}")
            return 2
        return run_ui(str(target))
    if args.mode == "init":
        try:
            destination = install_skill(args.repo, args.scope, args.update)
        except InstallError as error:
            print(f"Ошибка установки: {error}")
            return 2
        print(f"Skill установлен: {destination}")
        print("В Claude Code используй /repo-guardian для запуска.")
        return 0
    if args.mode == "context":
        print(render_context(args.repo)); return 0
    if args.mode == "refactor":
        print(render_refactor()); return 0
    target = Path(args.repo).expanduser().resolve()
    if not target.is_dir():
        print(f"Ошибка: репозиторий не найден: {target}\nУкажите существующую папку, например: repo-guardian full --repo /path/to/project")
        return 2
    result = audit(args.repo, args.mode)
    if args.symptom:
        result.commands.append({"command": "bug symptom", "result": args.symptom})
    if args.mode == "fix":
        print(render_fix(result)); return 0
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) if args.json else render(result, args.all))
    if args.fail_on == "never": return 0
    threshold = {"critical": 0, "high": 1, "medium": 2, "low": 3}[args.fail_on]
    rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    return 1 if any(rank[f.severity.value] <= threshold and f.confidence.value != "LOW" for f in result.findings) else 0
