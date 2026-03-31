# Product Roadmap

## Current Product State

Уже работает локальный fullstack-тренажёр с персональным профилем, dashboard, adaptive loop, lesson runner, speaking, writing, pronunciation, vocabulary, progress и professional tracks.

Что уже можно считать настоящей базой продукта:

- профиль влияет на рекомендации, quick actions и выбор lesson template;
- есть сохранение истории уроков, speaking attempts, writing attempts, pronunciation checks и vocabulary review;
- есть fallback-цепочка для LLM/STT/TTS, чтобы приложение не разваливалось при локальной разработке;
- интерфейс поддерживает `RU / EN`;
- professional tracks уже разведены на отдельные домены: `trainer_skills`, `insurance`, `banking`, `ai_business`.

## Near-Term Cleanup

Ближайший практический фокус перед крупным редизайном онбординга:

1. Убрать оставшиеся seed/demo-хвосты из activity, progress и dashboard copy.
2. Довести adaptive text generation до полностью product-facing подачи без developer-лексики.
3. Подчистить старые dead fixtures и legacy mock artifacts, которые больше не участвуют в runtime.
4. Усилить profile-driven логику для history, progress snapshots и lesson recommendations.

## Next-Gen Onboarding Vision

Цель: сделать современный, многошаговый онбординг, который не просто сохраняет профиль, а собирает качественный learning blueprint для любого будущего пользователя.

Онбординг должен:

- быстро объяснять ценность продукта и не перегружать пользователя на первом экране;
- собирать достаточно данных, чтобы строить сильный стартовый трек по grammar, reading, vocabulary, speaking, writing и profession English;
- быть пригодным для дальнейшей монетизации: reusable для разных сегментов пользователей, с понятным профилем, историей ответов и возможностью premium personalization;
- закладывать основу для multi-user сценария, а не быть заточенным только под одного локального пользователя.
- одинаково хорошо подходить для взрослых, подростков, детей, семейного сценария и parent-guided use case, а не только для professional audience.
- поддерживать не только рабочие цели, но и school support, exams, relocation, travel, general communication и long-tail личные запросы.

## Onboarding Question Line

Рекомендуемая линейка вопросов:

1. `Identity`
   Имя, язык интерфейса, язык объяснений, страна/часовой пояс при необходимости.
2. `Goal`
   Для чего нужен английский: работа, собеседования, переговоры, daily communication, career growth, certification.
3. `Target outcome`
   Желаемый уровень и желаемый practical outcome на горизонте 1-3 месяцев.
4. `Professional context`
   Сфера, роль, тип задач, рабочие сценарии, кто собеседник: клиенты, коллеги, менеджеры, кандидаты, команды. Для non-professional use case здесь нужен универсальный content lane: general English, school-safe conversation, travel, family, relocation.
5. `Skill self-rating`
   Самооценка по grammar, reading, vocabulary, speaking, listening, pronunciation, writing.
6. `Confidence and blockers`
   Где сложнее всего: времена, словарь, скорость речи, понимание аудио, small talk, письма, созвоны, чтение документов.
7. `Learner setup`
   Кто учится: сам пользователь, ребёнок, подросток, семейный аккаунт, parent-guided сценарий, adult career learner.
8. `Input preferences`
   Как удобнее учиться: короткие daily sessions, длинные deep-work sessions, voice-first, text-first, mixed.
9. `Time budget`
   Длительность уроков, частота в неделю, preferred session windows.
10. `Diagnostic readiness`
   Готов ли пользователь пройти короткий стартовый checkpoint сейчас или хочет начать мягко.
11. `Content preference`
   Больше general English, profession English, reading-heavy, speaking-heavy, vocabulary-heavy или balanced plan.
12. `Support profile`
   Нужны ли gentle feedback, more repetition, slower pace, visual structure, child-safe wording или parent notes.

## How Answers Should Drive the Track

Ответы из онбординга должны напрямую влиять на систему:

- `grammar`
  Вес grammar topics, тип recovery drills, глубина rule explanations.
- `reading`
  Подбор reading blocks, длина текстов, тип comprehension questions, business vs general reading.
- `vocabulary`
  Домены словаря, скорость повторения, объём новых слов, связь с mistake map.
- `speaking`
  Тип speaking scenarios, voice-first or text-first flow, приоритет обратной связи по fluency/accuracy/confidence.
- `writing`
  Тип writing tasks: emails, updates, summaries, client replies, structured opinions.
- `profession`
  Выбор track-specific content, roleplay direction, topic bank и client-facing language.
- `adaptive loop`
  Начальный focus area, threshold для recovery lessons, next-step rotation и quick actions.
- `family and child mode`
  Мягкость формулировок, длина сессий, допустимые темы, parent-guided framing и безопасный стартовый workload.

## Delivery Plan

### Phase 1. Product Onboarding Flow

- новый route-level onboarding flow с progress bar и step navigation;
- 8-10 экранов вместо одной формы;
- draft save между шагами;
- summary screen перед финальным сохранением;
- mobile-safe и desktop-first presentation.
- отдельный `onboarding_answers` слой в профиле, чтобы можно было хранить гибкие ответы без поломки текущего lesson engine.

### Phase 2. Learning Blueprint Engine

- вычисление стартового learner profile из ответов;
- генерация стартовых priorities по grammar/reading/vocabulary/speaking/writing;
- формирование стартового diagnostic mode:
  мягкий старт или checkpoint-first;
- стартовый profession pack и initial vocabulary pack.
- универсальный `general communication` lane для тех, кому не нужен pure professional track.

### Phase 3. Monetization Readiness

- несколько onboarding presets для разных user segments;
- платные deeper diagnostics и richer track personalization;
- сегментация free vs premium generation depth;
- хранение onboarding answers как отдельной сущности, пригодной для аналитики и повторного запуска.

## Implementation Notes

Для этого онбординга почти наверняка понадобятся новые сущности:

- `onboarding_session`
- `onboarding_answer`
- `learner_goal_profile`
- `skill_self_assessment`
- `content_preference_profile`

И новые сервисы:

- `OnboardingFlowService`
- `TrackPlannerService`
- `InitialDiagnosticPlannerService`

## Success Criteria

Будем считать новый онбординг сильным, если после его прохождения:

- пользователь видит понятный персональный learning plan уже на первом dashboard;
- lesson flow ощущается логичным именно для его целей, а не как generic demo;
- стартовый track заметно отличается для разных ролей и skill profiles;
- ответы реально влияют на grammar, reading, vocabulary и speaking rotation;
- продукт выглядит готовым не только для локального MVP, но и для реального масштабирования.
