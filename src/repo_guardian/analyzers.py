from __future__ import annotations

import re
import json
import tomllib
from collections.abc import Callable
from .models import Confidence, Finding, Severity, Score
from .repository import Repository

Analyzer = Callable[[Repository], list[Finding]]


def _finding(code: str, severity: Severity, category: str, title: str, evidence: list[str], impact: str, recommendation: str, fix: str | None = None, confidence: Confidence = Confidence.HIGH) -> Finding:
    return Finding(code, severity, category, title, evidence, impact, confidence, recommendation, fix, verified=confidence == Confidence.HIGH)


def security(repo: Repository) -> list[Finding]:
    findings = []
    secret = re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]")
    dangerous = re.compile(r"(?i)(eval\s*\(|exec\s*\(|child_process\.exec\s*\(|os\.system\s*\()")
    for path in repo.files():
        if any(part in {"tests", "fixtures"} for part in path.relative_to(repo.root).parts): continue
        if path.name in {".env.example", "README.md"}: continue
        for number, line in enumerate(repo.read(path).splitlines(), 1):
            if secret.search(line) and not re.search(r"(?i)(example|dummy|changeme|test|your[_-]?|placeholder|replace[_-]?me)", line):
                findings.append(_finding("RG-SEC-001", Severity.HIGH, "Security", "Возможный секрет в исходниках", [f"{path.relative_to(repo.root)}:{number}", "[redacted: matching assignment]"], "Секрет может попасть в историю Git или логи.", "Проверьте значение и вынесите его в secret store/переменную окружения; не показывайте значение в отчёте.", "Удалить секрет из истории только отдельным подтверждённым процессом.", Confidence.MEDIUM))
            if dangerous.search(line):
                findings.append(_finding("RG-SEC-002", Severity.MEDIUM, "Security", "Динамическое выполнение команды/кода", [f"{path.relative_to(repo.root)}:{number}", "[redacted: command expression]"], "Непроверенный ввод может привести к выполнению кода или команд.", "Проследить источник аргумента и заменить на безопасный API с allow-list.", "Добавить валидацию и тест на вредоносный ввод.", Confidence.MEDIUM))
    return findings


def testing(repo: Repository) -> list[Finding]:
    files = repo.files(); tests = [p for p in files if "test" in p.name.lower() or "spec" in p.name.lower()]
    if files and not tests:
        return [_finding("RG-TST-001", Severity.HIGH, "Testing", "Тестовые файлы не обнаружены", ["repository root"], "Регрессии в критическом коде не имеют автоматического барьера.", "Добавить тестовый runner и минимальные тесты для критических путей.", "Начать с smoke/integration теста главного entry point.", Confidence.HIGH)]
    return []


def quality(repo: Repository) -> list[Finding]:
    findings = []
    for path in repo.files():
        if path.suffix not in {".py", ".js", ".ts", ".go", ".rs", ".java"}: continue
        lines = repo.read(path).splitlines()
        if len(lines) > 500:
            findings.append(_finding("RG-QUA-001", Severity.MEDIUM, "Code Quality", "Крупный модуль требует проверки границ ответственности", [f"{path.relative_to(repo.root)}:1", f"{len(lines)} lines"], "Большие модули повышают стоимость изменений и риск побочных эффектов.", "Разделять только после понимания public API и зависимостей.", "Сначала добавить characterization tests; затем выделить одну ответственность.", Confidence.MEDIUM))
    return findings


def docs(repo: Repository) -> list[Finding]:
    if not repo.exists("README.md"):
        return [_finding("RG-DOC-001", Severity.MEDIUM, "Documentation", "README отсутствует", ["README.md (missing)"], "Новому разработчику трудно запустить проект и понять его границы.", "Добавить краткий setup, команды проверки и описание архитектуры.", "Создать README без раскрытия секретов.", Confidence.HIGH)]
    return []


