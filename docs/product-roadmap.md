# Product Roadmap

## Current Product State

Уже работает локальный fullstack-тренажёр с персональным профилем, dashboard, adaptive loop, lesson runner, speaking, writing, pronunciation, vocabulary, progress и professional tracks.

Что уже можно считать настоящей базой продукта:

- есть welcome/proof lesson с голосом Лизы, pronunciation check и handoff в onboarding;
- onboarding уже реализован как короткий многошаговый flow с account layer, review step, persistent draft save и сохранением `onboarding_answers`;
- dashboard собирает recommendation, diagnostic roadmap, adaptive loop, quick actions, daily loop plan и resume/recovery lesson state;
- dashboard теперь также отдаёт `journey_state`, чтобы ключевые экраны могли объяснять текущую стратегию и next-best-action из одного источника;
- `journey_state.strategy_snapshot` теперь также хранит `sessionSummary`, `tomorrowPreview` и completed-lesson signal после завершения daily loop;
- grammar, vocabulary, speaking, pronunciation, writing, profession, progress, activity и settings работают как отдельные продуктовые поверхности поверх общей persistence-модели;
- `Liza layer` уже покрывает `dashboard`, `daily loop`, `grammar`, `vocabulary`, `pronunciation`, `writing`, `speaking`, `progress`, `activity`, `settings`, `lesson results`;
- на ключевых экранах появились interactive explain-actions: `объясни проще`, `почему это важно`, `что важнее всего`, `следующий лучший шаг`;
- dashboard получил мягкий `re-entry` слой: если маршрут ещё не начат, пользователь видит явный prompt на возврат; если маршрут завершён, видит `tomorrow preview`;
- shell-level `JourneyReentryPrompt` теперь дотягивает continuity и до вторичных экранов: можно вернуться к активной session, стартовать today route или открыть tomorrow-state через dashboard;
- live avatar WebRTC + fallback render уже подняты как отдельный runtime slice;
- профиль влияет на рекомендации, quick actions и выбор lesson template;
- есть сохранение истории уроков, speaking attempts, writing attempts, pronunciation checks и vocabulary review;
- есть отдельный journey-layer для `proof lesson -> onboarding -> daily loop`: `onboarding_sessions`, `learner_journey_states`, `daily_loop_plans`;
- есть fallback-цепочка для LLM/STT/TTS, чтобы приложение не разваливалось при локальной разработке;
- интерфейс поддерживает `RU / EN`;
- professional tracks уже разведены на отдельные домены: `trainer_skills`, `insurance`, `banking`, `ai_business`.

## Execution Checkpoint - 2026-04-13

Сейчас продукт находится между поздней `Phase 2` и ранней `Phase 3` roadmap:

- `Phase 1. Product Onboarding Flow` - по сути закрыта для первого сильного пути: есть route-level flow, step navigation, review step, handoff из proof lesson, persistent draft save и отдельное хранение onboarding answers.
- `Phase 2. Learning Blueprint Engine` - продвинулась: профиль уже влияет на recommendation, dashboard, diagnostic roadmap, adaptive loop, recovery lessons и первый persisted daily loop plan, но стартовый blueprint ещё не оформлен как отдельная прозрачная сущность.
- `Phase 3. Monetization Readiness` - архитектурно не начата: есть user/onboarding persistence, но нет сегментных presets, free/premium depth и аналитического слоя повторного запуска.

## Current Practical Focus

Ближайший практический фокус после завершения first-path stage:

1. Убрать оставшиеся seed/demo-хвосты из activity, progress, dashboard copy и vocabulary metadata.
2. Дотянуть Global Liza Layer до `speaking`, `progress`, `activity`, `settings` и `lesson results`, чтобы после onboarding всё ещё ощущалось как одно приложение с одним наставником.
3. Превратить текущий persisted daily loop plan в более сильный session ritual с обязательным `session summary` и более явным `next best action`.
4. Начать обновлять learner strategy model после результатов session не только через историю уроков, но и через отдельный explainable strategy snapshot.
5. Подготовить retention-слой: resume session, continuity signals и мягкие re-entry prompts без тяжёлой геймификации.

Прогресс на `2026-04-13` после следующего execution slice:

