# Режимы Repo Guardian

| Режим | Фокус | Минимальное evidence |
| --- | --- | --- |
| `doctor` | health-check | структура, команды, git, найденные конфиги |
| `map` | codebase map | entry points, модули, интеграции и критические потоки |
| `bugs` | расследование | симптом, execution flow, тесты, при необходимости история |
| `tests` | тестовая стратегия | тестовые файлы, критические пути, assertions и результаты |
| `security` | security review | конкретный sink/source/config и confidence |
| `dependencies` | зависимости | manifest, lockfile и диапазоны версий |
| `performance` | bottlenecks | дорогой вызов в цикле с MEDIUM confidence, без микрооптимизаций |
| `architecture` | границы | oversized module и конкретный blast radius |
| `refactor` | безопасное изменение | UNDERSTAND → PLAN → CONFIRM → IMPLEMENT → TEST → REVIEW |
| `review` | diff review | только изменённые строки и их regression risk |
| `docs` | документация | missing/outdated file or command |
| `release` | release readiness | test/build/lint/typecheck/config/git state |
| `context` | AI context | commands, conventions, important files and hazards |
| `full` | приоритизированный аудит | стек и git state до выбора проверок |
| `ui` | terminal dashboard | интерактивный локальный просмотр score, findings и map |

Режимы `dependencies`, `performance`, `architecture`, `release` и `review` теперь используют отдельные analyzers, а не fallback на общий health-check. Внешние vulnerability databases и runtime benchmarks не запускаются автоматически: для них нужен явно доступный инструмент и разрешение пользователя.

Для поведения AI-агента во всех режимах используется строгий [agent contract](agent-contract.md): scope → evidence → minimal patch → verification gate.

## Scoring

Стартовая оценка каждой категории равна 100. Подтверждённый `CRITICAL/HIGH/MEDIUM/LOW` finding уменьшает её на `30/20/10/3` балла соответственно. `LOW` confidence не штрафует score автоматически. Это эвристика для сравнения запусков, а не объективная метрика качества.
