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
  profile: UserProfile;
}

export interface CompleteOnboardingResponse {
  user: UserAccount;
  onboarding: UserOnboarding;
  profile: UserProfile;
}
