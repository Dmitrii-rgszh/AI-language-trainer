# Product Roadmap

## Current Product State

Уже работает локальный fullstack-тренажёр с персональным профилем, dashboard, adaptive loop, lesson runner, speaking, writing, pronunciation, vocabulary, progress и professional tracks.

Что уже можно считать настоящей базой продукта:

- есть welcome/proof lesson с голосом Лизы, pronunciation check и handoff в onboarding;
- onboarding уже реализован как короткий многошаговый flow с account layer, review step, persistent draft save и сохранением `onboarding_answers`;
- dashboard собирает recommendation, diagnostic roadmap, adaptive loop, quick actions, daily loop plan и resume/recovery lesson state;
- dashboard теперь также отдаёт `journey_state`, чтобы ключевые экраны могли объяснять текущую стратегию и next-best-action из одного источника;
- `journey_state.strategy_snapshot` теперь также хранит `sessionSummary`, `tomorrowPreview` и completed-lesson signal после завершения daily loop;
- `journey_state.strategy_snapshot` теперь также может хранить `skillTrajectory`, то есть короткую multi-day memory по skill-verticals из последних progress snapshots;
- поверх этого `journey_state.strategy_snapshot` теперь также хранит `strategyMemory`, то есть более длинный 5-snapshot signal о persistent / recurring / emerging pressure по skill-verticals;
- `journey_state.strategy_snapshot` теперь также хранит `routeCadenceMemory`, чтобы маршрут учитывал не только skill-pressure, но и то, как стабильно пользователь возвращается в daily ritual;
- поверх cadence и longer-memory `journey_state.strategy_snapshot` теперь также хранит `routeRecoveryMemory`, чтобы система вела пользователя не только через один re-entry, а через короткую multi-day recovery arc на 2-3 маршрута вперёд;
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
- `Phase 2. Learning Blueprint Engine` - уже materially built как отдельный слой: `learningBlueprint` теперь persistится в `journey_state.strategy_snapshot`, собирается из onboarding/profile + learner memory + recovery/re-entry signals, показывается на dashboard как explainable personal strategy и доезжает до guided lesson context.
- `Unified Daily Learning Ritual` - уже formalized как отдельный execution layer поверх `daily_loop_plan`: ritual имеет собственные stages / completion rule / closure rule, показывается на dashboard и daily loop, доезжает до guided lesson context и начинает закрывать `lesson runner -> results` как один канонический daily scenario. Поверх этого ritual уже начал вбирать и `You & English` методы: `daily word journal` теперь существует как persisted vocabulary capture, а promise ритуала уже может явно держать этот живой phrase-capture внутри маршрута.
- `Spontaneous voice ritual` теперь тоже начал жить внутри того же слоя: в speaking появился отдельный `Highlight / Lowlight Reflection` pass, который можно делать текстом или голосом, он сохраняется в speaking history и поддерживает идею route-first живого daily ritual вместо isolated drill.
- Эти `You & English` ритуалы уже начинают влиять и на backend decision layer: `word journal` и `spontaneous voice` могут регистрироваться как persisted `ritual signals` в `journey_state`, после чего recommendation и ближайший route focus умеют подхватывать их как короткое 1-2 session окно.
- следующий шаг в этом же слое уже включён: `ritual signals` теперь доезжают и до самого `daily_loop_plan` плюс guided lesson composition, так что ближайшие 1-2 сессии могут реально собираться как relationship-aware ritual arc. Это уже меняет `headline / summary / why this now / next best action` и поднимает `vocabulary/writing` или `speaking/pronunciation` внутри `practice mix` следующего guided route.
- следующий слой над этим тоже уже включён: `ritualSignalMemory` перестал быть только “свежим capture-флагом” и начал жить как короткое multi-day окно `capture -> reuse -> carry forward`. Это даёт системе возможность не только поднимать один следующий день, но и осознанно проводить живой phrase/voice signal через 2-3 ближайших route decisions.
- дополнительно этот ritual-window уже перестал быть purely descriptive: стадия `ready_to_carry` теперь реально ослабляет принудительный ritual-focus в recommendation и guided `practice mix`, чтобы broader lesson route снова вёл день, а `word journal / spontaneous voice` оставались живыми support-lanes внутри него.
- следующий слой над этим тоже уже включён: ritual-дуга теперь живёт как route-shaped mini-program `protect_ritual -> reuse_in_response -> carry_inside_route`, который доезжает до `daily_loop_plan`, `next step`, route context и самого shape шагов дня.
- поверх этого UI route surfaces уже тоже понимают этот ritual-window: `dashboard`, `daily loop`, `route intelligence` и `lesson runner` теперь могут явно показать, это сейчас protected ritual pass, connected reuse или quiet carry-inside-route.
- следующий навигационный слой тоже уже собран: ritual-window влияет на `quick actions`, shell smart entry, `AppTopRail` ordering и `route governance`, так что в `protect ritual` продукт раньше поднимает ritual-entry, а в `carry inside route` мягко возвращает пользователя к более широкому daily route уже на уровне CTA и navigation bias.
- поверх этого уже выровнен и `route follow-up` слой: после ritual-support completion handoff корректно показывает именно следующий connected step, а не дублирует текущую surface, и умеет собирать ritual-aware fallback transition даже когда persisted follow-up ещё минимален.
- теперь это поддержано и на backend: `routeFollowUpMemory` для ritual-window хранит не только ближайший шаг, но и более явный `broader carry` ход, а после completed ritual reuse-pass пересобирается из нового ritual stage, чтобы relationship-aware мини-дуга была заранее зашита в стратегию следующих шагов.
- поверх этого уже дотянут и UI handoff-surfaces: `dashboard hero`, `lesson results`, `lesson runner` launch bridge и shell `route entry notice` умеют показывать трёхшаговую continuity-линию `Now -> Then -> Carry`, когда такая дуга реально есть в стратегии.
- следующий важный шаг теперь тоже начат: философия `You & English` перестаёт жить только в новых ritual/path слоях и начинает перепрошивать существующие инструменты. Для `grammar / vocabulary / speaking / pronunciation / writing / reading / listening / progress` уже появился общий relationship-aware lens со сдвигом success criteria и pressure-release framing.
- следующий UI continuity-слой теперь тоже закрыт: `dashboard route continuity`, `route intelligence` и `shell re-entry prompt` тоже умеют показывать этот третий `Carry` ход, так что relationship-aware follow-up больше не живёт только в hero/results, а читается и в повторном входе, и в explainable strategy surfaces.
- поверх этого окно уже стало completion-driven: post-lesson evaluation теперь умеет продвигать, удерживать или закрывать `ritual window` по качеству самого reuse-pass, а `tomorrowPreview` уже различает `ritual_capture / ritual_reuse / ritual_carry / ritual_close`.
- `Phase 3. Monetization Readiness` - архитектурно не начата: есть user/onboarding persistence, но нет сегментных presets, free/premium depth и аналитического слоя повторного запуска.

