from __future__ import annotations

import curses
import textwrap

from .audit import audit
from .repository import Repository


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


def _color(score: int) -> int:
    if score >= 80:
        return curses.color_pair(2)
    if score >= 60:
        return curses.color_pair(3)
    return curses.color_pair(4)


def _header(window, title: str, repo: Repository, result) -> None:
    height, width = window.getmaxyx()
    _safe_add(window, 0, 0, " REPO GUARDIAN ", curses.color_pair(1) | curses.A_BOLD)
    _safe_add(window, 0, 17, f" {title} ", curses.A_BOLD)
    _safe_add(window, 1, 2, f"{repo.root}  |  Stack: {', '.join(result.stacks) or 'unknown'}", curses.A_DIM)
    _safe_add(window, 2, 0, "=" * max(1, width - 1), curses.color_pair(1))


def _dashboard(window, repo: Repository, result) -> None:
    window.erase()
    _header(window, "OVERVIEW", repo, result)
    height, width = window.getmaxyx()
    _safe_add(window, 4, 2, "REPOSITORY HEALTH", curses.A_BOLD)
    _safe_add(window, 5, 3, f"Overall  {result.overall:>3}/100  [{_bar(result.overall, 28)}]", _color(result.overall) | curses.A_BOLD)
    row = 7
    for score in result.scores:
        if row >= height - 5:
            break
        _safe_add(window, row, 3, f"{score.category:<21} {score.value:>3}/100", _color(score.value))
        _safe_add(window, row, 31, _bar(score.value, min(25, max(8, width - 57))), _color(score.value))
        row += 1
    panel_x = max(55, width // 2)
    _safe_add(window, 4, panel_x, "TOP FINDINGS", curses.A_BOLD)
    findings = result.findings[:5]
    if not findings:
        _safe_add(window, 6, panel_x, "[OK] No confirmed findings", curses.color_pair(2))
    for index, finding in enumerate(findings):
        if 6 + index * 2 >= height - 4:
            break
        label = f"{finding.severity.value[:4]}/{finding.confidence.value[:4]} {finding.id}"
        _safe_add(window, 6 + index * 2, panel_x, label, curses.color_pair(4 if finding.severity.value in {"HIGH", "CRITICAL"} else 3))
        _safe_add(window, 7 + index * 2, panel_x + 2, finding.title)
    _safe_add(window, height - 2, 2, "[r] refresh   [f] findings   [m] map   [q] quit", curses.color_pair(1) | curses.A_BOLD)
    window.refresh()


def _findings(window, repo: Repository, result) -> None:
    window.erase()
    _header(window, "FINDINGS", repo, result)
    height, width = window.getmaxyx()
    row = 4
    if not result.findings:
        _safe_add(window, row, 2, "No confirmed findings.", curses.color_pair(2) | curses.A_BOLD)
    for finding in result.findings:
        if row >= height - 3:
            _safe_add(window, row, 2, "More findings are available in --json or --all output.", curses.A_DIM)
            break
        attr = curses.color_pair(4) if finding.severity.value in {"HIGH", "CRITICAL"} else curses.color_pair(3)
        _safe_add(window, row, 2, f"{finding.id}  [{finding.severity.value}/{finding.confidence.value}] {finding.title}", attr | curses.A_BOLD)
        row += 1
        for line in [f"Evidence: {', '.join(finding.evidence)}", f"Impact: {finding.impact}", f"Next: {finding.recommendation}"]:
            for wrapped in textwrap.wrap(line, max(20, width - 6)):
                if row >= height - 3:
                    break
                _safe_add(window, row, 4, wrapped)
                row += 1
        row += 1
    _safe_add(window, height - 2, 2, "[b] back   [r] refresh   [q] quit", curses.color_pair(1) | curses.A_BOLD)
    window.refresh()


def _map(window, repo: Repository, result) -> None:
    window.erase()
    _header(window, "CODEBASE MAP", repo, result)
    files = repo.files()
    commands = repo.project_commands()
    entrypoint_names = {"main.py", "app.py", "server.py", "main.go", "index.js", "index.ts", "manage.py"}
    entrypoints = [str(path.relative_to(repo.root)) for path in files if path.name in entrypoint_names]
    rows = [
        f"Files: {len(files)}",
        f"Tests/specs: {sum(1 for path in files if 'test' in path.name.lower() or 'spec' in path.name.lower())}",
        f"Entry points: {', '.join(entrypoints) or 'not found'}",
        f"Commands (not run): {', '.join(item['command'] for item in commands) or 'not found'}",
        "",
        "Critical flows are not invented by the map.",
        "Use an explicit analyzer or ask the agent to trace a named flow.",
    ]
    for row, line in enumerate(rows, 4):
        _safe_add(window, row, 3, line)
    _safe_add(window, window.getmaxyx()[0] - 2, 2, "[b] back   [r] refresh   [q] quit", curses.color_pair(1) | curses.A_BOLD)
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
        while True:
            if screen == "overview":
                _dashboard(window, repo, result)
            elif screen == "findings":
                _findings(window, repo, result)
            else:
                _map(window, repo, result)
            key = window.getch()
            if key in (ord("q"), ord("Q"), 27):
                return
            if key in (ord("r"), ord("R")):
                result = audit(root, "full")
            elif key in (ord("f"), ord("F")):
                screen = "findings"
            elif key in (ord("m"), ord("M")):
                screen = "map"
            elif key in (ord("b"), ord("B")):
                screen = "overview"

    curses.wrapper(app)
    return 0

