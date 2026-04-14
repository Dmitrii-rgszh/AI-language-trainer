import type { Lesson, LessonRecommendation } from "../../entities/lesson/model";
import type { Mistake, WeakSpot } from "../../entities/mistake/model";
import type { ProgressSnapshot } from "../../entities/progress/model";
import { defaultOnboardingAnswers, type UserProfile } from "../../entities/user/model";
import type {
  DailyLoopPlan,
  DiagnosticRoadmap,
  DashboardData,
  GrammarTopic,
  LearnerJourneyState,
  ProfessionTrackCard,
  PronunciationDrill,
  ProviderStatus,
  QuickAction,
  SpeakingScenario,
  WritingTask,
} from "../types/app-data";
import { routes } from "../constants/routes";

export const mockProfile: UserProfile = {
  id: "user-local-1",
  name: "Alex",
  nativeLanguage: "ru",
  currentLevel: "A2",
  targetLevel: "B2",
  professionTrack: "cross_cultural",
  preferredUiLanguage: "ru",
  preferredExplanationLanguage: "ru",
  lessonDuration: 25,
  speakingPriority: 8,
  grammarPriority: 7,
  professionPriority: 5,
  onboardingAnswers: {
    ...defaultOnboardingAnswers,
    primaryGoal: "everyday_communication",
    learningContext: "general_english",
    interestTopics: ["daily_life", "travel", "stories"],
  },
};

export const mockProgress: ProgressSnapshot = {
  id: "progress-1",
  grammarScore: 54,
  speakingScore: 48,
  listeningScore: 42,
  pronunciationScore: 40,
  writingScore: 51,
  professionScore: 46,
  regulationScore: 18,
  streak: 6,
  dailyGoalMinutes: 25,
  minutesCompletedToday: 12,
  history: [
    {
      id: "lesson-history-1",
      title: "Present Perfect and Work Updates",
      lessonType: "mixed",
      completedAt: "2026-03-19",
      score: 74,
    },
    {
      id: "lesson-history-2",
      title: "Trainer Feedback Language",
      lessonType: "professional",
      completedAt: "2026-03-18",
      score: 69,
    },
  ],
};

export const mockWeakSpots: WeakSpot[] = [
  {
    id: "weak-1",
    title: "Present Perfect vs Past Simple",
    category: "grammar",
    recommendation: "Нужен короткий review + speaking drill на опыт и недавние действия.",
  },
  {
    id: "weak-2",
    title: "Sound /th/",
    category: "pronunciation",
    recommendation: "Добавить 5 минут shadowing и minimal pairs.",
  },
  {
    id: "weak-3",
    title: "Feedback language for workshops",
    category: "profession",
    recommendation: "Повторить мягкие формулировки для фасилитации и coaching.",
  },
];

export const mockRecommendation: LessonRecommendation = {
  id: "lesson-recommendation-1",
  title: "Daily Mixed Lesson: Grammar + Speaking + Trainer English",
  lessonType: "mixed",
  goal: "Укрепить Present Perfect и потренировать trainer feedback language.",
  duration: 25,
  focusArea: "grammar,speaking,profession",
};

export const mockQuickActions: QuickAction[] = [
  {
    id: "action-1",
    title: "Grammar Sprint",
    description: "10 минут на ключевую тему и быстрый drill.",
    route: routes.grammar,
  },
  {
    id: "action-2",
    title: "Speaking Check-in",
    description: "Короткий guided speaking с фидбеком.",
    route: routes.speaking,
  },
  {
    id: "action-3",
    title: "Profession Hub",
    description: "Профессиональный английский по текущему треку.",
    route: routes.profession,
  },
];

export const mockDailyLoopPlan: DailyLoopPlan = {
  id: "daily-loop-1",
  planDateKey: "2026-04-13",
  status: "planned",
  stage: "first_path",
  sessionKind: "recommended",
  focusArea: "speaking",
  headline: "Alex, your first guided daily loop is ready.",
  summary:
    "Start from speaking confidence, reinforce grammar in context, and let the system shape tomorrow's next best step from one connected session.",
  whyThisNow:
    "The proof lesson and onboarding both point to a voice-led start, so the first loop keeps the path simple and immediately useful.",
  nextStepHint: "Open today's loop, finish the first guided session, and then review the updated next step.",
  preferredMode: "voice_first",
  timeBudgetMinutes: 25,
  estimatedMinutes: 24,
  recommendedLessonType: "mixed",
  recommendedLessonTitle: "First Guided Daily Loop",
  lessonRunId: null,
  completedAt: null,
  steps: [
    {
      id: "warm-start",
      skill: "coach",
      title: "Warm start",
      description: "Liza frames the session and explains why this is the right move today.",
      durationMinutes: 2,
    },
    {
      id: "vocabulary-recall",
      skill: "vocabulary",
      title: "Vocabulary recall",
      description: "Bring back a few words that the next speaking response will need.",
      durationMinutes: 3,
    },
    {
      id: "response",
      skill: "speaking",
      title: "Speaking response",
      description: "Answer one guided prompt and convert correction into a stronger version.",
      durationMinutes: 6,
    },
  ],
};

