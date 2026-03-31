# Техническое задание
## Проект: локальное AI-приложение для изучения английского языка с профессиональным треком

### Рабочее название
**AI English Trainer Pro**

### Версия ТЗ
v1.0

---

## 1. Цель проекта

Создать локальное desktop/web-приложение для изучения английского языка с упором на:
- доведение пользователя от уровня A2 к уверенному B1/B2;
- разговорный английский;
- грамматику с понятными объяснениями и системным закреплением;
- понимание английской речи;
- уменьшение русского акцента;
- подготовку к собеседованиям;
- профессиональный английский для ролей:
  - business trainer,
  - sales trainer,
  - insurance trainer,
  - sales enablement specialist,
  - product trainer,
  - learning & development specialist,
  - training manager;
- изучение страховой и банковской сферы Европы;
- изучение базовых и средних по глубине регуляторных тем ЕС;
- освоение прикладного использования ИИ в работе, обучении и продажах.

Приложение должно быть ориентировано на пользователя, которому нужен **единый центр обучения**, а не набор разрозненных сервисов.

---

## 2. Ключевые принципы разработки

### 2.1. Главный архитектурный принцип
**Архитектура должна быть строго модульной и масштабируемой.**

### 2.2. Обязательные правила для AI-кодера и разработчика
1. Любая повторяющаяся логика должна выноситься в отдельный модуль.
2. Нельзя держать большие куски бизнес-логики в одном файле страницы.
3. UI, логика, хранилище состояния, API-слой, voice-слой, scoring-слой и prompt-слой должны быть разделены.
4. Каждый крупный блок приложения должен быть независимым модулем.
5. Все режимы обучения должны подключаться как плагины/feature-modules.
6. Любая новая функция должна добавляться без переписывания существующего ядра.
7. Все промпты ИИ должны храниться отдельно от UI-кода.
8. Все сценарии уроков и режимов должны быть конфигурируемыми.
9. Все типы упражнений должны быть описаны через общую схему/интерфейс.
10. Любые voice-функции, grammar-функции, scoring-функции и progress-функции должны быть переиспользуемыми.

### 2.3. Требование к структуре файлов
- Повторяющиеся функции выносить в отдельные `.js/.ts` файлы.
- Все UI-компоненты выносить в отдельные компоненты.
- Никаких гигантских файлов на 1000+ строк с перемешанной логикой.
- Каждая feature должна иметь свою папку.
- Общие типы, интерфейсы, хелперы, константы и схемы должны жить отдельно.

---

## 3. Формат приложения

### 3.1. Основной формат
Предпочтительный формат:
- **Desktop-first приложение**, запускаемое локально на ПК пользователя;
- с возможностью дальнейшей упаковки в Electron/Tauri shell.

### 3.2. UI/Frontend
Рекомендуемый стек:
- **React**
- **TypeScript**
- **Tailwind CSS**
- Zustand или Redux Toolkit для состояния
- React Router
- shadcn/ui для базовых компонентов

### 3.3. Backend
Рекомендуемый вариант:
- **Python backend** как orchestration-layer

Почему Python:
- удобнее интеграция с локальными LLM;
- удобнее интеграция с whisper/STT/TTS;
- удобнее NLP/оценка текста/обработка транскриптов;
- проще для voice и AI pipeline;
- легче масштабировать AI-логику отдельно от фронта.

Рекомендуемый стек backend:
- **FastAPI**
- Pydantic
- SQLAlchemy
- Alembic
- SQLite для локальной базы на старте
- позже возможность PostgreSQL

### 3.4. Локальный AI-стек
Система должна проектироваться с учётом поддержки:
- локальной LLM через Ollama / LM Studio API;
- локального STT;
- локального TTS;
- опционально fallback на облачные сервисы в будущем.

На старте проектировать через абстрактные провайдеры:
- `LLMProvider`
- `STTProvider`
- `TTSProvider`
- `ScoringProvider`

---

## 4. Целевая аудитория

Основной пользователь:
- русскоязычный взрослый пользователь;
- стартовый уровень A2;
- цель — уверенный B1/B2;
- хочет учиться через ИИ;
- не любит перегруженные системы;
- хочет единое приложение;
- хочет английский как для жизни, так и для профессии;
- профессиональный контекст: страхование, банковские продукты, обучение продавцов, кураторов, менеджеров, AI в бизнесе.

