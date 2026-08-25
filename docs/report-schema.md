# Схема finding

JSON-отчёт содержит `root`, `stacks`, `overall`, `scores`, `findings` и `commands`.

Каждый finding имеет стабильный `id`, `severity`, `category`, `title`, массив `evidence`, `impact`, `confidence`, `recommendation`, optional `suggested_fix`, `source` и `verified`. Значение evidence никогда не должно содержать секрет.