export const mockJourneyState: LearnerJourneyState = {
  userId: "user-local-1",
  stage: "daily_loop_ready",
  source: "proof_lesson",
  preferredMode: "voice_first",
  diagnosticReadiness: "soft_start",
  timeBudgetMinutes: 25,
  currentFocusArea: "speaking",
  currentStrategySummary:
    "The current strategy starts from speaking confidence, then reinforces grammar and vocabulary inside one connected daily ritual.",
  nextBestAction:
    "Finish today's guided loop, review the result summary, and let tomorrow's route sharpen around the same signal.",
  lastDailyPlanId: "daily-loop-1",
  strategySnapshot: {
    focusArea: "speaking",
    primaryGoal: "everyday_communication",
    sessionSummary: {
      outcomeBand: "stable",
      headline: "This session kept the route stable.",
      whatWorked: "Speaking response gave the system enough confidence to keep the main route connected instead of rebuilding it from zero.",
      watchSignal: "The system should still watch Present Perfect vs Past Simple so the same weak pattern does not reappear in the next route.",
      strategyShift: "Tomorrow stays centered on grammar while keeping a light watch on Present Perfect vs Past Simple.",
      coachNote: "This is the moment to keep the ritual going and let the next route sharpen naturally.",
      carryOverSignalLabel: "Speaking response",
      watchSignalLabel: "Present Perfect vs Past Simple",
      weakSpotTitle: "Present Perfect vs Past Simple",
      strongestSignalLabel: "Speaking response",
      weakestSignalLabel: "Grammar pattern",
    },
    tomorrowPreview: {
      focusArea: "grammar",
      sessionKind: "recommended",
      headline: "Tomorrow returns with a guided grammar-led loop.",
      reason: "The next route narrows a little so the corrected speaking signal can become more stable.",
      nextStepHint: "Come back tomorrow and start from the guided grammar-led loop.",
      recommendedLessonTitle: "Tomorrow Guided Loop",
      continuityMode: "guided",
      carryOverSignalLabel: "Speaking response",
      watchSignalLabel: "Present Perfect vs Past Simple",
    },
  },
  onboardingCompletedAt: "2026-04-13T10:10:00",
  createdAt: "2026-04-13T10:10:00",
  updatedAt: "2026-04-13T10:10:00",
};

