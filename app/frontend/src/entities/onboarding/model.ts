import type { UserAccountDraft } from "../account/model";
import type { UserAccount } from "../account/model";
import type { OnboardingAnswers, UserProfile } from "../user/model";

export interface UserOnboarding {
  id: string;
  userId: string;
  answers: OnboardingAnswers;
  completedAt: string;
  createdAt: string;
  updatedAt: string;
}

export interface CompleteOnboardingRequest {
  login: string;
  email: string;
  sessionId?: string | null;
  profile: UserProfile;
}

export interface CompleteOnboardingResponse {
  user: UserAccount;
  onboarding: UserOnboarding;
  profile: UserProfile;
}

export interface ProofLessonHandoff {
  locale: "ru" | "en";
  scenarioId: string;
  beforePhrase: string;
  afterPhrase: string;
  clarityStatusLabel: string;
  directions: string[];
  wins: string[];
  createdAt: string;
}

export interface OnboardingJourneySession {
  id: string;
  userId?: string | null;
  status: string;
  source: string;
  proofLessonHandoff?: ProofLessonHandoff | null;
  accountDraft: UserAccountDraft;
  profileDraft?: UserProfile | null;
  currentStep: number;
  completedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}