---

## 5. Продуктовые цели

Приложение должно закрывать **все основные направления**:

1. Grammar
2. Speaking
3. Listening
4. Pronunciation / Accent Reduction
5. Writing
6. Vocabulary
7. Interview Prep
8. Everyday English
9. Professional English
10. Insurance / Banking EU knowledge
11. EU Regulation Basics
12. Cross-cultural Europe track
13. AI for Business track
14. Progress tracking
15. Error tracking
16. Personalized lesson generation

---

## 6. Основные режимы приложения

### 6.1. Режим Grammar Coach
Функции:
- объяснение правил по-русски;
- объяснение правил на простом английском;
- примеры;
- упражнения;
- проверка ответов;
- объяснение ошибок;
- генерация дополнительных упражнений по слабым местам.

### 6.2. Режим Speaking Partner
Функции:
- голосовой диалог;
- текстовый диалог;
- бытовые разговорные темы;
- свободные монологи;
- guided speaking;
- разбор ответа после диалога.

### 6.3. Режим Pronunciation Coach
Функции:
- работа со звуками;
- работа с минимальными парами;
- чтение вслух;
- shadowing;
- работа с ритмом и интонацией;
- спецрежим «уменьшение русского акцента».

### 6.4. Режим Listening Trainer
Функции:
- короткие аудио/реплики;
- понимание основной мысли;
- распознавание ключевых слов;
- пересказ;
- вопросы после аудио.

### 6.5. Режим Writing Coach
Функции:
- письма;
- короткие сообщения;
- self-introduction;
- ответы работодателю;
- учебные материалы;
- корректировка грамматики;
- улучшение естественности текста.

### 6.6. Режим Interview Trainer
Функции:
- собеседование в голосовом/текстовом формате;
- поведенческие вопросы;
- вопросы о мотивации;
- вопросы о сильных/слабых сторонах;
- вопросы о карьере;
- оценка ответа;
- улучшенная версия ответа.

### 6.7. Режим Professional English
Подрежимы:
- Insurance English
- Banking English
- Sales English
- Trainer English
- AI for Business English
- L&D / Enablement English

### 6.8. Режим Europe Knowledge
Подрежимы:
- Insurance in Europe
- Banking in Europe
- Consumer Protection
- EU Regulation Basics
- Country mindset / cross-cultural communication

### 6.9. Режим Lesson Builder
Функции:
- генерация персонального урока;
- подбор урока по слабым местам;
- сбор урока из grammar + speaking + profession + listening + pronunciation.

### 6.10. Режим Mini Training Simulator
Функции:
- пользователь проводит мини-тренинг на английском;
- ИИ оценивает структуру;
- ИИ оценивает ясность;
- ИИ оценивает лексику;
- ИИ оценивает тренерский стиль;
- ИИ даёт рекомендации.

---

## 7. Главные экраны приложения

### 7.1. Главный экран / Dashboard
Должен содержать:
- кнопку «Начать урок»;
- прогресс за день;
- текущий уровень;
- слабые места;
- рекомендованный следующий шаг;
- streak/серия дней;
- быстрые входы в режимы.

### 7.2. Экран Lesson Flow
- текущий урок;
- шаги урока;
- таймер;
- подсказки;
- переключение между блоками.

### 7.3. Экран Grammar
- список тем;
- прогресс по темам;
- объяснение;
- упражнения;
- ошибки по теме.

### 7.4. Экран Speaking
- сценарии разговора;
- кнопка микрофона;
- live transcript;
- исправления;
- replay ответа.

### 7.5. Экран Pronunciation
- список звуков;
- минимальные пары;
- shadowing;
- оценка произношения;
- карта проблемных звуков.

### 7.6. Экран Listening
- аудио;
- вопросы;
- проверка понимания;
- повтор проигрывания;
- замедление аудио.

### 7.7. Экран Writing
- поле редактора;
- проверка;
- объяснение ошибок;
- improved version;
- vocabulary suggestions.

### 7.8. Экран Profession
Разделы:
- страхование;
- банкинг;
- продажи;
- обучение;
- AI в работе;
- законы и регуляторика ЕС.

### 7.9. Экран Interview
- тип интервью;
- список вопросов;
- live mode;
- оценка ответов;
- сохранённые ответы.

