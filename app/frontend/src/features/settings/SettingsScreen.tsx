import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { UserAccountDraft } from "../../entities/account/model";
import type { UserProfile } from "../../entities/user/model";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { LizaExplainActions } from "../../widgets/liza/LizaExplainActions";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { LizaGuidanceGrid } from "../../widgets/liza/LizaGuidanceGrid";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";
import { AccountIdentityCard } from "../../widgets/profile-settings/AccountIdentityCard";
import { ProfileEditorCard } from "../../widgets/profile-settings/ProfileEditorCard";

export function SettingsScreen() {
  const { tr, locale } = useLocale();
  const currentUser = useAppStore((state) => state.currentUser);
  const profile = useAppStore((state) => state.profile);
  const dashboard = useAppStore((state) => state.dashboard);
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
  const currentFocusArea = dashboard?.journeyState?.currentFocusArea ?? dashboard?.dailyLoopPlan?.focusArea ?? "daily loop";
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

  const coachMessage =
    locale === "ru"
      ? `Настройки здесь нужны не ради техники самой по себе. Я использую их, чтобы твой путь вокруг ${currentFocusArea} оставался стабильным: identity не терялась, профиль не расходился, а voice-and-AI stack не ломал ежедневный ритуал.`
      : `Settings here are not just technical controls. I use them to keep your ${currentFocusArea} path stable: identity stays intact, the profile stays aligned, and the voice-and-AI stack does not break the daily ritual.`;
  const coachSupportingText =
    dashboard?.journeyState?.currentStrategySummary ??
    (locale === "ru"
      ? "Этот экран должен помогать сохранить консистентность продукта: кто учится, как система объясняет, и какие провайдеры реально поддерживают живой опыт."
      : "This screen should protect product consistency: who is learning, how the system explains, and which providers truly support the live experience.");
  const nextSettingsStep =
    dashboard?.journeyState?.nextBestAction ??
    (locale === "ru"
      ? "Проверь профиль и runtime stack, затем вернись в dashboard или daily loop, чтобы продолжить без разрыва маршрута."
      : "Check the profile and runtime stack, then return to the dashboard or daily loop so the route continues without a break.");
  const explainActions = [
    {
      id: "settings-simpler",
      label: locale === "ru" ? "Объясни проще" : "Explain simpler",
      text:
        locale === "ru"
          ? "Этот экран нужен, чтобы профиль, аккаунт и AI-стек не расходились между собой и не ломали опыт."
          : "This screen exists so the profile, account, and AI stack do not drift apart and break the experience.",
    },
    {
      id: "settings-why",
      label: locale === "ru" ? "Почему это важно" : "Why it matters",
      text: coachSupportingText,
    },
    {
      id: "settings-priority",
      label: locale === "ru" ? "Что важнее всего" : "What matters most",
      text:
        locale === "ru"
          ? `Сейчас важнее всего сохранить консистентность маршрута вокруг ${currentFocusArea}, а не просто включить как можно больше провайдеров.`
          : `What matters most right now is preserving route consistency around ${currentFocusArea}, not simply enabling as many providers as possible.`,
    },
    {
      id: "settings-next",
      label: locale === "ru" ? "Следующий лучший шаг" : "Next best step",
      text: nextSettingsStep,
    },
  ];

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Settings")}
        title={tr("Settings And Providers")}
        description={tr(
          "User settings and provider health live here. This screen lets you control the local LLM, STT, TTS, and fallback runtime behavior.",
        )}
      />

      <LivingDepthSection id={livingDepthSectionIds.settingsCoach}>
        <LizaCoachPanel
          locale={locale}
          playKey={`settings:${currentFocusArea}:${runtimeReadyCount}:${enabledCount}`}
          title={tr("Liza Settings Layer")}
          message={coachMessage}
          spokenMessage={coachMessage}
          spokenLanguage={locale}
          replayCta={tr("Послушать ещё раз")}
          primaryAction={(
            <Link to={routes.dashboard} className="proof-lesson-primary-button">
              {tr("Вернуться в dashboard")}
            </Link>
          )}
          secondaryAction={(
            <Link to={routes.pronunciation} className="proof-lesson-secondary-action">
              {tr("Проверить voice lab")}
            </Link>
          )}
          supportingText={coachSupportingText}
        />
      </LivingDepthSection>

      <LizaGuidanceGrid
        currentLabel={locale === "ru" ? "Что сейчас происходит" : "What is happening now"}
        currentText={
          locale === "ru"
            ? "Здесь хранится identity, профиль и состояние AI runtime, который нужен для живого coach experience."
            : "This is where identity, profile data, and the AI runtime state behind the live coach experience are managed."
        }
        whyLabel={locale === "ru" ? "Почему это важно тебе" : "Why it matters for you"}
        whyText={
          locale === "ru"
            ? "Если здесь появляется рассинхрон, продукт начинает ощущаться как набор режимов. Если всё ровно, Лиза и daily loop ведут тебя как одна система."
            : "If this layer drifts out of sync, the product starts feeling like separate modes. When it stays clean, Liza and the daily loop guide you as one system."
        }
        nextLabel={locale === "ru" ? "Что делать дальше" : "What to do next"}
        nextText={nextSettingsStep}
      />

      <LizaExplainActions
        title={locale === "ru" ? "Разобрать настройки с Лизой" : "Break down settings with Liza"}
        actions={explainActions}
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