export const mockDashboardData: DashboardData = {
  profile: mockProfile,
  progress: mockProgress,
  weakSpots: mockWeakSpots,
  recommendation: mockRecommendation,
  dailyLoopPlan: mockDailyLoopPlan,
  journeyState: mockJourneyState,
  studyLoop: {
    focusArea: "grammar",
    headline: "Alex, today's adaptive focus is grammar.",
    summary:
      "Start from Present Perfect vs Past Simple, keep the daily chain moving, and clear 1 vocabulary review item. Minutes completed today: 12.",
    recommendation: mockRecommendation,
    weakSpots: mockWeakSpots.slice(0, 2),
    dueVocabulary: [
      {
        id: "vocab-1",
        word: "stakeholder",
        translation: "заинтересованная сторона",
        context: "Our stakeholders have asked for a shorter training format.",
        category: "trainer_skills",
        sourceModule: "seed",
        reviewReason: "Core vocabulary practice for the current profession track.",
        linkedMistakeSubtype: null,
        linkedMistakeTitle: null,
        learnedStatus: "active",
        repetitionStage: 2,
        dueNow: true,
      },
    ],
    vocabularyBacklinks: [
      {
        weakSpotTitle: "Present Perfect vs Past Simple",
        weakSpotCategory: "grammar",
        dueCount: 1,
        activeCount: 2,
        exampleWords: ["I have worked", "already sent"],
        sourceModules: ["speaking", "writing"],
      },
    ],
    mistakeResolution: [
      {
        weakSpotTitle: "Present Perfect vs Past Simple",
        weakSpotCategory: "grammar",
        status: "recovering",
        repetitionCount: 4,
        lastSeenDaysAgo: 2,
        linkedVocabularyCount: 2,
        resolutionHint: "The pattern is still being reviewed, but it is appearing less often in fresh corrections.",
      },
      {
        weakSpotTitle: "Feedback language for workshops",
        weakSpotCategory: "profession",
        status: "active",
        repetitionCount: 3,
        lastSeenDaysAgo: 1,
        linkedVocabularyCount: 0,
        resolutionHint: "This weak spot is still repeating often enough that it should stay in active recovery.",
      },
    ],
    moduleRotation: [
      {
        moduleKey: "speaking",
        title: "Speaking refresh",
        reason: "Short guided speaking keeps the corrected pattern active without forcing a full recovery loop.",
        route: routes.speaking,
        priority: 1,
      },
      {
        moduleKey: "vocabulary",
        title: "Vocabulary repetition",
        reason: "Review 1 due item before the next larger module.",
        route: routes.vocabulary,
        priority: 2,
      },
      {
        moduleKey: "lesson",
        title: "Return to the main lesson flow",
        reason: "Use the broader lesson track to keep corrected patterns alive in context.",
        route: routes.lessonRunner,
        priority: 3,
      },
    ],
    vocabularySummary: {
      dueCount: 1,
      newCount: 0,
      activeCount: 1,
      masteredCount: 0,
      weakestCategory: "trainer_skills",
    },
    listeningFocus: "audio_comprehension",
    generationRationale: [
      "Primary weak spot: Present Perfect vs Past Simple.",
      "Listening support added for audio comprehension.",
      "Vocabulary queue has 1 due item.",
      "Most overloaded vocabulary category: trainer_skills.",
      "Next lesson generation is recovery-first.",
    ],
    nextSteps: [
      {
        id: "step-1",
        title: "Recover your main weak spot",
        description: "Open a focused drill for grammar and fix the repeated pattern.",
        route: routes.grammar,
        stepType: "recovery",
      },
      {
        id: "step-2",
        title: "Review due vocabulary",
        description: "Repeat 1 word before the next full lesson block.",
        route: routes.activity,
        stepType: "vocabulary",
      },
      {
        id: "step-3",
        title: "Continue with the recommended lesson",
        description: "Move forward after recovery so the app keeps pushing the long-term track ahead.",
        route: routes.lessonRunner,
        stepType: "lesson",
      },
    ],
  },
  quickActions: mockQuickActions,
  resumeLesson: null,
};

export const mockDiagnosticRoadmap: DiagnosticRoadmap = {
  declaredCurrentLevel: "A2",
  estimatedLevel: "A2",
  targetLevel: "B2",
  overallScore: 43,
  summary:
    "Roadmap towards B2: strengthen pronunciation and listening first, then convert recovery work into longer lesson gains. Immediate focus: Present Perfect vs Past Simple, Sound /th/.",
  weakestSkills: ["pronunciation", "listening", "profession English"],
  nextFocus: ["Present Perfect vs Past Simple", "Sound /th/"],
  milestones: [
    {
      level: "A2",
      status: "current",
      readiness: 100,
      requiredScore: 35,
      currentScore: 43,
      description: "Stabilize everyday grammar, short speaking turns and basic work vocabulary.",
      focusSkills: ["pronunciation", "listening"],
    },
    {
      level: "B1",
      status: "upcoming",
      readiness: 83,
      requiredScore: 52,
      currentScore: 43,
      description: "Build longer explanations, better time control and more reliable listening coverage.",
      focusSkills: ["pronunciation", "listening"],
    },
    {
      level: "B2",
      status: "upcoming",
      readiness: 61,
      requiredScore: 70,
      currentScore: 43,
      description: "Push fluency, nuanced feedback language and confident professional communication.",
      focusSkills: ["pronunciation", "listening"],
    },
  ],
};

