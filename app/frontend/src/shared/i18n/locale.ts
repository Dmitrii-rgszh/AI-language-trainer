export type AppLocale = "ru" | "en";

export const APP_LOCALE_STORAGE_KEY = "ai-english-trainer:locale";

type TranslationEntry = {
  en: string;
  ru: string;
};

const translationEntries: TranslationEntry[] = [
  { en: "Onboarding", ru: "Онбординг" },
  { en: "Dashboard", ru: "Дашборд" },
  { en: "Activity", ru: "Активность" },
  { en: "Vocabulary", ru: "Словарь" },
  { en: "Reading", ru: "Чтение" },
  { en: "Lesson Runner", ru: "Урок" },
  { en: "Grammar", ru: "Грамматика" },
  { en: "Speaking", ru: "Разговорная речь" },
  { en: "Pronunciation", ru: "Произношение" },
  { en: "Writing", ru: "Письмо" },
  { en: "Profession", ru: "Профессия" },
  { en: "My Mistakes", ru: "Мои ошибки" },
  { en: "Progress", ru: "Прогресс" },
  { en: "Settings", ru: "Настройки" },
  { en: "AI English Trainer Pro", ru: "AI English Trainer Pro" },
  { en: "Today", ru: "Сегодня" },
  { en: "Daily progress", ru: "Прогресс за день" },
  { en: "Current streak", ru: "Текущая серия" },
  { en: "Language", ru: "Язык" },
  { en: "Interface language", ru: "Язык интерфейса" },
  { en: "Russian", ru: "Русский" },
  { en: "English", ru: "English" },
  { en: "RU", ru: "RU" },
  { en: "EN", ru: "EN" },
  { en: "Start lesson", ru: "Начать урок" },
  { en: "See progress", ru: "Открыть прогресс" },
  { en: "Open roadmap", ru: "Открыть roadmap" },
  { en: "Run checkpoint", ru: "Запустить checkpoint" },
  { en: "Start recovery lesson", ru: "Начать восстановительный урок" },
  { en: "Resume lesson", ru: "Продолжить урок" },
  { en: "Restart lesson", ru: "Начать урок заново" },
  { en: "Discard draft", ru: "Сбросить черновик" },
  { en: "Open activity", ru: "Открыть активность" },
  { en: "Open progress", ru: "Открыть прогресс" },
  { en: "Open settings", ru: "Открыть настройки" },
  { en: "Mark reviewed", ru: "Отметить как повторённое" },
  { en: "Saving...", ru: "Сохраняю..." },
  { en: "Active", ru: "Активно" },
  { en: "Use", ru: "Выбрать" },
  { en: "Play", ru: "Проиграть" },
  { en: "Playing", ru: "Проигрывается" },
  { en: "Playing...", ru: "Проигрываю..." },
  { en: "Record", ru: "Записать" },
  { en: "Scoring...", ru: "Оцениваю..." },
  { en: "Stop & score", ru: "Остановить и оценить" },
  { en: "Loading...", ru: "Загрузка..." },
  { en: "Back", ru: "Назад" },
  { en: "Previous", ru: "Назад" },
  { en: "Next block", ru: "Следующий блок" },
  { en: "Save block", ru: "Сохранить блок" },
  { en: "Complete lesson", ru: "Завершить урок" },
  { en: "Step", ru: "Шаг" },
  { en: "ready", ru: "готов" },
  { en: "fallback", ru: "резерв" },
  { en: "offline", ru: "офлайн" },
  { en: "mock", ru: "mock" },
  { en: "voice", ru: "голос" },
  { en: "text", ru: "текст" },
  { en: "mixed", ru: "смешанный" },
  { en: "diagnostic", ru: "диагностический" },
  { en: "professional", ru: "профессиональный" },
  { en: "recovery", ru: "восстановительный" },
  { en: "grammar", ru: "грамматика" },
  { en: "speaking", ru: "говорение" },
  { en: "pronunciation", ru: "произношение" },
  { en: "writing", ru: "письмо" },
  { en: "trainer_skills", ru: "навыки тренера" },
  { en: "insurance", ru: "страхование" },
  { en: "banking", ru: "банкинг" },
  { en: "ai_business", ru: "AI для бизнеса" },
  { en: "stable", ru: "стабильно" },
  { en: "none", ru: "нет" },
  { en: "source", ru: "источник" },
  { en: "sources", ru: "источники" },
  { en: "Unified English hub with a professional track", ru: "Единый центр английского с профессиональным треком" },
  { en: "Desktop-first MVP foundation with lesson runner, progress and modular features.", ru: "Desktop-first MVP-основа с lesson runner, progress и modular features." },
  { en: "Personal English workspace for focused daily progress.", ru: "Персональное пространство для английского с понятным ежедневным прогрессом." },
  { en: "Complete onboarding", ru: "Заверши онбординг" },
  { en: "Loading dashboard", ru: "Загружаю дашборд" },
  { en: "Backend unavailable", ru: "Бэкенд недоступен" },
  { en: "Профиль ещё не создан. Заверши onboarding, и я соберу персональный roadmap.", ru: "Профиль ещё не создан. Заверши онбординг, и я соберу персональный roadmap." },
  { en: "Нужен первый create profile, после этого dashboard наполнится автоматически.", ru: "Нужно создать первый профиль, после этого dashboard наполнится автоматически." },
  { en: "Подгружаю состояние MVP...", ru: "Подгружаю состояние MVP..." },
  { en: "Собираю данные по профилю, слабым местам и следующему уроку.", ru: "Собираю данные по профилю, слабым местам и следующему уроку." },
  { en: "Finish onboarding to unlock your personal lesson plan.", ru: "Заверши онбординг, чтобы открыть персональный план обучения." },
  { en: "Loading your learning plan.", ru: "Собираю твой учебный план." },
  { en: "Create your profile to unlock the first dashboard and lesson track.", ru: "Создай профиль, чтобы открыть первый дашборд и стартовый трек уроков." },
  { en: "Loading your learning workspace...", ru: "Подгружаю твоё учебное пространство..." },
  { en: "Primary onboarding and profile setup.", ru: "Первичная настройка профиля." },
  { en: "Первичная настройка профиля, приоритетов и professional track. Этот экран уже подключён к общему store и готов к дальнейшему развитию диагностики.", ru: "Первичная настройка профиля, приоритетов и professional track. Этот экран уже подключён к общему store и готов к дальнейшему развитию диагностики." },
  { en: "Your profile drives the roadmap, lesson flow, and skill balance from the first session.", ru: "Профиль сразу задаёт roadmap, поток уроков и баланс навыков уже с первой сессии." },
  { en: "Profile summary", ru: "Профиль" },
  { en: "Сохрани базовый профиль, чтобы dashboard, recommendations и lesson flow сразу подстроились под твой уровень и трек.", ru: "Сохрани базовый профиль, чтобы dashboard, recommendations и lesson flow сразу подстроились под твой уровень и трек." },
  { en: "Save profile and continue", ru: "Сохранить профиль и продолжить" },
  { en: "Name", ru: "Имя" },
  { en: "Your name", ru: "Твоё имя" },
  { en: "This profile", ru: "Этот профиль" },
  { en: "Current level", ru: "Текущий уровень" },
  { en: "Target level", ru: "Целевой уровень" },
  { en: "Profession track", ru: "Профессиональный трек" },
  { en: "UI language", ru: "Язык интерфейса" },
  { en: "Explanation language", ru: "Язык объяснений" },
  { en: "Login", ru: "Логин" },
  { en: "Choose a login", ru: "Придумай логин" },
  { en: "Email", ru: "Почта" },
  { en: "name@example.com", ru: "name@example.com" },
  { en: "Lesson duration", ru: "Длительность урока" },
  { en: "Speaking priority", ru: "Приоритет speaking" },
  { en: "Grammar priority", ru: "Приоритет grammar" },
  { en: "Profession priority", ru: "Приоритет profession" },
  { en: "starts from", ru: "начинает с" },
  { en: "and moves to", ru: "и движется к" },
  { en: "with the", ru: "с" },
  { en: "track", ru: "треком" },
  { en: "Lesson format", ru: "Формат урока" },
  { en: "minutes", ru: "минут" },
  { en: "explanations in", ru: "объяснения на" },
  { en: "Priority mix", ru: "Баланс приоритетов" },
  { en: "Settings And Providers", ru: "Настройки и провайдеры" },
  { en: "User settings and provider health live here. This screen lets you control the local LLM, STT, TTS, and fallback runtime behavior.", ru: "Здесь собраны настройки пользователя и состояние провайдеров. На этом экране можно управлять локальными LLM, STT, TTS и резервным поведением runtime." },
  { en: "Runtime readiness", ru: "Готовность runtime" },
  { en: "Core providers that are fully live right now.", ru: "Ключевые провайдеры, которые уже полностью доступны." },
  { en: "Enabled stack", ru: "Активный стек" },
  { en: "Provider types currently allowed in runtime.", ru: "Типы провайдеров, которые сейчас разрешены в runtime." },
  { en: "Fallback modes", ru: "Fallback-режимы" },
  { en: "Modules working through fallback or non-primary providers.", ru: "Модули, которые сейчас работают через резервный или неосновной провайдер." },
  { en: "Profile settings", ru: "Настройки профиля" },
  { en: "This profile drives recommendations, the daily flow, and how focus is split between speaking, grammar, and profession.", ru: "Этот профиль управляет рекомендациями, ежедневным потоком и тем, как распределяется фокус между speaking, grammar и profession." },
  { en: "Save profile updates", ru: "Сохранить профиль" },
  { en: "Provider status and preferences", ru: "Статус и предпочтения провайдеров" },
  { en: "LLM, STT, and TTS matter most for the live voice-and-AI loop. If any of them moves into fallback or offline mode, the impact will show up on the dashboard and in the related practice modules.", ru: "Для живого voice-and-AI цикла особенно важны `LLM`, `STT` и `TTS`. Если какой-то модуль уйдёт в резервный или офлайн-режим, это сразу проявится на dashboard и в связанных practice-модулях." },
  { en: "Selected runtime key", ru: "Выбранный runtime key" },
  { en: "Use this provider in runtime", ru: "Использовать этого провайдера в runtime" },
  { en: "Back to dashboard", ru: "Назад к дашборду" },
  { en: "Check voice lab", ru: "Открыть voice lab" },
  { en: "Dashboard", ru: "Дашборд" },
  { en: "Welcome back", ru: "С возвращением" },
  { en: "Главный экран уже собирает recommended lesson, слабые места, quick actions и skill progress из общего состояния приложения.", ru: "Главный экран уже собирает recommended lesson, слабые места, quick actions и skill progress из общего состояния приложения." },
  { en: "Choose the next lesson, review weak spots, and keep the daily rhythm moving.", ru: "Выбирай следующий урок, закрывай слабые места и держи ежедневный ритм." },
  { en: "Recommended lesson", ru: "Рекомендуемый урок" },
  { en: "Duration", ru: "Длительность" },
  { en: "Focus", ru: "Фокус" },
  { en: "Recovery pressure is easing for", ru: "Давление на восстановление снижается для" },
  { en: "The roadmap can lean back toward the main lesson flow.", ru: "Roadmap может мягче вернуться к основному потоку уроков." },
  { en: "Daily goal completion", ru: "Выполнение дневной цели" },
  { en: "Consistency", ru: "Стабильность" },
  { en: "Current streak and habit continuity across your recent sessions.", ru: "Текущая серия и устойчивость привычки на последних сессиях." },
  { en: "Runtime Stack", ru: "Runtime-стек" },
  { en: "Ready", ru: "Готово" },
  { en: "Level roadmap", ru: "Roadmap уровня" },
  { en: "Declared level", ru: "Заявленный уровень" },
  { en: "Estimated level", ru: "Оценочный уровень" },
  { en: "Overall score", ru: "Общий балл" },
  { en: "Current block", ru: "Текущий блок" },
  { en: "blocks completed", ru: "блоков завершено" },
  { en: "Weak spots", ru: "Слабые места" },
  { en: "active", ru: "активно" },
  { en: "Quick actions", ru: "Быстрые действия" },
  { en: "Continue", ru: "Продолжить" },
  { en: "Current engine mix", ru: "Текущий баланс движка" },
  { en: "Adaptive study loop", ru: "Адаптивный учебный цикл" },
  { en: "Due vocab", ru: "Слов на повторение" },
  { en: "Active vocab", ru: "Активный словарь" },
  { en: "Listening focus", ru: "Фокус listening" },
  { en: "Why this loop was generated", ru: "Почему был собран этот цикл" },
  { en: "Main flow rotation", ru: "Ротация основного потока" },
  { en: "priority", ru: "приоритет" },
  { en: "Open full loop", ru: "Открыть весь цикл" },
  { en: "Vocabulary due now", ru: "Слова на повторение сейчас" },
  { en: "cards", ru: "карточек" },
  { en: "Queue balance", ru: "Баланс очереди" },
  { en: "new", ru: "новых" },
  { en: "mastered", ru: "освоено" },
  { en: "Most loaded category", ru: "Самая нагруженная категория" },
  { en: "No urgent vocabulary reviews right now. Stay with the current lesson flow.", ru: "Срочных повторений слов сейчас нет. Можно остаться в текущем потоке уроков." },
  { en: "stage", ru: "этап" },
  { en: "Listening contribution", ru: "Вклад listening" },
  { en: "Listening score", ru: "Баллы listening" },
  { en: "Vocabulary contribution", ru: "Вклад словаря" },
  { en: "Due now", ru: "Нужно сейчас" },
  { en: "Recent activity", ru: "Недавняя активность" },
  { en: "Activity will appear here after the first completed lesson or speaking attempt.", ru: "Активность появится здесь после первого завершённого урока или speaking attempt." },
  { en: "Provider health", ru: "Состояние провайдеров" },
  { en: "Open activity center", ru: "Открыть центр активности" },
  { en: "See lesson history, speaking attempts, current results and mistake patterns in one place.", ru: "Смотри историю уроков, speaking attempts, текущие результаты и паттерны ошибок в одном месте." },
  { en: "Update profile", ru: "Обновить профиль" },
  { en: "Adjust current level, target, lesson duration and priority mix without leaving the base flow.", ru: "Измени текущий уровень, цель, длительность урока и баланс приоритетов, не выходя из основного потока." },
  { en: "Activity", ru: "Активность" },
  { en: "Unified Activity And History", ru: "Единая активность и история" },
  { en: "Единая точка истории по урокам, speaking practice, текущим lesson results и накопленным mistake patterns.", ru: "Единая точка истории по урокам, speaking practice, текущим lesson results и накопленным mistake patterns." },
  { en: "One timeline for lessons, speaking practice, listening signals, and result history.", ru: "Единая лента по урокам, speaking-практике, listening-сигналам и истории результатов." },
  { en: "Lessons", ru: "Уроки" },
  { en: "Completed lessons in current progress history.", ru: "Завершённые уроки в текущей истории прогресса." },
  { en: "Speaking attempts", ru: "Speaking attempts" },
  { en: "Voice and text practice attempts collected so far.", ru: "Попытки голосовой и текстовой практики, собранные на данный момент." },
  { en: "Open patterns", ru: "Открытые паттерны" },
  { en: "Mistake records currently tracked in the system.", ru: "Записи об ошибках, которые сейчас отслеживаются системой." },
  { en: "Latest result", ru: "Последний результат" },
  { en: "Current session lesson result is available.", ru: "Результат текущей сессии доступен." },
  { en: "No current session result yet.", ru: "Результата текущей сессии пока нет." },
  { en: "Open lab", ru: "Открыть lab" },
  { en: "Average score", ru: "Средний балл" },
  { en: "Recent checks", ru: "Недавние проверки" },
  { en: "Adaptive loop summary", ru: "Сводка adaptive loop" },
  { en: "Generation rationale", ru: "Логика генерации" },
  { en: "Vocabulary repetition", ru: "Повторение слов" },
  { en: "due", ru: "к повторению" },
  { en: "Vocabulary queue is clear for now.", ru: "Очередь словаря сейчас чистая." },
  { en: "Mistake to vocabulary loop", ru: "Связка ошибок и словаря" },
  { en: "Open hub", ru: "Открыть hub" },
  { en: "Converted examples", ru: "Преобразованные примеры" },
  { en: "Linked vocabulary", ru: "Связанный словарь" },
  { en: "Weak spot recovery visibility", ru: "Видимость восстановления слабых мест" },
  { en: "Repeats", ru: "Повторы" },
  { en: "Last seen", ru: "Последний раз замечено" },
  { en: "Module rotation balance", ru: "Баланс ротации модулей" },
  { en: "Open dashboard", ru: "Открыть дашборд" },
  { en: "Recent timeline", ru: "Недавняя лента" },
  { en: "current session", ru: "текущая сессия" },
  { en: "Activity feed will populate after the first lesson completion or speaking attempt.", ru: "Лента активности заполнится после первого завершённого урока или speaking attempt." },
  { en: "Top mistake patterns", ru: "Главные паттерны ошибок" },
  { en: "Open all", ru: "Открыть все" },
  { en: "Mistake analytics will appear here after lesson completion and correction extraction.", ru: "Аналитика ошибок появится здесь после завершения урока и извлечения исправлений." },
  { en: "Quick jumps", ru: "Быстрые переходы" },
  { en: "Current lesson result", ru: "Текущий результат урока" },
  { en: "Open the latest in-session result screen if a recent completion happened.", ru: "Открой экран последнего результата в текущей сессии, если недавно было завершение." },
  { en: "Progress deep dive", ru: "Глубокий просмотр прогресса" },
  { en: "See skill balances, daily goal and recent lesson history.", ru: "Смотри баланс навыков, дневную цель и недавнюю историю уроков." },
  { en: "Speaking practice log", ru: "Журнал speaking practice" },
  { en: "Continue voice training and review speaking attempts in detail.", ru: "Продолжай голосовую практику и смотри speaking attempts подробнее." },
  { en: "Pronunciation trend view", ru: "Обзор трендов произношения" },
  { en: "Review recurring weak sounds and pronunciation history outside the lab context.", ru: "Смотри повторяющиеся слабые звуки и историю произношения вне контекста lab." },
  { en: "Vocabulary hub", ru: "Словарный hub" },
  { en: "Review due cards, recent vocabulary activity and queue balance.", ru: "Смотри карточки на повторение, недавнюю активность словаря и баланс очереди." },
  { en: "Grammar Coach", ru: "Grammar Coach" },
  { en: "Grammar Center", ru: "Центр грамматики" },
  { en: "MVP-модуль хранит темы отдельно от UI и уже показывает mastery, explanation и checkpoints для дальнейшего расширения упражнениями.", ru: "MVP-модуль хранит темы отдельно от UI и уже показывает mastery, explanation и checkpoints для дальнейшего расширения упражнениями." },
  { en: "Build control over the grammar patterns that matter most in your next lessons.", ru: "Укрепляй те грамматические паттерны, которые сильнее всего влияют на ближайшие уроки." },
  { en: "Mistake Analytics", ru: "Аналитика ошибок" },
  { en: "Отдельный модуль ошибок уже собирает source module, corrected text, explanation и repetition counter. Это база для weak spot analytics и recovery lessons.", ru: "Отдельный модуль ошибок уже собирает source module, corrected text, explanation и repetition counter. Это база для weak spot analytics и recovery lessons." },
  { en: "Review recurring patterns, compare corrections, and see what still needs active recovery.", ru: "Смотри повторяющиеся паттерны, сравнивай исправления и понимай, что ещё требует активного восстановления." },
  { en: "Professional English", ru: "Профессиональный английский" },
  { en: "Profession Hub", ru: "Профессиональный hub" },
  { en: "Professional tracks уже декомпозированы на отдельные карточки-домены и готовы к расширению в полноценные submodules.", ru: "Professional tracks уже декомпозированы на отдельные карточки-домены и готовы к расширению в полноценные submodules." },
  { en: "Choose the professional track that should shape your vocabulary, scenarios, and lesson emphasis.", ru: "Выбери профессиональный трек, который должен формировать словарь, сценарии и акценты уроков." },
  { en: "Skill Progress", ru: "Прогресс навыков" },
  { en: "В этом модуле уже есть skill scores, streak, daily goal и lesson history. Следующий шаг — добавить реальные charts и persistence layer.", ru: "В этом модуле уже есть skill scores, streak, daily goal и lesson history. Следующий шаг — добавить реальные charts и persistence layer." },
  { en: "Follow your scores, recent practice, and roadmap shifts in one view.", ru: "Следи за баллами, последней практикой и изменениями roadmap в одном месте." },
  { en: "Level diagnostic", ru: "Диагностика уровня" },
  { en: "Declared", ru: "Заявлено" },
  { en: "Estimated", ru: "Оценено" },
  { en: "Target", ru: "Цель" },
  { en: "Weakest skills", ru: "Самые слабые навыки" },
  { en: "Run diagnostic checkpoint", ru: "Запустить диагностический checkpoint" },
  { en: "Roadmap milestones", ru: "Этапы roadmap" },
  { en: "Daily goal", ru: "Дневная цель" },
  { en: "Today completion", ru: "Выполнение за сегодня" },
  { en: "Current streak across active learning days.", ru: "Текущая серия на активных учебных днях." },
  { en: "Average lesson score", ru: "Средний балл уроков" },
  { en: "Based on", ru: "На основе" },
  { en: "completed lesson", ru: "завершённого урока" },
  { en: "completed lessons", ru: "завершённых уроков" },
  { en: "Learning balance", ru: "Баланс обучения" },
  { en: "Profession score", ru: "Баллы profession" },
  { en: "Regulation score", ru: "Баллы regulation" },
  { en: "Recent lessons", ru: "Недавние уроки" },
  { en: "Recent highlight", ru: "Последний highlight" },
  { en: "Score", ru: "Балл" },
  { en: "Last completed at", ru: "Последнее завершение" },
  { en: "First completed lesson will appear here as soon as history starts filling up.", ru: "Первый завершённый урок появится здесь, как только история начнёт заполняться." },
  { en: "Roadmap reading", ru: "Чтение roadmap" },
  { en: "Lesson history", ru: "История уроков" },
  { en: "Speaking activity", ru: "Speaking activity" },
  { en: "Voice and text speaking attempts will appear here after the first practice session.", ru: "Голосовые и текстовые speaking attempts появятся здесь после первой практики." },
  { en: "Mistake to vocabulary contribution", ru: "Вклад ошибок в словарь" },
  { en: "Some weak spots are already being recycled into vocabulary review, so the app is no longer treating them as isolated corrections.", ru: "Часть слабых мест уже перерабатывается в повторение словаря, поэтому приложение больше не воспринимает их как изолированные исправления." },
  { en: "Once weak spots start converting into vocabulary review, the closed loop will appear here.", ru: "Как только слабые места начнут превращаться в повторение словаря, замкнутый цикл появится здесь." },
  { en: "Recovering weak spots", ru: "Восстанавливающиеся слабые места" },
  { en: "Linked vocabulary support", ru: "Связанная поддержка словаря" },
  { en: "Recovery visibility will appear once weak spots have enough history to show whether they are staying active or starting to settle down.", ru: "Видимость recovery появится, когда у слабых мест накопится достаточно истории, чтобы понять, остаются ли они активными или начинают затухать." },
  { en: "Listening activity", ru: "Listening activity" },
  { en: "Listening attempts will appear here after completing audio-first lesson blocks.", ru: "Listening attempts появятся здесь после завершения аудио-блоков." },
  { en: "Transcript support used", ru: "Использована поддержка transcript" },
  { en: "Audio-first answer", ru: "Ответ сначала по аудио" },
  { en: "Listening trend reading", ru: "Чтение тренда listening" },
  { en: "Listening now has saved attempt memory, not just one score inside the roadmap.", ru: "У listening теперь есть память сохранённых попыток, а не только один балл внутри roadmap." },
  { en: "Recurring weak prompts", ru: "Повторяющиеся слабые промпты" },
  { en: "No recurring weak listening prompt has emerged yet.", ru: "Повторяющийся слабый listening-промпт пока не появился." },
  { en: "Use transcript support rate as a confidence signal: lower support over time means listening is stabilizing.", ru: "Используй долю transcript support как сигнал уверенности: чем ниже она со временем, тем стабильнее listening." },
  { en: "Pronunciation now contributes through saved audio checks, not just a single lab verdict.", ru: "Произношение теперь влияет через сохранённые аудио-проверки, а не только через один verdict из lab." },
  { en: "If repeating weak sounds stay visible here, your readiness to the next milestone should be treated as less stable even when grammar or writing move faster.", ru: "Если повторяющиеся слабые звуки остаются видимыми здесь, готовность к следующему milestone стоит считать менее стабильной, даже если grammar или writing растут быстрее." },
  { en: "Use `Pronunciation Lab` to clear the top weak sound, then rerun a checkpoint to see whether the roadmap shifts upward more confidently.", ru: "Используй `Pronunciation Lab`, чтобы убрать главный слабый звук, а затем перезапусти checkpoint и посмотри, сместится ли roadmap вверх увереннее." },
  { en: "Weak-word trend will appear after repeated pronunciation checks.", ru: "Тренд по слабым словам появится после повторных проверок произношения." },
  { en: "Pronunciation trend data will appear here after the first saved audio checks.", ru: "Данные по тренду произношения появятся здесь после первых сохранённых аудио-проверок." },
  { en: "Pronunciation Coach", ru: "Pronunciation Coach" },
  { en: "Pronunciation Lab", ru: "Лаборатория произношения" },
  { en: "Теперь lab хранит историю попыток и показывает повторяющиеся слабые звуки и слова, а не только последний verdict.", ru: "Теперь lab хранит историю попыток и показывает повторяющиеся слабые звуки и слова, а не только последний verdict." },
  { en: "Voice playback", ru: "Воспроизведение голоса" },
  { en: "No TTS provider detected.", ru: "TTS-провайдер не найден." },
  { en: "Scoring layer", ru: "Слой оценивания" },
  { en: "Pronunciation scoring is not fully wired yet.", ru: "Оценка произношения ещё не полностью подключена." },
  { en: "Practice mode", ru: "Режим практики" },
  { en: "Drill packs available for immediate listen-and-repeat practice.", ru: "Наборы drill доступны для немедленной listen-and-repeat практики." },
  { en: "Pronunciation checks saved in rolling history.", ru: "Проверки произношения сохраняются в скользящей истории." },
  { en: "Recent pronunciation average across saved attempts.", ru: "Средний балл по недавним сохранённым попыткам произношения." },
  { en: "Weakest sound trend", ru: "Тренд самого слабого звука" },
  { en: "Seen", ru: "Замечено" },
  { en: "times in recent checks.", ru: "раз в недавних проверках." },
  { en: "No repeating weak sound pattern detected yet.", ru: "Повторяющийся слабый звук пока не обнаружен." },
  { en: "Latest pronunciation check", ru: "Последняя проверка произношения" },
  { en: "Matched tokens", ru: "Совпавшие токены" },
  { en: "Missed tokens", ru: "Пропущенные токены" },
  { en: "not detected", ru: "не распознано" },
  { en: "Priority fix words", ru: "Слова в приоритете" },
  { en: "Sound focus diagnostics", ru: "Диагностика по фокусу звука" },
  { en: "Word-level assessment", ru: "Оценка на уровне слов" },
  { en: "Heard", ru: "Распознано" },
  { en: "Weakest sound trends", ru: "Тренды слабых звуков" },
  { en: "Recurring weak sounds", ru: "Повторяющиеся слабые звуки" },
  { en: "No repeating sound issue yet.", ru: "Повторяющейся проблемы со звуком пока нет." },
  { en: "Recurring weak words", ru: "Повторяющиеся слабые слова" },
  { en: "No repeating weak word yet.", ru: "Повторяющегося слабого слова пока нет." },
  { en: "How to use this lab", ru: "Как использовать эту лабораторию" },
  { en: "Recent pronunciation history", ru: "Недавняя история произношения" },
  { en: "Custom phrase", ru: "Своя фраза" },
  { en: "focus", ru: "фокус" },
  { en: "word", ru: "слово" },
  { en: "sound", ru: "звук" },
  { en: "Speaking Partner", ru: "Speaking Partner" },
  { en: "Speaking Studio", ru: "Speaking Studio" },
  { en: "Теперь voice loop уже замкнут: запись голоса, transcript, AI feedback, autoplay tutor voice и история попыток. Повторяющиеся ошибки отсюда тоже попадают в общий adaptive loop.", ru: "Теперь voice loop уже замкнут: запись голоса, transcript, AI feedback, autoplay tutor voice и история попыток. Повторяющиеся ошибки отсюда тоже попадают в общий adaptive loop." },
  { en: "Use text and voice practice to train clarity, confidence, and faster self-correction.", ru: "Используй текстовую и голосовую практику, чтобы развивать ясность речи, уверенность и более быструю самокоррекцию." },
  { en: "Feedback focus", ru: "Фокус feedback" },
  { en: "Total Attempts", ru: "Всего попыток" },
  { en: "Все speaking попытки, включая voice и text input.", ru: "Все speaking attempts, включая voice и text input." },
  { en: "Voice Ratio", ru: "Доля голоса" },
  { en: "Доля попыток, где ты реально говорил голосом.", ru: "Доля попыток, где ты реально говорил голосом." },
  { en: "Avg Length", ru: "Средняя длина" },
  { en: "Средняя длина transcript в словах.", ru: "Средняя длина transcript в словах." },
  { en: "Live transcript", ru: "Живой transcript" },
  { en: "Goal", ru: "Цель" },
  { en: "Выбери speaking scenario", ru: "Выбери speaking scenario" },
  { en: "Autoplay tutor voice after voice analysis", ru: "Автопроигрывать голос тьютора после голосового анализа" },
  { en: "Analyzing...", ru: "Анализирую..." },
  { en: "Get AI feedback", ru: "Получить AI feedback" },
  { en: "Play tutor voice", ru: "Проиграть голос тьютора" },
  { en: "Record voice", ru: "Записать голос" },
  { en: "Stop & analyze voice", ru: "Остановить и проанализировать голос" },
  { en: "Здесь появится живой speaking feedback от модели.", ru: "Здесь появится живой speaking feedback от модели." },
  { en: "Repeated corrections from speaking review are added to the shared mistake map and can reshape the next adaptive recommendation.", ru: "Повторяющиеся исправления из speaking review попадают в общую карту ошибок и могут изменить следующую adaptive recommendation." },
  { en: "Useful corrected words and phrases from this review can also appear later in the vocabulary repetition loop.", ru: "Полезные исправленные слова и фразы из этого review позже тоже могут попасть в цикл повторения словаря." },
  { en: "AI-backed", ru: "С AI" },
  { en: "Fallback review", ru: "Резервный review" },
  { en: "История пока пустая. Сделай первую speaking попытку.", ru: "История пока пустая. Сделай первую speaking attempt." },
  { en: "Play again", ru: "Проиграть снова" },
  { en: "Reuse transcript", ru: "Использовать transcript снова" },
  { en: "Writing Coach", ru: "Writing Coach" },
  { en: "Подгружаю writing task...", ru: "Подгружаю writing task..." },
  { en: "Writing теперь уже не одноразовый review: черновики и feedback копятся в истории, удачные версии можно быстро переиспользовать, а повторяющиеся ошибки попадают в общую mistake map.", ru: "Writing теперь уже не одноразовый review: черновики и feedback копятся в истории, удачные версии можно быстро переиспользовать, а повторяющиеся ошибки попадают в общую mistake map." },
  { en: "Draft, revise, and reuse stronger versions while the app keeps track of recurring writing issues.", ru: "Пиши, дорабатывай и переиспользуй сильные версии, пока приложение отслеживает повторяющиеся проблемы в письме." },
  { en: "Tone", ru: "Тон" },
  { en: "Reviewing...", ru: "Проверяю..." },
  { en: "Get AI review", ru: "Получить AI review" },
  { en: "Clear draft", ru: "Очистить черновик" },
  { en: "AI writing review", ru: "AI review текста" },
  { en: "Feedback source", ru: "Источник feedback" },
  { en: "Сначала отправь черновик на review.", ru: "Сначала отправь черновик на review." },
  { en: "Writing corrections now feed the same adaptive mistake map as lessons and speaking practice, so repeated issues can change the next recovery focus.", ru: "Исправления из writing теперь попадают в ту же adaptive mistake map, что и уроки со speaking practice, поэтому повторяющиеся проблемы могут менять следующий recovery focus." },
  { en: "Stronger corrected words and phrase patterns from this draft can now move into the shared vocabulary review queue too.", ru: "Более сильные исправленные слова и шаблоны фраз из этого черновика теперь тоже могут переходить в общую очередь повторения словаря." },
  { en: "Draft history", ru: "История черновиков" },
  { en: "Последние версии и feedback теперь можно переиспользовать.", ru: "Последние версии и feedback теперь можно переиспользовать." },
  { en: "saved", ru: "сохранено" },
  { en: "После первого review здесь появятся сохранённые черновики и tutor feedback.", ru: "После первого review здесь появятся сохранённые черновики и tutor feedback." },
  { en: "Reuse draft", ru: "Использовать черновик снова" },
  { en: "Vocabulary Hub", ru: "Vocabulary Hub" },
  { en: "Лёгкий центр словаря: due queue, недавние ревью, баланс между new/active/mastered и теперь ещё видимый источник каждого item.", ru: "Лёгкий центр словаря: due queue, недавние ревью, баланс между new/active/mastered и теперь ещё видимый источник каждого item." },
  { en: "Подгружаю vocabulary hub...", ru: "Подгружаю vocabulary hub..." },
  { en: "New", ru: "Новые" },
  { en: "Active", ru: "Активные" },
  { en: "Mastered", ru: "Освоенные" },
  { en: "Queue looks balanced", ru: "Очередь выглядит сбалансированной" },
  { en: "Why these items are here", ru: "Почему эти элементы здесь" },
  { en: "Vocabulary review now mixes core study words with captured corrections from lessons, speaking and writing. Source labels show where the item came from, and review reason explains why it is back in your queue now.", ru: "Vocabulary review теперь смешивает базовые учебные слова с исправлениями, собранными из уроков, speaking и writing. Source labels показывают, откуда пришёл item, а review reason объясняет, почему он вернулся в очередь." },
  { en: "Due vocabulary queue", ru: "Очередь слов на повторение" },
  { en: "No due items right now.", ru: "Сейчас нет слов на повторение." },
  { en: "Mark correct", ru: "Отметить как верное" },
  { en: "Need review", ru: "Нужно повторить" },
  { en: "Recently reviewed", ru: "Недавно повторённые" },
  { en: "Recent vocabulary activity will appear here.", ru: "Недавняя активность словаря появится здесь." },
  { en: "Failed to load vocabulary hub", ru: "Не удалось загрузить vocabulary hub" },
  { en: "Lesson engine already works through config-driven blocks.", ru: "Механика урока уже работает через блоки, управляемые конфигом." },
  { en: "No lesson loaded yet", ru: "Урок пока не загружен" },
  { en: "Если незавершённый draft есть в backend, экран автоматически попробует его восстановить.", ru: "Если незавершённый draft есть в backend, экран автоматически попробует его восстановить." },
  { en: "Build recommended lesson", ru: "Собрать рекомендуемый урок" },
  { en: "Checkpoint mode active. This run is intended to refresh your long-term roadmap across grammar, speaking, listening, pronunciation and writing.", ru: "Режим checkpoint активен. Этот запуск нужен, чтобы обновить долгосрочный roadmap по grammar, speaking, listening, pronunciation и writing." },
  { en: "Listening audio", ru: "Listening audio" },
  { en: "Active variant", ru: "Активный вариант" },
  { en: "Variant", ru: "Вариант" },
  { en: "Questions", ru: "Вопросы" },
  { en: "Play audio prompt", ru: "Проиграть аудио" },
  { en: "Switch audio variant", ru: "Переключить вариант аудио" },
  { en: "Hide transcript", ru: "Скрыть transcript" },
  { en: "Reveal transcript", ru: "Показать transcript" },
  { en: "Try answering from audio first, then reveal transcript only if needed.", ru: "Сначала попробуй ответить по аудио, а transcript открывай только если нужно." },
  { en: "Transcript support was used for this checkpoint. Listening score will stay slightly more conservative.", ru: "Для этого checkpoint использовалась поддержка transcript. Оценка listening останется чуть более консервативной." },
  { en: "Pronunciation checkpoint", ru: "Checkpoint по произношению" },
  { en: "Play model", ru: "Проиграть образец" },
  { en: "Record response", ru: "Записать ответ" },
  { en: "Your response", ru: "Твой ответ" },
  { en: "Напиши или вставь свой ответ по этому блоку. Он сохранится в lesson run и может попасть в mistakes analytics.", ru: "Напиши или вставь свой ответ по этому блоку. Он сохранится в lesson run и может попасть в mistakes analytics." },
  { en: "Lesson complete. Estimated score", ru: "Урок завершён. Оценочный балл" },
  { en: "Results can now be forwarded into progress and mistakes analytics.", ru: "Теперь результаты можно отправить в progress и mistakes analytics." },
  { en: "Draft mode active. Saved block responses will be restored if you leave and reopen this lesson.", ru: "Активен режим черновика. Сохранённые ответы по блокам восстановятся, если выйти и снова открыть этот урок." },
  { en: "Results", ru: "Результаты" },
  { en: "Итоги lesson run: score, найденные ошибки, обновление progress и следующий рекомендуемый шаг.", ru: "Итоги lesson run: score, найденные ошибки, обновление progress и следующий рекомендуемый шаг." },
  { en: "Lesson summary", ru: "Сводка урока" },
  { en: "Diagnostic checkpoint completed. Your roadmap and next focus should now be refreshed from this control run.", ru: "Diagnostic checkpoint завершён. Теперь твой roadmap и следующий фокус должны обновиться после этого контрольного запуска." },
  { en: "Completed blocks", ru: "Завершённые блоки" },
  { en: "Completed at", ru: "Завершено" },
  { en: "just now", ru: "только что" },
  { en: "Detected mistakes", ru: "Обнаруженные ошибки" },
  { en: "Original", ru: "Оригинал" },
  { en: "Fix", ru: "Исправление" },
  { en: "No new mistakes were detected in this run.", ru: "В этом запуске новых ошибок не найдено." },
  { en: "Next lesson", ru: "Следующий урок" },
  { en: "Next recommended step", ru: "Следующий рекомендуемый шаг" },
  { en: "Открой dashboard для следующей персональной рекомендации.", ru: "Открой dashboard для следующей персональной рекомендации." },
  { en: "Continue personal roadmap", ru: "Продолжить личный roadmap" },
  { en: "Open dashboard recommendation", ru: "Открыть рекомендацию с дашборда" },
  { en: "Checkpoint impact on roadmap", ru: "Влияние checkpoint на roadmap" },
  { en: "Overall diagnostic score", ru: "Общий диагностический балл" },
  { en: "checkpoint", ru: "checkpoint" },
  { en: "This score now reflects word-level matching and sound-focus checks, not just a generic voice proxy.", ru: "Этот балл теперь отражает совпадение на уровне слов и проверки по sound-focus, а не просто общий voice proxy." },
  { en: "readiness", ru: "готовность" },
  { en: "Checkpoint performance pulled this milestone upward.", ru: "Результат checkpoint подтянул этот milestone вверх." },
  { en: "Checkpoint performance exposed a weaker area and reduced readiness.", ru: "Результат checkpoint показал слабую зону и снизил readiness." },
  { en: "This checkpoint confirmed the current roadmap without changing milestone readiness.", ru: "Этот checkpoint подтвердил текущий roadmap без изменения readiness milestone." },
  { en: "now", ru: "сейчас" },
  { en: "no change", ru: "без изменений" },
  { en: "score", ru: "балл" },
  { en: "Present Perfect vs Past Simple", ru: "Present Perfect vs Past Simple" },
  { en: "Sound /th/", ru: "Звук /th/" },
  { en: "Feedback language for workshops", ru: "Язык обратной связи для воркшопов" },
  { en: "Daily Mixed Lesson: Grammar + Speaking + Trainer English", ru: "Ежедневный смешанный урок: grammar + speaking + English для тренера" },
  { en: "Grammar Sprint", ru: "Grammar sprint" },
  { en: "Speaking Check-in", ru: "Speaking check-in" },
  { en: "Adaptive Loop", ru: "Адаптивный цикл" },
  { en: "Tight review of the current grammar weak spot before the next full lesson.", ru: "Короткий разбор текущего grammar weak spot перед следующим полным уроком." },
  { en: "Short guided speaking with focused feedback before the next full lesson.", ru: "Короткий guided speaking с фокусным feedback перед следующим полным уроком." },
  { en: "Feedback language, facilitation phrasing and workshop English for your current track.", ru: "Язык обратной связи, facilitation phrasing и workshop English для твоего текущего трека." },
  { en: "Protection language, needs analysis and client follow-up for your current track.", ru: "Язык protection, needs analysis и client follow-up для твоего текущего трека." },
  { en: "Product explanations, transfer updates and client-friendly banking phrasing.", ru: "Объяснение продуктов, transfer updates и client-friendly banking phrasing." },
  { en: "Workflow explanations, guardrails and business-facing AI language for your current track.", ru: "Объяснение workflow, guardrails и business-facing AI language для твоего текущего трека." },
  { en: "Clear the top weak sound and keep your speech more stable before the next speaking block.", ru: "Убери главный слабый звук и стабилизируй речь перед следующим speaking block." },
  { en: "Tighten wording, structure and tone in a short guided writing pass.", ru: "Подтяни wording, структуру и tone в коротком guided writing pass." },
  { en: "Review due words linked to recent mistakes and keep the queue under control.", ru: "Повтори слова, связанные с недавними ошибками, и удерживай очередь под контролем." },
  { en: "Daily Stand-up", ru: "Ежедневный стендап" },
  { en: "Training Debrief", ru: "Разбор тренинга" },
  { en: "Soft /th/ control", ru: "Контроль мягкого /th/" },
  { en: "Sentence stress", ru: "Фразовое ударение" },
  { en: "Reply to a hiring manager", ru: "Ответ менеджеру по найму" },
  { en: "Insurance English", ru: "Английский для страхования" },
  { en: "Banking English", ru: "Английский для банковской сферы" },
  { en: "Trainer Skills", ru: "Навыки тренера" },
  { en: "AI for Business", ru: "AI для бизнеса" },
  { en: "Checkpoint Diagnostic: A2 -> B2", ru: "Диагностический checkpoint: A2 -> B2" },
  { en: "Trainer Daily Flow", ru: "Ежедневный поток тренера" },
  { en: "Present Perfect Basics", ru: "Основы Present Perfect" },
  { en: "Past Simple vs Present Perfect", ru: "Past Simple и Present Perfect" },
  { en: "Future Forms for Planning", ru: "Будущие формы для планирования" },
  { en: "client conversations", ru: "разговоры с клиентами" },
  { en: "value communication", ru: "коммуникация ценности" },
  { en: "customer protection", ru: "защита клиента" },
  { en: "payments", ru: "платежи" },
  { en: "cards", ru: "карты" },
  { en: "financial conversations", ru: "финансовые разговоры" },
  { en: "facilitation", ru: "фасилитация" },
  { en: "feedback language", ru: "язык обратной связи" },
  { en: "coaching language", ru: "язык коучинга" },
  { en: "prompts", ru: "промпты" },
  { en: "AI assistants", ru: "AI-ассистенты" },
  { en: "risk-aware explanations", ru: "объяснения с учётом рисков" },
  { en: "tense-choice", ru: "выбор времени" },
  { en: "th-sound", ru: "звук th" },
  { en: "feedback-language", ru: "язык обратной связи" },
  { en: "Fallback LLM", ru: "Резервный LLM" },
  { en: "Local fallback responses stay available during development and whenever LM Studio is unavailable.", ru: "Локальные резервные ответы остаются доступны во время разработки и всякий раз, когда LM Studio недоступен." },
  { en: "LM Studio is unavailable, so the app is using local fallback responses.", ru: "LM Studio недоступен, поэтому приложение использует локальные резервные ответы." },
  { en: "STT Bridge", ru: "STT Bridge" },
  { en: "TTS Bridge", ru: "TTS Bridge" },
  { en: "Scoring Engine", ru: "Scoring Engine" },
  { en: "Укрепить Present Perfect и потренировать trainer feedback language.", ru: "Укрепить Present Perfect и потренировать trainer feedback language." },
  { en: "Strengthen Present Perfect and practice trainer feedback language.", ru: "Укрепить Present Perfect и потренировать trainer feedback language." },
  { en: "Нужен короткий review + speaking drill на опыт и недавние действия.", ru: "Нужен короткий review + speaking drill на опыт и недавние действия." },
  { en: "Add a short review plus a speaking drill on experience and recent actions.", ru: "Нужен короткий review + speaking drill на опыт и недавние действия." },
  { en: "Добавить 5 минут shadowing и minimal pairs.", ru: "Добавить 5 минут shadowing и minimal pairs." },
  { en: "Add 5 minutes of shadowing and minimal pairs.", ru: "Добавить 5 минут shadowing и minimal pairs." },
  { en: "Повторить мягкие формулировки для фасилитации и coaching.", ru: "Повторить мягкие формулировки для фасилитации и coaching." },
  { en: "Review softer facilitation and coaching phrasing.", ru: "Повторить мягкие формулировки для фасилитации и coaching." },
  { en: "10 минут на ключевую тему и быстрый drill.", ru: "10 минут на ключевую тему и быстрый drill." },
  { en: "10 minutes on one key topic and a quick drill.", ru: "10 минут на ключевую тему и быстрый drill." },
  { en: "Короткий guided speaking с фидбеком.", ru: "Короткий guided speaking с фидбеком." },
  { en: "A short guided speaking session with feedback.", ru: "Короткий guided speaking с фидбеком." },
  { en: "Профессиональный английский по текущему треку.", ru: "Профессиональный английский по текущему треку." },
  { en: "Professional English for the current track.", ru: "Профессиональный английский по текущему треку." },
  { en: "Roadmap towards B2: strengthen pronunciation and listening first, then convert recovery work into longer lesson gains. Immediate focus: Present Perfect vs Past Simple, Sound /th/.", ru: "Roadmap к B2: сначала усили pronunciation и listening, потом переводи recovery-работу в более длинные lesson gains. Немедленный фокус: Present Perfect vs Past Simple, звук /th/." },
  { en: "Используй для опыта, недавних действий и результата в настоящем.", ru: "Используй для опыта, недавних действий и результата в настоящем." },
  { en: "Use it for experience, recent actions and a present result.", ru: "Используй для опыта, недавних действий и результата в настоящем." },
  { en: "Past Simple = finished time. Present Perfect = result or experience.", ru: "Past Simple = finished time. Present Perfect = result or experience." },
  { en: "be going to, will и present continuous для планов и решений.", ru: "be going to, will и present continuous для планов и решений." },
  { en: "Клиентские разговоры, продукты, objections и needs analysis.", ru: "Клиентские разговоры, продукты, objections и needs analysis." },
  { en: "Client conversations, products, objections and needs analysis.", ru: "Клиентские разговоры, продукты, objections и needs analysis." },
  { en: "Базовая лексика по продуктам, платежам и retail banking.", ru: "Базовая лексика по продуктам, платежам и retail banking." },
  { en: "Core vocabulary for products, payments and retail banking.", ru: "Базовая лексика по продуктам, платежам и retail banking." },
  { en: "Язык фасилитации, coaching, структурирование тренинга и feedback.", ru: "Язык фасилитации, coaching, структурирование тренинга и feedback." },
  { en: "Facilitation language, coaching, training structure and feedback.", ru: "Язык фасилитации, coaching, структурирование тренинга и feedback." },
  { en: "AI workflows, prompts, limitations и объяснение кейсов на английском.", ru: "AI workflows, prompts, limitations и объяснение кейсов на английском." },
  { en: "AI workflows, prompts, limitations and explaining cases in English.", ru: "AI workflows, prompts, limitations и объяснение кейсов на английском." },
  { en: "Adaptive loop is actively supporting listening around", ru: "Адаптивный цикл сейчас специально поддерживает listening вокруг" },
  { en: "Listening is not the primary recovery pressure right now.", ru: "Сейчас listening не является главным источником нагрузки в восстановлении." },
  { en: "Adaptive loop is currently surfacing more vocabulary from", ru: "Адаптивный цикл сейчас чаще поднимает лексику из категории" },
  { en: "Vocabulary load is balanced across categories right now.", ru: "Сейчас словарная нагрузка распределена по категориям достаточно ровно." },
  { en: "audio comprehension", ru: "понимание аудио" },
  { en: "detail capture", ru: "улавливание деталей" },
  { en: "profession English", ru: "профессиональный английский" },
  { en: "Готов для локальной разработки и замены на Ollama.", ru: "Готов для локальной разработки и замены на Ollama." },
  { en: "Ready for local development and replacement with Ollama.", ru: "Готов для локальной разработки и замены на Ollama." },
  { en: "Подключение не настроено, предусмотрен graceful degradation.", ru: "Подключение не настроено, предусмотрен graceful degradation." },
  { en: "Connection is not configured; graceful degradation is in place.", ru: "Подключение не настроено, предусмотрен graceful degradation." },
  { en: "Пока не активирован, UI должен работать без озвучки.", ru: "Пока не активирован, UI должен работать без озвучки." },
  { en: "Not active yet; the UI should still work without speech output.", ru: "Пока не активирован, UI должен работать без озвучки." },
  { en: "Базовая оценка готова к замене на rule-based или AI scoring.", ru: "Базовая оценка готова к замене на rule-based или AI scoring." },
  { en: "Baseline scoring is ready to be replaced with rule-based or AI scoring.", ru: "Базовая оценка готова к замене на rule-based или AI scoring." },
  { en: "Alex, today's adaptive focus is grammar.", ru: "Alex, сегодня адаптивный фокус — grammar." },
  { en: "Start from Present Perfect vs Past Simple, keep the daily chain moving, and clear 1 vocabulary review item. Minutes completed today: 12.", ru: "Начни с Present Perfect vs Past Simple, сохрани дневную цепочку и закрой 1 словарное повторение. За сегодня уже выполнено: 12 минут." },
  { en: "Core vocabulary practice for the current profession track.", ru: "Практика ключевой лексики для текущего профессионального трека." },
  { en: "The pattern is still being reviewed, but it is appearing less often in fresh corrections.", ru: "Паттерн всё ещё в повторении, но в новых исправлениях появляется уже реже." },
  { en: "This weak spot is still repeating often enough that it should stay in active recovery.", ru: "Это слабое место всё ещё повторяется достаточно часто, поэтому его стоит держать в активном восстановлении." },
  { en: "Speaking refresh", ru: "Освежить speaking" },
  { en: "Short guided speaking keeps the corrected pattern active without forcing a full recovery loop.", ru: "Короткий guided speaking поддерживает исправленный паттерн активным без полного recovery loop." },
  { en: "Vocabulary repetition", ru: "Повторение словаря" },
  { en: "Review 1 due item before the next larger module.", ru: "Повтори 1 item из очереди перед следующим большим модулем." },
  { en: "Return to the main lesson flow", ru: "Вернуться к основному потоку урока" },
  { en: "Use the broader lesson track to keep corrected patterns alive in context.", ru: "Используй более широкий учебный трек, чтобы удерживать исправленные паттерны в контексте." },
  { en: "Primary weak spot: Present Perfect vs Past Simple.", ru: "Главное слабое место: Present Perfect vs Past Simple." },
  { en: "Listening support added for audio comprehension.", ru: "Для понимания аудио добавлена поддержка listening." },
  { en: "Vocabulary queue has 1 due item.", ru: "В очереди словаря есть 1 item на повторение." },
  { en: "Most overloaded vocabulary category: trainer_skills.", ru: "Самая перегруженная категория словаря: trainer_skills." },
  { en: "Next lesson generation is recovery-first.", ru: "Следующая генерация урока ориентирована сначала на recovery." },
  { en: "Recover your main weak spot", ru: "Восстанови главное слабое место" },
  { en: "Open a focused drill for grammar and fix the repeated pattern.", ru: "Открой focused drill по grammar и исправь повторяющийся паттерн." },
  { en: "Review due vocabulary", ru: "Повтори словарь из очереди" },
  { en: "Repeat 1 word before the next full lesson block.", ru: "Повтори 1 слово перед следующим полным lesson block." },
  { en: "Continue with the recommended lesson", ru: "Продолжить рекомендуемый урок" },
  { en: "Move forward after recovery so the app keeps pushing the long-term track ahead.", ru: "Продвигайся дальше после recovery, чтобы приложение продолжало двигать долгосрочный трек вперёд." },
  { en: "Повторить проблемную грамматику и встроить её в professional speaking.", ru: "Повторить проблемную грамматику и встроить её в professional speaking." },
  { en: "Review weak spots", ru: "Повтор слабых мест" },
  { en: "Посмотри на частые ошибки и повтори правильные паттерны.", ru: "Посмотри на частые ошибки и повтори правильные паттерны." },
  { en: "Present Perfect in professional updates", ru: "Present Perfect в профессиональных обновлениях" },
  { en: "Собери 3 коротких ответа про опыт и недавние результаты.", ru: "Собери 3 коротких ответа про опыт и недавние результаты." },
  { en: "Guided speaking", ru: "Guided speaking" },
  { en: "Ответь устно или текстом на 2 guided prompts.", ru: "Ответь устно или текстом на 2 guided prompts." },
  { en: "Trainer feedback language", ru: "Язык обратной связи тренера" },
  { en: "Смягчи обратную связь и сделай её более естественной.", ru: "Смягчи обратную связь и сделай её более естественной." },
  { en: "Summary and next step", ru: "Итог и следующий шаг" },
  { en: "Зафиксируй 1 правило, 1 фразу и 1 навык на завтра.", ru: "Зафиксируй 1 правило, 1 фразу и 1 навык на завтра." },
  { en: "Проверить grammar, speaking, listening и writing и обновить roadmap.", ru: "Проверить grammar, speaking, listening и writing и обновить roadmap." },
  { en: "Grammar checkpoint", ru: "Grammar checkpoint" },
  { en: "Speaking checkpoint", ru: "Speaking checkpoint" },
  { en: "Listening checkpoint", ru: "Listening checkpoint" },
  { en: "Writing checkpoint", ru: "Writing checkpoint" },
  { en: "Checkpoint summary", ru: "Итог checkpoint" },
  { en: "Рассказывать о прогрессе коротко и уверенно.", ru: "Рассказывать о прогрессе коротко и уверенно." },
  { en: "Сделай акцент на времени и результатах.", ru: "Сделай акцент на времени и результатах." },
  { en: "Давать мягкий feedback after workshop.", ru: "Давать мягкий feedback after workshop." },
  { en: "Используй softer language: could, might, let's.", ru: "Используй softer language: could, might, let's." },
  { en: "Уменьшить русскую замену на /z/ и /s/.", ru: "Уменьшить русскую замену на /z/ и /s/." },
  { en: "Усилить смысловые слова в коротких рабочих фразах.", ru: "Усилить смысловые слова в коротких рабочих фразах." },
  { en: "Напиши короткий ответ с благодарностью, интересом к роли и готовностью обсудить детали.", ru: "Напиши короткий ответ с благодарностью, интересом к роли и готовностью обсудить детали." },
  { en: "Нужен Present Perfect, потому что действие началось в прошлом и продолжается сейчас.", ru: "Нужен Present Perfect, потому что действие началось в прошлом и продолжается сейчас." },
  { en: "Нужно вывести язык слегка между зубами и не заменять звук на /s/.", ru: "Нужно вывести язык слегка между зубами и не заменять звук на /s/." },
  { en: "Для trainer context лучше использовать мягкие формулировки.", ru: "Для trainer context лучше использовать мягкие формулировки." },
  { en: "Insurance Client Flow", ru: "Страховой клиентский флоу" },
  { en: "Отработать needs analysis, language of protection и уверенный follow-up после разговора с клиентом.", ru: "Отработать needs analysis, language of protection и уверенный follow-up после разговора с клиентом." },
  { en: "Review client wording", ru: "Повтор клиентских формулировок" },
  { en: "Повтори ключевые исправления перед новым client update.", ru: "Повтори ключевые исправления перед новым client update." },
  { en: "Future forms for protection planning", ru: "Future forms для планирования защиты" },
  { en: "Собери 3 коротких client-facing sentence о следующем шаге и coverage planning.", ru: "Собери 3 коротких client-facing sentence о следующем шаге и coverage planning." },
  { en: "Guided client update", ru: "Guided client update" },
  { en: "Ответь на guided prompts так, будто это короткий follow-up после needs analysis.", ru: "Ответь на guided prompts так, будто это короткий follow-up после needs analysis." },
  { en: "Insurance needs analysis", ru: "Анализ страховых потребностей" },
  { en: "Сделай формулировки мягкими, точными и понятными для клиента.", ru: "Сделай формулировки мягкими, точными и понятными для клиента." },
  { en: "Summary and next client step", ru: "Итог и следующий клиентский шаг" },
  { en: "Зафиксируй одну удачную фразу, одно grammar правило и один next step.", ru: "Зафиксируй одну удачную фразу, одно grammar правило и один next step." },
  { en: "Banking Client Flow", ru: "Банковский клиентский флоу" },
  { en: "Потренировать product explanations, short updates по операциям и спокойный client-facing tone.", ru: "Потренировать product explanations, short updates по операциям и спокойный client-facing tone." },
  { en: "Review account update language", ru: "Повтор языка для account update" },
  { en: "Повтори короткие исправления перед новым banking explanation.", ru: "Повтори короткие исправления перед новым banking explanation." },
  { en: "Present Perfect in account updates", ru: "Present Perfect в account updates" },
  { en: "Собери 3 коротких banking update о статусе операции и recent changes.", ru: "Собери 3 коротких banking update о статусе операции и recent changes." },
  { en: "Guided banking explanation", ru: "Guided banking explanation" },
  { en: "Дай короткий spoken explanation о платеже, комиссии или следующем шаге.", ru: "Дай короткий spoken explanation о платеже, комиссии или следующем шаге." },
  { en: "Banking product explainer", ru: "Объяснение банковского продукта" },
  { en: "Упростить language around fees, transfers и account options.", ru: "Упростить language around fees, transfers и account options." },
  { en: "Summary and next banking step", ru: "Итог и следующий банковский шаг" },
  { en: "Зафиксируй одну ясную client phrase, одно grammar правило и один next step.", ru: "Зафиксируй одну ясную client phrase, одно grammar правило и один next step." },
  { en: "AI Business Flow", ru: "AI business flow" },
  { en: "Отработать объяснение AI workflow, limits, guardrails и следующего шага для бизнеса.", ru: "Отработать объяснение AI workflow, limits, guardrails и следующего шага для бизнеса." },
  { en: "Review AI workflow language", ru: "Повтор языка для AI workflow" },
  { en: "Повтори ключевые исправления перед новым AI workflow update.", ru: "Повтори ключевые исправления перед новым AI workflow update." },
  { en: "Present Perfect for AI updates", ru: "Present Perfect для AI updates" },
  { en: "Собери 3 коротких update о том, что уже протестировано и что изменилось в workflow.", ru: "Собери 3 коротких update о том, что уже протестировано и что изменилось в workflow." },
  { en: "Guided AI project update", ru: "Guided AI project update" },
  { en: "Дай short business update about an AI workflow and keep the explanation calm and concrete.", ru: "Дай short business update about an AI workflow and keep the explanation calm and concrete." },
  { en: "AI workflow briefing", ru: "Объяснение AI workflow" },
  { en: "Сделай language practical, risk-aware и понятным для business audience.", ru: "Сделай language practical, risk-aware и понятным для business audience." },
  { en: "Summary and next workflow step", ru: "Итог и следующий шаг по workflow" },
  { en: "Зафиксируй одну clear phrase, один limit statement и один next step.", ru: "Зафиксируй одну clear phrase, один limit statement и один next step." },
  { en: "Future Forms for Next Steps", ru: "Future Forms для следующих шагов" },
  { en: "Client needs analysis language", ru: "Язык для анализа клиентских потребностей" },
  { en: "Banking product clarity", ru: "Понятное объяснение банковских продуктов" },
  { en: "Risk-aware AI explanations", ru: "Risk-aware объяснение AI" },
  { en: "cross_cultural", ru: "повседневное общение" },
  { en: "Basics", ru: "Основа" },
  { en: "Learner", ru: "Ученик" },
  { en: "Goals", ru: "Цели" },
  { en: "Skills", ru: "Навыки" },
  { en: "Style", ru: "Формат" },
  { en: "Review", ru: "Проверка" },
  { en: "Name or profile label", ru: "Имя или название профиля" },
  { en: "Native language", ru: "Родной язык" },
  { en: "Other language", ru: "Другой язык" },
  { en: "User account", ru: "Аккаунт пользователя" },
  { en: "Start by choosing the login and email for this learner. The app uses them to create or find a personal account before saving onboarding answers.", ru: "Сначала выбери логин и почту для этого ученика. Приложение использует их, чтобы создать или найти личный аккаунт до сохранения onboarding-ответов." },
  { en: "Add a valid login and email first so the app can create or load the personal account.", ru: "Сначала добавь корректный логин и почту, чтобы приложение смогло создать или загрузить личный аккаунт." },
  { en: "Login and email are stored in the user account table. Learning answers stay in a separate onboarding table.", ru: "Логин и почта хранятся в таблице пользователей. Учебные ответы живут отдельно в таблице онбординга." },
  { en: "Personal cabinet", ru: "Личный кабинет" },
  { en: "Login and email live in the user account table. Update them here without touching the learning profile itself.", ru: "Логин и почта живут в таблице пользователей. Обновляй их здесь, не затрагивая сам учебный профиль." },
  { en: "Save cabinet updates", ru: "Сохранить кабинет" },
  { en: "Build a flexible learner profile for adults, children, career goals, school support, and future multi-user use cases.", ru: "Собери гибкий профиль для взрослых, детей, карьерных целей, школьных задач и будущего multi-user сценария." },
  { en: "Save a broader learning blueprint so the dashboard, lesson flow, and future personalization can adapt to different ages, goals, and study styles.", ru: "Сохрани более широкий learning blueprint, чтобы dashboard, lesson flow и будущая персонализация подстраивались под разный возраст, цели и формат обучения." },
  { en: "Self learner", ru: "Самостоятельный ученик" },
  { en: "School learner", ru: "Школьный ученик" },
  { en: "Professional learner", ru: "Профессиональный пользователь" },
  { en: "Parent or guardian", ru: "Родитель или опекун" },
  { en: "Child", ru: "Ребёнок" },
  { en: "Teen", ru: "Подросток" },
  { en: "Adult", ru: "Взрослый" },
  { en: "Family plan", ru: "Семейный сценарий" },
  { en: "General English", ru: "Общий английский" },
  { en: "School support", ru: "Поддержка для школы" },
  { en: "Exam prep", ru: "Подготовка к экзамену" },
  { en: "Career growth", ru: "Карьерный рост" },
  { en: "Relocation", ru: "Переезд" },
  { en: "Travel", ru: "Путешествия" },
  { en: "Everyday communication", ru: "Повседневное общение" },
  { en: "Speaking confidence", ru: "Уверенность в разговоре" },
  { en: "Vocabulary growth", ru: "Рост словарного запаса" },
  { en: "Grammar accuracy", ru: "Точность грамматики" },
  { en: "Reading comprehension", ru: "Понимание чтения" },
  { en: "Work communication", ru: "Рабочая коммуникация" },
  { en: "School results", ru: "Школьный результат" },
  { en: "Exam result", ru: "Экзаменационный результат" },
  { en: "Travel confidence", ru: "Уверенность в поездках" },
  { en: "Short sessions", ru: "Короткие сессии" },
  { en: "Deep sessions", ru: "Длинные сессии" },
  { en: "Voice first", ru: "Сначала голос" },
  { en: "Text first", ru: "Сначала текст" },
  { en: "Playful learning", ru: "Игровой формат" },
  { en: "Structured plan", ru: "Структурный план" },
  { en: "Gentle feedback", ru: "Мягкая обратная связь" },
  { en: "Parent guided", ru: "С участием родителя" },
  { en: "Clear examples", ru: "Понятные примеры" },
  { en: "Slower pace", ru: "Более медленный темп" },
  { en: "More repetition", ru: "Больше повторения" },
  { en: "Confidence support", ru: "Поддержка уверенности" },
  { en: "Visual structure", ru: "Визуальная структура" },
  { en: "Daily life", ru: "Повседневная жизнь" },
  { en: "Stories", ru: "Истории" },
  { en: "Games", ru: "Игры" },
  { en: "School topics", ru: "Школьные темы" },
  { en: "Technology", ru: "Технологии" },
  { en: "Work and business", ru: "Работа и бизнес" },
  { en: "Culture", ru: "Культура" },
  { en: "Who is this plan for?", ru: "Для кого этот план?" },
  { en: "Learning context", ru: "Контекст обучения" },
  { en: "Primary goal", ru: "Главная цель" },
  { en: "Secondary goals", ru: "Дополнительные цели" },
  { en: "Content lane for the first lesson pack", ru: "Контентный трек для первого набора уроков" },
  { en: "What should the plan train most?", ru: "Что этот план должен прокачивать сильнее всего?" },
  { en: "Track priority", ru: "Приоритет трека" },
  { en: "Study preferences", ru: "Предпочтения по обучению" },
  { en: "Support needs", ru: "Нужная поддержка" },
  { en: "Interest topics", ru: "Интересные темы" },
  { en: "Flexible notes", ru: "Дополнительные заметки" },
  { en: "Add anything important: special goals, child-safe preferences, exam target, or personal context.", ru: "Добавь всё важное: особые цели, child-safe пожелания, цель по экзамену или личный контекст." },
  { en: "Saved skill focus", ru: "Сохранённый фокус навыков" },
  { en: "Learner type", ru: "Тип ученика" },
  { en: "The first content lane is", ru: "Первый контентный трек —" },
  { en: "This learner", ru: "Этот ученик" },
  { en: "is building a plan for", ru: "собирает план для" },
  { en: "This onboarding is designed to stay flexible for adults, teens, children, parent-guided study, and future multi-user product scenarios.", ru: "Этот онбординг специально сделан гибким для взрослых, подростков, детей, занятий с участием родителя и будущих multi-user сценариев продукта." },
  { en: "Everyday Communication", ru: "Повседневное общение" },
  { en: "Everyday English Flow", ru: "Флоу повседневного английского" },
  { en: "Повседневное общение, travel English, school-safe practice и понятные разговорные паттерны.", ru: "Повседневное общение, travel English, school-safe practice и понятные разговорные паттерны." },
  { en: "Укрепить everyday grammar, словарь и уверенное общение в понятных жизненных сценариях.", ru: "Укрепить everyday grammar, словарь и уверенное общение в понятных жизненных сценариях." },
  { en: "Review useful phrases", ru: "Повтор полезных фраз" },
  { en: "Повтори короткие исправления перед новым everyday conversation.", ru: "Повтори короткие исправления перед новым everyday conversation." },
  { en: "Present Perfect in real-life updates", ru: "Present Perfect в жизненных апдейтах" },
  { en: "Собери 3 коротких everyday answers про опыт, недавние действия и планы.", ru: "Собери 3 коротких everyday answers про опыт, недавние действия и планы." },
  { en: "Guided everyday speaking", ru: "Guided everyday speaking" },
  { en: "Ответь на короткие prompts так, будто это дружелюбный everyday conversation.", ru: "Ответь на короткие prompts так, будто это дружелюбный everyday conversation." },
  { en: "Everyday conversation builder", ru: "Конструктор everyday conversation" },
  { en: "Сделай фразы дружелюбными, понятными и удобными для реального общения.", ru: "Сделай фразы дружелюбными, понятными и удобными для реального общения." },
  { en: "Summary and next conversation step", ru: "Итог и следующий разговорный шаг" },
  { en: "Зафиксируй одну удобную фразу, одно правило и один next step.", ru: "Зафиксируй одну удобную фразу, одно правило и один next step." },
  { en: "Everyday conversation flow", ru: "Поток everyday conversation" },
  { en: "Not set yet", ru: "Пока не задано" },
  {
    en: "Pick a login and email so we can create a private learner workspace and save onboarding answers under the right person.",
    ru: "Выбери логин и почту, чтобы создать личное пространство ученика и сохранить ответы онбординга за нужным пользователем.",
  },
  { en: "Add a valid login and email first.", ru: "Сначала добавь корректный логин и почту." },
  {
    en: "Set the learner name, languages, and target level so explanations and lesson pacing start in the right place.",
    ru: "Задай имя ученика, языки и целевой уровень, чтобы объяснения и темп уроков сразу стартовали с правильной точки.",
  },
  { en: "Add a learner name to continue.", ru: "Добавь имя ученика, чтобы продолжить." },
  {
    en: "Tell us who this plan is for and in what context English matters most right now.",
    ru: "Расскажи, для кого этот план и в каком жизненном контексте английский сейчас важнее всего.",
  },
  { en: "You can refine this later in Settings.", ru: "Позже это можно спокойно уточнить в настройках." },
  {
    en: "Choose the strongest outcomes and the first content lane to shape the starting lesson pack.",
    ru: "Выбери главные результаты и первый контентный трек, чтобы собрать стартовый набор уроков.",
  },
  { en: "Pick a main goal and a first content lane.", ru: "Выбери главную цель и первый контентный трек." },
  {
    en: "Balance the engine between speaking, grammar, track depth, and the skills this learner needs most.",
    ru: "Сбалансируй движок между разговорной практикой, грамматикой, глубиной трека и навыками, которые сейчас важнее всего.",
  },
  { en: "Select at least one active skill focus.", ru: "Выбери хотя бы один ключевой навык." },
  {
    en: "Tune the rhythm, support needs, and topics so the trainer feels gentle, useful, and personal.",
    ru: "Настрой ритм, поддержку и темы так, чтобы тренажёр ощущался мягким, полезным и личным.",
  },
  { en: "Keep lesson duration between 10 and 60 minutes.", ru: "Оставь длительность урока в диапазоне от 10 до 60 минут." },
  {
    en: "Check the summary before we open the personal dashboard and the first lesson track.",
    ru: "Проверь итог перед тем, как мы откроем личный дашборд и первый учебный трек.",
  },
  { en: "Review the setup and create the workspace.", ru: "Проверь настройку и создай личное пространство." },
  {
    en: "Login and email create the learner account in one table. The onboarding answers stay separate, so the product can scale cleanly to multiple users later.",
    ru: "Логин и почта создают аккаунт ученика в одной таблице. Ответы онбординга хранятся отдельно, чтобы продукт чисто масштабировался на нескольких пользователей.",
  },
  {
    en: "This is the only setup screen the learner sees before entering the real workspace. Once it is complete, the dashboard and lesson track open automatically.",
    ru: "Это единственный экран настройки перед входом в рабочее пространство. Как только он заполнен, дашборд и учебный трек открываются автоматически.",
  },
  { en: "Account", ru: "Аккаунт" },
  {
    en: "After this step, the learner gets a private dashboard, a first lesson lane, and profile-aware recommendations instead of demo placeholders.",
    ru: "После этого шага ученик получает личный дашборд, первый маршрут уроков и рекомендации по профилю вместо демо-заглушек.",
  },
  { en: "Create a calm, personal start", ru: "Собери спокойный и личный старт" },
  {
    en: "This setup replaces the regular workspace until onboarding is complete, so the learner sees only the questions that matter right now.",
    ru: "Этот экран полностью заменяет обычное рабочее пространство, пока онбординг не завершён, чтобы ученик видел только важные вопросы.",
  },
  { en: "What unlocks after setup", ru: "Что откроется после настройки" },
  { en: "Private learner space", ru: "Личное пространство ученика" },
  { en: "Skill-balanced lesson track", ru: "Сбалансированный учебный трек" },
  { en: "Friendly daily dashboard", ru: "Дружелюбный ежедневный дашборд" },
  { en: "Completion", ru: "Готовность" },
  { en: "Create workspace", ru: "Создать пространство" },
  { en: "Current setup", ru: "Текущая настройка" },
  { en: "Tell us the learner's age and where English is most needed right now.", ru: "Расскажи, какой возраст у ученика и где английский нужнее всего прямо сейчас." },
  { en: "Choose the age group and the main context.", ru: "Выбери возрастную группу и главный контекст." },
  { en: "Learner age group", ru: "Возраст ученика" },
  { en: "Where is English most needed right now?", ru: "Где английский нужен больше всего сейчас?" },
  { en: "For life and communication", ru: "Для жизни и общения" },
  { en: "For work", ru: "Для работы" },
  { en: "For school", ru: "Для школы" },
  { en: "For trips", ru: "Для поездок" },
  { en: "For relocation", ru: "Для переезда" },
  { en: "For exams", ru: "Для экзамена" },
  { en: "Does the learner need adult support?", ru: "Нужна ли ученику поддержка взрослого?" },
  { en: "Yes, adult support helps", ru: "Да, поддержка взрослого поможет" },
  { en: "No, independent enough", ru: "Нет, справится самостоятельно" },
  { en: "Study format", ru: "Формат занятий" },
  { en: "With adult support", ru: "С поддержкой взрослого" },
  { en: "Independent format", ru: "Самостоятельный формат" },
  { en: "Checking login...", ru: "Проверяю имя..." },
  { en: "Name is available", ru: "Имя свободно" },
  { en: "Name is taken", ru: "Имя занято" },
  { en: "Checking if this name is free...", ru: "Проверяю, свободно ли это имя..." },
  { en: "Nice choice, this name is free.", ru: "Хороший выбор, это имя свободно." },
  { en: "This name is already taken.", ru: "Это имя уже занято." },
  { en: "This looks like your existing account.", ru: "Похоже, это уже твой существующий аккаунт." },
  { en: "We could not check this name right now.", ru: "Сейчас не удалось проверить это имя." },
  { en: "Use at least 3 characters so we can check it.", ru: "Используй минимум 3 символа, чтобы мы могли проверить имя." },
  { en: "Existing account found for this login and email", ru: "Найден существующий аккаунт с этим логином и почтой" },
  { en: "Could not verify the login right now", ru: "Сейчас не удалось проверить имя" },
  { en: "Use at least 3 characters", ru: "Используй минимум 3 символа" },
  {
    en: "This login is already taken. Pick one of the free alternatives or enter another one.",
    ru: "Этот логин уже занят. Выбери один из свободных вариантов или введи другой.",
  },
  {
    en: "This login and email already match an existing account. You can continue.",
    ru: "Этот логин и эта почта уже соответствуют существующему аккаунту. Можно продолжить.",
  },
  {
    en: "This name is already in use, but you can tap one of the free options below.",
    ru: "Это имя уже используется, но ниже есть свободные варианты, которые можно выбрать.",
  },
  { en: "Try one of these free options", ru: "Попробуй один из свободных вариантов" },
  {
    en: "Looks good, we will use this email for your account.",
    ru: "Отлично, эту почту мы используем для твоего аккаунта.",
  },
  {
    en: "Enter an email in the usual format, for example name@example.com.",
    ru: "Введи почту в обычном формате, например name@example.com.",
  },
  {
    en: "Add a valid email so we can create the learner workspace.",
    ru: "Добавь корректную почту, чтобы мы могли создать пространство ученика.",
  },
  {
    en: "Checking the login against the current user base...",
    ru: "Проверяю логин по текущей базе пользователей...",
  },
  {
    en: "This login or email is already linked to another account.",
    ru: "Этот логин или эта почта уже привязаны к другому аккаунту.",
  },
  {
    en: "Could not complete onboarding right now.",
    ru: "Сейчас не удалось завершить онбординг.",
  },
  { en: "Start free", ru: "Старт бесплатно" },
  {
    en: "Find your first useful English lesson before any registration.",
    ru: "Найди свой первый полезный урок английского ещё до регистрации.",
  },
  {
    en: "Pick one to three directions, and we will shape the first route around the result you want to feel right away.",
    ru: "Выбери от одного до трёх направлений, и мы соберём первый маршрут вокруг результата, который хочется почувствовать сразу.",
  },
  { en: "No account wall at the start", ru: "Без аккаунта и барьера на старте" },
  { en: "Choose up to 3 focus areas", ru: "Выбери до 3 направлений" },
  { en: "Personal route starts from your picks", ru: "Личный маршрут начнётся с твоего выбора" },
  { en: "Pick your direction", ru: "Выбери направление" },
  { en: "What should this trainer help with first?", ru: "С чем этот тренажёр должен помочь в первую очередь?" },
  {
    en: "Choose from one to three goals. The first experience should feel relevant, light, and worth continuing.",
    ru: "Выбери от одной до трёх целей. Первый опыт должен ощущаться уместным, лёгким и стоящим продолжения.",
  },
  { en: "Speaking confidence", ru: "Уверенное говорение" },
  {
    en: "Short real-life prompts, answers, and quick speaking support.",
    ru: "Короткие жизненные prompts, ответы и быстрая поддержка разговорной практики.",
  },
  { en: "Grammar clarity", ru: "Понятная грамматика" },
  {
    en: "Fix the mistakes that slow your speech down in daily use.",
    ru: "Исправляй ошибки, которые тормозят речь в обычном общении.",
  },
  { en: "Vocabulary growth", ru: "Рост словаря" },
  {
    en: "Useful words you can actually use, not random word lists.",
    ru: "Полезные слова, которые реально пригодятся, а не случайные списки.",
  },
  { en: "Reading flow", ru: "Лёгкое чтение" },
  {
    en: "Understand texts faster and keep the main idea without stress.",
    ru: "Понимай тексты быстрее и держи главный смысл без лишнего стресса.",
  },
  { en: "English for work", ru: "Английский для работы" },
  {
    en: "Meetings, clients, messages, and confident professional wording.",
    ru: "Встречи, клиенты, сообщения и уверенные профессиональные формулировки.",
  },
  { en: "Travel English", ru: "Английский для поездок" },
  {
    en: "Phrases and confidence for airports, hotels, and everyday situations.",
    ru: "Фразы и уверенность для аэропортов, отелей и повседневных ситуаций.",
  },
  { en: "Exam focus", ru: "Фокус на экзамене" },
  {
    en: "A cleaner route toward test tasks, structure, and steady progress.",
    ru: "Более понятный маршрут к заданиям, структуре и спокойному прогрессу.",
  },
  { en: "Your preview", ru: "Твой предварительный маршрут" },
  { en: "Personal English route", ru: "Личный маршрут по английскому" },
  {
    en: "Good start. We will carry these directions into the next setup so your route already leans toward what matters most.",
    ru: "Хороший старт. Мы перенесём эти направления в следующую настройку, чтобы маршрут сразу опирался на то, что для тебя важнее всего.",
  },
  {
    en: "Choose at least one direction to build a more relevant first experience.",
    ru: "Выбери хотя бы одно направление, чтобы собрать более уместный первый опыт.",
  },
  { en: "1 to 3 choices", ru: "От 1 до 3 выборов" },
  {
    en: "The full free lesson hook is the next layer we will shape around these picks.",
    ru: "Полный бесплатный урок-хук станет следующим слоем, который мы соберём вокруг этих выборов.",
  },
  {
    en: "For now this first page already removes the cold account wall and starts from the learner's intention.",
    ru: "Пока что эта первая страница уже убирает холодный барьер аккаунта и начинает путь с намерения ученика.",
  },
  { en: "Build my route", ru: "Собрать мой маршрут" },
  { en: "Skip to full onboarding", ru: "Сразу перейти к полному онбордингу" },
  {
    en: "You already picked 3 directions. Remove one if you want to swap the focus.",
    ru: "Ты уже выбрал 3 направления. Убери одно, если хочешь сменить фокус.",
  },
  {
    en: "The strongest start usually comes from one to three priorities, not from trying to fix everything at once.",
    ru: "Самый сильный старт обычно рождается из 1-3 приоритетов, а не из попытки исправить всё сразу.",
  },
  {
    en: "One platform instead of a stack of disconnected language tools.",
    ru: "Одна платформа вместо стека разрозненных языковых инструментов.",
  },
  { en: "First lesson hook", ru: "Первый урок-хук" },
  { en: "3 short questions", ru: "3 коротких вопроса" },
  { en: "Stop searching", ru: "Хватит искать" },
  {
    en: "You no longer need to search for language-learning tools.",
    ru: "Больше не нужно искать сервисы для изучения языка.",
  },
  {
    en: "Language learning no longer has to be stitched together from separate tools.",
    ru: "Изучение языка больше не нужно собирать по кускам.",
  },
  { en: "The pain", ru: "Боль" },
  {
    en: "Most learners waste time building a personal stack of apps just to cover the basics.",
    ru: "Большинство учеников тратят время на сборку личного стека приложений, чтобы просто закрыть базовые задачи.",
  },
  { en: "The promise", ru: "Обещание" },
  {
    en: "This platform replaces that stack with one smarter route that adapts around you.",
    ru: "Эта платформа заменяет такой стек одним более умным маршрутом, который подстраивается под тебя.",
  },
  {
    en: "Your first lesson and skill snapshot start before payment or registration.",
    ru: "Твой первый урок и краткий срез навыков начинаются ещё до оплаты и регистрации.",
  },
  {
    en: "Do not pay until you try it yourself.",
    ru: "Не плати, пока не попробуешь сам.",
  },
  {
    en: "Do not register until you see the value.",
    ru: "Не регистрируйся, пока не увидишь ценность.",
  },
  {
    en: "Start with three light questions, see what the platform can tailor, and only then move deeper.",
    ru: "Начни с трёх лёгких вопросов, посмотри, как платформа умеет подстроиться, и только потом иди глубже.",
  },
  {
    en: "The first lesson should already feel like relief: one place, one route, one clear next step.",
    ru: "Первый урок уже должен ощущаться как облегчение: одно место, один маршрут, один понятный следующий шаг.",
  },
  {
    en: "What do you want the platform to improve first?",
    ru: "Что платформа должна улучшить для тебя в первую очередь?",
  },
  {
    en: "Choose one to three directions so the first lesson starts from your real goal, not from a generic template.",
    ru: "Выбери от одного до трёх направлений, чтобы первый урок стартовал от твоей реальной цели, а не от общего шаблона.",
  },
  {
    en: "What is the most annoying part of learning right now?",
    ru: "Что в обучении раздражает сильнее всего прямо сейчас?",
  },
  {
    en: "Pick the pain that feels closest right now. We will use it as the emotional entry point for the first experience.",
    ru: "Выбери боль, которая ощущается ближе всего сейчас. Мы используем её как эмоциональную точку входа в первый опыт.",
  },
  { en: "What should your first mini-lesson feel like?", ru: "Каким должен ощущаться твой первый мини-урок?" },
  {
    en: "Choose the tone of the first experience. We will use it to shape the mini-lesson and the handoff into the full route.",
    ru: "Выбери тон первого опыта. Мы используем его, чтобы собрать мини-урок и переход в полный маршрут.",
  },
  {
    en: "Start speaking more freely instead of freezing on simple phrases.",
    ru: "Начни говорить свободнее вместо того, чтобы замирать на простых фразах.",
  },
  {
    en: "Fix the patterns that keep making your speech feel uncertain.",
    ru: "Исправь паттерны, из-за которых речь всё ещё звучит неуверенно.",
  },
  {
    en: "Learn words you can actually reuse in daily conversations.",
    ru: "Учи слова, которые реально можно повторно использовать в обычных разговорах.",
  },
  {
    en: "Read faster and keep the meaning without translating every line.",
    ru: "Читай быстрее и держи смысл без перевода каждой строки.",
  },
  {
    en: "Handle meetings, client language, and work messages in one place.",
    ru: "Закрывай встречи, клиентский язык и рабочие сообщения в одном месте.",
  },
  {
    en: "Feel calmer in airports, hotels, directions, and everyday trip situations.",
    ru: "Чувствуй себя спокойнее в аэропортах, отелях, маршрутах и обычных дорожных ситуациях.",
  },
  {
    en: "Build a cleaner route to tasks, structure, and measurable progress.",
    ru: "Собери более понятный путь к заданиям, структуре и измеримому прогрессу.",
  },
  {
    en: "I am tired of jumping between different apps",
    ru: "Я устал прыгать между разными приложениями",
  },
  {
    en: "I want one place for grammar, words, speaking, and progress.",
    ru: "Я хочу одно место для грамматики, слов, разговорной практики и прогресса.",
  },
  {
    en: "I understand more than I can say",
    ru: "Я понимаю больше, чем могу сказать",
  },
  {
    en: "I know something already, but confidence breaks at the moment of speaking.",
    ru: "Я уже что-то знаю, но уверенность ломается в момент говорения.",
  },
  {
    en: "I keep forgetting words and structures",
    ru: "Я постоянно забываю слова и конструкции",
  },
  {
    en: "I get lost in grammar and start doubting myself",
    ru: "Я путаюсь в грамматике и начинаю сомневаться в себе",
  },
  {
    en: "I want clearer explanations and simple progress.",
    ru: "Я хочу более понятные объяснения и простой прогресс.",
  },
  {
    en: "I learn something, then lose it because there is no steady route.",
    ru: "Я что-то учу, а потом теряю, потому что нет стабильного маршрута.",
  },
  {
    en: "I need a clear daily system",
    ru: "Мне нужна понятная ежедневная система",
  },
  {
    en: "I want the platform to tell me what matters next instead of guessing alone.",
    ru: "Я хочу, чтобы платформа подсказывала, что важно дальше, а не заставляла угадывать в одиночку.",
  },
  {
    en: "Quick win in a few minutes",
    ru: "Быстрый результат за несколько минут",
  },
  {
    en: "Show me the platform value fast and keep the first step light.",
    ru: "Покажи ценность платформы быстро и сохрани первый шаг лёгким.",
  },
  { en: "Calm guided mini-lesson", ru: "Спокойный мини-урок с сопровождением" },
  {
    en: "I want a smooth first lesson with a clear sense of progress.",
    ru: "Я хочу плавный первый урок с ясным ощущением прогресса.",
  },
  { en: "Smart diagnostic preview", ru: "Умный диагностический preview" },
  {
    en: "Show me where my first strong result can come from.",
    ru: "Покажи, откуда может прийти мой первый сильный результат.",
  },
  {
    en: "What do you want to improve first?",
    ru: "Что ты хочешь улучшить в первую очередь?",
  },
  {
    en: "How should the first lesson feel?",
    ru: "Каким должен ощущаться первый урок?",
  },
  {
    en: "Choose one to three directions for the first 1-2 minute lesson.",
    ru: "Выбери от одного до трёх направлений для первого урока на 1-2 минуты.",
  },
  {
    en: "Choose the main friction so the first lesson solves something real.",
    ru: "Выбери главное затруднение, чтобы первый урок решил что-то реальное.",
  },
  {
    en: "Choose the tone of the first mini-lesson and quick skill snapshot.",
    ru: "Выбери тон первого мини-урока и короткого среза навыков.",
  },
  {
    en: "Pick the tone, then start the first short lesson and see the result.",
    ru: "Выбери тон, а затем начни первый короткий урок и увидь результат.",
  },
  {
    en: "A short lesson comes first. Registration and payment can wait until the value feels obvious.",
    ru: "Сначала идёт короткий урок. Регистрация и оплата подождут, пока ценность не станет очевидной.",
  },
  { en: "One system", ru: "Одна система" },
  { en: "Motivation", ru: "Мотивация" },
  { en: "AI first", ru: "Сначала AI" },
  { en: "Value first", ru: "Сначала польза" },
  {
    en: "Everything for language learning in one calm system.",
    ru: "Всё для изучения языка в одной спокойной системе.",
  },
  {
    en: "Motivation should go into learning, not platform search.",
    ru: "Мотивацию нужно направлять в обучение, а не в поиск платформ.",
  },
  {
    en: "The platform shows value first, and only then asks for details.",
    ru: "Платформа сначала показывает пользу, а уже потом просит данные.",
  },
  {
    en: "Starting is hard when every platform only solves one part of the language.",
    ru: "Трудно начать, когда каждая платформа закрывает только одну часть изучения языка.",
  },
  {
    en: "One app pushes vocabulary, another focuses on grammar, a third on speaking. That split makes it harder to start with confidence.",
    ru: "Одна платформа про слова, другая про грамматику, третья про разговорную речь. Из-за такого разделения старт становится сложнее и неувереннее.",
  },
  {
    en: "The search for the right stack kills the first wave of motivation.",
    ru: "Поиск правильного стека сервисов убивает первую волну мотивации.",
  },
  {
    en: "People want to start learning in the moment of motivation, but platform-hopping, comparison, and early forms drain that energy fast.",
    ru: "Люди хотят начать учиться в моменте мотивации, но прыжки между платформами, сравнение и ранние формы быстро забирают этот импульс.",
  },
  {
    en: "AI should show value first: a mini-lesson, a skill snapshot, and a smart next step.",
    ru: "AI должен сначала показывать ценность: мини-урок, срез навыков и умный следующий шаг.",
  },
  {
    en: "Instead of asking for registration up front, the platform can use AI to build a 1-2 minute lesson, surface early strengths, and show what to do next.",
    ru: "Вместо ранней регистрации платформа может с помощью AI собрать урок на 1-2 минуты, показать сильные стороны и подсказать, что делать дальше.",
  },
  {
    en: "Scroll to build the first lesson",
    ru: "Прокрути вниз, чтобы собрать первый урок",
  },
  {
    en: "Try the first lesson",
    ru: "Попробовать первый урок",
  },
  {
    en: "Answer 3 short questions and build the first lesson.",
    ru: "Ответь на 3 коротких вопроса и собери первый урок.",
  },
  { en: "Unified English route", ru: "Единый маршрут по английскому" },
  { en: "Mini-onboarding", ru: "Мини-онбординг" },
  { en: "Mini-lesson preview", ru: "Предпросмотр мини-урока" },
  {
    en: "Your first route will start from these choices, then hand off into the deeper onboarding and your full learning workspace.",
    ru: "Твой первый маршрут начнётся с этих выборов, а затем плавно перейдёт в более глубокий онбординг и полное учебное пространство.",
  },
  {
    en: "You already picked 3 directions. That is enough for a strong focused start.",
    ru: "Ты уже выбрал 3 направления. Этого достаточно для сильного сфокусированного старта.",
  },
  {
    en: "Choose one to three directions. A focused start works better than trying to fix everything.",
    ru: "Выбери от одного до трёх направлений. Сфокусированный старт работает лучше, чем попытка исправить всё сразу.",
  },
  {
    en: "Pick the frustration we should solve first. That is where the wow-effect should begin.",
    ru: "Выбери фрустрацию, которую мы должны снять первой. Именно там и должен начаться вау-эффект.",
  },
  {
    en: "Choose the tone, then we will carry this setup into your next step.",
    ru: "Выбери тон, и мы перенесём эту настройку в следующий шаг.",
  },
  { en: "Build my mini-lesson", ru: "Собрать мой мини-урок" },
  { en: "Focus", ru: "Фокус" },
  { en: "Pain", ru: "Боль" },
  { en: "Tone", ru: "Тон" },
  { en: "What happens next", ru: "Что будет дальше" },
  {
    en: "We use these answers to shape the first lesson feeling, then carry them into the deeper onboarding and your full route.",
    ru: "Мы используем эти ответы, чтобы задать ощущение первого урока, а затем переносим их в более глубокий онбординг и твой полный маршрут.",
  },
];

