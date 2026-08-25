# Вклад

1. Создайте ветку и небольшое изменение с тестом поведения.
2. Не добавляйте реальные секреты в fixtures, logs или snapshots.
3. Для нового analyzer добавьте его в `ANALYZERS`, отдельные finding IDs и fixture, проверяющий evidence.
4. Запустите `python -m unittest discover -s tests -v` и `python -m compileall -q src`.

Изменения должны быть узкими, обратимыми и объяснять trade-offs в pull request.

