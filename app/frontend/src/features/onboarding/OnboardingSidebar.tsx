import { Card } from "../../shared/ui/Card";
import { BrandLogo } from "../../shared/ui/BrandLogo";
import { StepRailButton } from "./OnboardingUi";
import type { OnboardingFlowController } from "./useOnboardingFlow";

type OnboardingSidebarProps = Pick<OnboardingFlowController, "setStep" | "step" | "steps"> & {
  tr: (value: string) => string;
};

export function OnboardingSidebar({ setStep, step, steps, tr }: OnboardingSidebarProps) {
  return (
    <Card className="onboarding-hero relative overflow-hidden p-0">
      <div className="border-b border-white/50 px-5 py-5">
        <div className="max-w-[20rem]">
          <div className="inline-flex rounded-[24px] bg-white/96 px-4 py-3 shadow-soft">
            <BrandLogo className="w-[118px]" />
          </div>
          <div className="mt-4 text-3xl font-[700] leading-[1.02] tracking-[-0.04em] text-white">
            {tr("Create a calm, personal start")}
          </div>
          <div className="mt-4 text-sm leading-6 text-slate-200">
            {tr(
              "This setup replaces the regular workspace until onboarding is complete, so the learner sees only the questions that matter right now.",
            )}
          </div>
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        <div className="rounded-[24px] bg-white/12 p-4 text-sm leading-6 text-white/90">
          {tr(
            "Build a flexible learner profile for adults, children, career goals, school support, and future multi-user use cases.",
          )}
        </div>

        <div className="space-y-3">
          {steps.map((item, index) => (
            <StepRailButton
              key={item.title}
              index={index}
              title={item.title}
              active={index === step}
              completed={index < step && item.ready}
              unlocked={index <= step}
              onClick={() => setStep(index)}
            />
          ))}
        </div>

        <div className="rounded-[24px] bg-white/12 p-4 text-sm leading-6 text-white/90">
          <div className="text-xs uppercase tracking-[0.18em] text-white/60">{tr("What unlocks after setup")}</div>
          <div className="mt-3">{tr("Private learner space")}</div>
          <div>{tr("Skill-balanced lesson track")}</div>
          <div>{tr("Friendly daily dashboard")}</div>
        </div>
      </div>
    </Card>
  );
}
