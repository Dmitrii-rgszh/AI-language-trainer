import { defaultOnboardingAnswers, type OnboardingAnswers, type UserProfile } from "../../entities/user/model";
import type { ProfessionTrackCard } from "../types/app-data";

export type OnboardingOption = {
  value: string;
  label: string;
};

export const learnerPersonaOptions: OnboardingOption[] = [
  { value: "self_learner", label: "Self learner" },
  { value: "school_learner", label: "School learner" },
  { value: "professional_learner", label: "Professional learner" },
  { value: "parent_or_guardian", label: "Parent or guardian" },
];

export const ageGroupOptions: OnboardingOption[] = [
  { value: "child", label: "Child" },
  { value: "teen", label: "Teen" },
  { value: "adult", label: "Adult" },
  { value: "family_plan", label: "Family plan" },
];

export const learningContextOptions: OnboardingOption[] = [
  { value: "general_english", label: "For life and communication" },
  { value: "career_growth", label: "For work" },
  { value: "school_support", label: "For school" },
  { value: "travel", label: "For trips" },
  { value: "relocation", label: "For relocation" },
  { value: "exam_prep", label: "For exams" },
];

export const goalOptions: OnboardingOption[] = [
  { value: "everyday_communication", label: "Everyday communication" },
  { value: "speaking_confidence", label: "Speaking confidence" },
  { value: "vocabulary_growth", label: "Vocabulary growth" },
  { value: "grammar_accuracy", label: "Grammar accuracy" },
  { value: "reading_comprehension", label: "Reading comprehension" },
  { value: "work_communication", label: "Work communication" },
  { value: "school_results", label: "School results" },
  { value: "exam_result", label: "Exam result" },
  { value: "travel_confidence", label: "Travel confidence" },
];

export const skillFocusOptions: OnboardingOption[] = [
  { value: "speaking", label: "Speaking" },
  { value: "listening", label: "Listening" },
  { value: "reading", label: "Reading" },
  { value: "grammar", label: "Grammar" },
  { value: "vocabulary", label: "Vocabulary" },
  { value: "writing", label: "Writing" },
  { value: "pronunciation", label: "Pronunciation" },
];

export const studyPreferenceOptions: OnboardingOption[] = [
  { value: "short_sessions", label: "Short sessions" },
  { value: "deep_sessions", label: "Deep sessions" },
  { value: "voice_first", label: "Voice first" },
  { value: "text_first", label: "Text first" },
  { value: "playful_learning", label: "Playful learning" },
  { value: "structured_plan", label: "Structured plan" },
  { value: "gentle_feedback", label: "Gentle feedback" },
  { value: "parent_guided", label: "Parent guided" },
];

export const supportNeedOptions: OnboardingOption[] = [
  { value: "clear_examples", label: "Clear examples" },
  { value: "slower_pace", label: "Slower pace" },
  { value: "more_repetition", label: "More repetition" },
  { value: "confidence_support", label: "Confidence support" },
  { value: "visual_structure", label: "Visual structure" },
];

export const interestTopicOptions: OnboardingOption[] = [
  { value: "daily_life", label: "Daily life" },
  { value: "travel", label: "Travel" },
  { value: "stories", label: "Stories" },
  { value: "games", label: "Games" },
  { value: "school_topics", label: "School topics" },
  { value: "technology", label: "Technology" },
  { value: "work_and_business", label: "Work and business" },
  { value: "culture", label: "Culture" },
];

export const fallbackProfessionTracks: ProfessionTrackCard[] = [
  {
    id: "track-cross-cultural",
    title: "Everyday Communication",
    domain: "cross_cultural",
    summary: "Повседневный английский, travel English и дружелюбные разговорные сценарии.",
    lessonFocus: [],
  },
  {
    id: "track-trainer-skills",
    title: "Trainer Skills",
    domain: "trainer_skills",
    summary: "Фасилитация, coaching language, feedback style и структура тренинга.",
    lessonFocus: [],
  },
  {
    id: "track-insurance",
    title: "Insurance English",
    domain: "insurance",
    summary: "Клиентские разговоры, продукты, objections и needs analysis.",
    lessonFocus: [],
  },
  {
    id: "track-banking",
    title: "Banking English",
    domain: "banking",
    summary: "Базовая лексика по продуктам, платежам и retail banking.",
    lessonFocus: [],
  },
  {
    id: "track-ai-business",
    title: "AI for Business",
    domain: "ai_business",
    summary: "Промпты, AI assistants, workflows и explanation style для бизнеса.",
    lessonFocus: [],
  },
];

export const defaultProfile: UserProfile = {
  id: "user-local-1",
  name: "",
  nativeLanguage: "ru",
  currentLevel: "A2",
  targetLevel: "B1",
  professionTrack: "cross_cultural",
  preferredUiLanguage: "ru",
  preferredExplanationLanguage: "ru",
  lessonDuration: 20,
  speakingPriority: 8,
  grammarPriority: 7,
  professionPriority: 5,
  onboardingAnswers: defaultOnboardingAnswers,
};

export function cloneAnswers(answers?: Partial<OnboardingAnswers>): OnboardingAnswers {
  return {
    learnerPersona: answers?.learnerPersona ?? defaultOnboardingAnswers.learnerPersona,
    ageGroup: answers?.ageGroup ?? defaultOnboardingAnswers.ageGroup,
    learningContext: answers?.learningContext ?? defaultOnboardingAnswers.learningContext,
    primaryGoal: answers?.primaryGoal ?? defaultOnboardingAnswers.primaryGoal,
    secondaryGoals: [...(answers?.secondaryGoals ?? defaultOnboardingAnswers.secondaryGoals)],
    activeSkillFocus: [...(answers?.activeSkillFocus ?? defaultOnboardingAnswers.activeSkillFocus)],
    studyPreferences: [...(answers?.studyPreferences ?? defaultOnboardingAnswers.studyPreferences)],
    interestTopics: [...(answers?.interestTopics ?? defaultOnboardingAnswers.interestTopics)],
    supportNeeds: [...(answers?.supportNeeds ?? defaultOnboardingAnswers.supportNeeds)],
    notes: answers?.notes ?? defaultOnboardingAnswers.notes,
  };
}

export function buildProfileDraft(profile: UserProfile | null) {
  return profile
    ? { ...defaultProfile, ...profile, onboardingAnswers: cloneAnswers(profile.onboardingAnswers) }
    : { ...defaultProfile, onboardingAnswers: cloneAnswers() };
}

export function toggleValue(values: string[], nextValue: string) {
  return values.includes(nextValue) ? values.filter((value) => value !== nextValue) : [...values, nextValue];
}