### 7.10. Экран My Mistakes
Подразделы:
- grammar mistakes;
- pronunciation mistakes;
- vocabulary gaps;
- speaking issues;
- writing issues;
- profession gaps.

### 7.11. Экран Progress
- общий прогресс;
- прогресс по навыкам;
- прогресс по темам;
- weekly/monthly charts;
- карта сильных и слабых сторон.

### 7.12. Экран Settings
- язык интерфейса;
- язык объяснений;
- режим голоса;
- скорость речи;
- выбор AI-провайдера;
- режим локально/облако;
- сохранение аудио.

---

## 8. Структура одного урока

Каждый урок должен быть **модульным** и собираться из блоков.

### Базовый формат урока
1. Повтор ошибок прошлого урока
2. Новая тема / цель урока
3. Короткое объяснение
4. Практика grammar или vocabulary
5. Speaking block
6. Listening or pronunciation block
7. Professional block (если включён)
8. Итог
9. Сохранение ошибок и прогресса
10. План следующего шага

### Типы уроков
- Core lesson
- Grammar lesson
- Speaking lesson
- Pronunciation lesson
- Interview lesson
- Professional lesson
- Mixed lesson
- Recovery lesson по слабым местам

---

## 9. Логика обратной связи

### 9.1. Исправление ошибок
Система должна поддерживать 3 режима:
1. Исправлять сразу;
2. Исправлять после блока;
3. Исправлять только критичные ошибки.

### 9.2. Формат фидбека
После ответа пользователя нужно показывать:
- что хорошо;
- что неправильно;
- правильный вариант;
- короткое объяснение;
- более естественный вариант;
- 1–3 дополнительных упражнения или фразы.

### 9.3. Обязательный принцип
Фидбек не должен демотивировать. Даже в строгом режиме сначала коротко отмечать, что получилось.

---

## 10. Хранение прогресса

Система должна сохранять:
- пройденные уроки;
- темы;
- новые слова;
- грамматические ошибки;
- ошибки произношения;
- результаты speaking;
- результаты writing;
- интервью-ответы;
- профессиональные темы;
- voice recordings (опционально);
- preferred lesson style;
- streak и активность.

### 10.1. Модель прогресса
Прогресс должен считаться отдельно по направлениям:
- Grammar
- Speaking
- Listening
- Pronunciation
- Writing
- Vocabulary
- Interview
- Profession English
- Insurance EU
- Banking EU
- Regulation EU
- AI for Business

### 10.2. Экран слабых мест
Обязательный отдельный экран с автоматическим выводом:
- повторяющихся грамматических ошибок;
- забываемых слов;
- сложных тем;
- проблемных звуков;
- слабых профессиональных тем.

---

## 11. Профессиональный контент

### 11.1. Блок Insurance
Темы:
- страхование жизни;
- страховые продукты;
- needs analysis;
- objections;
- value communication;
- client conversations;
- insurance sales structure;
- customer protection.

### 11.2. Блок Banking
Темы:
- банковские продукты;
- deposits;
- payments;
- cards;
- bancassurance;
- financial conversations;
- retail banking basics.

### 11.3. Блок Trainer Skills
Темы:
- как строить тренинг;
- как объяснять сложное просто;
- как давать обратную связь;
- как тренировать продавцов;
- как тренировать кураторов/менеджеров;
- how to facilitate group learning;
- coaching language.

### 11.4. Блок EU Laws and Regulation
Темы:
- IDD basics;
- Solvency II basics;
- consumer protection;
- retail finance basics;
- compliance language;
- AI regulation overview;
- disclosure and suitability mindset.

### 11.5. Блок Cross-Cultural Europe
Темы:
- Germany;
- Ireland;
- Netherlands;
- Spain;
- Portugal;
- Cyprus;
- Malta;
- styles of communication;
- hierarchy vs informality;
- directness;
- meeting style;
- feedback style.

### 11.6. Блок AI for Business
Темы:
- AI in training;
- AI in sales enablement;
- AI in content creation;
- AI assistants;
- prompts;
- AI ethics and limitations;
- AI in business workflows.

---

## 12. Персонализация

