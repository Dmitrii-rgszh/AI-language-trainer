import { useLocale } from "../../shared/i18n/useLocale";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { OnboardingSidebar } from "./OnboardingSidebar";
import { OnboardingStepContent } from "./OnboardingStepContent";
import { useOnboardingFlow } from "./useOnboardingFlow";

export function OnboardingScreen() {
  const { tr } = useLocale();
  const onboarding = useOnboardingFlow();
  const completionPercent = Math.round(((onboarding.step + 1) / onboarding.steps.length) * 100);

  return (
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
              <div className="text-xs uppercase tracking-[0.34em] text-coral">
                {`${tr("Step")} ${onboarding.step + 1}/${onboarding.steps.length}`}
              </div>
              <div className="mt-3 text-3xl font-semibold text-ink">{onboarding.activeStep.title}</div>
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
                  {onboarding.isSaving ? tr("Saving...") : tr("Create workspace")}
                </Button>
              ) : (
                <Button
                  type="button"
                  onClick={onboarding.goNext}
                  disabled={!onboarding.activeStep.ready || onboarding.isSaving}
                >
                  {tr("Continue")}
                </Button>
              )}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