def dependencies(repo: Repository) -> list[Finding]:
    findings = []
    manifests = [p for p in repo.files() if p.name in {"package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml", "composer.json", "Gemfile"}]
    lock_names = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock", "go.sum", "Cargo.lock", "composer.lock", "Gemfile.lock"}
    locks = [p for p in repo.files() if p.name in lock_names]
    for manifest in manifests:
        if manifest.parent != repo.root: continue
        if manifest.name == "pyproject.toml":
            try:
                project = tomllib.loads(repo.read(manifest)).get("project", {})
                if not project.get("dependencies") and not project.get("optional-dependencies"): continue
            except tomllib.TOMLDecodeError: pass
        if manifest.parent == repo.root and not any(lock.parent == manifest.parent for lock in locks):
            findings.append(_finding("RG-DEP-001", Severity.MEDIUM, "Dependencies", "Manifest не сопровождается lockfile", [f"{manifest.relative_to(repo.root)}:1", "lockfile (missing)"], "Разные окружения могут установить разные версии зависимостей.", "Добавить и проверять lockfile, если его поддерживает выбранная экосистема.", "Сгенерировать lockfile штатным менеджером после подтверждения.", Confidence.HIGH))
    package = repo.root / "package.json"
    if package.exists():
        try:
            data = json.loads(repo.read(package))
            for section in ("dependencies", "devDependencies"):
                for name, version in data.get(section, {}).items():
                    if str(version).startswith(("*", "latest", ">", "^0", "~0")):
                        findings.append(_finding("RG-DEP-002", Severity.LOW, "Dependencies", "Слишком широкий диапазон версии", [f"package.json:{section}.{name}", str(version)], "Обновление может неожиданно изменить поведение сборки.", "Зафиксировать совместимый диапазон после проверки lockfile и тестов.", "Не обновлять автоматически.", Confidence.MEDIUM))
        except json.JSONDecodeError:
            findings.append(_finding("RG-DEP-003", Severity.HIGH, "Dependencies", "package.json не является валидным JSON", ["package.json:1"], "Package manager и CI могут не установить проект.", "Исправить синтаксис и повторить install в изолированном окружении.", "Требует подтверждённого исправления файла.", Confidence.HIGH))
    return findings


def performance(repo: Repository) -> list[Finding]:
    findings = []
    loop = re.compile(r"(?i)\b(for|while)\b|\.forEach\s*\(")
    expensive = re.compile(r"(?i)(SELECT\s+|requests?\.(get|post)|fetch\s*\(|axios\.|httpx\.|urllib\.)")
    for path in repo.files():
        if any(part in {"tests", "fixtures"} for part in path.relative_to(repo.root).parts): continue
        if path.suffix not in {".py", ".js", ".ts", ".go", ".java", ".rs"}: continue
        lines = repo.read(path).splitlines()
        for number, line in enumerate(lines, 1):
            if loop.search(line) and any(expensive.search(candidate) for candidate in lines[number:min(len(lines), number + 8)]):
                findings.append(_finding("RG-PERF-001", Severity.MEDIUM, "Performance", "Потенциально дорогая операция внутри цикла", [f"{path.relative_to(repo.root)}:{number}", "loop + network/query call within next 8 lines"], "При росте входных данных время и нагрузка могут расти линейно или хуже.", "Проверить профилем/метрикой; рассмотреть batching, caching или prefetch только после измерения.", "Добавить benchmark или regression test до оптимизации.", Confidence.MEDIUM))
    return findings


def architecture(repo: Repository) -> list[Finding]:
    findings = []
    for path in repo.files():
        if any(part in {"tests", "fixtures"} for part in path.relative_to(repo.root).parts): continue
        if path.suffix not in {".py", ".js", ".ts", ".go", ".rs", ".java", ".cs"}: continue
        lines = repo.read(path).splitlines()
        if len(lines) > 300:
            findings.append(_finding("RG-ARC-001", Severity.MEDIUM, "Architecture", "Крупный модуль требует проверки границ", [f"{path.relative_to(repo.root)}:1", f"{len(lines)} lines"], "Изменения в oversized module имеют повышенный blast radius.", "Проверить public API, imports и ответственность до рефакторинга.", "Сначала characterization tests, затем выделять одну ответственность.", Confidence.MEDIUM))
    return findings