Система должна учитывать:
- текущий уровень английского;
- цели пользователя;
- профессиональный трек;
- слабые места;
- комфортный стиль обучения;
- желаемый язык объяснений;
- желаемую длительность урока;
- акцентный профиль;
- приоритет speaking/grammar/profession.

---

## 13. MVP — с чего начать

Разработка должна идти поэтапно.

### MVP Phase 1
Собрать минимально рабочее ядро:

#### Функции MVP:
1. Dashboard
2. Grammar Coach (база)
3. Speaking Partner (текст + голос)
4. Pronunciation basics
5. Writing correction basics
6. Progress tracking basics
7. My Mistakes screen
8. Professional English basics
9. Local LLM integration
10. Lesson Builder v1

### В MVP не перегружать
Не надо сразу делать всё идеально. Но архитектура должна с первого дня поддерживать масштабирование.

---

## 14. Рекомендованная модульная структура проекта

```text
/app
  /frontend
    /src
      /app
      /pages
      /widgets
      /features
        /dashboard
        /lesson-runner
        /grammar
        /speaking
        /pronunciation
        /listening
        /writing
        /interview
        /profession
        /progress
        /mistakes
        /settings
      /entities
        /lesson
        /user
        /progress
        /mistake
        /vocabulary
        /profession-topic
      /shared
        /ui
        /lib
        /hooks
        /types
        /constants
        /utils
        /api
        /prompts
        /schemas

  /backend
    /app
      /api
      /core
      /db
      /models
      /schemas
      /services
        /lesson_service
        /grammar_service
        /speaking_service
        /pronunciation_service
        /listening_service
        /writing_service
        /interview_service
        /profession_service
        /progress_service
        /mistake_service
        /recommendation_service
      /providers
        /llm
        /stt
        /tts
        /scoring
      /prompts
      /content
      /utils
```

---

## 15. Базовые сущности данных

### UserProfile
- id
- name
- native_language
- current_level
- target_level
- profession_track
- preferred_ui_language
- preferred_explanation_language
- lesson_duration
- speaking_priority
- grammar_priority
- profession_priority

### Lesson
- id
- lesson_type
- goal
- modules
- difficulty
- duration
- completed
- score

### Mistake
- id
- category
- subtype
- source_module
- original_text
- corrected_text
- explanation
- repetition_count

### ProgressSnapshot
- id
- grammar_score
- speaking_score
- listening_score
- pronunciation_score
- writing_score
- profession_score
- regulation_score

### VocabularyItem
- id
- word
- translation
- context
- category
- learned_status
- repetition_stage

### ProfessionTopic
- id
- domain
- title
- difficulty
- content
- examples

---

## 16. Нефункциональные требования

1. Приложение должно работать локально.
2. Интерфейс должен быть быстрым и не перегруженным.
3. Должна быть поддержка русского UI.
4. Должно быть удобно постепенно переключаться на английский UI.
5. Все модули должны быть переиспользуемыми.
6. Все провайдеры должны быть заменяемыми.
7. Контент и промпты должны обновляться без переписывания UI.
8. Весь код должен быть готов к дальнейшему расширению.
9. Каждая feature должна быть тестируемой отдельно.
10. Нужна логика graceful degradation, если voice-модуль временно недоступен.

---

## 17. UX-принципы

1. Минимализм.
2. Один главный следующий шаг.
3. Не перегружать экран.
4. Не заставлять пользователя самому собирать маршрут.
5. Урок должен вести пользователя сам.
6. После каждого блока — маленькое ощущение прогресса.
7. Ошибки показывать понятно и не токсично.
8. Профессиональный трек должен быть встроен органично, а не как отдельный страшный раздел.

---

## 18. Что важно не допустить

- монолитную архитектуру;
- смешивание UI и AI-логики;
- жёсткую привязку к одному LLM-провайдеру;
- жёсткую привязку к одному voice-движку;
- хранение промптов прямо в React-компонентах;
- хранение учебной логики только на фронте;
- невозможность добавлять новые режимы;
- перегруженность интерфейса;
- зависимость от десятков внешних сервисов.

---

## 19. Следующий этап после этого ТЗ

После согласования данного документа следующим шагом надо сделать:

1. Product architecture map
2. User flow map
3. Screen map
4. ER-модель данных
5. Feature decomposition
6. MVP backlog
7. API contract
8. Prompt architecture
9. Local AI providers abstraction
10. UI wireframes

