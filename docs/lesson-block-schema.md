# Lesson Block Schema

## Purpose

Lesson blocks являются базовой единицей lesson engine. Они позволяют собирать любой урок из независимых модулей без прошивки сценария в UI или backend route.

## Core Contract

Каждый block обязан иметь:

- `id`
- `blockType`
- `title`
- `instructions`
- `estimatedMinutes`
- `feedbackMode`
- `dependsOnBlockIds`
- `payload`

## Supported Block Types

1. `intro_block`
2. `review_block`
3. `grammar_block`
4. `vocab_block`
5. `speaking_block`
6. `pronunciation_block`
7. `listening_block`
8. `reading_block`
9. `writing_block`
10. `profession_block`
11. `reflection_block`
12. `summary_block`

## Validation Rules

1. Первый блок урока должен быть `intro_block` или `review_block`.
2. Последний блок урока должен быть `summary_block`.
3. `estimatedMinutes` должен быть от `1` до `60`.
4. `feedbackMode` может быть только `immediate`, `after_block`, `critical_only`.
5. `dependsOnBlockIds` может ссылаться только на block ids внутри того же lesson template.
6. Payload обязан соответствовать типу блока.

## Payload Rules By Block

### `intro_block`

- задаёт цель урока
- содержит warmup prompt
- содержит success criteria

### `review_block`

- ссылается на предыдущие ошибки
- содержит review items
- может таргетировать типы ошибок

### `grammar_block`

- содержит `topicId`
- список `focusPoints`
- список prompts
- список `targetErrorTypes`

### `vocab_block`

- содержит lexical set
- массив vocabulary ids
- phrases для активизации лексики

### `speaking_block`

- содержит `scenarioId`
- `mode`
- список prompts
- флаг `expectsVoice`
- список `feedbackFocus`

### `pronunciation_block`

- содержит `soundFocus`
- `phraseDrills`
- `minimalPairs`
- опциональный `shadowingScript`

### `listening_block`

- содержит `audioAssetId`
- опциональный transcript
- comprehension questions
- флаг `slowModeAllowed`

### `reading_block`

- содержит `passageTitle`
- содержит `passage`
- comprehension questions
- опциональный `answerKey`

### `writing_block`

- содержит `taskId`
- `brief`
- `checklist`
- `tone`

### `profession_block`

- содержит `domain`
- `topicId`
- `scenario`
- список `targetTerms`

### `reflection_block`

- содержит reflection prompts
- язык, в котором сохраняется reflection

### `summary_block`

- recap prompts
- next step
- флаг `saveToProgress`

## Assembly Rules

- lesson builder выбирает block mix на основе level, priorities, weak spots и profession track
- mixed lesson обычно включает `review_block` + `grammar_block` или `vocab_block` + `speaking_block` + `profession_block` + `summary_block`
- recovery lesson усиливает `review_block`, `grammar_block` и `pronunciation_block`
- professional lesson обязан включать `profession_block`

## Source Of Truth

- Pydantic blueprint: `backend/app/schemas/blueprint.py`
- generated JSON schema: `docs/schemas/lesson-block.schema.json`
