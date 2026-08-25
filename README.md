<div align="center">

# Repo Guardian

### An AI-powered senior engineer for your codebase.

Evidence-first аудит репозитория для Claude Code и совместимых AI coding agents.

[![CI](https://github.com/HeyDander/repo-guardian-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/HeyDander/repo-guardian-ai/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-111827.svg)](LICENSE)

    repo-guardian full --repo .

</div>

---

## Зачем

AI-агент полезен ровно настолько, насколько хорошо он понимает кодовую базу. Repo Guardian помогает ему сначала собрать факты, затем найти главное и только после этого предлагать изменения.

Главное правило:

> Никаких серьёзных выводов без evidence.

Evidence может быть:

- файл и реальная строка;
- manifest, lockfile или конфигурация;
- результат Git-команды;
- обнаруженный test/build command;
- конкретный кодовый паттерн;
- verified test result.

Repo Guardian не пытается выдать сотни «critical vulnerabilities». Он показывает короткий приоритетный список, объясняет confidence и отделяет доказанные проблемы от гипотез.

## Strict Engineer Mode

В Skill есть строгий контракт для AI-агента, который уменьшает выдуманные факты и лишние изменения.

Агент обязан:

- сначала определить задачу, scope и acceptance criteria;
- изучить существующий код, инструкции, tests и Git state;
- писать минимальный рабочий patch без самовольного refactor;
- не придумывать файлы, строки, API, команды и результаты;
- помечать незапущенные проверки как `NOT RUN`;
- после изменения проверить diff, syntax, tests и доступные quality checks;
- не говорить «готово», пока не пройден verification gate.

Полный контракт: [docs/agent-contract.md](docs/agent-contract.md).

## Установка

    git clone https://github.com/HeyDander/repo-guardian-ai.git
    cd repo-guardian-ai

    python3 -m venv .venv
    . .venv/bin/activate
    python3 -m pip install -e .

Проверка установки:

    repo-guardian --help
    repo-guardian full --repo .

Для Claude Code подключите [SKILL.md](SKILL.md) как Skill. CLI и analyzers находятся в src/repo_guardian и не зависят от AI-провайдера.

## Два способа работы

### Интерактивный terminal dashboard

Если работаешь в терминале сам, запусти полноценный интерфейс:

    repo-guardian ui --repo /path/to/project

В dashboard есть Overview, score bars, цветные severity, Top Findings и Codebase Map.

    +-------------------------------------------------------------+
    | REPO GUARDIAN  OVERVIEW                                     |
    | /path/to/project  |  Stack: Python                         |
    +-------------------------------------------------------------+
    | Overall  94/100  [#######################.....]             |
    | Security             100/100  ####################           |
    | Testing               80/100  ################....           |
    | Architecture          90/100  ##################..           |
    |                                                             |
    | TOP FINDINGS                                               |
    | HIGH/HIGH RG-TST-001  Test files not found                 |
    +-------------------------------------------------------------+
    | [r] refresh  [f] findings  [m] map  [q] quit                |
    +-------------------------------------------------------------+

Язык интерфейса переключается прямо во время работы:

- русский — режим по умолчанию;
- английский — клавиша `l`;
- повторное нажатие `l` возвращает русский.

Клавиши:

- `r` — обновить аудит;
- `f` — открыть полный список findings;
- `m` — открыть карту codebase;
- `b` — вернуться на Overview;
- `q` — выйти.

### Командный режим

Для CI, скриптов и AI-агентов остаются обычный вывод и JSON:

    repo-guardian full --repo .
    repo-guardian full --repo . --json --fail-on high

Интерактивный `ui` предназначен для человека в терминале и не используется в CI.

## Быстрый старт

Проверить другой репозиторий:

    repo-guardian full --repo /path/to/project

JSON для CI или другого агента:

    repo-guardian doctor --repo . --json

Проверить безопасность:

    repo-guardian security --repo . --all

Проверить текущий diff:

    repo-guardian review --repo .

Расследовать симптом:

    repo-guardian bugs --repo . --symptom "login иногда возвращает 401"

Проверка для CI:

    repo-guardian full --repo . --fail-on high

Показать план исправлений без изменения файлов:

    repo-guardian fix --repo .

Открыть интерактивный terminal dashboard:

    repo-guardian ui --repo /Users/daniel/CYBER

В dashboard используются клавиши `r` для обновления, `f` для findings, `m` для codebase map, `b` для возврата и `q` для выхода.

## Все режимы

| Режим | Что делает | Когда использовать |
| --- | --- | --- |
| doctor | Health-check структуры, Git, документации и analyzers | Перед началом работы с неизвестным repo |
| map | Показывает файлы, entry points, тесты, конфигурацию и команды | Чтобы быстро понять устройство проекта |
| bugs | Evidence-oriented набор проверок для симптома | Когда есть регрессия или bug report |
| tests | Проверяет наличие тестов и critical-path signals | Перед feature или refactor |
| security | Ищет secrets и опасные dynamic execution patterns | Перед PR/release |
| dependencies | Проверяет manifests, lockfiles и version ranges | Перед upgrade или release |
| performance | Ищет network/query вызовы внутри циклов | При latency/load подозрении |
| architecture | Ищет oversized modules и blast radius | Перед большим refactor |
| refactor | Даёт безопасный workflow без слепого изменения | Для пошагового рефакторинга |
| review | Проверяет Git diff и scope изменений | Перед commit или pull request |
| docs | Проверяет минимальную документацию | При onboarding и release |
| release | Проверяет dirty tree, changelog и CI | Перед публикацией версии |
| context | Создаёт компактный AI context | Для передачи проекта агенту |
| full | Полный evidence-based audit и score | Для первого health-check |
| fix | Разделяет safe fixes и risky changes | Перед внесением исправлений |
| ui | Интерактивный terminal dashboard | Для ежедневной работы в терминале |

## Что реально анализируется

### Security

Ищет:

- возможные secrets в исходниках;
- API keys, passwords, tokens и secret assignments;
- eval/exec;
- child_process.exec;
- os.system;
- другие очевидные dynamic execution patterns.

Security evidence редактируется и не показывает значение секрета. Потенциальный паттерн получает confidence и не называется доказанной уязвимостью без проверки source/sink.

### Testing

Проверяет наличие test/spec файлов и минимального автоматического барьера. Если тестов нет, finding содержит repository-level evidence. Если тесты есть, Repo Guardian не выдумывает coverage без реального coverage output.

### Dependencies

Проверяет:

- package.json;
- pyproject.toml;
- requirements.txt;
- go.mod;
- Cargo.toml;
- pom.xml;
- composer.json;
- Gemfile;
- соответствующие lockfiles;
- слишком широкие version ranges;
- невалидный package.json.

Зависимости не обновляются автоматически. CVE не заявляются без доступного внешнего audit tool.

### Performance

Ищет консервативные сигналы:

- SQL/query внутри циклов;
- fetch, axios, requests, httpx, urllib внутри циклов;
- expensive calls в for, while и forEach.

Такие findings имеют MEDIUM confidence и требуют profiling или benchmark.

### Architecture и Code Quality

Проверяет:

- oversized modules;
- потенциальный blast radius;
- entry points;
- типы файлов;
- конфигурационные boundaries;
- структуру проекта.

Большой файл не объявляется архитектурной ошибкой автоматически. Рекомендация предлагает characterization tests и проверку imports/public API.

### Release Readiness

Проверяет:

- текущую ветку;
- последний commit;
- незакоммиченные изменения;
- CHANGELOG;
- GitHub Actions workflows.

Dirty tree не исправляется автоматически.

### Git Review

review использует git diff --stat и показывает scope текущих изменений. Если Git недоступен или diff пуст, это отдельный finding.

### Codebase Map и Context

map показывает:

- количество файлов;
- entry points;
- количество test/spec файлов;
- конфигурационные файлы;
- обнаруженные project commands;
- распределение расширений.

context создаёт Markdown-сводку со stack, key files, командами, branch, last commit и safety rule. Критические execution flows не выдумываются: для полноценного call/import graph нужен language-aware analyzer.

## Scoring

Каждая категория начинается со score 100.

| Severity | Penalty |
| --- | ---: |
| CRITICAL | -30 |
| HIGH | -20 |
| MEDIUM | -10 |
| LOW | -3 |
| INFO | 0 |

LOW confidence не штрафует score автоматически. Overall — среднее значение категорий. Score объяснимый, но не объективная метрика качества.

## Finding contract

Каждый finding содержит:

    ID
    Severity
    Category
    Title
    Evidence
    Impact
    Confidence
    Recommendation
    Suggested fix
    Source
    Verified

Пример:

    RG-PERF-001
    Severity: MEDIUM
    Category: Performance
    Evidence: app/handlers.py:42
    Confidence: MEDIUM
    Recommendation: проверить профилем
    Suggested fix: добавить benchmark

Консоль показывает top 5:

    repo-guardian full --repo . --all
    repo-guardian full --repo . --json

## Safe Fix System

fix только строит план:

    SAFE FIXES
      - добавить тест
      - исправить документацию
      - подготовить безопасный refactor plan

    REQUIRES CONFIRMATION
      - authentication / authorization changes
      - major dependency upgrade
      - database migration
      - destructive file or data operation
      - public API change
      - rewrite Git history

Repo Guardian не удаляет файлы молча, не делает force push/reset/clean, не удаляет database data, не публикует secrets и не изменяет код командой fix.

## Project command discovery

Команды обнаруживаются из:

- package.json scripts;
- pyproject.toml project scripts;
- Makefile targets.

Например:

    npm:test   -> npm run test
    npm:lint   -> npm run lint
    make:build -> make build

Они показываются в map, context и JSON как project commands (discovered, not run). Команды не запускаются автоматически: неизвестный script может менять файлы, обращаться к сети или быть destructive.

## CI integration

    repo-guardian full --repo . --json --fail-on high

Thresholds:

- critical;
- high по умолчанию;
- medium;
- low;
- never.

Пример workflow:

    - name: Repo Guardian
      run: |
        python3 -m pip install -e .
        repo-guardian full --repo . --json --fail-on high

LOW confidence findings не ломают CI автоматически.

## Поддерживаемые стеки

JavaScript, TypeScript, Node.js, React, Next.js, Vue, Python, FastAPI, Django, Go, Rust, Java/Kotlin, PHP, Ruby, C#/.NET, C/C++, Docker и Terraform.

Новые стеки добавляются в [detect.py](src/repo_guardian/detect.py), новые analyzers — через registry в [analyzers.py](src/repo_guardian/analyzers.py).

## Архитектура

    Claude Code / compatible agent
                    |
                    v
                 SKILL.md
                    |
                    v
             provider-neutral CLI
                    |
          +---------+---------+
          v                   v
        audit              JSON contract
          |
      analyzers ---- Repository tools ---- files / Git
          |
          v
    findings + evidence + confidence + score

Основные точки расширения:

- [models.py](src/repo_guardian/models.py) — Finding, Score, AuditResult;
- [repository.py](src/repo_guardian/repository.py) — files, Git, command discovery;
- [detect.py](src/repo_guardian/detect.py) — stack detection;
- [analyzers.py](src/repo_guardian/analyzers.py) — analyzers и scoring;
- [audit.py](src/repo_guardian/audit.py) — orchestration;
- [cli.py](src/repo_guardian/cli.py) — CLI и output.

## Разработка

    python3 -m unittest discover -s tests -v
    python3 -m compileall -q src
    git diff --check

Тесты проверяют:

- empty repository;
- security redaction;
- отсутствие тестов;
- polyglot stack detection;
- dependency findings;
- performance loop detection;
- oversized architecture module;
- release readiness;
- command discovery;
- JSON output;
- fail-on thresholds;
- блокировку destructive commands.

## Безопасность

Не добавляйте в issues, fixtures или отчёты реальные passwords, API keys, private keys, production credentials или персональные данные.

См. [SECURITY.md](SECURITY.md).

## Структура

    multi-skill/
    ├── SKILL.md
    ├── README.md
    ├── pyproject.toml
    ├── src/repo_guardian/
    │   ├── analyzers.py
    │   ├── audit.py
    │   ├── cli.py
    │   ├── detect.py
    │   ├── models.py
    │   └── repository.py
    ├── tests/
    ├── docs/
    ├── examples/
    └── .github/workflows/ci.yml

## Roadmap

- полноценный import/call graph для языков с AST;
- lockfile-aware vulnerability adapters;
- запуск project checks только с явным allow-list;
- CI и PR provider adapters;
- repo-guardian.toml для project-specific правил;
- analyzers для Docker, Kubernetes, databases, cloud и mobile.

## License

MIT — [LICENSE](LICENSE).