export const mockLesson: Lesson = {
  id: "lesson-1",
  lessonType: "mixed",
  title: "Trainer Daily Flow",
  goal: "Повторить проблемную грамматику и встроить её в professional speaking.",
  difficulty: "A2-B1",
  duration: 25,
  modules: [
    "review_block",
    "grammar_block",
    "speaking_block",
    "profession_block",
    "summary_block",
  ],
  completed: false,
  blocks: [
    {
      id: "block-1",
      blockType: "review_block",
      title: "Review weak spots",
      instructions: "Посмотри на частые ошибки и повтори правильные паттерны.",
      estimatedMinutes: 4,
      payload: {
        items: [
          "I have worked with teams from 2021.",
          "I have already sent the workshop notes.",
        ],
      },
    },
    {
      id: "block-2",
      blockType: "grammar_block",
      title: "Present Perfect in professional updates",
      instructions: "Собери 3 коротких ответа про опыт и недавние результаты.",
      estimatedMinutes: 6,
      payload: {
        prompts: [
          "Tell me what projects you have completed this month.",
          "Explain what you have learned as a trainer recently.",
        ],
      },
    },
    {
      id: "block-3",
      blockType: "speaking_block",
      title: "Guided speaking",
      instructions: "Ответь устно или текстом на 2 guided prompts.",
      estimatedMinutes: 7,
      payload: {
        prompts: [
          "How have you improved your training sessions lately?",
          "What have your learners asked for this quarter?",
        ],
      },
    },
    {
      id: "block-4",
      blockType: "profession_block",
      title: "Trainer feedback language",
      instructions: "Смягчи обратную связь и сделай её более естественной.",
      estimatedMinutes: 5,
      payload: {
        phrases: [
          "Let's tighten the structure a little.",
          "Your example is useful, but we can make it clearer for beginners.",
        ],
      },
    },
    {
      id: "block-5",
      blockType: "summary_block",
      title: "Summary and next step",
      instructions: "Зафиксируй 1 правило, 1 фразу и 1 навык на завтра.",
      estimatedMinutes: 3,
      payload: {
        nextStep: "Завтра сделать pronunciation mini-session на /th/.",
      },
    },
  ],
};

export const mockDiagnosticLesson: Lesson = {
  id: "lesson-diagnostic-1",
  lessonType: "diagnostic",
  title: "Checkpoint Diagnostic: A2 -> B2",
  goal: "Проверить grammar, speaking, listening и writing и обновить roadmap.",
  difficulty: "A2-B2",
  duration: 20,
  modules: ["grammar_block", "speaking_block", "listening_block", "writing_block", "summary_block"],
  completed: false,
  blocks: [
    {
      id: "diagnostic-block-1",
      blockType: "grammar_block",
      title: "Grammar checkpoint",
      instructions: "Answer two short grammar prompts.",
      estimatedMinutes: 5,
      payload: { prompts: ["Use present perfect in a work update.", "Fix one incorrect sentence."] },
    },
    {
      id: "diagnostic-block-2",
      blockType: "speaking_block",
      title: "Speaking checkpoint",
      instructions: "Give one structured answer about your progress.",
      estimatedMinutes: 5,
      payload: { prompts: ["Summarize your recent learning progress."] },
    },
    {
      id: "diagnostic-block-3",
      blockType: "listening_block",
      title: "Listening checkpoint",
      instructions: "Read the transcript and answer the questions.",
      estimatedMinutes: 4,
      payload: { transcript: "I have updated the training deck for new managers.", questions: ["What was updated?"] },
    },
    {
      id: "diagnostic-block-4",
      blockType: "writing_block",
      title: "Writing checkpoint",
      instructions: "Write a concise professional reply.",
      estimatedMinutes: 4,
      payload: { brief: "Reply to a teammate and confirm next steps." },
    },
    {
      id: "diagnostic-block-5",
      blockType: "summary_block",
      title: "Checkpoint summary",
      instructions: "Note the strongest and weakest skill.",
      estimatedMinutes: 2,
      payload: { nextStep: "Open refreshed roadmap." },
    },
  ],
};

export const mockGrammarTopics: GrammarTopic[] = [
  {
    id: "grammar-1",
    title: "Present Perfect Basics",
    level: "A2-B1",
    mastery: 58,
    explanation: "Используй для опыта, недавних действий и результата в настоящем.",
    checkpoints: ["have/has + V3", "already / yet / just", "experience"],
  },
  {
    id: "grammar-2",
    title: "Past Simple vs Present Perfect",
    level: "A2-B1",
    mastery: 43,
    explanation: "Past Simple = finished time. Present Perfect = result or experience.",
    checkpoints: ["finished time markers", "experience questions", "recent updates"],
  },
  {
    id: "grammar-3",
    title: "Future Forms for Planning",
    level: "A2-B1",
    mastery: 61,
    explanation: "be going to, will и present continuous для планов и решений.",
    checkpoints: ["plans", "promises", "schedule"],
  },
];

export const mockSpeakingScenarios: SpeakingScenario[] = [
  {
    id: "speaking-1",
    title: "Daily Stand-up",
    mode: "guided",
    goal: "Рассказывать о прогрессе коротко и уверенно.",
    prompt: "Share what you have completed, what you are doing next, and one blocker.",
    feedbackHint: "Сделай акцент на времени и результатах.",
  },
  {
    id: "speaking-2",
    title: "Training Debrief",
    mode: "roleplay",
    goal: "Давать мягкий feedback after workshop.",
    prompt: "Explain what went well and what should improve before the next session.",
    feedbackHint: "Используй softer language: could, might, let's.",
  },
];

