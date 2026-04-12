# Wow Product Master Plan

## Product Intent

Цель продукта: создать не просто тренажёр английского, а premium web-приложение нового класса, где один AI-компаньон ведёт взрослого пользователя от любого стартового уровня к свободному, грамотному и уверенному английскому языку.

Этот продукт должен:

- учить не отдельным разрозненным навыкам, а всей системе языка целиком;
- объединять grammar, vocabulary, speaking, pronunciation, listening, reading и writing в один связанный learning engine;
- позволять как идти по полной стратегии обучения, так и резко сужать обучение под конкретную цель пользователя;
- давать ощущение премиальности, интеллектуальной глубины, заботы, поддержки и предвосхищения следующего шага;
- опираться на Лизу как на центральный слой продукта: учитель, проводник, помощник по интерфейсу, коуч, объясняющий логику обучения.

## Core Product Thesis

Главная идея продукта:

`Один умный AI-компаньон + одна личная стратегия обучения + один единый learning loop + полное покрытие всех языковых навыков`.

Пользователь не должен чувствовать, что он прыгает между разными сервисами:

- здесь grammar отдельно,
- здесь словарь отдельно,
- здесь speaking отдельно,
- здесь pronunciation отдельно.

Он должен чувствовать, что всё это части одного живого пути, который понимает его цели, ошибки, прогресс, слабые места, мотивацию, интересы и контекст.

## Target User

Главный пользователь первой сильной версии:

- взрослый learner;
- хочет выучить английский “под ключ”;
- хочет говорить свободно, грамотно и без сильного акцента;
- хочет понимать речь, писать, читать и проходить реальные жизненные сценарии;
- может идти как в long-term mastery, так и в narrow goal mode:
  - отпуск;
  - переезд;
  - экзамен;
  - работа;
  - собеседования;
  - small talk;
  - everyday English.

## Product Principles

### 1. One System, Not Many Tools

Все навыки должны ощущаться как части одной системы.

### 2. Liza Is The Product Layer

Лиза не должна быть декоративной фичей. Она должна быть основной точкой взаимодействия с системой.

### 3. Fast Value In 3-5 Minutes

Пользователь уже в первые минуты должен почувствовать:

- пользу;
- персонализацию;
- запоминаемость;
- премиальность;
- уверенность, что система понимает именно его.

### 4. Premium Means Guidance, Not Decoration

Премиальность — это не только красивый UI и lip sync.
Премиальность — это:

- ясная логика;
- сильное объяснение;
- глубокая персонализация;
- спокойная уверенность продукта;
- ощущение, что система знает, что делать дальше.

### 5. Every Action Must Feed The Strategy

Любое действие пользователя должно обновлять его learning model:

- ошибки;
- сильные стороны;
- скорость обучения;
- preferred mode;
- pronunciation profile;
- vocabulary gaps;
- grammar gaps;
- confidence patterns;
- listening resilience;
- writing quality.

## Desired Product Shape

Продукт должен состоять из двух уровней одновременно.

### Level 1. Unified Daily Learning Experience

Это основной путь пользователя.

Один daily loop, в котором:

- Лиза ставит цель сессии;
- даётся контекст;
- идут упражнения по разным навыкам;
- система связывает ошибки между модулями;
- пользователь видит не просто “баллы”, а смысл;
- в конце есть понятный итог, что закрепилось и что делать дальше.

### Level 2. Dedicated Skill Verticals

При этом должны существовать и отдельные вертикали:

- grammar;
- vocabulary;
- pronunciation;
- speaking;
- writing;
- listening;
- reading.

Но это не отдельные острова, а “увеличительное стекло” над общей стратегией.

Пользователь может:

- учиться в общем потоке;
- нырять в отдельный навык глубже;
- возвращаться обратно в единую траекторию.

## Liza System Design

## Role Of Liza

Лиза должна быть:

- AI-учителем;
- навигатором по приложению;
- объясняющим коучем;
- интерпретатором оценок и ошибок;
- адаптивным помощником по задачам пользователя;
- мягким мотивационным слоем;
- голосом премиальности продукта.

