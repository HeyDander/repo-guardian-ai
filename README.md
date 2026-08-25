<div align="center">

# Repo Guardian

### An AI-powered senior engineer for your codebase.

Понимает репозиторий. Находит главное. Показывает доказательства.

[![CI](https://github.com/your-org/repo-guardian-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/repo-guardian-ai/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-111827.svg)](LICENSE)

```bash
repo-guardian full --repo .
```

</div>

---

## Что это

Repo Guardian превращает AI coding agent в системного senior-аудитора репозитория.

Он помогает понять codebase, найти реальные риски, расставить приоритеты и подготовить безопасный план изменений. Каждое существенное наблюдение должно опираться на evidence: файл, строку, тест, конфигурацию, команду или Git.

```text
┌─────────────────────────────────────────────────────────────┐
│  Repo Guardian                                              │
│  AI context  ·  health score  ·  evidence  ·  safe fixes    │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   codebase map     risk review      release check
```

Это не «AI нашёл 300 проблем». Это короткий список наиболее важных вещей, которые можно проверить и исправить.

## За минуту

```bash
git clone https://github.com/your-org/repo-guardian-ai
cd repo-guardian-ai

python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .

repo-guardian full --repo /path/to/your-project
```

Машиночитаемый отчёт для CI или другого агента:

```bash
repo-guardian security --repo . --json
```

Для Claude Code используйте [SKILL.md](SKILL.md) как portable Skill. Ядро CLI не зависит от конкретного AI-провайдера.

## Режимы

| Команда | Что делает |
| --- | --- |
| `/repo-guardian` | Выбирает наиболее полезный режим |
| `/repo-guardian doctor` | Полный health-check проекта |
| `/repo-guardian map` | Строит карту файлов, entry points и конфигурации |
| `/repo-guardian bugs` | Расследует симптом через code flow, тесты и Git |
| `/repo-guardian tests` | Проверяет тестовую стратегию и critical paths |
| `/repo-guardian security` | Ищет подтверждённые security-риск-паттерны |
| `/repo-guardian dependencies` | Анализирует manifests и lockfiles |
| `/repo-guardian performance` | Ищет очевидные bottlenecks, а не микрооптимизации |
| `/repo-guardian architecture` | Проверяет coupling, границы и drift |
| `/repo-guardian review` | Ревьюит diff и изменённые файлы |
| `/repo-guardian docs` | Проверяет README, setup и API-документацию |
| `/repo-guardian release` | Проверяет готовность к release |
| `/repo-guardian context` | Готовит компактный контекст для AI-агента |
| `/repo-guardian full` | Выполняет умный комплексный аудит |
| `/repo-guardian fix` | Разделяет safe fixes и изменения с подтверждением |

## Как выглядит результат

```text
Repository Health Score: 68/100

Architecture          91/100
Security              72/100
Testing               63/100
Dependencies          88/100
Documentation         79/100
Performance            94/100
Code Quality           81/100
Release Readiness      70/100

Top 5 things to fix

1. [HIGH / HIGH] RG-SEC-001  Missing authorization check
   Evidence: src/api/users.ts:42

2. [HIGH / HIGH] RG-TST-001  Critical API path lacks coverage
   Evidence: tests/ (missing)

3. [MEDIUM / MEDIUM] RG-SEC-002  Dynamic command execution
   Evidence: scripts/import.py:31
```

Каждый finding содержит:

`ID` · `Severity` · `Category` · `Title` · `Evidence` · `Impact` · `Confidence` · `Recommendation` · `Suggested fix`

`LOW confidence` не превращается автоматически в `HIGH priority`. Если доказательств недостаточно, Repo Guardian прямо говорит, что это гипотеза.

## Безопасные изменения

Команда `fix` сначала показывает план и ничего не меняет молча.

```text
SAFE FIXES
  - добавить недостающий тест
  - исправить документацию
  - удалить очевидный unused import

REQUIRES CONFIRMATION
  - изменить authentication или authorization
  - обновить major dependency
  - выполнить database migration
  - менять публичный API или большой refactor
```

Repo Guardian не делает `git reset`, force push, удаление данных или переписывание истории. Содержимое похожее на секреты не попадает в evidence отчёта.

## Поддерживаемые стеки

JavaScript · TypeScript · Node.js · React · Next.js · Vue · Python · FastAPI · Django · Go · Rust · Java/Kotlin · PHP · Ruby · C#/.NET · C/C++ · Docker · Terraform

Детектирование отделено от анализаторов. Новый модуль вроде `docker`, `kubernetes`, `database` или `ci` добавляется через registry, не переписывая core.

## Архитектура

```text
Claude Code / compatible agent
              │
              ▼
           SKILL.md
              │
              ▼
        provider-neutral CLI
              │
      ┌───────┴────────┐
      ▼                ▼
    audit           JSON contract
      │
  analyzers ─── Repository tools ─── files / Git / explicit commands
      │
      ▼
 findings + evidence + confidence + score
```

Ключевые точки расширения:

- [analyzers.py](src/repo_guardian/analyzers.py) — анализаторы и scoring;
- [detect.py](src/repo_guardian/detect.py) — stack detection;
- [repository.py](src/repo_guardian/repository.py) — безопасная работа с файлами и Git;
- [models.py](src/repo_guardian/models.py) — единый report contract.

## Demo

Полный сценарий находится в [examples/demo.md](examples/demo.md):

```text
messy repository
       ↓
/repo-guardian full
       ↓
Health Score: 68/100
       ↓
Top findings with evidence
       ↓
/repo-guardian fix
       ↓
tests + review
       ↓
Health Score: 84/100
```

Цифры в demo иллюстративны; фактический score всегда рассчитывается по найденным evidence.

## Разработка

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q src
```

Текущий набор тестов проверяет empty repository, security fixture, отсутствие тестов, polyglot repository, JSON contract и блокировку destructive commands.

Документы для contributors: [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [CHANGELOG.md](CHANGELOG.md).

## Roadmap

- полноценный import/call graph для codebase map;
- анализ lockfiles через доступные ecosystem audit tools;
- CI и PR adapters с явным разрешением пользователя;
- `repo-guardian.toml` для project-specific правил;
- дополнительные analyzers для Docker, Kubernetes, databases и cloud.

## License

MIT — [LICENSE](LICENSE).

