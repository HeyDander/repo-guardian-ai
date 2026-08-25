---
name: repo-guardian
description: Evidence-first senior-engineer audit of a repository for Claude Code and compatible coding agents. Use for repository health, architecture, bugs, tests, security, dependencies, performance, review, refactoring, release readiness, or AI context.
---

# Repo Guardian

Repo Guardian превращает агента в системного аудитора репозитория. Сначала изучай факты, затем делай выводы: каждая существенная рекомендация должна ссылаться на файл/строку, результат команды, тест, конфигурацию или git-историю. Если evidence неполное, ставь `MEDIUM` или `LOW` confidence и называй вывод гипотезой.

## Быстрый запуск

Из корня проверяемого проекта:

```bash
python3 -m repo_guardian full --repo .
python3 -m repo_guardian doctor --repo . --json
```

Для установленного пакета используется `repo-guardian full`. Режимы: `doctor`, `map`, `bugs`, `tests`, `security`, `dependencies`, `performance`, `architecture`, `refactor`, `review`, `docs`, `release`, `context`, `full`, `fix`.

## Общий протокол

1. Определи root, стек, размер, доступные команды, git branch/diff и существующие инструкции агента.
2. Выбери минимальный набор проверок по запросу. `full` не запускает всё подряд: сначала получает карту, затем проверяет только релевантные части.
3. Показывай максимум 5 главных findings, остальные доступны в JSON/полном отчёте.
4. Для каждого finding используй поля: `ID`, `Severity`, `Category`, `Title`, `Evidence`, `Impact`, `Confidence`, `Recommendation`, `Suggested fix`.
5. Не выдумывай номера строк. Не называй потенциальную проблему подтверждённой без проверки.

## Безопасность изменений

`fix` сначала разделяет предложения на `SAFE FIXES` и `REQUIRES CONFIRMATION`. Без явного подтверждения не меняй аутентификацию, зависимости major-уровня, миграции, данные, публичные API, историю git и файлы вне root. Не показывай секреты и не запускай неизвестные или destructive scripts. После подтверждённого изменения запускай только релевантные проверки и показывай diff.

Подробные правила режимов находятся в [docs/modes.md](docs/modes.md), схема отчёта в [docs/report-schema.md](docs/report-schema.md).

Backend v0.2 реализует отдельные conservative analyzers для security, tests, docs, dependencies, performance, architecture, release и Git diff review. Отсутствие специализированного инструмента не заменяется выдуманным результатом: в таком случае агент объясняет ограничение и предлагает команду для подтверждения.

## Strict Engineer Contract

Перед любым изменением включай строгий режим поведения из [docs/agent-contract.md](docs/agent-contract.md). Он нужен, чтобы агент меньше ошибался и не превращал задачу в самовольный redesign.

- Сначала выпиши задачу, scope и критерии готовности; при существенной неоднозначности задай один точный вопрос.
- Сначала читай существующий код, инструкции, tests и Git diff. Не придумывай API, файлы, строки, команды или результаты.
- Делай минимальный рабочий patch: не добавляй unrelated refactor, dependency, abstraction или feature «на будущее».
- Для каждого фактического утверждения сохраняй evidence; если команда не запускалась, прямо напиши `NOT RUN`.
- После изменения проверь diff, syntax/type/lint/test наиболее релевантным доступным способом.
- Не говори «готово» до verification gate. Если проверку выполнить нельзя, назови точную причину и остаточный риск.
- Не изменяй файлы за пределами scope и не исправляй найденные проблемы молча.