## Strong Function Audit - 2026-04-19

После повторной сверки roadmap и master plan видно, что у продукта уже есть сильный skeleton, но ещё не все сильные функции дошли до `serious test ready`.

### Уже реально сильные и materially implemented

- `Proof lesson` как flagship entrance:
  есть voice-first flow, correction, retry, pronunciation layer и handoff в onboarding.
- `Connected first path`:
  `proof lesson -> onboarding -> dashboard -> daily loop / lesson runner -> lesson results -> updated dashboard` уже работает как связанный маршрут, а не как набор разрозненных экранов.
- `Global Liza layer` как продуктовый слой:
  guidance, explain-actions, continuity hints и route-entry/re-entry объяснения уже протянуты через основные экраны.
- `Route-first dashboard and continuity`:
  dashboard, activity, progress, shell re-entry и results уже подчинены одному main route.
- `Learner memory + route orchestration`:
  `sessionSummary`, `tomorrowPreview`, `skillTrajectory`, `strategyMemory`, `routeCadenceMemory`, `routeRecoveryMemory`, `routeReentryProgress`, `routeEntryMemory`, `routeFollowUpMemory`.
- `Adaptive guided lesson composition`:
  lesson engine уже умеет подхватывать route context, practice mix, support-step sequencing и recovery/widening logic.
