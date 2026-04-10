import type { AppLocale } from "../../shared/i18n/locale";
import type { GuestDirectionId } from "./guest-intent";

export type WelcomeProofLessonInputMode = "text" | "voice";
export type WelcomeProofLessonClarityStatusKey = "easy" | "almost" | "needsMore";

export type WelcomeProofLessonScenario = {
  id: string;
  guestIntentDirections: GuestDirectionId[];
  intro: {
    title: string;
    description: string;
    microCopy: string;
    cta: string;
  };
  situation: {
    label: string;
    title: string;
    description: string;
    coachLabel: string;
    coachPrompt: string;
    coachSpokenPrompt?: string;
    coachReplayCta: string;
    primaryCta: string;
    secondaryCta: string;
  };
  firstAttempt: {
    title: string;
    voiceStartCta: string;
    voiceRecordingCta: string;
    voiceDoneCta: string;
    fallbackCta: string;
    textPlaceholder: string;
    submitCta: string;
    saidLabel: string;
    wroteLabel: string;
  };
  feedback: {
    title: string;
    userVersionLabel: string;
    improvedVersionLabel: string;
    explanationPrimary: string;
    explanationSecondary: string;
    patternLabel: string;
    patternValue: string;
    examplesLabel: string;
    examples: string[];
    cta: string;
    followUp: string;
  };
  clarity: {
    title: string;
    subtitle: string;
    statuses: Record<WelcomeProofLessonClarityStatusKey, string>;
    hintsTitle: string;
    hints: string[];
    cta: string;
  };
  retry: {
    title: string;
    task: string;
    primaryCta: string;
    secondaryCta: string;
    voiceStartCta: string;
    voiceRecordingCta: string;
    voiceDoneCta: string;
    fallbackCta: string;
    textPlaceholder: string;
    submitCta: string;
    saidLabel: string;
    wroteLabel: string;
    successTitle: string;
    successDescription: string;
    acceptedAnswers: string[];
    idealAnswer: string;
  };
  result: {
    title: string;
    points: string[];
    comparisonTitle: string;
    beforeLabel: string;
    beforeValue: string;
    afterLabel: string;
    afterValue: string;
    comment: string;
    primaryCta: string;
    secondaryCta: string;
    note: string;
  };
  errors: {
    micUnavailable: string;
    recognitionFailed: string;
    answerTooShort: string;
    answerRequired: string;
    networkRetry: string;
  };
  languageTargets: {
    firstAttemptImproved: string;
  };
};

export const welcomeProofLessonScenarios: Record<
  AppLocale,
  readonly WelcomeProofLessonScenario[]
