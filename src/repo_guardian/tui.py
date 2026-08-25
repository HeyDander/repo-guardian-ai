from __future__ import annotations

import curses
import textwrap

from .audit import audit
from .repository import Repository


UI_TEXT = {
    "ru": {"overview": "ОБЗОР", "findings": "ПРОБЛЕМЫ", "map": "КАРТА CODEBASE", "stack": "Стек", "health": "ЗДОРОВЬЕ РЕПОЗИТОРИЯ", "overall": "Итог", "top": "ГЛАВНЫЕ FINDINGS", "ok": "Подтверждённых проблем нет", "evidence": "Evidence", "impact": "Влияние", "next": "Рекомендация", "files": "Файлов", "tests": "Тестов/spec", "entry": "Entry points", "commands": "Команды (не запускались)", "not_found": "не найдены", "flows": "Критические flows не выдумываются картой.", "ask_agent": "Для flow попросите агента проследить именованный путь.", "footer": "[r] обновить  [f] findings  [m] карта  [l] язык  [q] выйти", "back": "[b] назад  [r] обновить  [l] язык  [q] выйти"},
    "en": {"overview": "OVERVIEW", "findings": "FINDINGS", "map": "CODEBASE MAP", "stack": "Stack", "health": "REPOSITORY HEALTH", "overall": "Overall", "top": "TOP FINDINGS", "ok": "No confirmed findings", "evidence": "Evidence", "impact": "Impact", "next": "Next", "files": "Files", "tests": "Tests/specs", "entry": "Entry points", "commands": "Commands (not run)", "not_found": "not found", "flows": "Critical flows are not invented by the map.", "ask_agent": "Ask the agent to trace a named flow.", "footer": "[r] refresh  [f] findings  [m] map  [l] language  [q] quit", "back": "[b] back  [r] refresh  [l] language  [q] quit"},
}

FINDING_EN = {
    "RG-SEC-001": ("Possible secret in source", "A secret may enter Git history or logs.", "Move it to a secret store or environment variable."),
    "RG-SEC-002": ("Dynamic code or command execution", "Unchecked input may execute code or commands.", "Trace the input and use a validated allow-list API."),
    "RG-TST-001": ("No test files found", "Critical code has no automatic regression barrier.", "Add a smoke or integration test for the main entry point."),
    "RG-DEP-001": ("Manifest has no lockfile", "Different environments may install different versions.", "Add and verify a lockfile for the ecosystem."),
    "RG-DEP-002": ("Dependency version range is too broad", "An update may unexpectedly change behavior.", "Pin a compatible range after checking tests."),
    "RG-PERF-001": ("Potentially expensive operation inside a loop", "Cost may grow with input size.", "Confirm with profiling and consider batching or caching."),
    "RG-ARC-001": ("Large module needs boundary review", "Changes may have a larger blast radius.", "Check imports and public API before refactoring."),
    "RG-QUA-001": ("Oversized module needs responsibility review", "Large modules increase change and regression cost.", "Add characterization tests before extracting one responsibility."),
    "RG-REL-001": ("Uncommitted changes are present", "The release may not match the reviewed commit.", "Commit or explicitly exclude changes before release."),
    "RG-REL-002": ("CHANGELOG is missing", "Users cannot easily understand release changes.", "Add release notes or a changelog."),
    "RG-REL-003": ("CI workflow is missing", "Checks may not run on pull requests.", "Add a minimal test and build workflow."),
    "RG-REV-003": ("Changes need manual diff review", "Static analysis cannot replace business correctness review.", "Check correctness, security, compatibility and tests."),
}


def _t(lang: str, key: str) -> str:
    return UI_TEXT[lang][key]


def _finding_text(finding, lang: str, field: str) -> str:
    if lang == "en" and finding.id in FINDING_EN:
        return FINDING_EN[finding.id][{"title": 0, "impact": 1, "recommendation": 2}[field]]
    return getattr(finding, field)


def _bar(value: int, width: int = 20) -> str:
    filled = round(value / 100 * width)
    return "#" * filled + "." * (width - filled)


def _safe_add(window, y: int, x: int, value: str, attr: int = 0) -> None:
    height, width = window.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    try:
        window.addnstr(y, max(0, x), value, max(0, width - max(0, x) - 1), attr)
    except curses.error:
        pass


def _short(value: str, width: int) -> str:
    if width <= 3:
        return value[:width]
    return value if len(value) <= width else value[: width - 3] + "..."


def _color(score: int) -> int:
    if score >= 80:
        return curses.color_pair(2)
    if score >= 60:
        return curses.color_pair(3)
    return curses.color_pair(4)


def _header(window, title: str, repo: Repository, result, lang: str) -> None:
    height, width = window.getmaxyx()
    _safe_add(window, 0, 0, f" REPO GUARDIAN  /  {title} ", curses.color_pair(1) | curses.A_BOLD)
    _safe_add(window, 1, 2, _short(f"{repo.root}  |  {_t(lang, 'stack')}: {', '.join(result.stacks) or 'unknown'}", max(10, width - 4)), curses.A_DIM)
    _safe_add(window, 2, 0, "=" * max(1, width - 1), curses.color_pair(1))


