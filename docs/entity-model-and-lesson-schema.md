# Data Model Package

Этот пакет документов фиксирует следующий обязательный слой проекта после архитектурной декомпозиции:

1. ER-модель
2. JSON Schema сущностей
3. lesson block schema

## Documents

- `docs/er-model.md` — ER-модель и связи между content/runtime/analytics сущностями
- `docs/lesson-block-schema.md` — правила и payload contract для lesson engine

## Generated JSON Schemas

Схемы генерируются из `backend/app/schemas/blueprint.py` скриптом `backend/scripts/export_json_schemas.py`.

Ожидаемые файлы:

- `docs/schemas/user-profile.schema.json`
- `docs/schemas/lesson-template.schema.json`
- `docs/schemas/lesson-block.schema.json`
- `docs/schemas/lesson-run.schema.json`
- `docs/schemas/lesson-block-run.schema.json`
- `docs/schemas/mistake-record.schema.json`
- `docs/schemas/progress-snapshot.schema.json`
- `docs/schemas/vocabulary-item.schema.json`
- `docs/schemas/profession-topic.schema.json`

## Why This Matters

- backend получает единую базу для persistence и API contracts
- lesson engine получает строго типизированный block contract
- frontend и content layer могут опираться на один и тот же источник правды
- новые типы уроков и новые provider flows можно добавлять без переписывания ядра