const translationTable = new Map<string, TranslationEntry>();

for (const entry of translationEntries) {
  translationTable.set(entry.en, entry);
  translationTable.set(entry.ru, entry);
}

function localeTag(locale: AppLocale) {
  return locale === "ru" ? "ru-RU" : "en-US";
}

function parseDateValue(value: string) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return new Date(`${value}T00:00:00`);
  }

  return new Date(value);
}

function pluralizeRussian(value: number, one: string, few: string, many: string) {
  const mod10 = value % 10;
  const mod100 = value % 100;

  if (mod10 === 1 && mod100 !== 11) {
    return one;
  }

  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return few;
  }

  return many;
}

export function isAppLocale(value: unknown): value is AppLocale {
  return value === "ru" || value === "en";
}

export function normalizeLocale(value: unknown, fallback: AppLocale = "ru"): AppLocale {
  return isAppLocale(value) ? value : fallback;
}

export function readStoredLocale() {
  if (typeof window === "undefined") {
    return null;
  }

  const storedValue = window.localStorage.getItem(APP_LOCALE_STORAGE_KEY);
  return isAppLocale(storedValue) ? storedValue : null;
}

export function writeStoredLocale(locale: AppLocale) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(APP_LOCALE_STORAGE_KEY, locale);
}

export function translateText(locale: AppLocale, value: string) {
  return translationTable.get(value)?.[locale] ?? value;
}

