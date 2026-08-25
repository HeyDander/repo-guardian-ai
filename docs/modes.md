# Режимы Repo Guardian

| Режим | Фокус | Минимальное evidence |
| --- | --- | --- |
| `doctor` | health-check | структура, команды, git, найденные конфиги |
| `map` | codebase map | entry points, модули, интеграции и критические потоки |
| `bugs` | расследование | симптом, execution flow, тесты, при необходимости история |
| `tests` | тестовая стратегия | тестовые файлы, критические пути, assertions и результаты |
| `security` | security review | конкретный sink/source/config и confidence |
| `dependencies` | зависимости | manifest, lockfile, доступный audit output |
| `performance` | bottlenecks | измерение или чёткий кодовый паттерн, без микрооптимизаций |
| `architecture` | границы | import/call graph или конкретный oversized/circular module |
| `refactor` | безопасное изменение | UNDERSTAND → PLAN → CONFIRM → IMPLEMENT → TEST → REVIEW |
| `review` | diff review | только изменённые строки и их regression risk |
| `docs` | документация | missing/outdated file or command |
| `release` | release readiness | test/build/lint/typecheck/config/git state |
| `context` | AI context | commands, conventions, important files and hazards |
| `full` | приоритизированный аудит | стек и git state до выбора проверок |

## Scoring

Стартовая оценка каждой категории равна 100. Подтверждённый `CRITICAL/HIGH/MEDIUM/LOW` finding уменьшает её на `30/20/10/3` балла соответственно. `LOW` confidence не штрафует score автоматически. Это эвристика для сравнения запусков, а не объективная метрика качества.

