import { useLocale } from "../../shared/i18n/useLocale";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { OnboardingSidebar } from "./OnboardingSidebar";
import { OnboardingStepContent } from "./OnboardingStepContent";
import { useOnboardingFlow } from "./useOnboardingFlow";

export function OnboardingScreen() {
  const { locale, tr } = useLocale();
  const onboarding = useOnboardingFlow();
  const completionPercent = Math.round(((onboarding.step + 1) / onboarding.steps.length) * 100);
  const handoffDirections = onboarding.welcomeHandoff?.directions.map((direction) => {
    if (locale === "ru") {
      switch (direction) {
        case "speaking":
          return "Речь";
        case "grammar":
          return "Грамматика";
        case "vocabulary":
          return "Словарь";
        case "reading":
          return "Чтение";
        case "work":
          return "Работа";
        case "travel":
          return "Путешествия";
        case "exam":
          return "Экзамен";
        default:
          return direction;
      }
    }

    switch (direction) {
      case "speaking":
        return "Speaking";
      case "grammar":
        return "Grammar";
      case "vocabulary":
        return "Vocabulary";
      case "reading":
        return "Reading";
      case "work":
        return "Work";
      case "travel":
        return "Travel";
      case "exam":
        return "Exam";
      default:
        return direction;
    }
  });
  const handoffTitle =
    locale === "ru"
      ? "Сохраним этот старт и соберём твой личный трек"
      : "Save this start and build your personal track";
  const handoffDescription =
    locale === "ru"
      ? "Ты уже прошёл первый живой мини-урок. Теперь создадим твоё учебное пространство, сохраним этот результат и сразу соберём продолжение под твою цель."
      : "You already completed the first live mini-lesson. Next we create your learning space, save this result, and immediately build the continuation around your goal.";
  const handoffCoachMessage =
    locale === "ru"
      ? "Мы уже увидели твой первый результат. Теперь осталось сохранить этот старт, уточнить цель и собрать для тебя персональный трек обучения."
      : "We already saw your first result. Next we save this start, clarify your goal, and build a personal learning track around it.";
  const handoffReplayCta =
    locale === "ru" ? "Послушать план ещё раз" : "Hear the plan again";
  const handoffNextSteps =
    locale === "ru"
      ? [
          "Сохраним аккаунт и первый результат под одним профилем",
          "Уточним цель, уровень и желаемый формат обучения",
          "Откроем стартовый трек вместо общего набора экранов",
        ]
      : [
          "Save the account and the first result under one profile",
          "Clarify your goal, level, and preferred learning format",
          "Open a starter track instead of a generic set of screens",
        ];
  const continueLabel =
    onboarding.step === 0 && onboarding.welcomeHandoff
      ? locale === "ru"
        ? "Сохранить старт и продолжить"
        : "Save this start and continue"
      : tr("Continue");
  const submitLabel = onboarding.welcomeHandoff
    ? locale === "ru"
      ? "Создать пространство и собрать трек"
      : "Create my space and build the track"
    : tr("Create workspace");

  return (
    <div className="space-y-6">
      {onboarding.welcomeHandoff ? (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_380px] xl:items-start">
          <Card className="overflow-hidden border-accent/15 bg-white/82 p-6 lg:p-7">
            <div className="text-xs uppercase tracking-[0.28em] text-coral">
              {locale === "ru" ? "Пробный урок пройден" : "Proof lesson completed"}
            </div>
            <div className="mt-3 text-3xl font-[700] tracking-[-0.03em] text-ink">
              {handoffTitle}
            </div>
            <div className="mt-3 max-w-[52rem] text-sm leading-6 text-slate-600">
              {handoffDescription}
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              <span className="rounded-full border border-accent/20 bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
                {locale === "ru"
                  ? `Понятность речи: ${onboarding.welcomeHandoff.clarityStatusLabel}`
                  : `Speech clarity: ${onboarding.welcomeHandoff.clarityStatusLabel}`}
              </span>
              {handoffDirections?.map((item) => (
                <span
                  key={item}
                  className="rounded-full border border-white/70 bg-white/78 px-3 py-1 text-xs font-semibold text-slate-600"
                >
                  {item}
                </span>
              ))}
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              <div className="rounded-[24px] border border-white/70 bg-white/76 p-4">
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {locale === "ru" ? "Твоя фраза" : "Your phrase"}
                </div>
                <div className="mt-3 text-lg font-[700] tracking-[-0.03em] text-slate-500">
                  {onboarding.welcomeHandoff.beforePhrase}
                </div>
              </div>
              <div className="rounded-[24px] border border-accent/18 bg-accent/[0.06] p-4">
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-coral">
                  {locale === "ru" ? "Сохраним как опору" : "We will carry this forward"}
                </div>
                <div className="mt-3 text-lg font-[700] tracking-[-0.03em] text-ink">
                  {onboarding.welcomeHandoff.afterPhrase}
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-3 md:grid-cols-3">
              {onboarding.welcomeHandoff.wins.map((item, index) => (
                <div
                  key={`${index}-${item}`}
                  className="rounded-[22px] border border-white/70 bg-white/72 p-4"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-sm font-[700] text-white">
                    {index + 1}
                  </div>
                  <div className="mt-3 text-sm leading-6 text-slate-700">{item}</div>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-[26px] border border-white/70 bg-[#fff8ef]/86 p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-coral">
                {locale === "ru" ? "Что будет дальше" : "What happens next"}
              </div>
              <div className="mt-4 space-y-3">
                {handoffNextSteps.map((item, index) => (
                  <div key={`${index}-${item}`} className="flex items-start gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#d7f0eb] text-sm font-[700] text-[#f8efe2] shadow-[0_8px_18px_rgba(39,145,140,0.18)]">
                      {index + 1}
                    </div>
                    <div className="pt-1 text-sm leading-6 text-slate-700">{item}</div>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          <div className="xl:sticky xl:top-6">
            <LizaCoachPanel
              isVisible
              locale={locale}
              playKey={`onboarding-handoff:${onboarding.welcomeHandoff.scenarioId}:${onboarding.welcomeHandoff.afterPhrase}`}
              message={handoffCoachMessage}
              replayCta={handoffReplayCta}
              allowAudioFallback={false}
              supportingText={
                locale === "ru"
                  ? "Сначала сохраним этот старт, потом Лиза соберёт первый маршрут под твою цель."
                  : "First we save this start, then Liza builds the first route around your goal."
              }
            />
          </div>
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <OnboardingSidebar
          setStep={onboarding.setStep}
          step={onboarding.step}
          steps={onboarding.steps}
          tr={tr}
        />

        <Card className="overflow-hidden p-0">
          <div className="border-b border-white/50 px-6 py-5">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.28em] text-coral">
                  {`${tr("Step")} ${onboarding.step + 1}/${onboarding.steps.length}`}
                </div>
                <div className="mt-3 text-3xl font-[700] tracking-[-0.03em] text-ink">{onboarding.activeStep.title}</div>
                <div className="mt-3 max-w-[46rem] text-sm leading-6 text-slate-600">
                  {onboarding.activeStep.description}
                </div>
              </div>
              <div className="min-w-[220px] rounded-[24px] bg-white/70 px-4 py-4">
                <div className="flex items-center justify-between text-sm text-slate-600">
                  <span>{tr("Completion")}</span>
                  <span>{completionPercent}%</span>
                </div>
                <div className="mt-3 h-2 rounded-full bg-white">
                  <div
                    className="h-full rounded-full bg-accent transition-all duration-500"
                    style={{ width: `${completionPercent}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="px-6 py-6">
            <div key={onboarding.step} className="onboarding-step-panel">
              <OnboardingStepContent {...onboarding} tr={tr} />
            </div>
          </div>

          <div className="border-t border-white/50 px-6 py-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="space-y-2">
                {onboarding.activeStepHelper ? (
                  <div className="text-sm leading-6 text-slate-500">{onboarding.activeStepHelper}</div>
                ) : null}
                {onboarding.submitError ? (
                  <div className="text-sm font-medium text-coral">{onboarding.submitError}</div>
                ) : null}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={onboarding.goBack}
                  disabled={onboarding.step === 0 || onboarding.isSaving}
                >
                  {tr("Back")}
                </Button>
                {onboarding.step === onboarding.steps.length - 1 ? (
                  <Button
                    type="button"
                    onClick={() => void onboarding.submit()}
                    disabled={!onboarding.allCoreStepsReady || onboarding.isSaving}
                  >
                    {onboarding.isSaving ? tr("Saving...") : submitLabel}
                  </Button>
                ) : (
                  <Button
                    type="button"
                    onClick={onboarding.goNext}
                    disabled={!onboarding.activeStep.ready || onboarding.isSaving}
                  >
                    {continueLabel}
                  </Button>
                )}
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
