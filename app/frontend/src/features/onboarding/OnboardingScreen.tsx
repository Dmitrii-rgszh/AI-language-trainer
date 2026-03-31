import { useNavigate } from "react-router-dom";
import { useLocale } from "../../shared/i18n/useLocale";
import { routes } from "../../shared/constants/routes";
import { useAppStore } from "../../shared/store/app-store";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { ProfileEditorCard } from "./ProfileEditorCard";

export function OnboardingScreen() {
  const { tr } = useLocale();
  const profile = useAppStore((state) => state.profile);
  const professionTracks = useAppStore((state) => state.professionTracks);
  const saveProfile = useAppStore((state) => state.saveProfile);
  const navigate = useNavigate();

  const handleSubmit = async (nextProfile: typeof profile extends null ? never : NonNullable<typeof profile>) => {
    await saveProfile(nextProfile);
    navigate(routes.dashboard);
  };

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Start")}
        title={tr("Onboarding")}
        description={tr(
          "Build a flexible learner profile for adults, children, career goals, school support, and future multi-user use cases.",
        )}
      />
      <ProfileEditorCard
        initialProfile={profile}
        professionTracks={professionTracks}
        title={tr("Profile summary")}
        description={tr(
          "Save a broader learning blueprint so the dashboard, lesson flow, and future personalization can adapt to different ages, goals, and study styles.",
        )}
        submitLabel={tr("Save profile and continue")}
        onSave={handleSubmit}
      />
    </div>
  );
}