- `Task-driven mission contract`:
  `daily_loop_plan` теперь может не только фронтово намекать на `reading/listening` вход, но и реально нести backend-level `taskDrivenInput`, который доезжает до guided lesson context и делает input-first миссию частью самого маршрута.
  Completion таких `reading/listening` mini-missions теперь тоже persistится в `journey_state`: backend переводит маршрут в response-step и обновляет `routeFollowUpMemory / next_best_action`, так что следующие 1-2 route decisions уже читают этот handoff как часть общей оркестрации.
  Плюс этот `task-driven handoff` теперь не теряется сразу на route-entry: он переживает вход в response-surface, поднимает `focus_area` следующего daily plan и смещает guided `practice mix` в сторону `input -> response` дуги.
  Поверх этого post-lesson `sessionSummary` и `tomorrowPreview` теперь уже оценивают и качество самого переноса `input -> response`: маршрут различает, когда reading/listening сигнал реально удержался в writing/speaking, а когда transfer ещё хрупкий и response-lane нужно защищать ещё один день.
  Следующий слой уже тоже включён: recommendation engine и guided `practice mix` теперь прямо читают этот `task-driven transfer evaluation`, так что после хрупкого `reading -> writing` или `listening -> speaking` переноса система не только пишет более честный tomorrow-preview, но и реально поднимает response-lane в следующем recommendation и составе ближайшей guided session.
  И ещё глубже: fragile/usable transfer теперь уже разворачивается в короткое backend `task_transfer_window` окно `protect -> stabilize -> widen`, так что следующие 1-2 route decisions перестраиваются не только как один response-aware день, а как маленькая controlled arc вокруг response-lane.
  Последний шаг в этом слое тоже уже включён: completion следующего `writing/speaking response-pass` теперь может прямо продвигать, откатывать или закрывать это окно. То есть `task_transfer_window` больше не живёт только по памяти/счётчику дней, а учится на качестве самого свежего response-pass.

### Сильные функции, которые уже начаты, но ещё не закрыты как продуктовые differentiators

- `Unified daily learning ritual`:
  это уже не просто идея: `DailyLoopPlan` теперь хранит явный `ritual`, dashboard и daily loop показывают канонический ритм дня, guided lesson context знает ritual headline/promise/stage path, а runner/results уже начинают закрывать сессию как один connected daily scenario. Плюс маршрут уже умеет открываться через task-driven `reading/listening input`, когда день реально требует такого старта, и переводить этот input в следующий response-step как отдельную мини-миссию. Но слой всё ещё нужно дотянуть до более глубокого multi-skill execution и richer vertical coverage.
- `Learning Blueprint Engine`:
  базовый explainable engine теперь уже собран как отдельная blueprint-entity и перестал быть только скрытым влиянием profile/recommendation. Следующий шаг здесь уже не “сделать blueprint”, а углубить его до richer editing, stronger daily ritual coupling и later task/track branching.
  После интеграции `You & English` blueprint теперь начинает читать и `english relationship` слой: не только goal/track/mode, но и то, к какой внутренней форме английского идёт ученик (`freedom/lightness/spontaneity/confidence`), что сейчас мешает, и какие ритуалы должны делать маршрут живым.
- `Deep skill verticals`:
  grammar / speaking / pronunciation / writing / vocabulary уже заметные; listening теперь тоже поднят из скрытого support-layer в отдельную governed route-surface с history/trend memory и follow-up orchestration, а reading уже существует не только в lesson engine через `reading_block`, но и как отдельная governed route-surface. Поверх этого daily route уже умеет поднимать `task-driven input surface` как реальный первый шаг дня, а сами `reading/listening` уже умеют вести в следующий response-step как task-driven mini-missions. Но listening/reading ещё нужно дотянуть до уровня самостоятельных сильных режимов и richer task-driven loops.
- `Conversational Liza layer`:
  explainable guidance сильная, но это всё ещё больше intelligent UI layer, чем настоящий persistent conversational teacher layer.
- `Real-life task mode`:
  архитектурная база есть, но полноценные task-driven flows пока не собраны как отдельный сильный срез.

### Крупные сильные функции, которые ещё по сути не начаты

- `Monetization readiness`:
  free vs premium depth, paid personalization, package logic.
- `Gamification and retention architecture`:
  кроме streak/progress/continuity signals, тяжёлый retention layer ещё не строился.
- `Dedicated exam / relocation / travel / work tracks`:
  пока нет как полноценных route families.
- `Event and analytics layer`:
  roadmap-level observability, serious funnel tracking и product analytics ещё не подняты.