## Presence Modes

Нужны два режима присутствия Лизы:

### Mode A. Full Presence

Для:

- welcome;
- proof lesson;
- speaking flows;
- pronunciation coaching;
- сложных разборов;
- критических переходов;
- wow-моментов.

В этом режиме допустимы:

- talking avatar;
- lip sync;
- голос;
- richer coach-card;
- live conversational moments.

### Mode B. Smart Ambient Presence

Для:

- dashboard;
- grammar;
- vocabulary;
- writing;
- progress;
- task planning.

В этом режиме Лиза не мешает, но всегда рядом:

- компактный dock;
- contextual hints;
- voice-on-demand;
- explain button;
- ask Liza button;
- step guidance;
- next best action.

## Core Rule

Лиза не должна исчезать из опыта.
Она может менять плотность присутствия, но не должна пропадать как проводник продукта.

## The Main Learning Engine

## Strategic Decision

Основой продукта должен стать не один speaking-loop в чистом виде, а единый adaptive learning loop, внутрь которого уже встроены все навыки.

Рекомендуемая базовая структура:

1. `Context`
   Лиза объясняет, зачем эта мини-сессия нужна именно сейчас.
2. `Input`
   Пользователь слышит, читает или получает ситуацию.
3. `Response`
   Пользователь говорит, пишет, выбирает, собирает, повторяет или отвечает.
4. `Analysis`
   Система анализирует не только correctness, но и стратегический смысл ошибки.
5. `Improvement`
   Даётся более сильный вариант, объяснение, микро-дрилл, мнемоника или pattern.
6. `Reinforcement`
   Пользователь закрепляет через повторение, перенос в новый пример, mini quiz или recall.
7. `Memory Update`
   Результат сохраняется в learner model.
8. `Next Step`
   Лиза объясняет, что делать дальше.

## Why This Engine Matters

Такой движок позволяет в одну систему встроить:

- grammar;
- vocabulary;
- speaking;
- pronunciation;
- listening;
- reading;
- writing;
- exam prep;
- task solving.

То есть продукт перестаёт быть “набором модулей” и становится “одной обучающей машиной”.

## Skill Strategy

## 1. Grammar

Grammar должен стать одним из сильнейших модулей продукта.

### Goals

- снять страх перед английской грамматикой;
- объяснять легко;
- делать grammar наглядной, не академически душной;
- связывать grammar с живой речью и письмом;
- превращать правила в patterns, а не в абстрактные таблицы.

### Required Product Shape

- отдельная grammar vertical;
- visual grammar maps;
- short rule explanation;
- “why this matters” block;
- contrastive examples;
- common mistakes from learner history;
- conversion drills:
  - read;
  - say;
  - write;
  - transform;
- memory anchors and mnemonics;
- grammar tied to speaking and writing corrections.

### Premium Features

- Лиза объясняет тему простым языком;
- “объясни ещё проще”;
- “покажи на 3 жизненных примерах”;
- “сравни с русской логикой”;
- “почему я всё время ошибаюсь именно здесь”.

## 2. Vocabulary

Vocabulary должен быть не просто word list.

### Required Layers

- персональная память слов и выражений;
- слова из ошибок;
- слова из уроков;
- слова из реальных задач пользователя;
- phrasebook by goals;
- smart review engine;
- usage examples;
- pronunciation binding;
- topic collections;
- active vs passive knowledge distinction.

### Premium Features

- phrase-first approach, а не word-first;
- capture from mistakes;
- capture from writing/speaking;
- capture from user requests;
- memory reinforcement through spaced repetition, recall and application;
- объяснение оттенков значений;
- “когда это реально говорят”.

## 3. Speaking

Speaking должен оцениваться не как “одно текстовое поле и один отзыв”, а как настоящая устная практика.

### Required Dimensions

- fluency;
- clarity;
- correctness;
- confidence;
- naturalness;
- situational appropriateness.

### Required Flow