export const mockPronunciationDrills: PronunciationDrill[] = [
  {
    id: "pronunciation-1",
    title: "Soft /th/ control",
    sound: "/th/",
    focus: "Уменьшить русскую замену на /z/ и /s/.",
    phrases: ["thank the team", "three thoughtful themes", "this method works"],
    difficulty: "A2-B1",
  },
  {
    id: "pronunciation-2",
    title: "Sentence stress",
    sound: "stress",
    focus: "Усилить смысловые слова в коротких рабочих фразах.",
    phrases: ["I HAVE updated the module", "We NEED a clearer example"],
    difficulty: "A2-B1",
  },
];

export const mockWritingTask: WritingTask = {
  id: "writing-1",
  title: "Reply to a hiring manager",
  brief: "Напиши короткий ответ с благодарностью, интересом к роли и готовностью обсудить детали.",
  tone: "professional and warm",
  checklist: [
    "thank the person",
    "show interest",
    "offer next step",
    "keep it concise",
  ],
  improvedVersionPreview:
    "Thank you for reaching out. I would be glad to discuss the role in more detail and share how my training background could support the team.",
};

export const mockProfessionTracks: ProfessionTrackCard[] = [
  {
    id: "track-1",
    title: "Insurance English",
    domain: "insurance",
    summary: "Клиентские разговоры, продукты, objections и needs analysis.",
    lessonFocus: ["client conversations", "value communication", "customer protection"],
  },
  {
    id: "track-2",
    title: "Banking English",
    domain: "banking",
    summary: "Базовая лексика по продуктам, платежам и retail banking.",
    lessonFocus: ["payments", "cards", "financial conversations"],
  },
  {
    id: "track-3",
    title: "Trainer Skills",
    domain: "trainer_skills",
    summary: "Язык фасилитации, coaching, структурирование тренинга и feedback.",
    lessonFocus: ["facilitation", "feedback language", "coaching language"],
  },
  {
    id: "track-4",
    title: "AI for Business",
    domain: "ai_business",
    summary: "AI workflows, prompts, limitations и объяснение кейсов на английском.",
    lessonFocus: ["prompts", "AI assistants", "risk-aware explanations"],
  },
  {
    id: "track-5",
    title: "Everyday Communication",
    domain: "cross_cultural",
    summary: "Повседневный английский, поездки, дружелюбные разговорные сценарии и school-safe practice.",
    lessonFocus: ["daily conversations", "travel confidence", "friendly communication"],
  },
];

export const mockMistakes: Mistake[] = [
  {
    id: "mistake-1",
    category: "grammar",
    subtype: "tense-choice",
    sourceModule: "speaking",
    originalText: "I work with this team since 2022.",
    correctedText: "I have worked with this team since 2022.",
    explanation: "Нужен Present Perfect, потому что действие началось в прошлом и продолжается сейчас.",
    repetitionCount: 4,
    lastSeenAt: "2026-03-19T18:15:00",
  },
  {
    id: "mistake-2",
    category: "pronunciation",
    subtype: "th-sound",
    sourceModule: "pronunciation",
    originalText: "sink",
    correctedText: "think",
    explanation: "Нужно вывести язык слегка между зубами и не заменять звук на /s/.",
    repetitionCount: 6,
    lastSeenAt: "2026-03-20T11:30:00",
  },
  {
    id: "mistake-3",
    category: "profession",
    subtype: "feedback-language",
    sourceModule: "profession",
    originalText: "This part is wrong.",
    correctedText: "This part could be clearer for the audience.",
    explanation: "Для trainer context лучше использовать мягкие формулировки.",
    repetitionCount: 3,
    lastSeenAt: "2026-03-19T18:19:00",
  },
];

export const mockProviderStatus: ProviderStatus[] = [
  {
    key: "mock_llm",
    name: "Fallback LLM",
    type: "llm",
    status: "mock",
    details: "Local fallback responses stay available during development and whenever LM Studio is unavailable.",
  },
  {
    key: "stt_bridge",
    name: "STT Bridge",
    type: "stt",
    status: "offline",
    details: "Подключение не настроено, предусмотрен graceful degradation.",
  },
  {
    key: "tts_bridge",
    name: "TTS Bridge",
    type: "tts",
    status: "offline",
    details: "Пока не активирован, UI должен работать без озвучки.",
  },
  {
    key: "scoring_engine",
    name: "Scoring Engine",
    type: "scoring",
    status: "mock",
    details: "Базовая оценка готова к замене на rule-based или AI scoring.",
  },
];