---

## 20. Приоритет следующего шага

**Следующим документом после этого ТЗ должен быть:**
### "Архитектура проекта + декомпозиция на модули и экраны"

Именно с этого нужно начинать разработку.

---

## 21. Архитектура проекта: верхнеуровневая схема

Система должна строиться по принципу разделения на 6 независимых слоёв:

1. **Presentation Layer** — экраны, страницы, UI-компоненты.
2. **Application Layer** — сценарии, lesson flow, orchestration.
3. **Domain Layer** — сущности, правила, бизнес-логика обучения.
4. **AI Layer** — LLM/STT/TTS/scoring/prompt orchestration.
5. **Data Layer** — локальная БД, user progress, mistakes, vocabulary.
6. **Content Layer** — учебные темы, сценарии, конфиги, уроки, профтемы.

### 21.1. Ключевой принцип
Ни один слой не должен напрямую хаотично обращаться ко всем остальным.
Взаимодействие должно идти через чёткие сервисы и интерфейсы.

### 21.2. Обязательное правило
React-компоненты не должны содержать сложную AI-логику.
AI-логика не должна жить внутри UI.
Учебная логика не должна быть размазана по кнопкам и страницам.

---

## 22. Декомпозиция на модули

Ниже — обязательные модули первой большой версии.

### 22.1. Core App Module
Отвечает за:
- инициализацию приложения;
- маршрутизацию;
- глобальные настройки;
- выбор языка UI;
- theme/config;
- bootstrapping user profile.

### 22.2. Dashboard Module
Отвечает за:
- главный экран;
- дневную задачу;
- быстрый старт урока;
- weekly summary;
- streak;
- рекомендации следующего шага.

### 22.3. Lesson Runner Module
Это центральный модуль приложения.

Отвечает за:
- запуск урока;
- порядок блоков;
- lesson pipeline;
- переключение между grammar/speaking/listening/profession/summary;
- lesson state;
- завершение урока;
- сохранение результатов.

### 22.4. Grammar Module
Отвечает за:
- темы грамматики;
- объяснения;
- типы упражнений;
- проверку ответов;
- генерацию дополнительных упражнений;
- grammar mistake tracking.

### 22.5. Vocabulary Module
Отвечает за:
- словарь;
- категории слов;
- активные/пассивные слова;
- интервальные повторения;
- слова по профессии;
- слова из ошибок пользователя.

### 22.6. Speaking Module
Отвечает за:
- guided speaking;
- free speaking;
- роль ИИ-партнёра;
- диалоги;
- монологи;
- speaking prompts;
- post-speaking feedback.

### 22.7. Pronunciation Module
Отвечает за:
- минимальные пары;
- произносительные тренировки;
- чтение вслух;
- shadowing;
- анализ проблемных звуков;
- accent reduction flow.

### 22.8. Listening Module
Отвечает за:
- короткие аудио;
- comprehension tasks;
- retelling;
- listening quizzes;
- контроль понимания речи.

### 22.9. Writing Module
Отвечает за:
- написание ответов;
- письма;
- мини-эссе;
- корректировку;
- improved version;
- объяснение ошибок.

### 22.10. Interview Module
Отвечает за:
- mock interviews;
- сценарии интервью;
- оценку ответов;
- типовые вопросы;
- сохранённые ответы;
- сравнение прошлых и текущих ответов.

### 22.11. Profession Module
Это контейнер для профессиональных подмодулей:
- Insurance Module
- Banking Module
- Trainer Skills Module
- AI for Business Module
- Regulation Module
- Cross-Cultural Module

### 22.12. Insurance Module
Отвечает за:
- English for insurance;
- life insurance vocabulary;
- sales of insurance products;
- customer conversation scenarios;
- objections;
- needs analysis.

### 22.13. Banking Module
Отвечает за:
- retail banking English;
- deposits/cards/payments vocabulary;
- bancassurance scenarios;
- banking conversation blocks.

### 22.14. Regulation Module
Отвечает за:
- IDD basics;
- Solvency II basics;
- consumer protection;
- EU finance regulation overview;
- compliance-oriented explanations.

### 22.15. Trainer Skills Module
Отвечает за:
- проведение тренингов;
- объяснение сложного простым языком;
- фасилитацию;
- feedback language;
- coaching language;
- trainer simulations.

