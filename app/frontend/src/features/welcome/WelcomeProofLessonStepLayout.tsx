import type { ReactNode } from "react";
import { cn } from "../../shared/utils/cn";

type WelcomeProofLessonProgressProps = {
  currentStep: number;
  totalSteps: number;
  progressLabel: string;
};

type WelcomeProofLessonStepLayoutProps = {
  isVisible: boolean;
  currentStep: number;
  totalSteps: number;
  progressLabel: string;
  stepKey?: string;
  eyebrow?: string;
  title: string;
  description?: string;
  content?: ReactNode;
  contentClassName?: string;
  cardClassName?: string;
  stepClassName?: string;
  primaryAction?: ReactNode;
  secondaryAction?: ReactNode;
  helperText?: ReactNode;
};

export function WelcomeProofLessonProgress({
  currentStep,
  totalSteps,
  progressLabel,
}: WelcomeProofLessonProgressProps) {
  const progressPercent = (currentStep / totalSteps) * 100;

  return (
    <div className="proof-lesson-progress">
      <div className="proof-lesson-progress__track">
        <div
          className="proof-lesson-progress__bar"
          style={{ width: `${progressPercent}%` }}
        />
      </div>
      <div className="proof-lesson-progress__label">{progressLabel}</div>
    </div>
  );
}

export function WelcomeProofLessonStepLayout({
  isVisible,
  currentStep,
  totalSteps,
  progressLabel,
  stepKey,
  eyebrow,
  title,
  description,
  content,
  contentClassName,
  cardClassName,
  stepClassName,
  primaryAction,
  secondaryAction,
  helperText,
}: WelcomeProofLessonStepLayoutProps) {
  const hasFooter = Boolean(primaryAction || secondaryAction || helperText);

  return (
    <div className="relative z-10 mx-auto max-w-[980px]">
      <div
        className={cn(
          "welcome-reveal proof-lesson-card",
          isVisible && "is-visible",
          cardClassName,
        )}
        style={{ transitionDelay: "120ms" }}
      >
        <WelcomeProofLessonProgress
          currentStep={currentStep}
          totalSteps={totalSteps}
          progressLabel={progressLabel}
        />

        <div
          key={stepKey}
          className={cn("onboarding-step-panel proof-lesson-step", stepClassName)}
        >
          <div className="proof-lesson-step__body">
            <div className="proof-lesson-step__header">
              {eyebrow ? (
                <div className="proof-lesson-step__eyebrow">{eyebrow}</div>
              ) : null}
              <h2 className="proof-lesson-step__title">{title}</h2>
              {description ? (
                <p className="proof-lesson-step__description">{description}</p>
              ) : null}
            </div>

            {content ? (
              <div className={cn("proof-lesson-step__content", contentClassName)}>
                {content}
              </div>
            ) : null}
          </div>

          {hasFooter ? (
            <div className="proof-lesson-step__footer">
              {primaryAction ? (
                <div className="proof-lesson-step__actions">{primaryAction}</div>
              ) : null}
              {secondaryAction ? (
                <div className="proof-lesson-step__secondary">{secondaryAction}</div>
              ) : null}
              {helperText ? (
                <div className="proof-lesson-step__helper">{helperText}</div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