- Global Liza Layer уже существенно усилена на ключевых экранах;
- guidance на screens now опирается на persisted `journey_state`, а не только на локальную copy;
- `lesson results` и `daily loop` теперь лучше закрывают вопрос `что произошло -> почему это важно -> что делать дальше`;
- после завершения daily loop система уже умеет показывать `tomorrow preview`, а не только общий completion state.
- dashboard уже начинает работать как re-entry point, а не только как summary page.
- continuity теперь не привязана только к dashboard: shell reminder сохраняет маршрут заметным на `progress`, `activity`, `speaking`, `settings` и других вторичных экранах.
- post-session continuity теперь опирается на persisted `sessionSummary`, поэтому `lesson results`, `dashboard` и `daily loop` объясняют один и тот же strategy shift, а не три разные локальные интерпретации.
- persisted `tomorrowPreview` теперь начинает влиять и на реальный next-day `daily_loop_plan`: новый день может подхватывать carry-over signal, watch signal и next-step hint из вчерашнего результата.
- continuity seed теперь доходит и до самого `lesson run`: для next-day recommended session создаётся continuity-aware template overlay, а `lesson runner` показывает carry/watch context прямо внутри блока.
- dashboard теперь всё явнее становится route-first surface: главный CTA, hero и adaptive section ведут в `today's route`, а `route intelligence` уже выведен в dashboard, activity и progress.
- `activity` и `progress` теперь тоже перестают быть competing entry points: их главный CTA и guidance сначала возвращают в `today's route`, если она уже собрана, и только потом ведут в recovery/checkpoint.
- recommended `daily loop` теперь стартует через guided-route template overlay: сами lesson blocks получают `routeContext`, `why now`, `preferred mode`, active skill focus и weaker signals прямо внутри run-а, а не только на окружающих экранах.
- guided route теперь влияет и на сам block composition: route может добавить support `vocab` / `listening` blocks и перевести response в `writing_block` для `text_first`, если это лучше соответствует текущему маршруту.

## Keep As Is

Что в продуктовой стратегии сохраняем без пересборки:

- центральную идею `one AI companion + one strategy + one connected learning loop`;
- Лизу как системный слой, а не как декоративную фичу;
- proof lesson как главный wow-вход;
- основной маршрут `proof lesson -> onboarding -> dashboard -> daily loop`;
- explainable personalization как обязательную часть premium-опыта.

## Freeze For Now

Что сознательно не расширяем в ближайшем execution cycle:

- family / child / parent-guided expansion как отдельный большой сегмент;
- social layer, speaking rooms и кооперативные режимы;
- тяжёлую геймификацию с XP, валютами, badge chains и unlock loops;
- отдельные большие ветки `exam / relocation / travel / work`;
- длинный first-entry onboarding;
- форсированное расширение listening/reading verticals до того, как daily loop станет привычкой.

## Next-Gen Onboarding Vision

Цель: сделать современный, короткий и убедительный онбординг, который не просто сохраняет профиль, а собирает качественный стартовый learning blueprint без ощущения длинного интервью.

Онбординг должен:

- быстро объяснять ценность продукта и не перегружать пользователя на первом экране;
- собирать достаточно данных, чтобы строить сильный стартовый трек по grammar, reading, vocabulary, speaking, writing и profession English;
- в первом сильном продукте быть оптимизированным под взрослого learner, а не под все сегменты одновременно;
- быть пригодным для дальнейшей монетизации: reusable для разных сегментов пользователей, с понятным профилем, историей ответов и возможностью premium personalization;
- позволять переносить часть вопросов в мягкое доуточнение после первого dashboard;
- поддерживать рабочие и general communication goals без разведения продукта на много тяжёлых стартовых веток.

## Onboarding Question Line

Рекомендуемая линейка вопросов для полного профиля:

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

Для первого входа обязательными должны оставаться только:

1. `Goal`
2. `Current level / self-rating`
3. `Preferred mode`
4. `Time budget`
5. `Diagnostic readiness`

Все остальные сигналы лучше собирать после первого dashboard и внутри первых daily sessions.

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

Статус на `2026-04-13`: materially implemented для первого сильного пути.

- новый route-level onboarding flow с progress bar и step navigation;
- короткий onboarding вместо длинного интервью;
- draft save между шагами и перезагрузками;
- summary screen перед финальным сохранением;
- mobile-safe и desktop-first presentation.
- отдельный `onboarding_answers` слой в профиле, чтобы можно было хранить гибкие ответы без поломки текущего lesson engine.
- handoff из proof lesson в onboarding session и дальше в first dashboard.

Ближайшая корректировка:

- убрать последние copy/demo-хвосты;
- усилить объяснение следующего шага сразу после завершения onboarding;
- зафиксировать post-onboarding mini-prompts как отдельный контур доуточнения профиля.

### Phase 2. Learning Blueprint Engine

Статус на `2026-04-13`: частично реализована через recommendation, adaptive loop, diagnostic roadmap, recovery lessons и первый persisted daily loop plan, но ещё не оформлена как отдельный explainable blueprint engine.

- вычисление стартового learner profile из ответов;
- генерация стартовых priorities по grammar/reading/vocabulary/speaking/writing;
- формирование стартового diagnostic mode:
  мягкий старт или checkpoint-first;