def release(repo: Repository) -> list[Finding]:
    findings = []
    state = repo.git_state()
    if state["status"]:
        changed = state["status"].splitlines()[:10]
        findings.append(_finding("RG-REL-001", Severity.MEDIUM, "Release Readiness", "В рабочем дереве есть незакоммиченные изменения", changed or ["git status --short"], "Release может не соответствовать проверенному commit.", "Зафиксировать или явно исключить изменения перед release.", "Не выполнять commit автоматически.", Confidence.HIGH))
    if not repo.exists("CHANGELOG.md"):
        findings.append(_finding("RG-REL-002", Severity.LOW, "Release Readiness", "CHANGELOG отсутствует", ["CHANGELOG.md (missing)"], "Пользователям сложнее понять изменения и breaking changes.", "Добавить release notes или changelog.", "Создать документацию без изменения runtime.", Confidence.HIGH))
    if not any(p.as_posix().startswith(str(repo.root / ".github")) and p.name.endswith((".yml", ".yaml")) for p in repo.files()):
        findings.append(_finding("RG-REL-003", Severity.LOW, "Release Readiness", "CI workflow не обнаружен", [".github/workflows (missing)"], "Проверки могут не запускаться на pull request.", "Добавить минимальный CI для тестов и сборки.", "Создать workflow после выбора поддерживаемого runtime.", Confidence.MEDIUM))
    return findings


def review(repo: Repository) -> list[Finding]:
    result = repo.git("diff", "--stat")
    if result.returncode != 0:
        return [_finding("RG-REV-001", Severity.INFO, "Review", "Git diff недоступен", [result.stderr or "not a git repository"], "Невозможно подтвердить scope изменений.", "Запустить review внутри Git repository.", confidence=Confidence.LOW)]
    if not result.stdout:
        return [_finding("RG-REV-002", Severity.INFO, "Review", "Изменений для review не обнаружено", ["git diff --stat (empty)"], "Проверять нечего в текущем рабочем дереве.", "Передать branch diff или staged changes.", confidence=Confidence.HIGH)]
    return [_finding("RG-REV-003", Severity.INFO, "Review", "Изменения требуют ручной проверки diff", [line.strip() for line in result.stdout.splitlines()[:5]], "Статический backend не заменяет анализ бизнес-корректности.", "Проверить correctness, security, compatibility и тесты изменённых файлов.", confidence=Confidence.HIGH)]


ANALYZERS: dict[str, Analyzer] = {"security": security, "tests": testing, "quality": quality, "docs": docs, "dependencies": dependencies, "performance": performance, "architecture": architecture, "release": release, "review": review}
FULL_ANALYZERS = tuple(name for name in ANALYZERS if name != "review")


def run(repo: Repository, mode: str = "full") -> list[Finding]:
    selected = list(FULL_ANALYZERS) if mode in {"full", "doctor", "bugs"} else [mode] if mode in ANALYZERS else list(FULL_ANALYZERS)
    findings: list[Finding] = []
    for name in selected: findings.extend(ANALYZERS[name](repo))
    severity_rank = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4}
    confidence_rank = {Confidence.HIGH: 0, Confidence.MEDIUM: 1, Confidence.LOW: 2}
    unique: dict[tuple[str, tuple[str, ...]], Finding] = {}
    for finding in findings:
        unique[(finding.id, tuple(finding.evidence))] = finding
    return sorted(unique.values(), key=lambda item: (severity_rank[item.severity], confidence_rank[item.confidence], item.id, item.title))


def score(category: str, findings: list[Finding]) -> Score:
    relevant = [f for f in findings if f.category.lower() == category.lower()]
    penalties = sum({Severity.CRITICAL: 30, Severity.HIGH: 20, Severity.MEDIUM: 10, Severity.LOW: 3, Severity.INFO: 0}[f.severity] for f in relevant if f.confidence != Confidence.LOW)
    value = max(0, min(100, 100 - penalties))
    reasons = [f.title for f in relevant[:3]] or ["Подтверждённых проблем этого типа не найдено"]
    return Score(category, value, reasons)