export function translateToken(locale: AppLocale, value: string) {
  return translateText(locale, value.replace(/_/g, " "));
}

export function translateList(locale: AppLocale, values: string[]) {
  return values.map((value) => translateToken(locale, value)).join(", ");
}

function formatVocabularyItemCount(locale: AppLocale, count: number) {
  if (locale === "ru") {
    return `${count} ${pluralizeRussian(count, "слово", "слова", "слов")}`;
  }

  return `${count} vocabulary item${count === 1 ? "" : "s"}`;
}

export function formatAdaptiveHeadline(locale: AppLocale, name: string, focusArea: string) {
  const translatedFocus = translateToken(locale, focusArea);
  const safeName = name.trim();

  if (locale === "ru") {
    return safeName ? `${safeName}, сегодня главный фокус — ${translatedFocus}.` : `Сегодня главный фокус — ${translatedFocus}.`;
  }

  return safeName ? `${safeName}, today's main focus is ${translatedFocus}.` : `Today's main focus is ${translatedFocus}.`;
}

export function formatAdaptiveSummary(
  locale: AppLocale,
  options: {
    weakSpotTitle?: string | null;
    dueVocabularyCount: number;
    listeningFocus?: string | null;
    activeVocabularyCount: number;
    masteredVocabularyCount: number;
    minutesCompletedToday: number;
  },
) {
  const weakSpot = options.weakSpotTitle ? translateText(locale, options.weakSpotTitle) : null;
  const listeningFocus = options.listeningFocus ? translateToken(locale, options.listeningFocus) : null;

  if (locale === "ru") {
    const parts = [
      weakSpot ? `Начни с ${weakSpot}.` : "Начни с самого актуального слабого места.",
      options.dueVocabularyCount > 0
        ? `На повторение ждут ${formatVocabularyItemCount(locale, options.dueVocabularyCount)}.`
        : "Срочных слов на повторение сейчас нет.",
      listeningFocus ? `По listening сейчас нужен акцент на ${listeningFocus}.` : null,
      `Активных карточек: ${options.activeVocabularyCount}, закреплённых: ${options.masteredVocabularyCount}.`,
      `Сегодня уже закрыто ${options.minutesCompletedToday} мин.`,
    ].filter(Boolean);

    return parts.join(" ");
  }

  const parts = [
    weakSpot ? `Start with ${weakSpot}.` : "Start with the most active weak spot.",
    options.dueVocabularyCount > 0
      ? `You have ${formatVocabularyItemCount(locale, options.dueVocabularyCount)} due for review.`
      : "There are no urgent vocabulary reviews right now.",
    listeningFocus ? `Listening still needs support around ${listeningFocus}.` : null,
    `Vocabulary queue: ${options.activeVocabularyCount} active, ${options.masteredVocabularyCount} mastered.`,
    `You have already logged ${options.minutesCompletedToday} min today.`,
  ].filter(Boolean);

  return parts.join(" ");
}