- стартовый profession pack и initial vocabulary pack.
- универсальный `general communication` lane для тех, кому не нужен pure professional track.

### Phase 3. Monetization Readiness

Статус на `2026-04-13`: как отдельный product layer ещё не начата.

- несколько onboarding presets для разных user segments;
- платные deeper diagnostics и richer track personalization;
- сегментация free vs premium generation depth;
- хранение onboarding answers как отдельной сущности, пригодной для аналитики и повторного запуска.

## Implementation Notes

Для первого полного пути уже используются следующие сущности:

- `users` для identity layer;
- `user_profiles` для боевого learner profile;
- `user_onboarding` для завершённого onboarding snapshot;
- `onboarding_sessions` для draft + proof lesson handoff;
- `learner_journey_states` для текущего stage и next-best-action;
- `daily_loop_plans` для explainable daily plan.

Ключевые сервисы этого слоя:

- `OnboardingService`;
- `JourneyService`;
- `RecommendationService`;
- `LessonRuntimeService`.

## Success Criteria

Будем считать новый онбординг сильным, если после его прохождения:

- пользователь видит понятный персональный learning plan уже на первом dashboard;
- lesson flow ощущается логичным именно для его целей, а не как generic demo;
- стартовый track заметно отличается для разных ролей и skill profiles;
- ответы реально влияют на grammar, reading, vocabulary и speaking rotation;
- продукт выглядит готовым не только для локального MVP, но и для реального масштабирования.

## Next 3 Sprints

### Sprint 1. One Connected First Path

Главная цель: сделать так, чтобы путь `proof lesson -> onboarding -> dashboard -> daily loop` ощущался как один сценарий.

Фокус:

1. Довести до идеала связку `proof lesson -> handoff -> onboarding finish -> first personal dashboard`.
2. Сократить обязательный onboarding до минимума: goal, current level, preferred mode, time budget, diagnostic readiness.
3. Вынести остальные вопросы в мягкое уточнение позже через dashboard и mini-prompts от Лизы.
4. Добавить persistent draft save.
5. Убрать seed/demo-хвосты из copy, activity, progress и vocabulary metadata.

Статус на `2026-04-13`: core slice уже реализован. Следующий шаг внутри этого спринта не расширять маршрут, а polish-ить copy, Liza handoff и post-onboarding continuity.

### Sprint 2. Real Global Liza Layer

Главная цель: сделать приложение одной системой с одним наставником.

Фокус:

1. Дотянуть Liza layer до `speaking`, `progress`, `activity`, `settings`, `lesson results`.
2. На каждом ключевом экране отвечать на три вопроса: что сейчас происходит, почему это важно именно тебе, что делать дальше.
3. Укрепить единый паттерн `full presence` vs `ambient presence`.
4. Добавить explain-actions: `объясни проще`, `почему мне дали именно это`, `что мне сейчас важнее всего`, `следующий лучший шаг`.

Статус на `2026-04-13`: materially in progress. Базовый coach-presence и explainable guidance уже дотянуты до `speaking`, `progress`, `activity`, `settings`, `lesson results`, но ещё нужно превратить этот слой из сильной UI-системы в более интерактивный conversational layer.

Дополнительный прогресс на `2026-04-13`:

- explain-actions уже существуют как reusable interactive pattern;
- dashboard, daily loop и lesson results показывают более явный continuity between today-state and tomorrow-state;
- следующий шаг теперь можно объяснять не только статическим текстом, но и через persisted strategy snapshot.

### Sprint 3. Daily Loop Skeleton

Главная цель: превратить продукт из сильного входа в ежедневный ритуал.

Фокус:

1. Канонизировать структуру daily session: warm start, vocabulary recall, grammar pattern, listening/reading input, speaking/writing response, pronunciation micro-fix, reinforcement, strategic summary.
2. Сделать session summary обязательной частью опыта.
3. Явно обновлять learner model после session outcomes, а не только складывать историю.
4. Показать пользователю, как меняется его следующий шаг после каждой сессии.
5. Добавить лёгкий retention layer: resume session, next best action, мягкое напоминание о незавершённой траектории.

Статус на `2026-04-14`: retention slice уже перешёл из purely explainable в partially behavioral. `dashboard`, `AppShell`, `activity` и `progress` умеют возвращать пользователя в маршрут, завершённая session формирует persisted `sessionSummary` и richer `tomorrowPreview`, новый день уже может строить `daily_loop_plan` из этого continuity seed, recommended lesson run запускается через guided-route overlay, а сам route уже начал влиять на block composition; следующий шаг здесь сделать adaptive rotation и content mix ещё точнее согласованными с learner strategy уже не на уровне нескольких эвристик, а как более цельный composition engine.
