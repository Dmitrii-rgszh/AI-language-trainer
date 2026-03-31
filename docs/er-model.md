# ER Model

## Scope

Эта ER-модель фиксирует MVP storage-ядро для:

- user profile и preferences
- lesson templates и lesson runs
- execution of lesson blocks
- mistake analytics
- progress snapshots
- vocabulary retention
- professional content mapping

## Separation Principle

- `content entities` описывают учебный контент и lesson templates
- `runtime entities` фиксируют конкретные попытки пользователя
- `analytics entities` агрегируют ошибки, прогресс и интервальные повторы

## Mermaid ER Diagram

```mermaid
erDiagram
    USER_PROFILE ||--o{ LESSON_RUN : launches
    LESSON_TEMPLATE ||--o{ LESSON_RUN : instantiates
    LESSON_TEMPLATE ||--|{ LESSON_BLOCK : contains
    LESSON_RUN ||--o{ LESSON_BLOCK_RUN : executes
    LESSON_BLOCK ||--o{ LESSON_BLOCK_RUN : defines
    USER_PROFILE ||--o{ MISTAKE_RECORD : accumulates
    LESSON_BLOCK_RUN ||--o{ MISTAKE_RECORD : produces
    USER_PROFILE ||--o{ PROGRESS_SNAPSHOT : tracks
    LESSON_RUN ||--o{ PROGRESS_SNAPSHOT : updates
    USER_PROFILE ||--o{ VOCABULARY_ITEM : learns
    PROFESSION_TOPIC ||--o{ LESSON_TEMPLATE : enriches

    USER_PROFILE {
        string id PK
        string name
        string native_language
        string current_level
        string target_level
        string profession_track
        string preferred_ui_language
        string preferred_explanation_language
        int lesson_duration
    }

    LESSON_TEMPLATE {
        string id PK
        string lesson_type
        string title
        string goal
        string difficulty
        int estimated_duration
    }

    LESSON_BLOCK {
        string id PK
        string lesson_template_id FK
        string block_type
        int estimated_minutes
        string feedback_mode
    }

    LESSON_RUN {
        string id PK
        string user_id FK
        string template_id FK
        string status
        int score
        string started_at
        string completed_at
    }

    LESSON_BLOCK_RUN {
        string id PK
        string lesson_run_id FK
        string block_id FK
        string status
        string user_response_type
        int score
    }

    MISTAKE_RECORD {
        string id PK
        string user_id FK
        string source_block_run_id FK
        string category
        string subtype
        int repetition_count
        string severity
    }

    PROGRESS_SNAPSHOT {
        string id PK
        string user_id FK
        string lesson_run_id FK
        string snapshot_date
        int streak
    }

    VOCABULARY_ITEM {
        string id PK
        string user_id FK
        string word
        string category
        string learned_status
        int repetition_stage
    }

    PROFESSION_TOPIC {
        string id PK
        string domain
        string title
        string difficulty
    }
```

## Entity Notes

### USER_PROFILE

- один пользователь = один активный профиль
- хранит onboarding, goals, language preferences и приоритеты
- не должен содержать историю уроков напрямую

### LESSON_TEMPLATE

- это content entity
- хранит шаблон урока, а не конкретный запуск
- lesson builder может собрать runtime lesson на основе template + weak spots + priorities

### LESSON_BLOCK

- является частью template
- payload зависит от `block_type`
- порядок блоков хранится на уровне lesson template

### LESSON_RUN

- отдельный runtime instance урока
- нужен для истории, streak, analytics и повторного просмотра результатов

### LESSON_BLOCK_RUN

- granular execution-слой
- связывает пользовательский ответ, транскрипт, feedback и scoring с конкретным block instance

### MISTAKE_RECORD

- агрегированная сущность ошибки
- источник ошибки может ссылаться на `lesson_block_run`
- repetition count растёт при повторных совпадениях

### PROGRESS_SNAPSHOT

- моментальный срез по skills
- полезен для weekly/monthly charts
- может быть привязан к lesson run, но не обязан

### VOCABULARY_ITEM

- поддерживает интервальные повторения
- может рождаться из lesson blocks, mistakes и profession content

### PROFESSION_TOPIC

- content entity для insurance, banking, trainer skills, regulation, AI business
- lesson templates могут ссылаться на topic id, не копируя весь контент в каждый урок

## MVP Persistence Recommendation

- SQLite tables для runtime и analytics entities
- JSON fields допустимы для lesson block payload и flexible metadata
- content templates можно сначала держать в JSON/Python configs, а позже перенести в БД