- scenario;
- user response;
- STT;
- meaning check;
- language correction;
- pronunciation layer;
- better phrasing;
- repeat;
- transfer to a new variant.

### Premium Features

- roleplay with Liza;
- pressure mode;
- exam mode;
- real-life mode;
- business mode;
- confidence coaching;
- conversation continuation;
- social speaking unlock later.

## 4. Pronunciation

Pronunciation — один из самых сильных будущих дифференциаторов.

### Required Stack

- transcript alignment;
- word-by-word feedback;
- phoneme-level coaching;
- stress and rhythm feedback;
- intonation guidance;
- shadowing;
- minimal pairs;
- comparison with native model;
- repeated attempts tracking;
- pronunciation profile memory per user.

### Premium Features

- модельная фраза голосом Лизы;
- lip-sync demo;
- explain-the-sound mode;
- “покажи ртом как произносится” in future;
- native-flow mode;
- phrase linking coaching;
- accent reduction path.

## 5. Listening

Listening должен стать не только lesson block, а полноценным skill vertical.

### Required Modes

- listening inside guided lessons;
- standalone listening mode;
- listening by difficulty;
- listening by accent;
- listening by situation;
- listening by exam target;
- transcript-hidden first;
- transcript reveal after effort;
- question answering;
- detail spotting;
- meaning reconstruction.

### Premium Features

- adaptive transcript reveal;
- replay by chunk;
- slow/normal compare mode;
- key phrase extraction;
- “why you missed it”;
- listening tied to pronunciation and vocabulary.

## 6. Reading

Reading тоже должен стать отдельной vertical плюс частью общей сессии.

### Required Modes

- standalone reading mode;
- guided reading inside lessons;
- reading by goal:
  - exam;
  - work;
  - relocation;
  - travel;
  - daily life;
- comprehension questions;
- phrase highlighting;
- grammar in context;
- vocabulary extraction;
- summary and retelling.

### Premium Features

- adaptive text complexity;
- phrase-by-phrase explanation;
- “simplify this paragraph”;
- reading aloud handoff into pronunciation;
- “explain why this sentence is built this way”.

## 7. Writing

Writing должен быть простым, понятным, поддерживающим и очень полезным.

### Required Shape

- clear task;
- writing assistant mode;
- write with Liza mode;
- review mode;
- before/after comparison;
- targeted corrections;
- rewrite goals;
- second submission;
- writing memory.

### Premium Features

- structured editor;
- explain correction inline;
- tone switch;
- better version with rationale;
- task-aware writing:
  - email;
  - message;
  - exam answer;
  - short opinion;
  - work update.

## Personalization Engine

## Product Requirement

Нужна не просто recommendation system, а личная образовательная стратегия пользователя.

## Inputs Into Strategy

- onboarding answers;
- declared goal;
- real-life constraints;
- level;
- exam target;
- weak areas;
- mistakes;
- pronunciation diagnostics;
- listening performance;
- reading speed and comprehension;
- vocabulary retention;
- confidence patterns;
- user-stated requests by voice or text.

## Outputs Of Strategy

- daily session structure;
- skill balance;
- review pressure;
- content lane;
- scenario type;
- exam trajectory;
- difficulty pacing;
- speaking vs text ratio;
- motivation framing;
- next-week plan;
- “why this matters now”.

## Required User Control

Пользователь должен иметь возможность:

- увидеть свой текущий трек;
- понять, почему система выбрала именно его;
- скорректировать трек;
- сообщить новую цель голосом или текстом;
- включить narrow mode;
- вернуться в broad mode.

## Real-Life Task Mode

Один из ключевых differentiators продукта.

Пользователь должен иметь возможность прийти с задачей:

- “мне нужно письмо”;
- “мне нужно подготовиться к звонку”;
- “мне нужен английский для отпуска”;
- “мне надо сдать экзамен на B2”;
- “я хочу уметь понимать сериалы”;
- “я хочу перестать бояться speaking”.

Система должна:

