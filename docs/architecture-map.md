# Architecture Map

## Слои

1. `Presentation Layer`
   - frontend pages, widgets, shared UI
   - feature screens без AI-логики
2. `Application Layer`
   - lesson runner
   - onboarding flow
   - recommendation flow
3. `Domain Layer`
   - user profile
   - lesson
   - mistake
   - progress
   - profession topic
4. `AI Layer`
   - AI orchestrator
   - LLM/STT/TTS/Scoring provider contracts
   - prompts
5. `Data Layer`
   - SQLite-ready backend structure
   - schemas
   - future SQLAlchemy models
6. `Content Layer`
   - grammar topics
   - profession tracks
   - lesson templates

## Frontend модули

- `app` — router и shell
- `pages` — route-level страницы
- `widgets` — общий каркас приложения
- `features/dashboard`
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
- `providers/*` — provider abstractions
- `prompts/*` — prompt templates
- `content/*` — учебный контент и lesson configs
- `db` / `models` — база для persistence layer

## Первый инкремент MVP

- onboarding profile setup
- dashboard summary
- recommendation + lesson build
- grammar topics
- speaking scenarios
- pronunciation drills
- writing review
- profession hub
- mistakes + progress
- provider status