- `Frontend quality system`:
  нет полноценного e2e / visual regression / flagship-path quality harness.

## Main Strategic Correction - 2026-04-19

Да, после повторной сверки видно, что дальше не стоит бесконечно углубляться только в polishing.

Следующий правильный крупный implementation focus:

1. `Finish Unified Daily Learning Ritual`
   не только continuity around sessions, а сам канонический multi-skill daily experience.
2. `Deepen Missing Skill Verticals`
   в первую очередь listening / reading и task-driven integration.
3. `Only then continue broad polish`
   polishing дальше должен усиливать уже закрытые сильные функции, а не подменять их.

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
- adaptive rotation теперь учитывает `active_skill_focus`, `preferred_mode` и `route seed source`, поэтому guided route уже может поднимать `grammar / writing / pronunciation / profession` не как случайные модули, а как часть текущей learner strategy.
- поверх этого появился явный `practice mix`: маршрут теперь взвешивает `speaking / writing / grammar / vocabulary / listening / pronunciation / profession`, а lesson composition использует эти веса для вставки, перестановки и усиления блоков.
- post-lesson `sessionSummary` теперь умеет оценивать сам `practice mix` по block-level scores, поэтому `strategy shift` и tomorrow-state начинают опираться не только на общий результат, но и на то, какой тип практики реально удержал маршрут, а какой просел.
- continuity UI теперь тоже показывает этот `practice shift`: dashboard, daily loop, lesson results, route intelligence и shell re-entry reminder начинают объяснять не только общий итог, но и какой practice-type повёл маршрут дальше.
- `practice shift` теперь влияет и на реальный next-day route seed: headline/summary/why-now/steps у `daily_loop_plan` и guided prompts внутри lesson blocks начинают подстраиваться под то, какая практика вчера удержалась лучше, а какая всё ещё требует опоры.
- learner model inside `progress snapshots` теперь обновляется точнее по skill-verticals из block-level scores: `grammar`, `speaking`, `writing`, `pronunciation`, `listening` и `profession` больше не получают одинаковый generic growth после каждого урока.
- recommendation engine и adaptive loop теперь тоже начинают использовать живой learner model: при ослаблении recovery pressure и в non-recovery сценариях свежий `progress snapshot` может смещать `focus area` и strategy alignment в сторону реально проседающего skill.
- adaptive surfaces теперь начали показывать этот progress-aware signal явно: dashboard и activity loop объясняют не только `recommended module`, но и `live learner signal`, который подтолкнул систему к текущему фокусу.
- поверх live signal теперь начинает работать и multi-day strategy memory: система собирает `skillTrajectory` из последних progress snapshots, сохраняет её в `journey_state`, использует в adaptive alignment и guided route, а UI уже показывает не только моментальный слабый сигнал, но и более длинную траекторию по skill-verticals.
- `skillTrajectory` теперь начинает влиять и на поведение маршрута: recommendation engine, adaptive loop, next-day `daily_loop_plan`, next-best-action и re-entry surfaces могут подхватывать multi-day slipping/stable skill даже тогда, когда один свежий snapshot сам по себе уже не даёт достаточно сильного live-focus сигнала.
- поверх короткой trajectory-memory теперь появляется и longer-horizon `strategyMemory`: она помогает recommendation, adaptive alignment и next-day copy держать в фокусе не только последние 2-3 колебания, но и более устойчивую learner pressure-memory по grammar / speaking / listening / writing / pronunciation / profession.
- next-day plan, re-entry prompt и guided route теперь начинают учитывать и `routeCadenceMemory`: система различает `steady return`, `gentle re-entry` и `route rescue after break`, а значит может мягче открывать маршрут после пропусков и не вести пользователя как будто вчера ничего не произошло.
- cadence-layer теперь влияет уже не только на continuity copy, но и на сам adaptive loop: strategy alignment, recommended module reason, focus recovery и module rotation умеют смягчаться для `gentle re-entry` и `route rescue`, чтобы возвращение после паузы не ощущалось как преждевременное давление.
- поверх этого появился `routeRecoveryMemory`: cadence, strategy memory и session outcome теперь собираются в короткую recovery arc (`route rebuild / protected return / skill repair cycle / targeted stabilization`), которая меняет headline, next-step, daily steps, guided route context и surfaces маршрута на несколько дней вперёд, а не только на одну следующую сессию.
- recommendation engine теперь тоже начал читать `routeRecoveryMemory`: при `route_rebuild / protected_return` система может предпочесть connected main-route recommendation вместо преждевременного hard-recovery path, а при `skill_repair_cycle / targeted_stabilization` — удерживать multi-day focus внутри самого выбора следующего урока.
- dashboard, activity и progress теперь тоже начали читать recovery-aware route priority: их главный CTA, supporting summary и порядок `daily loop` step-cards могут смещаться в `restart gently / protected return / repair cycle`, чтобы интерфейс вел пользователя в тот же режим, который уже выбрал strategy layer.
- quick actions и top-level navigation теперь тоже начали подстраиваться под этот route priority: dashboard сначала поднимает `main path`, supportive surfaces идут следом, а верхний rail перестаёт визуально спорить с фазой `protected return / route rebuild`.
- поверх этого появился и мягкий navigation protection layer: в фазах `route_rebuild / protected_return` конкурирующие side-modules остаются видимыми, но переводятся в `later in the route`, чтобы продукт не только советовал главный путь, но и последовательно защищал его от преждевременных ответвлений.
- этот protection layer теперь дошёл и до самих secondary skill-surfaces: `grammar`, `vocabulary`, `speaking`, `pronunciation`, `writing`, `profession` и `mistakes` показывают route-governance notice и в чувствительных фазах переводят свои coach CTA обратно в главный маршрут, а не в соседние side-paths.
- поверх этого route governance уже начала управлять и внутренними micro-flows: на `vocabulary`, `speaking`, `pronunciation` и `writing` активные practice-действия теперь мягко блокируются в `protected return`, а экран остаётся доступным как explainable supportive surface, а не как competing route.
- следующий слой над этим уже включён: side-surfaces теперь различают не только `protected hold`, но и `priority re-entry / sequenced hold`, поэтому после protected route поддерживающие практики возвращаются в правильной очередности, а не открываются все одновременно без стратегии.
- sequence-aware re-entry уже стал stateful и persisted: выполнение `vocabulary / speaking / pronunciation / writing` support-step теперь обновляет `journey_state.strategy_snapshot.routeReentryProgress`, а `grammar / profession` могут вручную подтвердить завершение support-pass через тот же backend journey-endpoint, чтобы recovery-последовательность переживала перезаходы и не жила только во фронте.
- следующий слой над этим тоже уже включён: активный `routeReentryProgress.nextRoute` теперь влияет не только на UI-governance, но и на backend recommendation plus `daily_loop_plan`, поэтому следующий маршрут реально может сместиться, например, в `writing support`, если именно этот sequenced support-step ещё не пройден.
- этот же sequence-сигнал теперь дошёл и до adaptive loop: `AdaptiveStrategyAlignment`, `moduleRotation`, `summary`, `generationRationale` и adaptive surfaces на `dashboard/activity` уже умеют поднимать конкретный `next support step`, а не только общую recovery-phase.
- поверх этого `routeReentryProgress.nextRoute` теперь уже влияет и на сам guided lesson composition: `practice mix` поднимает активный sequenced support-step как отдельный strategy signal, а guided route умеет вставлять, например, `writing support` block и поднимать его ближе к ответу, если именно этот шаг должен открыться следующим.
- `route day shape` теперь перестал жить только на главных route-panels: `activity`, `progress`, shell-level `re-entry prompt` и screen-level `route governance` тоже начали говорить языком `gentle restart / protected return / focused support`, чтобы secondary surfaces не выбивались из общего recovery-ритма.
- этот же язык дня теперь дошёл и до локальных `microflow guards` на `vocabulary / speaking / pronunciation / writing`, чтобы даже внутри заблокированных practice-зон пользователь видел, какой именно ритм дня сейчас защищает система.
- navigation-слой тоже начал подчиняться этому ритму: `top rail`, `quick actions` и shell-level navigation copy теперь показывают `day shape`, так что пользователь получает один и тот же recovery signal не только в содержимом экранов, но и в самих путях перемещения по продукту.
- поверх navigation-copy теперь появился и shell-level `route entry orchestration`: при новом входе приложение может один раз переводить пользователя не в нейтральный `dashboard`, а сразу в `daily loop`, `lesson runner` или нужный sequenced support-surface, если recovery-phase уже явно говорит, где должен начаться следующий шаг.
- этот автопереход теперь ещё и объясняется в UI: после smart re-entry shell показывает короткий `route entry notice`, чтобы пользователь видел, почему система открыла именно эту surface, а не воспринимал переход как немой редирект.
- поверх этого появился и persisted `routeEntryMemory`: shell теперь регистрирует реальные входы в `daily loop / lesson runner / support surfaces`, а re-entry orchestration может учитывать, не пытается ли система слишком настойчиво снова открыть один и тот же sequenced step вместо более безопасного возврата в main route.
- `routeEntryMemory` теперь влияет уже не только на shell re-entry: backend recommendation и следующий `daily_loop_plan` тоже умеют замечать повторяющиеся открытия одного и того же support-step и мягко сбрасывать день в calmer main route, прежде чем снова вести пользователя в тот же side-surface.
- guided route composition теперь тоже подчиняется этому reset-сигналу: после повторного re-entry один и тот же support-block больше не форсится механически, а `practice mix` и lesson composition сначала возвращают вес в calmer main lesson flow и только потом снова поднимают тот же side-surface.
- поверх этого repeated re-entry теперь влияет уже и на короткую multi-day recovery arc: `routeRecoveryMemory` и adaptive alignment умеют переводить маршрут в connected reset mode на ближайшие 2-3 сессии, а не только принять одноразовое решение на один lesson run.
- route surfaces теперь тоже умеют показать этот режим как отдельный `Connected reset` день: dashboard, daily loop, route intelligence, shell re-entry reminder и top-level day-shape копия больше не маскируют такой сценарий под generic `protected return`.
- после connected reset появился и явный `support reopen ready` слой: когда calmer main-route проходы уже выполнены, интерфейс теперь прямо показывает, что конкретный support-step снова готов вернуться в connected route, а не снимает reset молча.
- поверх этого backend тоже начал держать отдельную reopen-дугу: после connected reset маршрут теперь может войти в `support_reopen_arc`, где recommendation, `daily_loop_plan` и recovery-memory уже заранее перестраивают ближайшие 2-3 маршрута вокруг осознанного возврата support-step, а не только вокруг текущего дня.
- эту reopen-дугу я уже начал делать поведенческой, а не только смысловой: `daily_loop_plan` теперь даёт такому дню отдельный tempo, более длинный controlled session и более явную опору на connected route вместо мгновенного отката либо в reset, либо в side-surface deep dive.
- поверх этого она уже начала читать и недавнюю историю reopen-дней: если support-step уже возвращался 1-2 маршрута подряд, система умеет различать `first reopen / settling back in / ready to widen`, а значит маршрут начинает заранее понимать, когда support ещё нужно удержать в connected route, а когда уже можно снова мягко расширяться.
- этот reopen-substage теперь уже поднят и во фронт: `dashboard`, `daily loop`, `route intelligence` и shell `re-entry prompt` перестали показывать один и тот же generic reopen-state и начали явно различать первый controlled return, settling pass и widen-ready момент.
- теперь этот reopen-substage влияет уже и на route priority: hero CTA, quick actions, `activity/progress` primary route handlers и top rail начинают по-разному вести пользователя в `first reopen / settling pass / ready to widen`, так что reopened support-surface может становиться реальным главным входом дня, а не только пояснением в copy.
- shell-level re-entry orchestration теперь тоже стал substage-aware: на fresh return система не только открывает более сильную стартовую surface, но и передаёт explainable `what comes next` mini-sequence, чтобы было понятно, когда после reopened support-step маршрут вернётся в connected daily route, а когда наоборот сначала widening идёт через main path.
- этот `what comes next` слой теперь уже поднят и в сами route-surfaces: `dashboard continuity`, `daily loop`, `route intelligence` и shell `re-entry prompt` начали показывать один и тот же follow-up hint, чтобы продукт объяснял не только текущую точку входа, но и ближайший следующий шаг после неё.
- поверх этого follow-up sequence теперь стал persisted backend-side: `journey_state.strategy_snapshot` начал хранить `routeFollowUpMemory`, поэтому следующий шаг после re-entry/progression переживает перезагрузки и обновляется вместе с `routeReentryProgress`, а не вычисляется только локально на фронте.
- следующий слой над этим теперь уже поведенческий: `grammar / vocabulary / speaking / writing / pronunciation / profession` после реального completion support-step умеют читать persisted `routeFollowUpMemory` и мягко переводить пользователя в следующий ожидаемый route surface, так что recovery-дуга начинает двигаться не только в copy, но и в фактической навигации.
- теперь этот же persisted follow-up signal дошёл и до backend strategy builders: recommendation goal, `daily_loop_plan` copy и `next_best_action` уже могут подхватывать ту же дугу `куда сейчас -> что потом`, так что маршрут не распадается на отдельную фронтовую навигацию и backend-логику.
- поверх этого completion reopened support-step теперь уже продвигает и backend-side reopen arc: после реального support-pass система умеет переводить `support_reopen_arc` из `first reopen` в `settling pass`, а затем в `ready to widen`, не дожидаясь только истории прошлых daily plans.
- теперь widening после reopen уже влияет и на следующий execution slice продукта: `recommendation`, `adaptive loop` и `guided lesson composition` начали различать `settling pass` и `ready to widen`, поэтому reopened support-step больше не тащит одинаково весь день на себе и в нужный момент уступает лидерство более широкому connected route.
- следующий слой над этим тоже уже включён: `routeRecoveryMemory.sessionShape` теперь начинает менять и фактическую форму `daily_loop_plan`, так что `gentle_restart / protected_mix / focused_support / guided_balance / forward_mix` влияют на длительность дня, компактность шагов и ранний приоритет sequenced support-step, а не только на explanation copy.
- этот же day-shape слой уже поднят и во фронт: dashboard, daily loop screen, route continuity и route intelligence теперь прямо показывают пользователю, какой сегодня тип дня (`gentle restart / protected return / focused support / forward extension`) и насколько маршрут компактный или расширенный.
- walkthrough-полировка теперь тоже продвинулась: `RouteEntryNotice`, dashboard hero и lesson results начали показывать один и тот же mini-flow `сейчас -> потом`, так что smart re-entry, route CTA и post-lesson continuity ощущаются как одна живая дуга, а не как разрозненные explain-blocks.
- onboarding-handoff теперь тоже усилен как часть этой дуги: экран онбординга явно подхватывает proof-lesson result, показывает `route continuity` и текущий `handoff` шаг, так что переход `proof lesson -> onboarding -> dashboard` ощущается как одно непрерывное сопровождение Лизы.
- сам переход `proof lesson -> onboarding` теперь тоже идёт с явным route-entry handoff state, поэтому onboarding встречает пользователя как продолжение живого урока, а не как холодный reset в отдельный flow.
- shell и post-lesson CTA теперь тоже подписывают эти handoff-события единым языком маршрута, так что proof lesson, results и updated dashboard меньше ощущаются как отдельные страницы со случайной навигацией.
- финал пробного урока теперь тоже явно показывает mini-route `сейчас -> потом -> дальше`, а daily-loop CTA на dashboard говорит языком `today's route`, а не безличного loop-state.
- welcome hero и post-lesson CTA тоже сдвинуты в язык `живой пробный урок` и `следующий шаг маршрута`, чтобы самые частые кнопки не выбивали пользователя обратно в лексику отдельных экранов.
- continuity, re-entry и route-intelligence surfaces тоже постепенно уводятся от более технической лексики вроде `loop/trail/dashboard state` в единый язык маршрута, следующего шага и route-home.
- bridge `complete onboarding -> dashboard` тоже теперь прогрет: после submit shell сохраняет onboarding-handoff notice, пропускает обычный smart re-entry один раз и открывает dashboard как точку входа в уже готовый первый personal route, а не как нейтральную домашнюю страницу.
- первый запуск маршрута после dashboard тоже теперь прогрет: route CTA и daily-loop start передают в lesson runner explainable launch-state, а сам lesson runner встречает пользователя как следующий живой шаг уже собранного пути, а не как обезличенный `lesson engine` экран.
- конец первого guided loop тоже теперь теплее: завершение урока передаёт explainable handoff в `lesson results`, а `results -> updated dashboard` уже работает как мост к следующему витку маршрута, а не как возврат к старому состоянию.
- walkthrough-полировка конца сессии стала ещё глубже: lesson runner теперь заранее показывает mini-дугу после последнего блока, `discard draft` возвращает не в пустой dashboard, а в сохранённый route-context, а `lesson results` больше не опирается на случайный `history.back()`, а последовательно ведёт в обновлённый dashboard-state.

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