export function formatRecommendationGoal(
  locale: AppLocale,
  options: {
    lessonType: string;
    focusArea: string;
    weakSpotTitles: string[];
    dueVocabularyCount: number;
    professionTrack: string;
  },
) {
  const translatedWeakSpots = options.weakSpotTitles.slice(0, 2).map((item) => translateText(locale, item));
  const primaryTarget = translatedWeakSpots[0] ?? translateToken(locale, options.focusArea);
  const trackLabel = translateToken(locale, options.professionTrack);
  const duePart =
    options.dueVocabularyCount > 0
      ? locale === "ru"
        ? ` Заодно повтори ${formatVocabularyItemCount(locale, options.dueVocabularyCount)} из текущей очереди.`
        : ` Review ${formatVocabularyItemCount(locale, options.dueVocabularyCount)} from the current queue while the correction is fresh.`
      : "";

  if (options.lessonType === "recovery") {
    if (locale === "ru") {
      return `Сначала коротко закрой ${primaryTarget}, затем вернись в основной поток уроков для трека ${trackLabel}.${duePart}`;
    }

    return `Take a short repair pass on ${primaryTarget}, then return to the main ${trackLabel} lesson flow.${duePart}`;
  }

  if (locale === "ru") {
    const carryForward =
      translatedWeakSpots.length > 0
        ? `Держи в работе ${translatedWeakSpots.join(", ")} внутри основного трека ${trackLabel}.`
        : `Продолжай основной трек ${trackLabel} и закрепляй текущий фокус на ${translateToken(locale, options.focusArea)}.`;
    return `${carryForward}${duePart}`;
  }

  const carryForward =
    translatedWeakSpots.length > 0
      ? `Keep ${translatedWeakSpots.join(", ")} active inside the main ${trackLabel} track.`
      : `Continue the main ${trackLabel} track and keep the current focus on ${translateToken(locale, options.focusArea)}.`;
  return `${carryForward}${duePart}`;
}

