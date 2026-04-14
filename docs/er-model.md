# ER Model

## Scope

Эта ER-модель фиксирует уже не абстрактное MVP storage-ядро, а текущий рабочий storage contour для:

- identity и account resolution;
- proof lesson handoff и draft onboarding;
- completed onboarding snapshot;
- learner journey state и daily loop plan;
- lesson runtime;
- mistake, progress и vocabulary analytics.

## Separation Principle

- `identity entities` отвечают за login/email и точку входа пользователя;
- `learner state entities` держат профиль, онбординг, текущий этап journey и daily plan;
- `runtime entities` фиксируют конкретные lesson runs и block runs;
- `analytics entities` агрегируют ошибки, прогресс, speaking/pronunciation/writing history и интервальные повторы;
- `content entities` описывают templates, blocks и professional enrichment.

## Mermaid ER Diagram

```mermaid
erDiagram
    USER_ACCOUNT ||--|| USER_ONBOARDING : completes
    USER_ACCOUNT ||--o{ ONBOARDING_SESSION : drafts
    USER_ACCOUNT ||--|| LEARNER_JOURNEY_STATE : tracks
    USER_ACCOUNT ||--o{ DAILY_LOOP_PLAN : schedules
    USER_ACCOUNT ||--|| USER_PROFILE : shares_logical_id_with

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
    USER_PROFILE ||--o{ SPEAKING_ATTEMPT : records
    USER_PROFILE ||--o{ PRONUNCIATION_ATTEMPT : records
    USER_PROFILE ||--o{ WRITING_ATTEMPT : records
    PROFESSION_TOPIC ||--o{ LESSON_TEMPLATE : enriches
    DAILY_LOOP_PLAN o|--o| LESSON_RUN : may_launch

    USER_ACCOUNT {
        string id PK
        string login UK
        string email UK
        string created_at
        string updated_at
    }

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
        json onboarding_answers
    }

    USER_ONBOARDING {
        string id PK
        string user_id FK
        json answers
        string completed_at
    }

    ONBOARDING_SESSION {
        string id PK
        string user_id FK nullable
        string source
        string status
        json proof_lesson_handoff
        json account_draft
        json profile_draft
        int current_step
        string completed_at
    }

    LEARNER_JOURNEY_STATE {
        string user_id PK FK
        string stage
        string source
        string preferred_mode
        string diagnostic_readiness
        int time_budget_minutes
        string current_focus_area
        string current_strategy_summary
        string next_best_action
        string last_daily_plan_id
        json proof_lesson_handoff
        json strategy_snapshot
        string onboarding_completed_at
    }

    DAILY_LOOP_PLAN {
        string id PK
        string user_id FK
        string plan_date_key
        string stage
        string session_kind
        string status
        string focus_area
        string headline
        string recommended_lesson_type
        string lesson_run_id nullable
        json steps
        json completion_summary
        string completed_at
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

    SPEAKING_ATTEMPT {
        string id PK
        string user_id FK
        string scenario_id
        int score
        string created_at
    }

    PRONUNCIATION_ATTEMPT {
        string id PK
        string user_id FK
        string drill_id
        int score
        string created_at
    }

    WRITING_ATTEMPT {
        string id PK
        string user_id FK
        string task_id
        int score
        string created_at
    }

    PROFESSION_TOPIC {
        string id PK
        string domain
        string title
        string difficulty
    }
```

## First-Path Source Of Truth

### 1. Identity

- `users`
  Login, email и canonical user id.
- Этот слой нужен, чтобы proof lesson handoff можно было довести до нормальной регистрации, а не хранить его только в frontend state.

### 2. Stable learner profile

- `user_profiles`
  Основной runtime-профиль пользователя.
- Здесь лежат name, языковые настройки, current/target level, profession track, time budget и `onboarding_answers`.
- Все learning services уже читают именно этот слой как основной профиль для рекомендаций и lesson selection.

### 3. Completed onboarding snapshot

- `user_onboarding`
  Финальный слепок ответов, который завершает onboarding как продуктовый этап.
- Он нужен отдельно от `user_profiles`, чтобы:
  - хранить факт завершения onboarding;
  - не терять исходный слепок ответов;
  - позже использовать его для аналитики, repeat onboarding и cohort analysis.

### 4. Draft onboarding and proof-lesson handoff

- `onboarding_sessions`
  Черновой state первого пути пользователя.
- Что хранится:
  - `proof_lesson_handoff`: откуда пользователь пришёл и какой wow-signal уже получен;
  - `account_draft`: login/email до финального completion;
  - `profile_draft`: короткий onboarding draft;
  - `current_step`: текущий шаг;
  - `status`: stage черновика.
- Это позволяет не терять прогресс между reload, возвратом на onboarding и handoff из proof lesson.

### 5. Live journey state

- `learner_journey_states`
  Одна запись на пользователя, которая отвечает на вопрос:
  `на каком этапе человек сейчас находится и что ему показать дальше`.
- Что хранится:
  - текущий stage (`daily_loop_ready`, `daily_loop_active`, `daily_loop_completed`);
  - source входа;
  - preferred mode и diagnostic readiness;
  - current focus area;
  - current strategy summary;
  - next best action;
  - strategy snapshot;
  - ссылка на последний daily plan.

### 6. Daily ritual planning

- `daily_loop_plans`
  Персистентный план дня, один на пользователя в день.
- Что хранится:
  - `plan_date_key`;
  - `session_kind`;
  - `focus_area`;
  - explainable copy: headline, summary, why this now, next step hint;
  - рекомендованный тип урока;
  - список шагов daily loop;
  - `lesson_run_id`, если план уже запущен;
  - `completion_summary`, если цикл завершён.

### 7. Lesson execution and learning memory

- `lesson_runs` и `lesson_block_runs`
  Выполнение конкретного урока.
- `mistake_records`, `progress_snapshots`, `vocabulary_items`
  Долгая память системы о слабых местах, прогрессе и повторении слов.
- `speaking_attempts`, `pronunciation_attempts`, `writing_attempts`
  Узкоспециализированная история по вертикалям.

## Why The Split Works

- `onboarding_sessions` решают проблему draft и handoff, не засоряя боевой профиль.
- `user_profiles` остаётся быстрым runtime-слоем для рекомендаций и lesson engine.
- `user_onboarding` даёт отдельный product snapshot завершённого входа.
- `learner_journey_states` отвечает за текущее состояние маршрута пользователя, а не за все исторические детали.
- `daily_loop_plans` отделяют explainable planning от фактического lesson runtime, поэтому план можно строить, показывать, возобновлять и пересобирать независимо от lesson execution.

## Current Hardening Note

Сейчас `user_profiles.id` и `users.id` совпадают по сервисному контракту, но не связаны прямым FK.
Для текущего этапа это допустимо и сохраняет совместимость с уже существующим runtime-слоем.
Следующий DB-hardening шаг после стабилизации first path:

- либо ввести явный FK/one-to-one link между identity и profile;
- либо полностью унифицировать все user-facing runtime tables вокруг одного canonical user key.
