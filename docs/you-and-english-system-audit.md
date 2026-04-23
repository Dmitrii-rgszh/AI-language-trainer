# You & English System Audit

Дата: `2026-04-23`

## Принцип

Книга `YOU-and-ENGLISH` должна жить в продукте не как набор специальных упражнений, а как общая операционная линза для всех учебных инструментов.

Это значит:

- не отдельные `book features` рядом с обычным приложением;
- а перепрошивка того, как продукт объясняет успех, ошибки, прогресс, повторение и контакт с английским.

## Что уже хорошо совпадает с философией книги

### 1. Route strategy

- `learning blueprint`
- `daily ritual`
- `ritual signal memory`
- `route follow-up / carry`
- `relationship-aware recommendation`

Здесь продукт уже думает не только про skill gaps, но и про лёгкость, ритуал, повторное использование и живой контакт с языком.

### 2. Reading / Listening

- `reading` уже работает как meaning-first input, а не как академический разбор текста;
- `listening` уже работает как signal capture, а не как дрилл на тотальный контроль;
- `task-driven input -> response` уже соответствует идее книги лучше, чем isolated drills.

### 3. Vocabulary / Speaking

- `word journal` уже встроен правильно;
- `spontaneous voice ritual` тоже встроен правильно;
- оба ритуала уже влияют на маршрут, а не существуют отдельно.

## Что пока совпадает только частично

### 1. Grammar

Проблема:

- grammar уже объясняется мягче, но всё ещё местами ощущается как skill-support экран, а не как инструмент самовыражения.

Что нужно:

- ещё сильнее связывать grammar с `clear expression`;
- меньше framing через “правило”, больше через “что ты сможешь сказать яснее”.

### 2. Writing

Проблема:

- writing уже мягкий, но всё ещё местами похож на review loop вокруг correction.

Что нужно:

- ещё сильнее сместить критерий успеха из `fixing text` в `clearer self-expression`;
- сильнее защищать право на imperfect first draft.

### 3. Pronunciation

Проблема:

- pronunciation уже уходит от sterile scoring, но всё ещё может ощущаться как lab.

Что нужно:

- ещё глубже связывать pronunciation с `comfort`, `clarity`, `trust in voice`, а не с баллом.

### 4. Progress

Проблема:

- progress уже умнее обычных score screens, но всё ещё слишком опирается на numeric framing.

Что нужно:

- сильнее показывать `ease / courage / reuse / less fear / more voice ownership` как законные показатели роста.

## Что я внедрил в этом шаге

Чтобы книга стала именно системной линзой, а не набором отдельных фич, я добавил общий frontend-layer:

- [english-relationship-lens.ts](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/shared/journey/english-relationship-lens.ts>)
- [EnglishRelationshipLensCard.tsx](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/widgets/journey/EnglishRelationshipLensCard.tsx>)

И встроил его в основные инструменты:

- [GrammarScreen.tsx](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/features/grammar/GrammarScreen.tsx>)
- [VocabularyScreen.tsx](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/features/vocabulary/VocabularyScreen.tsx>)
- [SpeakingScreen.tsx](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/features/speaking/SpeakingScreen.tsx>)
- [PronunciationScreen.tsx](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/features/pronunciation/PronunciationScreen.tsx>)
- [WritingScreen.tsx](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/features/writing/WritingScreen.tsx>)
- [ReadingScreen.tsx](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/features/reading/ReadingScreen.tsx>)
- [ListeningScreen.tsx](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/features/listening/ListeningScreen.tsx>)
- [ProgressScreen.tsx](</C:/Users/shapeless/Desktop/Тренер английского языка/app/frontend/src/features/progress/ProgressScreen.tsx>)

Теперь каждый из этих экранов явно показывает:

- через какую `You & English` линзу он должен читаться;
- что считается успехом именно сейчас;
- какое давление система сознательно снимает.

Это ещё не полный конец работы, но это уже первый реальный системный слой, который перепрошивает существующие инструменты, а не добавляет рядом новые book-exercises.

## Следующие правильные шаги

### A. Backend success criteria

Перенести ту же философию глубже в:

- `sessionSummary`
- `progress interpretation`
- `next_best_action`
- `post-lesson evaluation`

### B. Correction reframing

Пройтись по:

- speaking feedback
- writing review
- mistake map
- pronunciation verdict

И сместить language от `error-centric` к `usable-language-centric`.

### C. Progress reframing

Добавить более явные product-level signals:

- less fear
- more spontaneity
- better reuse
- stronger personal phrase ownership
- steadier ritual consistency