- распознать намерение;
- определить skill mix;
- предложить mini strategy;
- запустить lesson flow;
- встроить результаты в общую долгую траекторию.

## Motivation And Gamification

Gamification должна быть глубокой, но не дешёвой.

Она не должна превращать продукт в шумный arcade layer.

## Core Gamification Stack

- XP and progress points;
- soft currency;
- streaks;
- learning quests;
- skill milestones;
- challenge chains;
- unlockable modes;
- mastery badges;
- weekly missions;
- leaderboard in later phase;
- social unlock after baseline speaking threshold.

## Important Rule

Геймификация должна усиливать обучение, а не заменять его.

То есть награды должны быть привязаны к:

- повторению;
- удержанию;
- transfer of skill;
- consistency;
- courage in speaking;
- mastery of weak spots;
- completion of strategic loops.

## Social Layer Later

После прохождения минимального conversational threshold:

- доступ к controlled social interaction;
- общение по интересам;
- тематические speaking rooms;
- кооперативные language games;
- safe moderated prompts;
- partner practice with AI scaffolding.

## Premium Experience Standard

Чтобы продукт ощущался “вау”, нужны не только функции, но и стандарты исполнения.

## UX Standard

- very fast perceived response;
- no dead states;
- no confusing transitions;
- clear reason behind each step;
- minimal friction to speak, listen, repeat, write;
- emotional warmth;
- visual consistency;
- premium motion;
- living UI with restraint.

## Feedback Standard

Любой feedback должен быть:

- точным;
- коротким, если это первый слой;
- глубоким по запросу;
- человечным;
- actionable;
- не унижающим;
- не generic.

## Audio/Avatar Standard

- voice must sound intentional;
- lip sync must feel reliable;
- model playback must be pedagogically useful;
- replay must be instant;
- presence should never feel broken or random.

## Current Product Reality

На текущем этапе strongest visible differentiator — это proof lesson и Liza-driven welcome experience.

Это означает:

- именно этот поток должен стать первым flagship slice;
- он должен не просто “красиво работать”, а доказать весь продукт за 3-5 минут;
- после него пользователь должен захотеть остаться внутри системы.

## Master Execution Plan

## Phase 1. Stabilize And Elevate Proof Lesson

Цель: превратить пробный урок в безупречный flagship demo, который уже демонстрирует ядро продукта.

### Must Deliver

- один цельный premium flow без сломанных переходов;
- Лиза как постоянный coach-presence;
- надёжный voice capture;
- адекватный STT;
- честный analysis pipeline;
- ясный value reveal;
- повторяемость;
- сильный финальный CTA в продолжение стратегии обучения.

### Concrete Work

- стабилизировать speech capture state machine;
- убрать fragile voice/lip-sync branches;
- унифицировать autoplay and replay behavior;
- сделать proof lesson truly pedagogical:
  - example by Liza;
  - user answer;
  - correction;
  - repeat;
  - pronunciation model;
  - reinforcement;
- привести тексты к premium-уровню;
- убедиться, что каждый шаг объясняет зачем он нужен.

### Success Criteria

- пользователь без инструкции понимает flow;
- ощущает магию;
- слышит Лизу как сильного teacher-companion;
- получает measurable win;
- хочет идти дальше.

## Phase 2. Build Global Liza Layer

Цель: сделать Лизу системным слоем приложения.

### Must Deliver

- global coach dock;
- voice-on-demand;
- explain-this button;
- ask Liza layer;
- next-step guidance;
- smart presence modes by context.

### Screens To Cover First

- dashboard;
- proof lesson continuation;
- grammar;
- vocabulary;
- speaking;
- pronunciation;
- writing;
- progress;
- task intake.

### Success Criteria

- пользователь больше не видит “набор страниц”;
- пользователь видит одно живое приложение с одним наставником.

## Phase 3. Build Unified Daily Learning Loop

Цель: сделать основной ежедневный опыт продукта.

### Must Deliver

- one daily session;
- multi-skill composition;
- strategy-aware sequencing;
- memory updates;
- next-step clarity;
- emotional continuity with Liza.

