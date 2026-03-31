import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { defaultUserAccountDraft, type UserAccountDraft } from "../../entities/account/model";
import { useLocale } from "../../shared/i18n/useLocale";
import { routes } from "../../shared/constants/routes";
import { useAppStore } from "../../shared/store/app-store";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { AccountIdentityCard } from "./AccountIdentityCard";
import { ProfileEditorCard } from "./ProfileEditorCard";

export function OnboardingScreen() {
  const { tr } = useLocale();
  const currentUser = useAppStore((state) => state.currentUser);
  const profile = useAppStore((state) => state.profile);
  const professionTracks = useAppStore((state) => state.professionTracks);
  const completeOnboarding = useAppStore((state) => state.completeOnboarding);
  const navigate = useNavigate();
  const [account, setAccount] = useState<UserAccountDraft>(defaultUserAccountDraft);

  useEffect(() => {
    setAccount(
      currentUser
        ? {
            login: currentUser.login,
            email: currentUser.email,
          }
        : defaultUserAccountDraft,
    );
  }, [currentUser]);

  const handleSubmit = async (nextProfile: typeof profile extends null ? never : NonNullable<typeof profile>) => {
    await completeOnboarding({
      login: account.login.trim(),
      email: account.email.trim(),
      profile: nextProfile,
    });
    navigate(routes.dashboard);
  };

  const accountReady = account.login.trim().length >= 3 && account.email.includes("@");

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Start")}
        title={tr("Onboarding")}
        description={tr(
          "Build a flexible learner profile for adults, children, career goals, school support, and future multi-user use cases.",
        )}
      />
      <AccountIdentityCard
        title={tr("User account")}
        description={tr(
          "Start by choosing the login and email for this learner. The app uses them to create or find a personal account before saving onboarding answers.",
        )}
        account={account}
        onChange={setAccount}
      />
      <ProfileEditorCard
        initialProfile={profile}
        professionTracks={professionTracks}
        title={tr("Profile summary")}
        description={tr(
          "Save a broader learning blueprint so the dashboard, lesson flow, and future personalization can adapt to different ages, goals, and study styles.",
        )}
        submitLabel={tr("Save profile and continue")}
        submitDisabled={!accountReady}
        submitHelperText={
          accountReady
            ? undefined
            : tr("Add a valid login and email first so the app can create or load the personal account.")
        }
        onSave={handleSubmit}
      />
    </div>
  );
}