Текущий backend-слой маршрута уже различает post-lesson reopen evaluation:
- `settling pass` и `ready to widen` теперь различаются не только по history memory, но и по фактическому результату завершённого reopen-урока;
- `sessionSummary` и `tomorrowPreview` уже умеют переводить support reopen arc в более широкий следующий день, если connected reopen pass действительно удержался.
- widening после reopen теперь живёт как короткое `decision window`, так что ближайшие route decisions и daily-plan copy могут держать controlled expansion, а не просто один widen-ready флаг.
- этот `decision window` теперь доезжает и до guided lesson composition: в widen-ready окне `practice mix` и block payload уже отдают лидерство broader `lesson` flow и не форсят тот же reopened support-block раньше времени.
- поверх этого widening-window теперь стало staged: backend различает `first widening pass`, `stabilizing widening` и `ready for extension`, так что recommendation, daily-plan copy, adaptive alignment и guided route уже начинают учитывать не просто факт widen-ready, а прогресс ближайших 2-3 route decisions внутри controlled expansion.
- этот staged widening уже поднят и во фронт: `dashboard`, `daily loop`, `route continuity`, `route intelligence` и shell `re-entry prompt` теперь показывают конкретный этап controlled expansion и остаток widening-window, а не только общий `ready to widen`.
- поверх этого widening-substages теперь уже влияют и на shell-level route behavior: `route priority`, `quick actions`, `top rail` и smart `route entry orchestration` различают `first widening pass / stabilizing widening / ready for extension`, поэтому CTA и стартовая surface уже меняются по реальному этапу controlled expansion.
- теперь этот же staged expansion дошёл и до secondary surfaces: `activity`, `progress`, `route governance` и `microflow guards` уже объясняют текущую фазу widening в coach-copy и next-best-action, а не только повторяют общий `ready to widen`.
- поверх этого widening-stage теперь уже меняет и локальные CTA/ordering в `activity loop` и `progress diagnostic`: secondary surfaces начинают поднимать более уместный `primary route` и перестраивать supportive actions под текущую фазу `first widening pass / stabilizing widening / ready for extension`, а не оставаться нейтральными.

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