### Example Session Shape

- 1 warm start;
- 1 vocabulary recall;
- 1 grammar pattern;
- 1 listening or reading input;
- 1 speaking or writing response;
- 1 pronunciation micro-fix;
- 1 reinforcement checkpoint;
- 1 strategic summary.

### Success Criteria

- вся система начинает ощущаться целостной;
- каждое занятие становится meaningful;
- продукт перестаёт быть набором отдельных режимов.

## Phase 4. Build Deep Skill Verticals

Цель: сделать каждый важный навык действительно сильным сам по себе.

### Priority Order

1. grammar
2. pronunciation
3. speaking
4. vocabulary
5. writing
6. listening
7. reading

### Important Note

Это не означает, что listening/reading не важны.
Это означает, что сначала надо усилить то, что уже ближе к сильному differentiator и уже частично существует.

## Phase 5. Build Personal Strategy Engine

Цель: перейти от рекомендаций к настоящей AI-guided educational strategy.

### Must Deliver

- strategy model per user;
- editable goal graph;
- goal intake by text or voice;
- short-term plan;
- long-term roadmap;
- strategy explanations;
- retuning after each meaningful activity.

### Success Criteria

- система ощущается как личный AI-методист;
- пользователь понимает, что его здесь реально ведут.

## Phase 6. Add Gamification And Retention Architecture

Цель: удержание без удешевления продукта.

### Must Deliver

- XP;
- currency;
- unlocks;
- challenge loops;
- weekly goals;
- skill mastery tracks;
- social unlock preparation.

### Success Criteria

- пользователь хочет возвращаться;
- мотивация не держится только на силе воли.

## Phase 7. Exam, Relocation, Travel And Real-Task Tracks

Цель: превратить систему в действительно универсальный продукт.

### Must Deliver

- exam path;
- relocation path;
- travel path;
- work path;
- custom task path.

### Success Criteria

- система покрывает и broad mastery, и narrow intent;
- пользователь может резко сменить режим без ощущения, что попал в другой продукт.

## Technical Foundation Plan

Чтобы всё выше было реально достижимо, нужно параллельно закрывать архитектурные блоки.

## Architecture Priorities

### 1. Lazy Runtime Initialization

Нужно убрать хрупкий eager startup тяжёлых AI-компонентов.

### 2. Stable Voice Pipeline

Нужен единый надёжный voice stack:

- record;
- stop;
- upload;
- transcribe;
- assess;
- replay;
- model playback;
- lip sync.

### 3. Learner Model

Нужна полноценная сущность learner strategy / learner memory.

### 4. Event And Analytics Layer

Нужно понимать:

- где пользователь теряется;
- где возвращается;
- что реально помогает;
- какие фразы/ошибки повторяются;
- какие loops удерживают.

### 5. Frontend Quality System

Нужны:

- lint;
- tests;
- state-machine tests for voice flows;
- e2e for flagship paths;
- visual regression for premium UI surfaces.

## First Implementation Recommendation

Следующий главный execution slice:

`Proof lesson -> Global Liza layer -> Daily learning loop skeleton`

Именно в такой последовательности.

Почему:

- proof lesson уже самый сильный differentiator;
- global Liza layer сделает продукт единым;
- daily loop превратит wow-demo в реальный продукт.

## Definition Of Wow

Продукт можно считать “wow-приложением, которого ещё нет”, если одновременно выполняются 5 условий:

1. Пользователь чувствует, что его ведёт один умный AI-компаньон, а не десяток отдельных модулей.
2. Все языковые навыки связаны в одну систему и реально усиливают друг друга.
3. Уже в первые минуты пользователь получает запоминающуюся, персональную и полезную победу.
4. Обучение ощущается одновременно премиальным, глубоким и живым.
5. Система адаптируется к большой стратегии пользователя и к его текущим жизненным задачам.

## Immediate Next Step

После утверждения этого документа начать не с распыления по всему продукту, а с детализированной реализации Phase 1 и подготовкой архитектурной основы для Phase 2.
