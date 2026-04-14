# Architecture Map

## Слои

1. `Presentation Layer`
   - frontend pages, widgets, shared UI
   - feature screens без AI-логики
2. `Application Layer`
   - lesson runner
   - onboarding flow
   - journey / daily loop flow
   - next-day continuity seeding from previous session outcome
   - guided-route template overlay for recommended runs
   - route-aware block composition for support modules and preferred-mode response shape
   - continuity-aware lesson template overlay for recommended runs
   - recommendation flow
   - global Liza guidance flow
3. `Domain Layer`
   - user account
   - user profile
   - onboarding session
   - learner journey state
   - daily loop plan
   - session summary / tomorrow preview continuity snapshot
   - lesson
   - mistake
   - progress
   - profession topic
4. `AI Layer`
   - AI orchestrator
   - LLM/STT/TTS/Scoring provider contracts
   - prompts
5. `Data Layer`
   - SQLite + Alembic persistence
   - schemas
   - SQLAlchemy models and repositories
6. `Content Layer`
   - grammar topics
   - profession tracks
   - lesson templates

## Frontend модули

- `app` — router и shell
- `pages` — route-level страницы
- `widgets` — общий каркас приложения
- `widgets/liza` — coach presence и explainable guidance
- `widgets/liza` — coach presence, guidance grids и interactive explain-actions
- `widgets/navigation` — top rail, route continuity и shell-level re-entry prompts
- `features/dashboard`
- `features/daily-loop`
- `features/onboarding`
- `features/lesson-runner`
- `features/grammar`
- `features/speaking`
- `features/pronunciation`
- `features/writing`
- `features/profession`
- `features/progress`
- `features/mistakes`
- `features/settings`
- `entities/*` — доменные типы
- `shared/*` — UI, API, store, constants, helpers

## Backend модули

- `api/routes` — endpoint groups
- `core` — settings и DI-ready dependencies
- `schemas` — Pydantic contracts
- `services/*` — модульные use-case services
- `repositories/*` — persistence access layer
- `providers/*` — provider abstractions
- `prompts/*` — prompt templates
- `content/*` — учебный контент и lesson configs
- `db` / `models` — база для persistence layer

## Первый инкремент MVP

- onboarding profile setup
- dashboard summary
- proof lesson -> onboarding session -> daily loop handoff
- shell-level re-entry prompt for route continuity outside the dashboard
- route-first secondary surfaces so `activity` and `progress` return into `today route` before launching side flows
- recommendation + lesson build
- grammar topics
- speaking scenarios
- pronunciation drills
- writing review
- profession hub
- mistakes + progress
- provider status