Статус на `2026-04-19`: базовый explainable engine уже реализован. `Learning Blueprint` теперь формализован как отдельная persisted strategy-entity внутри `journey_state.strategy_snapshot`, выводится на dashboard как личная стратегическая карта и доезжает до guided lesson context как long-plan explanation.

- вычисление стартового learner profile из ответов;
- генерация стартовых priorities по grammar/reading/vocabulary/speaking/writing;
- формирование стартового diagnostic mode:
  мягкий старт или checkpoint-first;
- стартовый profession pack и initial vocabulary pack.
- универсальный `general communication` lane для тех, кому не нужен pure professional track.
- explainable `learning blueprint` panel на dashboard;
- blueprint-aware `guided lesson context`, чтобы long-plan logic была видна и внутри lesson run.

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

Статус на `2026-04-14`: retention slice уже перешёл из purely explainable в partially behavioral. `dashboard`, `AppShell`, `activity` и `progress` умеют возвращать пользователя в маршрут, завершённая session формирует persisted `sessionSummary` и richer `tomorrowPreview`, новый день уже может строить `daily_loop_plan` из этого continuity seed, recommended lesson run запускается через guided-route overlay, а сам route уже начал влиять на block composition и strategy-aware module rotation; следующий шаг здесь сделать content mix ещё точнее согласованными с learner strategy уже не на уровне нескольких усиленных эвристик, а как более цельный composition engine.

Дополнительный walkthrough-прогресс на `2026-04-19`:

- welcome, proof lesson, onboarding, dashboard и lesson/results всё заметнее говорят единым языком `живой старт -> маршрут -> следующий шаг`, а не языком отдельных экранов;
- continuity, re-entry и route-intelligence surfaces уже меньше опираются на техничную лексику вроде `loop / trail / dashboard state`;
- top rail, adaptive route support и next-action surfaces тоже начинают звучать как один наставляемый путь, а не как набор системных блоков.