> = {
  ru: [
    {
      id: "proof-cafe-order",
      guestIntentDirections: ["speaking", "grammar", "vocabulary"],
      intro: {
        title: "Попробуй, как это работает",
        description:
          "За 90 секунд ты увидишь, как фраза превращается в речь, грамматику и готовый шаблон.",
        microCopy: "Без регистрации",
        cta: "Начать урок",
      },
      situation: {
        label: "Ситуация",
        title: "Представь: ты в кафе.",
        description: "Нужно вежливо заказать кофе без сахара.",
        coachLabel: "Лиза",
        coachPrompt:
          "Представь, что ты в кафе. Тебе нужно вежливо заказать кофе без сахара. Ответь так, как ты бы сказал это по-английски.",
        coachSpokenPrompt:
          "Как бы ты вежливо заказал кофе без сахара на английском языке?",
        coachReplayCta: "Послушать ещё раз",
        primaryCta: "Ответить голосом",
        secondaryCta: "Нет микрофона? Ответить текстом",
      },
      firstAttempt: {
        title: "Как бы ты сказал это по-английски?",
        voiceStartCta: "Начать запись",
        voiceRecordingCta: "Идёт запись...",
        voiceDoneCta: "Готово",
        fallbackCta: "Переключиться на текст",
        textPlaceholder: "Напиши свою версию фразы",
        submitCta: "Проверить",
        saidLabel: "Ты сказал:",
        wroteLabel: "Ты написал:",
      },
      feedback: {
        title: "Можно естественнее",
        userVersionLabel: "Твоя версия",
        improvedVersionLabel: "Более естественно",
        explanationPrimary:
          "Для вежливой просьбы здесь лучше использовать I’d like, а не I want.",
        explanationSecondary:
          "a coffee — это одна чашка или одна порция. В заказе напитки часто говорят именно так.",
        patternLabel: "Запомни шаблон",
        patternValue: "I’d like + a/an + drink + detail",
        examplesLabel: "Так этот шаблон работает в живой речи:",
        examples: [
          "I’d like a coffee without sugar.",
          "I’d like a tea without milk.",
        ],
        cta: "Применить ещё раз",
        followUp: "Сейчас сразу используем тот же шаблон ещё раз.",
      },
      clarity: {
        title: "Понятность речи",
        subtitle: "Насколько легко тебя понять в этой фразе",
        statuses: {
          easy: "Понять легко",
          almost: "Почти хорошо",
          needsMore: "Нужно чуть яснее",
        },
        hintsTitle: "Что можно улучшить",
        hints: [
          "Мягче склей I’d like",
          "Чётче выдели coffee",
          "Не теряй without",
        ],
        cta: "Повторить фразу",
      },
      retry: {
        title: "Теперь попробуй ещё раз",
        task: "Скажи: Я бы хотел чай без молока.",
        primaryCta: "Ответить голосом",
        secondaryCta: "Ответить текстом",
        voiceStartCta: "Начать запись",
        voiceRecordingCta: "Идёт запись...",
        voiceDoneCta: "Готово",
        fallbackCta: "Переключиться на текст",
        textPlaceholder: "Напиши свою версию фразы",
        submitCta: "Проверить",
        saidLabel: "Ты сказал:",
        wroteLabel: "Ты написал:",
        successTitle: "Да — шаблон уже работает.",
        successDescription: "Ты уже переносишь его в новую фразу.",
        acceptedAnswers: [
          "I'd like a tea without milk.",
          "I'd like tea without milk.",
          "I would like a tea without milk.",
          "I would like tea without milk.",
        ],
        idealAnswer: "I’d like a tea without milk.",
      },
      result: {
        title: "За 2 минуты ты уже:",
        points: [
          "сделал фразу вежливее и естественнее",
          "запомнил шаблон I’d like + drink + detail",
          "сразу перенёс его в новую фразу",
        ],
        comparisonTitle: "До / После",
        beforeLabel: "До",
        beforeValue: "I want coffee without sugar.",
        afterLabel: "После",
        afterValue: "I’d like a coffee without sugar.",
        comment: "Звучит мягче, естественнее и увереннее.",
        primaryCta: "Собрать урок под мою цель",
        secondaryCta: "Показать ещё один пример",
        note: "Можно перейти в урок под свою цель или посмотреть ещё один короткий кейс.",
      },
      errors: {
        micUnavailable: "Микрофон сейчас недоступен. Можно продолжить текстом.",
        recognitionFailed:
          "Не удалось уверенно распознать фразу. Попробуй ещё раз или ответь текстом.",
        answerTooShort: "Попробуй чуть полнее — хотя бы одной короткой фразой.",
        answerRequired:
          "Нужна хотя бы одна попытка, чтобы Verba показала разницу.",
        networkRetry: "Что-то пошло не так. Попробуем ещё раз.",
      },
      languageTargets: {
        firstAttemptImproved: "I’d like a coffee without sugar.",
      },
    },
  ],
  en: [
    {
      id: "proof-cafe-order",
      guestIntentDirections: ["speaking", "grammar", "vocabulary"],
      intro: {
        title: "Try a live lesson",
        description:
          "In 90 seconds Verba shows how one phrase becomes speaking, grammar, and a useful pattern.",
        microCopy: "No sign-up",
        cta: "Start the short lesson",
      },
      situation: {
        label: "Situation",
        title: "Imagine: you are in a cafe.",
        description: "You need to politely order a coffee without sugar.",
        coachLabel: "Liza",
        coachPrompt:
          "Imagine you are in a cafe. You need to order a coffee without sugar politely. Answer the way you would say it in English.",
        coachSpokenPrompt:
          "How would you politely order a coffee without sugar in English?",
        coachReplayCta: "Hear it again",
        primaryCta: "Answer by voice",
        secondaryCta: "No microphone? Answer by text",
      },
      firstAttempt: {
        title: "How would you say this in English?",
        voiceStartCta: "Start recording",
        voiceRecordingCta: "Recording...",
        voiceDoneCta: "Done",
        fallbackCta: "Switch to text",
        textPlaceholder: "Write your version of the phrase",
        submitCta: "Check",
        saidLabel: "You said:",
        wroteLabel: "You wrote:",
      },
      feedback: {
        title: "This can sound more natural",
        userVersionLabel: "Your version",
        improvedVersionLabel: "More natural",
        explanationPrimary:
          "For a polite request it is better to use I’d like instead of I want.",
        explanationSecondary:
          "a coffee means one cup or one serving. In drink orders people often say it this way.",
        patternLabel: "Remember the pattern",
        patternValue: "I’d like + a/an + drink + detail",
        examplesLabel: "This is how the pattern works in live speech:",
        examples: [
          "I’d like a coffee without sugar.",
          "I’d like a tea without milk.",
        ],
        cta: "Apply it once more",
        followUp: "Now we use the same pattern again right away.",
      },
      clarity: {
        title: "Speech clarity",
        subtitle: "How easy it is to understand you in this phrase",
        statuses: {
          easy: "Easy to understand",
          almost: "Almost good",
          needsMore: "Needs a little more clarity",
        },
        hintsTitle: "What can improve",
        hints: [
          "Blend I’d like more softly",
          "Stress coffee more clearly",
          "Do not lose without",
        ],
        cta: "Repeat the phrase",
      },
      retry: {
        title: "Now try once more",
        task: "Say: I’d like a tea without milk.",
        primaryCta: "Answer by voice",
        secondaryCta: "Answer by text",
        voiceStartCta: "Start recording",
        voiceRecordingCta: "Recording...",
        voiceDoneCta: "Done",
        fallbackCta: "Switch to text",
        textPlaceholder: "Write your version of the phrase",
        submitCta: "Check",
        saidLabel: "You said:",
        wroteLabel: "You wrote:",
        successTitle: "Yes — the pattern already works.",
        successDescription: "You are already moving it into a new phrase.",
        acceptedAnswers: [
          "I'd like a tea without milk.",
          "I'd like tea without milk.",
          "I would like a tea without milk.",
          "I would like tea without milk.",
        ],
        idealAnswer: "I’d like a tea without milk.",
      },
      result: {
        title: "In 2 minutes you already:",
        points: [
          "made the phrase sound more natural and polite",
          "learned the I’d like + drink + detail pattern",
          "used it right away in a new phrase",
        ],
        comparisonTitle: "Before / After",
        beforeLabel: "Before",
        beforeValue: "I want coffee without sugar.",
        afterLabel: "After",
        afterValue: "I’d like a coffee without sugar.",
        comment: "It sounds softer, more natural, and more confident.",
        primaryCta: "Build a lesson for my goal",
        secondaryCta: "Show another example",
        note: "You can move into a goal-based lesson or open one more short example.",
      },
      errors: {
        micUnavailable: "The microphone is not available right now. You can continue by text.",
        recognitionFailed:
          "We could not confidently recognize the phrase. Try again or answer by text.",
        answerTooShort: "Try a little more fully — at least one short phrase.",
        answerRequired:
          "We need at least one attempt so Verba can show the difference.",
        networkRetry: "Something went wrong. Let’s try once more.",
      },
      languageTargets: {
        firstAttemptImproved: "I’d like a coffee without sugar.",
      },
    },
  ],
};
