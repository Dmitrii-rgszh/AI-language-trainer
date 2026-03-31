# AI English Trainer Pro

Стартовая реализация локального модульного приложения для изучения английского языка по ТЗ из [tz_ai_english_trainer_modular_v_1.md](./tz_ai_english_trainer_modular_v_1.md).

## Что уже подготовлено

- модульный каркас `React + TypeScript + Tailwind` для desktop-first frontend;
- модульный каркас `FastAPI` backend с сервисным слоем, схемами и AI provider abstraction;
- начальные MVP-экраны: onboarding, dashboard, lesson runner, grammar, speaking, pronunciation, writing, profession, mistakes, progress, settings;
- lesson engine v1 на конфиге lesson blocks;
- моковые данные и локальные заглушки для AI orchestration, чтобы архитектуру можно было развивать без переписывания ядра.
- LM Studio integration layer для локального OpenAI-compatible LLM server с fallback на mock provider.

## Структура

- [app/frontend](./app/frontend) — frontend shell
- [backend](./backend) — backend API
- [docs/architecture-map.md](./docs/architecture-map.md) — карта модулей
- [docs/entity-model-and-lesson-schema.md](./docs/entity-model-and-lesson-schema.md) — сущности и lesson blocks

## Локальный запуск

### Frontend

```bash
cd app/frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
alembic upgrade head
python scripts/bootstrap_content.py
python scripts/seed_demo_data.py
uvicorn app.main:app --reload
```

Frontend ожидает backend по адресу `http://localhost:8000`.

### LM Studio

Для реального LLM вместо mock provider можно поднять локальный сервер LM Studio и задать переменные окружения:

```bash
set LLM_PROVIDER=lmstudio
set LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
set LMSTUDIO_MODEL=your-loaded-model
```

Если LM Studio недоступен, backend автоматически вернётся на mock LLM fallback.
