import type { UserProfile } from "../../entities/user/model";

export type GuestDirectionId =
  | "speaking"
  | "grammar"
  | "vocabulary"
  | "reading"
  | "work"
  | "travel"
  | "exam";

export type GuestIntent = {
  directions: GuestDirectionId[];
};

const GUEST_INTENT_STORAGE_KEY = "ai-english-trainer:guest-intent";

function unique(values: string[]) {
  return [...new Set(values)];
}

export function readGuestIntent(): GuestIntent | null {
  if (typeof window === "undefined") {
    return null;
  }

  const storedValue = window.localStorage.getItem(GUEST_INTENT_STORAGE_KEY);
  if (!storedValue) {
    return null;
  }

  try {
    const parsedValue = JSON.parse(storedValue) as GuestIntent;
    return Array.isArray(parsedValue.directions) ? { directions: parsedValue.directions } : null;
  } catch {
    return null;
  }
}

export function writeGuestIntent(intent: GuestIntent) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(GUEST_INTENT_STORAGE_KEY, JSON.stringify(intent));
}

export function consumeGuestIntent() {
  const intent = readGuestIntent();

  if (typeof window !== "undefined") {
    window.localStorage.removeItem(GUEST_INTENT_STORAGE_KEY);
  }

  return intent;
}

export function applyGuestIntentToProfile(profile: UserProfile, directions: GuestDirectionId[]) {
  if (directions.length === 0) {
    return profile;
  }

  const nextProfile: UserProfile = {
    ...profile,
    onboardingAnswers: {
      ...profile.onboardingAnswers,
      secondaryGoals: [...profile.onboardingAnswers.secondaryGoals],
      activeSkillFocus: [...profile.onboardingAnswers.activeSkillFocus],
      interestTopics: [...profile.onboardingAnswers.interestTopics],
      studyPreferences: [...profile.onboardingAnswers.studyPreferences],
    },
  };

  let primaryGoal = nextProfile.onboardingAnswers.primaryGoal;
  let learningContext = nextProfile.onboardingAnswers.learningContext;

  if (directions.includes("speaking")) {
    primaryGoal = "speaking_confidence";
    nextProfile.onboardingAnswers.activeSkillFocus = unique([
      "speaking",
      "listening",
      ...nextProfile.onboardingAnswers.activeSkillFocus,
    ]);
  }

  if (directions.includes("grammar")) {
    primaryGoal = primaryGoal === "everyday_communication" ? "grammar_accuracy" : primaryGoal;
    nextProfile.onboardingAnswers.activeSkillFocus = unique(["grammar", ...nextProfile.onboardingAnswers.activeSkillFocus]);
  }

  if (directions.includes("vocabulary")) {
    if (primaryGoal === "everyday_communication") {
      primaryGoal = "vocabulary_growth";
    }
    nextProfile.onboardingAnswers.activeSkillFocus = unique([
      "vocabulary",
      ...nextProfile.onboardingAnswers.activeSkillFocus,
    ]);
  }

  if (directions.includes("reading")) {
    if (primaryGoal === "everyday_communication") {
      primaryGoal = "reading_comprehension";
    }
    nextProfile.onboardingAnswers.activeSkillFocus = unique(["reading", ...nextProfile.onboardingAnswers.activeSkillFocus]);
    nextProfile.onboardingAnswers.interestTopics = unique([
      "stories",
      ...nextProfile.onboardingAnswers.interestTopics,
    ]);
  }

  if (directions.includes("work")) {
    primaryGoal = "work_communication";
    learningContext = "career_growth";
    nextProfile.professionTrack = nextProfile.professionTrack === "cross_cultural" ? "trainer_skills" : nextProfile.professionTrack;
    nextProfile.onboardingAnswers.interestTopics = unique([
      "work_and_business",
      "technology",
      ...nextProfile.onboardingAnswers.interestTopics,
    ]);
  }

  if (directions.includes("travel")) {
    primaryGoal = primaryGoal === "work_communication" ? primaryGoal : "travel_confidence";
    learningContext = learningContext === "career_growth" ? learningContext : "travel";
    nextProfile.onboardingAnswers.interestTopics = unique(["travel", ...nextProfile.onboardingAnswers.interestTopics]);
  }

  if (directions.includes("exam")) {
    primaryGoal = "exam_result";
    learningContext = "exam_prep";
    nextProfile.onboardingAnswers.studyPreferences = unique([
      "structured_plan",
      ...nextProfile.onboardingAnswers.studyPreferences,
    ]);
  }

  nextProfile.onboardingAnswers.primaryGoal = primaryGoal;
  nextProfile.onboardingAnswers.learningContext = learningContext;
  nextProfile.onboardingAnswers.secondaryGoals = unique([
    ...directions.flatMap((direction) => {
      switch (direction) {
        case "speaking":
          return ["speaking_confidence"];
        case "grammar":
          return ["grammar_accuracy"];
        case "vocabulary":
          return ["vocabulary_growth"];
        case "reading":
          return ["reading_comprehension"];
        case "work":
          return ["work_communication"];
        case "travel":
          return ["travel_confidence"];
        case "exam":
          return ["exam_result"];
        default:
          return [];
      }
    }),
    ...nextProfile.onboardingAnswers.secondaryGoals,
  ]).filter((goal) => goal !== nextProfile.onboardingAnswers.primaryGoal);

  return nextProfile;
}
