import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { UserAccountDraft } from "../../entities/account/model";
import type { UserProfile } from "../../entities/user/model";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { AccountIdentityCard } from "../../widgets/profile-settings/AccountIdentityCard";
import { ProfileEditorCard } from "../../widgets/profile-settings/ProfileEditorCard";

export function SettingsScreen() {
  const { tr } = useLocale();
  const currentUser = useAppStore((state) => state.currentUser);
  const profile = useAppStore((state) => state.profile);
  const providers = useAppStore((state) => state.providers);
  const providerPreferences = useAppStore((state) => state.providerPreferences);
  const professionTracks = useAppStore((state) => state.professionTracks);
  const saveProviderPreference = useAppStore((state) => state.saveProviderPreference);
  const saveCurrentUser = useAppStore((state) => state.saveCurrentUser);
  const saveProfile = useAppStore((state) => state.saveProfile);
  const [accountDraft, setAccountDraft] = useState<UserAccountDraft>({ login: "", email: "" });

  const getPreferenceEnabled = (providerType: "llm" | "stt" | "tts" | "scoring") =>
    providerPreferences.find((preference) => preference.providerType === providerType)?.enabled;
  const runtimeReadyCount = providers.filter((provider) => provider.status === "ready").length;
  const runtimeOptionalCount = providers.filter((provider) => provider.status === "mock").length;
  const enabledCount = providers.filter(
    (provider) => getPreferenceEnabled(provider.type) ?? provider.status !== "offline",
  ).length;
  const providerTypeLabels: Record<"llm" | "stt" | "tts" | "scoring", string> = {
    llm: "LLM",
    stt: "STT",
    tts: "TTS",
    scoring: "Scoring",
  };
  const providerStatusLabels = {
    ready: tr("ready"),
    mock: tr("fallback"),
    offline: tr("offline"),
  } as const;

  const handleSaveProfile = async (nextProfile: UserProfile) => {
    await saveProfile(nextProfile);
  };

  const handleSaveUser = async (nextUser: UserAccountDraft) => {
    await saveCurrentUser(nextUser);
  };

  useEffect(() => {
    setAccountDraft({
      login: currentUser?.login ?? "",
      email: currentUser?.email ?? "",
    });
  }, [currentUser]);

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Settings")}
        title={tr("Settings And Providers")}
        description={tr(
          "User settings and provider health live here. This screen lets you control the local LLM, STT, TTS, and fallback runtime behavior.",
        )}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Runtime readiness")}</div>
          <div className="text-3xl font-semibold text-ink">
            {runtimeReadyCount}/{providers.length}
          </div>
          <div className="text-sm text-slate-600">{tr("Core providers that are fully live right now.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Enabled stack")}</div>
          <div className="text-3xl font-semibold text-ink">
            {enabledCount}/{providers.length}
          </div>
          <div className="text-sm text-slate-600">{tr("Provider types currently allowed in runtime.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Fallback modes")}</div>
          <div className="text-3xl font-semibold text-ink">{runtimeOptionalCount}</div>
          <div className="text-sm text-slate-600">{tr("Modules working through fallback or non-primary providers.")}</div>
        </Card>
      </div>

      {currentUser ? (
        <AccountIdentityCard
          title={tr("Personal cabinet")}
          description={tr(
            "Login and email live in the user account table. Update them here without touching the learning profile itself.",
          )}
          account={accountDraft}
          onChange={setAccountDraft}
          submitLabel={tr("Save cabinet updates")}
          onSave={handleSaveUser}
        />
      ) : null}

      <ProfileEditorCard
        initialProfile={profile}
        professionTracks={professionTracks}
        title={tr("Profile settings")}
        description={tr(
          "This profile drives recommendations, the daily flow, and how focus is split between speaking, grammar, and profession.",
        )}
        submitLabel={tr("Save profile updates")}
        onSave={handleSaveProfile}
      />

      <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Provider status and preferences")}</div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {tr(
              "LLM, STT, and TTS matter most for the live voice-and-AI loop. If any of them moves into fallback or offline mode, the impact will show up on the dashboard and in the related practice modules.",
            )}
          </div>
          {providers.map((provider) => (
            <div key={`${provider.type}-${provider.name}`} className="rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{provider.name}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                    {providerTypeLabels[provider.type]}
                  </div>
                </div>
                <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">
                  {providerStatusLabels[provider.status]}
                </div>
              </div>
              <div className="mt-3 text-sm text-slate-600">{tr(provider.details)}</div>
              <div className="mt-4 rounded-2xl bg-sand/70 px-4 py-3 text-xs uppercase tracking-[0.14em] text-slate-600">
                {tr("Selected runtime key")}:{" "}
                <span className="font-semibold text-ink">
                  {providerPreferences.find((preference) => preference.providerType === provider.type)?.selectedProvider ??
                    provider.key}
                </span>
              </div>
              <label className="mt-4 flex items-center justify-between gap-3 rounded-2xl bg-white px-4 py-3 text-sm text-slate-700">
                <span>{tr("Use this provider in runtime")}</span>
                <input
                  type="checkbox"
                  checked={getPreferenceEnabled(provider.type) ?? provider.status !== "offline"}
                  onChange={(event) => void saveProviderPreference(provider.type, event.target.checked)}
                />
              </label>
            </div>
          ))}
          <div className="flex flex-wrap gap-3">
            <Link
              to={routes.dashboard}
              className="rounded-2xl bg-ink px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-ink/90"
            >
              {tr("Back to dashboard")}
            </Link>
            <Link
              to={routes.pronunciation}
              className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-[#ddccb6]"
            >
              {tr("Check voice lab")}
            </Link>
          </div>
      </Card>
    </div>
  );
}