export function formatRoadmapSummary(
  locale: AppLocale,
  options: {
    declaredCurrentLevel: string;
    estimatedLevel: string;
    targetLevel: string;
    weakestSkills: string[];
    nextFocus: string[];
  },
) {
  const weakestSkills = options.weakestSkills.slice(0, 2).map((item) => translateText(locale, item));
  const nextFocus = options.nextFocus.slice(0, 2).map((item) => translateText(locale, item));
  const weakestLabel = weakestSkills.join(", ") || (locale === "ru" ? "ключевые навыки" : "core skills");
  const focusLabel = nextFocus.join(", ") || (locale === "ru" ? "следующий адаптивный шаг" : "the next adaptive step");

  if (locale === "ru") {
    const mismatchNote =
      options.declaredCurrentLevel !== options.estimatedLevel
        ? ` По живым данным уровень сейчас ближе к ${options.estimatedLevel}.`
        : ` Текущая оценка подтверждает уровень ${options.estimatedLevel}.`;
    return `Путь к ${options.targetLevel}: сначала укрепить ${weakestLabel}, затем закрепить ${focusLabel}.${mismatchNote}`;
  }

  const mismatchNote =
    options.declaredCurrentLevel !== options.estimatedLevel
      ? ` Live progress currently looks closer to ${options.estimatedLevel}.`
      : ` Live progress is aligned with ${options.estimatedLevel}.`;
  return `Roadmap to ${options.targetLevel}: strengthen ${weakestLabel} first, then keep ${focusLabel} stable in the next cycle.${mismatchNote}`;
}

export function formatDate(locale: AppLocale, value: string) {
  const parsedValue = parseDateValue(value);
  if (Number.isNaN(parsedValue.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(localeTag(locale), {
    dateStyle: "medium",
  }).format(parsedValue);
}

export function formatDateTime(locale: AppLocale, value: string) {
  const parsedValue = parseDateValue(value);
  if (Number.isNaN(parsedValue.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(localeTag(locale), {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsedValue);
}

export function formatDays(locale: AppLocale, value: number) {
  if (locale === "ru") {
    return `${value} ${pluralizeRussian(value, "день", "дня", "дней")}`;
  }

  return `${value} day${value === 1 ? "" : "s"}`;
}