### 22.16. AI for Business Module
Отвечает за:
- business AI vocabulary;
- сценарии использования AI;
- prompts;
- AI in training/sales/content;
- risk-aware explanation style.

### 22.17. Cross-Cultural Module
Отвечает за:
- культурные особенности стран Европы;
- стили коммуникации;
- feedback style;
- formality/informality;
- meeting style;
- working norms by country.

### 22.18. Progress Module
Отвечает за:
- прогресс по навыкам;
- weekly/monthly динамику;
- диаграммы;
- snapshots;
- lesson history.

### 22.19. Mistake Analytics Module
Отвечает за:
- сбор ошибок;
- группировку;
- частотность;
- weak spots;
- рекомендации на основе ошибок.

### 22.20. Recommendation Engine Module
Отвечает за:
- что дать пользователю дальше;
- какой урок предложить;
- какие темы повторить;
- какие ошибки закрывать в первую очередь.

### 22.21. User Profile Module
Отвечает за:
- настройки пользователя;
- цели;
- язык интерфейса;
- длительность урока;
- приоритеты;
- профессиональный трек.

### 22.22. AI Orchestrator Module
Ключевой backend-модуль.

Отвечает за:
- маршрутизацию в LLM;
- выбор prompt template;
- сбор контекста;
- вызов scoring;
- форматирование structured response.

### 22.23. Voice Module
Подмодули:
- STT bridge
- TTS bridge
- microphone input controller
- playback controller
- speech session state

### 22.24. Content Module
Отвечает за:
- хранение уроков;
- шаблоны сценариев;
- профессиональные тексты;
- словари;
- grammar topics;
- prompt configs;
- lesson configs.

---

## 23. Декомпозиция экранов

### 23.1. Главный пользовательский маршрут
Пользователь почти всегда идёт по цепочке:
**Dashboard → Recommended lesson → Lesson Runner → Summary → Mistakes/Progress**

### 23.2. Экранная карта MVP

#### Экран 1. Onboarding
Содержит:
- первичную диагностику;
- цель пользователя;
- уровень;
- приоритеты;
- длительность уроков;
- выбор профессии/трека;
- выбор языка объяснений.

#### Экран 2. Dashboard
Содержит:
- daily goal;
- recommended lesson;
- quick actions;
- weak spots;
- streak;
- progress summary.

#### Экран 3. Lesson Runner
Содержит:
- текущий шаг;
- таймер;
- lesson map;
- instructions;
- content block;
- submit/next/skip.

#### Экран 4. Grammar Center
Содержит:
- список grammar topics;
- статус по темам;
- упражнения;
- ошибки;
- recommended next grammar topic.

#### Экран 5. Speaking Studio
Содержит:
- speaking modes;
- темы;
- transcript;
- replay;
- feedback after answer.

#### Экран 6. Pronunciation Lab
Содержит:
- sounds;
- word drills;
- phrase drills;
- shadowing mode;
- accent profile.

#### Экран 7. Listening Room
Содержит:
- аудио;
- задания;
- повтор;
- slow mode;
- retell mode.

#### Экран 8. Writing Desk
Содержит:
- editor;
- check button;
- mistakes;
- improved version;
- explanation.

#### Экран 9. Interview Simulator
Содержит:
- тип интервью;
- start mock interview;
- saved answers;
- scored responses;
- improvement suggestions.

#### Экран 10. Profession Hub
Содержит карточки:
- Insurance English
- Banking English
- Regulation EU
- Trainer Skills
- AI for Business
- Cross-Cultural Europe

#### Экран 11. My Mistakes
Содержит вкладки:
- Grammar
- Speaking
- Pronunciation
- Writing
- Vocabulary
- Profession

#### Экран 12. Progress
Содержит:
- уровни по навыкам;
- динамику;
- lesson history;
- charts;
- confidence indicators.

#### Экран 13. Settings
Содержит:
- voice settings;
- LLM provider settings;
- UI language;
- explanation language;
- lesson duration;
- privacy/storage.

---

## 24. User Flow Map

### 24.1. Первый запуск
1. Пользователь открывает приложение.
2. Проходит onboarding.
3. Система создаёт user profile.
4. Система определяет стартовый маршрут.
5. Пользователь попадает на Dashboard.

