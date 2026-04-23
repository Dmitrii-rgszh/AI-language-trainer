export interface OnboardingAnswers {
  learnerPersona: string;
  ageGroup: string;
  learningContext: string;
  primaryGoal: string;
  englishRelationshipGoal: string;
  preferredMode: string;
  diagnosticReadiness: string;
  secondaryGoals: string[];
  activeSkillFocus: string[];
  studyPreferences: string[];
  interestTopics: string[];
  supportNeeds: string[];
  emotionalBarriers: string[];
  ritualElements: string[];
  notes: string;
}

export const defaultOnboardingAnswers: OnboardingAnswers = {
  learnerPersona: "self_learner",
  ageGroup: "adult",
  learningContext: "general_english",
  primaryGoal: "everyday_communication",
  englishRelationshipGoal: "freedom_and_lightness",
  preferredMode: "mixed",
  diagnosticReadiness: "soft_start",
  secondaryGoals: ["speaking_confidence", "vocabulary_growth"],
  activeSkillFocus: ["speaking", "vocabulary", "grammar"],
  studyPreferences: ["structured_plan", "short_sessions", "gentle_feedback"],
  interestTopics: ["daily_life", "travel", "culture"],
  supportNeeds: ["clear_examples"],
  emotionalBarriers: ["fear_of_mistakes", "fear_of_judgment"],
  ritualElements: ["daily_word_journal", "reading_for_pleasure", "gentle_daily_consistency"],
  notes: "",
};

export interface UserProfile {
  id: string;
  name: string;
  nativeLanguage: string;
  currentLevel: string;
  targetLevel: string;
  professionTrack: string;
  preferredUiLanguage: string;
  preferredExplanationLanguage: string;
  lessonDuration: number;
  speakingPriority: number;
  grammarPriority: number;
  professionPriority: number;
  onboardingAnswers: OnboardingAnswers;
}