def _dashboard(window, repo: Repository, result, lang: str) -> None:
    window.erase()
    _header(window, _t(lang, "overview"), repo, result, lang)
    height, width = window.getmaxyx()
    _safe_add(window, 4, 2, _t(lang, "health"), curses.A_BOLD)
    health_width = min(48, max(36, width - 4))
    overall_bar = min(24, max(10, health_width - 22))
    _safe_add(window, 5, 3, f"{_t(lang, 'overall'):<12} {result.overall:>3}/100  [{_bar(result.overall, overall_bar)}]", _color(result.overall) | curses.A_BOLD)
    row = 7
    score_end = row
    for score in result.scores:
        if row >= height - 4:
            break
        _safe_add(window, row, 3, f"{score.category:<21} {score.value:>3}/100", _color(score.value))
        _safe_add(window, row, 35, _bar(score.value, min(20, max(6, health_width - 35))), _color(score.value))
        row += 1
        score_end = row
    wide = width >= 105
    panel_x = max(55, width // 2) if wide else 2
    findings_row = 4 if wide else score_end + 1
    _safe_add(window, findings_row, panel_x, f"{_t(lang, 'top')} ({min(5, len(result.findings))})", curses.A_BOLD)
    findings = result.findings[:5]
    if not findings:
        _safe_add(window, findings_row + 2, panel_x, f"[OK] {_t(lang, 'ok')}", curses.color_pair(2))
    for index, finding in enumerate(findings):
        item_row = findings_row + 2 + index * 2
        if item_row >= height - 3:
            break
        label = f"{finding.severity.value}/{finding.confidence.value}  {finding.id}"
        attr = curses.color_pair(4 if finding.severity.value in {"HIGH", "CRITICAL"} else 3)
        _safe_add(window, item_row, panel_x, _short(label, max(10, width - panel_x - 2)), attr | curses.A_BOLD)
        _safe_add(window, item_row + 1, panel_x + 2, _short(_finding_text(finding, lang, "title"), max(10, width - panel_x - 4)))
    _safe_add(window, height - 2, 2, _t(lang, "footer"), curses.color_pair(1) | curses.A_BOLD)
    window.refresh()


def _findings(window, repo: Repository, result, lang: str) -> None:
    window.erase()
    _header(window, _t(lang, "findings"), repo, result, lang)
    height, width = window.getmaxyx()
    row = 4
    if not result.findings:
        _safe_add(window, row, 2, _t(lang, "ok"), curses.color_pair(2) | curses.A_BOLD)
    for finding in result.findings:
        if row >= height - 3:
            _safe_add(window, row, 2, "More findings are available in --json or --all output.", curses.A_DIM)
            break
        attr = curses.color_pair(4) if finding.severity.value in {"HIGH", "CRITICAL"} else curses.color_pair(3)
        _safe_add(window, row, 2, _short(f"{finding.id}  [{finding.severity.value}/{finding.confidence.value}] {_finding_text(finding, lang, 'title')}", max(10, width - 4)), attr | curses.A_BOLD)
        row += 1
        for line in [f"{_t(lang, 'evidence')}: {', '.join(finding.evidence)}", f"{_t(lang, 'impact')}: {_finding_text(finding, lang, 'impact')}", f"{_t(lang, 'next')}: {_finding_text(finding, lang, 'recommendation')}"]:
            for wrapped in textwrap.wrap(line, max(20, width - 6)):
                if row >= height - 3:
                    break
                _safe_add(window, row, 4, wrapped)
                row += 1
        row += 1
    _safe_add(window, height - 2, 2, _t(lang, "back"), curses.color_pair(1) | curses.A_BOLD)
    window.refresh()


def _map(window, repo: Repository, result, lang: str) -> None:
    window.erase()
    _header(window, _t(lang, "map"), repo, result, lang)
    files = repo.files()
    commands = repo.project_commands()
    entrypoint_names = {"main.py", "app.py", "server.py", "main.go", "index.js", "index.ts", "manage.py"}
    entrypoints = [str(path.relative_to(repo.root)) for path in files if path.name in entrypoint_names]
    rows = [
        f"{_t(lang, 'files')}: {len(files)}",
        f"{_t(lang, 'tests')}: {sum(1 for path in files if 'test' in path.name.lower() or 'spec' in path.name.lower())}",
        f"{_t(lang, 'entry')}: {', '.join(entrypoints) or _t(lang, 'not_found')}",
        f"{_t(lang, 'commands')}: {', '.join(item['command'] for item in commands) or _t(lang, 'not_found')}",
        "",
        _t(lang, "flows"),
        _t(lang, "ask_agent"),
    ]
    for row, line in enumerate(rows, 4):
        _safe_add(window, row, 3, line)
    _safe_add(window, window.getmaxyx()[0] - 2, 2, _t(lang, "back"), curses.color_pair(1) | curses.A_BOLD)
    window.refresh()


def run_ui(root: str) -> int:
    repo = Repository(root)

    def app(window) -> None:
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        result = audit(root, "full")
        screen = "overview"
        lang = "ru"
        while True:
            if screen == "overview":
                _dashboard(window, repo, result, lang)
            elif screen == "findings":
                _findings(window, repo, result, lang)
            else:
                _map(window, repo, result, lang)
            key = window.getch()
            if key in (ord("q"), ord("Q"), 27):
                return
            if key in (ord("r"), ord("R")):
                result = audit(root, "full")
            elif key in (ord("l"), ord("L")):
                lang = "en" if lang == "ru" else "ru"
            elif key in (ord("f"), ord("F")):
                screen = "findings"
            elif key in (ord("m"), ord("M")):
                screen = "map"
            elif key in (ord("b"), ord("B")):
                screen = "overview"

    curses.wrapper(app)
    return 0