### 24.2. Ежедневный сценарий
1. Dashboard показывает recommended lesson.
2. Пользователь запускает урок.
3. Lesson Runner проходит через 3–6 блоков.
4. После урока показывается summary.
5. Ошибки сохраняются.
6. Recommendation Engine подбирает следующий шаг.

### 24.3. Свободный сценарий
1. Пользователь заходит в любой модуль отдельно.
2. Выбирает тему/режим.
3. Работает точечно.
4. Результаты всё равно сохраняются в общий progress.

---

## 25. MVP-декомпозиция по фазам

### 25.1. MVP Phase 1 — обязательный старт
Нужно реализовать:
- Onboarding
- Dashboard
- Lesson Runner
- Grammar Module v1
- Speaking Module v1
- Pronunciation Module v1
- Writing Module v1
- Progress Module v1
- My Mistakes Module v1
- Profession Hub v1
- AI Orchestrator v1
- Local LLM provider v1

### 25.2. MVP Phase 2
Добавить:
- Listening Module
- Interview Module
- Regulation Module
- Trainer Skills Module
- Vocabulary repetition engine
- Recommendation Engine v2
- Voice analytics improvements

### 25.3. MVP Phase 3
Добавить:
- полноценный Mini Training Simulator
- adaptive curriculum;
- advanced scoring;
- country-specific professional paths;
- export/import progress;
- cloud sync optional.

---

## 26. Декомпозиция backend-слоя

### 26.1. API layer
Эндпоинты по группам:
- auth/profile
- lessons
- grammar
- speaking
- pronunciation
- writing
- listening
- interview
- profession
- progress
- mistakes
- recommendations
- providers

### 26.2. Service layer
Каждый модуль должен иметь свой сервис.
Примеры:
- `grammar_service`
- `speaking_service`
- `pronunciation_service`
- `lesson_service`
- `progress_service`
- `recommendation_service`
- `profession_service`

### 26.3. Provider layer
Все внешние/локальные AI-компоненты подключать через интерфейсы.

Обязательные интерфейсы:
- `BaseLLMProvider`
- `BaseSTTProvider`
- `BaseTTSProvider`
- `BaseScoringProvider`

### 26.4. Prompt layer
Промпты хранить отдельно и типизировать.
Разделить на группы:
- grammar prompts
- speaking prompts
- interview prompts
- pronunciation prompts
- profession prompts
- correction prompts
- scoring prompts

---

## 27. Декомпозиция frontend-слоя

### 27.1. App shell
- роутинг;
- layout;
- sidebar/topbar;
- notifications;
- modals.

### 27.2. Feature-first структура
Каждая feature имеет:
- `components/`
- `hooks/`
- `services/`
- `store/`
- `types/`
- `utils/`
- `config/`

### 27.3. Общие UI-компоненты
Вынести отдельно:
- Button
- Card
- Tabs
- ProgressBar
- AudioControls
- TranscriptView
- FeedbackPanel
- ErrorList
- LessonStepper
- ScoreBadge
- ModuleHeader

---

## 28. Декомпозиция lesson engine

Lesson Engine — один из самых важных модулей.

Он должен уметь собирать урок из блоков.

### 28.1. Базовые типы lesson blocks
- intro_block
- review_block
- grammar_block
- vocab_block
- speaking_block
- pronunciation_block
- listening_block
- writing_block
- profession_block
- reflection_block
- summary_block

### 28.2. Принцип сборки урока
Lesson Builder должен собирать урок на основе:
- текущего уровня;
- приоритетов пользователя;
- прошлых ошибок;
- длительности урока;
- active professional track.

### 28.3. Формат lesson config
Урок должен быть описываем конфигом, а не вручную прошит в коде.

---

## 29. Что отдавать кодеру сразу после этого документа

Следующий комплект документов для старта разработки:

1. Screen map
2. Folder structure
3. Entity/data model
4. Feature backlog with priorities
5. API contract draft
6. Prompt contract draft
7. Lesson block schema
8. Provider interfaces
9. UX wireframes
10. MVP acceptance criteria

---

## 30. Следующий обязательный документ

После этой декомпозиции следующим документом нужно сделать:
### **ER-модель данных + JSON-схемы сущностей + схема lesson blocks**

Именно это даст кодеру возможность начать backend и storage-архитектуру без хаоса.

