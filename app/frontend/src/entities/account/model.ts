export interface UserAccount {
  id: string;
  login: string;
  email: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserAccountDraft {
  login: string;
  email: string;
}

export interface LoginAvailability {
  login: string;
  normalizedLogin: string;
  available: boolean;
  status: "available" | "taken" | "existing_account";
  suggestions: string[];
}

export const defaultUserAccountDraft: UserAccountDraft = {
  login: "",
  email: "",
};
