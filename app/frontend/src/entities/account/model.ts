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

export const defaultUserAccountDraft: UserAccountDraft = {
  login: "",
  email: "",
};
