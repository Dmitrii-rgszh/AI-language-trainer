import type { ReactNode } from "react";
import type { AppLocale } from "../../shared/i18n/locale";
import { Button } from "../../shared/ui/Button";
import { cn } from "../../shared/utils/cn";
import { useWelcomeProofLesson } from "./useWelcomeProofLesson";
import { WelcomeProofLessonStepLayout } from "./WelcomeProofLessonStepLayout";

type WelcomeProofLessonProps = {
  isVisible: boolean;
  locale: AppLocale;
};

type WelcomeProofLessonStepView = {
  eyebrow: string;
  title: string;
  description?: string;
  content?: ReactNode;
  primaryAction?: ReactNode;
  secondaryAction?: ReactNode;
  helperText?: ReactNode;
};

type ProofLessonSurfaceProps = {
  children: ReactNode;
  tone?: "default" | "accent" | "warm";
  className?: string;
};

type ProofLessonTextComposerProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  previewLabel: string;
  submitLabel: string;
  onSubmit: () => void;
};

type ProofLessonVoiceComposerProps = {
  value: string;
  isRecording: boolean;
  isProcessing: boolean;
  statusLabel: string;
  previewLabel: string;
};

const proofLessonStepCopy = {
  ru: {
    introEyebrow: "Быстрый старт в Verba",
    attemptEyebrow: "Первая попытка",
    attemptDescription:
      "Скажи или напиши одну естественную короткую фразу. Verba сразу покажет, как сделать её точнее.",
    feedbackEyebrow: "Разбор фразы",
    feedbackDescription:
      "Сохраняем твою мысль, но делаем фразу мягче, естественнее и полезнее для следующих ситуаций.",
    clarityEyebrow: "Понятность речи",
    retryEyebrow: "Применение шаблона",
    retryDescription:
      "Сразу перенеси тот же паттерн в новую фразу, чтобы он закрепился как рабочий инструмент.",
    retryTaskLabel: "Новая задача",
    resultEyebrow: "Итог mini-proof-lesson",
    resultDescription:
      "Одна живая ситуация уже превратилась в понятный speaking pattern, который можно переносить дальше.",
  },
  en: {
    introEyebrow: "Quick start in Verba",
    attemptEyebrow: "First response",
    attemptDescription:
      "Say or write one natural short phrase. Verba immediately shows how to make it clearer and more natural.",
    feedbackEyebrow: "Phrase refinement",
    feedbackDescription:
      "We keep your meaning, but shape the phrase into something softer, more natural, and easier to reuse.",
    clarityEyebrow: "Speech clarity",
    retryEyebrow: "Apply the pattern",
    retryDescription:
      "Move the same pattern into a new phrase right away so it starts to feel usable, not theoretical.",
    retryTaskLabel: "New task",
    resultEyebrow: "Mini-proof-lesson result",
    resultDescription:
      "One live situation already became a clearer speaking pattern you can transfer into the next phrase.",
  },
} as const;

function ProofLessonSurface({
  children,
  tone = "default",
  className,
}: ProofLessonSurfaceProps) {
  return (
    <div
      className={cn(
        "proof-lesson-surface",
        tone === "accent" && "proof-lesson-surface--accent",
        tone === "warm" && "proof-lesson-surface--warm",
        className,
      )}
    >
      {children}
    </div>
  );
}

function ProofLessonSectionLabel({
  children,
  accent = false,
}: {
  children: ReactNode;
  accent?: boolean;
}) {
  return (
    <div
      className={cn(
        "proof-lesson-section-label",
        accent && "proof-lesson-section-label--accent",
      )}
    >
      {children}
    </div>
  );
}

function ProofLessonSecondaryAction({
  children,
  onClick,
}: {
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="proof-lesson-secondary-action"
    >
      {children}
    </button>
  );
}

function ProofLessonTextComposer({
  value,
  onChange,
  placeholder,
  previewLabel,
  submitLabel,
  onSubmit,
}: ProofLessonTextComposerProps) {
  const trimmedValue = value.trim();

  return (
    <div className="proof-lesson-composer">
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={3}
        placeholder={placeholder}
        className="proof-lesson-textarea"
      />

      {trimmedValue ? (
        <ProofLessonSurface tone="warm">
          <ProofLessonSectionLabel>{previewLabel}</ProofLessonSectionLabel>
          <div className="proof-lesson-preview-text">{trimmedValue}</div>
        </ProofLessonSurface>
      ) : null}

      <Button type="button" onClick={onSubmit} className="proof-lesson-primary-button">
        {submitLabel}
      </Button>
    </div>
  );
}

function ProofLessonVoiceComposer({
  value,
  isRecording,
  isProcessing,
  statusLabel,
  previewLabel,
}: ProofLessonVoiceComposerProps) {
  return (
    <div className="proof-lesson-composer">
      <ProofLessonSurface className="proof-lesson-voice-surface">
        <div className="proof-lesson-voice-status">
          <span
            className={cn(
              "proof-lesson-voice-status__dot",
              isRecording && "proof-lesson-voice-status__dot--live",
            )}
            aria-hidden="true"
          />
          <span>{statusLabel}</span>
        </div>
      </ProofLessonSurface>

      {value.trim() ? (
        <ProofLessonSurface tone="warm">
          <ProofLessonSectionLabel>{previewLabel}</ProofLessonSectionLabel>
          <div className="proof-lesson-preview-text">{value.trim()}</div>
        </ProofLessonSurface>
      ) : null}

      {isProcessing ? (
        <ProofLessonSurface tone="warm">
          <div className="proof-lesson-supporting-copy">
            {statusLabel}
          </div>
        </ProofLessonSurface>
      ) : null}
    </div>
  );
}

function ProofLessonTrustBadge({ children }: { children: ReactNode }) {
  return (
    <div className="proof-lesson-trust-badge" aria-label={String(children)}>
      <span className="proof-lesson-trust-badge__icon" aria-hidden="true">
        <svg viewBox="0 0 16 16" className="proof-lesson-trust-badge__icon-svg">
          <path
            d="M6.55 11.4 3.6 8.45l.96-.97 1.99 1.99 4.89-4.89.96.96-5.85 5.86Z"
            fill="currentColor"
          />
        </svg>
      </span>
      <span>{children}</span>
    </div>
  );
}

export function WelcomeProofLesson({
  isVisible,
  locale,
}: WelcomeProofLessonProps) {
  const lesson = useWelcomeProofLesson(locale);
  const progressLabel =
    locale === "ru"
      ? `${lesson.stepIndex + 1} из ${lesson.totalSteps}`
      : `${lesson.stepIndex + 1} of ${lesson.totalSteps}`;
  const copy = proofLessonStepCopy[locale];

  const attemptContent =
    lesson.attemptInputMode === "voice" && lesson.voiceInputEnabled ? (
      <div className="proof-lesson-stack">
        {lesson.attemptMessage ? (
          <ProofLessonSurface tone="warm">{lesson.attemptMessage}</ProofLessonSurface>
        ) : null}
        <ProofLessonVoiceComposer
          value={lesson.attemptAnswer}
          isRecording={lesson.isVoiceRecording}
          isProcessing={lesson.isVoiceProcessing}
          statusLabel={
            lesson.isVoiceProcessing
              ? lesson.scenario.errors.networkRetry
              : lesson.isVoiceRecording
                ? lesson.scenario.firstAttempt.voiceRecordingCta
                : lesson.scenario.firstAttempt.voiceStartCta
          }
          previewLabel={lesson.scenario.firstAttempt.saidLabel}
        />
      </div>
    ) : (
      <div className="proof-lesson-stack">
        {lesson.attemptMessage ? (
          <ProofLessonSurface tone="warm">{lesson.attemptMessage}</ProofLessonSurface>
        ) : null}
        <ProofLessonTextComposer
          value={lesson.attemptAnswer}
          onChange={lesson.setAttemptAnswer}
          placeholder={lesson.scenario.firstAttempt.textPlaceholder}
          previewLabel={lesson.scenario.firstAttempt.wroteLabel}
          submitLabel={lesson.scenario.firstAttempt.submitCta}
          onSubmit={lesson.submitFirstAttempt}
        />
      </div>
    );

  const retryContent = (
    <div className="proof-lesson-stack">
      <ProofLessonSurface tone="accent">
        <ProofLessonSectionLabel accent>
          {copy.retryTaskLabel}
        </ProofLessonSectionLabel>
        <div className="proof-lesson-key-text">{lesson.scenario.retry.task}</div>
      </ProofLessonSurface>

      {lesson.retryMessage ? (
        <ProofLessonSurface tone="warm">{lesson.retryMessage}</ProofLessonSurface>
      ) : null}

      {lesson.retryInputMode === "voice" && lesson.voiceInputEnabled ? (
        <ProofLessonVoiceComposer
          value={lesson.retryAnswer}
          isRecording={lesson.isVoiceRecording}
          isProcessing={lesson.isVoiceProcessing}
          statusLabel={
            lesson.isVoiceProcessing
              ? lesson.scenario.errors.networkRetry
              : lesson.isVoiceRecording
                ? lesson.scenario.retry.voiceRecordingCta
                : lesson.scenario.retry.voiceStartCta
          }
          previewLabel={lesson.scenario.retry.saidLabel}
        />
      ) : null}

      {lesson.retryInputMode === "text" ? (
        <ProofLessonTextComposer
          value={lesson.retryAnswer}
          onChange={lesson.setRetryAnswer}
          placeholder={lesson.scenario.retry.textPlaceholder}
          previewLabel={lesson.scenario.retry.wroteLabel}
          submitLabel={lesson.scenario.retry.submitCta}
          onSubmit={lesson.submitRetry}
        />
      ) : null}

      {lesson.retrySuccessful ? (
        <ProofLessonSurface tone="accent">
          <div className="proof-lesson-key-text">
            {lesson.scenario.retry.successTitle}
          </div>
          <p className="proof-lesson-supporting-copy">
            {lesson.scenario.retry.successDescription}
          </p>
        </ProofLessonSurface>
      ) : null}
    </div>
  );

  let stepView: WelcomeProofLessonStepView;

  switch (lesson.currentStep) {
    case "intro":
      stepView = {
        eyebrow: copy.introEyebrow,
        title: lesson.scenario.intro.title,
        description: lesson.scenario.intro.description,
        content: (
          <ProofLessonTrustBadge>
            {lesson.scenario.intro.microCopy}
          </ProofLessonTrustBadge>
        ),
        primaryAction: (
          <Button
            type="button"
            onClick={lesson.startLesson}
            className="proof-lesson-primary-button"
          >
            {lesson.scenario.intro.cta}
          </Button>
        ),
      };
      break;
    case "situation":
      stepView = {
        eyebrow: lesson.scenario.situation.label,
        title: lesson.scenario.situation.title,
        description: lesson.scenario.situation.description,
        primaryAction: (
          <Button
            type="button"
            onClick={() => lesson.beginFirstAttempt("voice")}
            className="proof-lesson-primary-button"
          >
            {lesson.scenario.situation.primaryCta}
          </Button>
        ),
        secondaryAction: (
          <ProofLessonSecondaryAction
            onClick={() => lesson.beginFirstAttempt("text")}
          >
            {lesson.scenario.situation.secondaryCta}
          </ProofLessonSecondaryAction>
        ),
        helperText: lesson.scenario.situation.hint,
      };
      break;
    case "attempt":
      stepView = {
        eyebrow: copy.attemptEyebrow,
        title: lesson.scenario.firstAttempt.title,
        description: copy.attemptDescription,
        content: attemptContent,
        primaryAction:
          lesson.attemptInputMode === "voice" && lesson.voiceInputEnabled ? (
            <Button
              type="button"
              onClick={() =>
                void (lesson.isVoiceRecording
                  ? lesson.stopVoiceRecording()
                  : lesson.startVoiceRecording("attempt"))
              }
              disabled={lesson.isVoiceProcessing}
              className="proof-lesson-primary-button"
            >
              {lesson.isVoiceProcessing
                ? locale === "ru"
                  ? "Обрабатываем..."
                  : "Processing..."
                : lesson.isVoiceRecording
                  ? lesson.scenario.firstAttempt.voiceDoneCta
                  : lesson.scenario.firstAttempt.voiceStartCta}
            </Button>
          ) : undefined,
        secondaryAction:
          lesson.attemptInputMode === "voice" && lesson.voiceInputEnabled ? (
            <ProofLessonSecondaryAction
              onClick={() => lesson.beginFirstAttempt("text")}
            >
              {lesson.scenario.firstAttempt.fallbackCta}
            </ProofLessonSecondaryAction>
          ) : undefined,
      };
      break;
    case "feedback":
      stepView = {
        eyebrow: copy.feedbackEyebrow,
        title: lesson.feedback.title,
        description: copy.feedbackDescription,
        content: (
          <div className="proof-lesson-stack">
            <div className="grid gap-4 md:grid-cols-2">
              <ProofLessonSurface>
                <ProofLessonSectionLabel>
                  {lesson.scenario.feedback.userVersionLabel}
                </ProofLessonSectionLabel>
                <div className="proof-lesson-key-text">
                  {lesson.feedback.userVersion}
                </div>
              </ProofLessonSurface>

              <ProofLessonSurface tone="accent">
                <ProofLessonSectionLabel accent>
                  {lesson.scenario.feedback.improvedVersionLabel}
                </ProofLessonSectionLabel>
                <div className="proof-lesson-key-text">
                  {lesson.feedback.improvedVersion}
                </div>
              </ProofLessonSurface>
            </div>

            <ProofLessonSurface tone="warm">
              <div className="proof-lesson-stack-sm">
                <p className="proof-lesson-supporting-copy">
                  {lesson.feedback.explanationPrimary}
                </p>
                <p className="proof-lesson-supporting-copy">
                  {lesson.feedback.explanationSecondary}
                </p>
              </div>
            </ProofLessonSurface>

            <ProofLessonSurface>
              <ProofLessonSectionLabel>
                {lesson.scenario.feedback.patternLabel}
              </ProofLessonSectionLabel>
              <div className="proof-lesson-key-text">
                {lesson.scenario.feedback.patternValue}
              </div>
              <p className="proof-lesson-supporting-copy mt-5">
                {lesson.scenario.feedback.examplesLabel}
              </p>
              <div className="mt-4 grid gap-3">
                {lesson.scenario.feedback.examples.map((example) => (
                  <div key={example} className="proof-lesson-list-item">
                    {example}
                  </div>
                ))}
              </div>
            </ProofLessonSurface>
          </div>
        ),
        primaryAction: (
          <Button
            type="button"
            onClick={lesson.goToClarity}
            className="proof-lesson-primary-button"
          >
            {lesson.scenario.feedback.cta}
          </Button>
        ),
        helperText: lesson.scenario.feedback.followUp,
      };
      break;
    case "clarity":
      stepView = {
        eyebrow: copy.clarityEyebrow,
        title: lesson.scenario.clarity.title,
        description: lesson.scenario.clarity.subtitle,
        content: (
          <div className="proof-lesson-stack">
            <ProofLessonSurface tone="accent" className="max-w-[24rem]">
              <div className="proof-lesson-key-text">
                {lesson.clarityStatusLabel}
              </div>
            </ProofLessonSurface>

            <ProofLessonSurface>
              <ProofLessonSectionLabel>
                {lesson.scenario.clarity.hintsTitle}
              </ProofLessonSectionLabel>
              <div className="mt-4 grid gap-3">
                {lesson.scenario.clarity.hints.map((hint) => (
                  <div key={hint} className="proof-lesson-list-item">
                    {hint}
                  </div>
                ))}
              </div>
            </ProofLessonSurface>
          </div>
        ),
        primaryAction: (
          <Button
            type="button"
            onClick={lesson.goToRetry}
            className="proof-lesson-primary-button"
          >
            {lesson.scenario.clarity.cta}
          </Button>
        ),
      };
      break;
    case "retry":
      stepView = {
        eyebrow: copy.retryEyebrow,
        title: lesson.scenario.retry.title,
        description: copy.retryDescription,
        content: retryContent,
        primaryAction:
          lesson.retryInputMode === null ? (
            <Button
              type="button"
              onClick={() => lesson.beginRetry("voice")}
              className="proof-lesson-primary-button"
            >
              {lesson.scenario.retry.primaryCta}
            </Button>
          ) : lesson.retryInputMode === "voice" && lesson.voiceInputEnabled ? (
            <Button
              type="button"
              onClick={() =>
                void (lesson.isVoiceRecording
                  ? lesson.stopVoiceRecording()
                  : lesson.startVoiceRecording("retry"))
              }
              disabled={lesson.isVoiceProcessing}
              className="proof-lesson-primary-button"
            >
              {lesson.isVoiceProcessing
                ? locale === "ru"
                  ? "Обрабатываем..."
                  : "Processing..."
                : lesson.isVoiceRecording
                  ? lesson.scenario.retry.voiceDoneCta
                  : lesson.scenario.retry.voiceStartCta}
            </Button>
          ) : undefined,
        secondaryAction:
          lesson.retryInputMode === null ? (
            <ProofLessonSecondaryAction
              onClick={() => lesson.beginRetry("text")}
            >
              {lesson.scenario.retry.secondaryCta}
            </ProofLessonSecondaryAction>
          ) : lesson.retryInputMode === "voice" && lesson.voiceInputEnabled ? (
            <ProofLessonSecondaryAction
              onClick={() => lesson.beginRetry("text")}
            >
              {lesson.scenario.retry.fallbackCta}
            </ProofLessonSecondaryAction>
          ) : undefined,
      };
      break;
    case "result":
    default:
      stepView = {
        eyebrow: copy.resultEyebrow,
        title: lesson.scenario.result.title,
        description: copy.resultDescription,
        content: (
          <div className="proof-lesson-stack">
            <div className="grid gap-3">
              {lesson.scenario.result.points.map((point) => (
                <div key={point} className="proof-lesson-list-item">
                  {point}
                </div>
              ))}
            </div>

            <ProofLessonSurface>
              <ProofLessonSectionLabel>
                {lesson.scenario.result.comparisonTitle}
              </ProofLessonSectionLabel>
              <div className="mt-5 grid gap-5 md:grid-cols-2">
                <div>
                  <ProofLessonSectionLabel>
                    {lesson.scenario.result.beforeLabel}
                  </ProofLessonSectionLabel>
                  <div className="proof-lesson-key-text text-slate-500">
                    {lesson.scenario.result.beforeValue}
                  </div>
                </div>
                <div>
                  <ProofLessonSectionLabel accent>
                    {lesson.scenario.result.afterLabel}
                  </ProofLessonSectionLabel>
                  <div className="proof-lesson-key-text">
                    {lesson.scenario.result.afterValue}
                  </div>
                </div>
              </div>
              <p className="proof-lesson-supporting-copy mt-5">
                {lesson.scenario.result.comment}
              </p>
            </ProofLessonSurface>
          </div>
        ),
        primaryAction: (
          <Button
            type="button"
            onClick={lesson.buildNextLesson}
            className="proof-lesson-primary-button"
          >
            {lesson.scenario.result.primaryCta}
          </Button>
        ),
        secondaryAction: (
          <ProofLessonSecondaryAction onClick={lesson.showAnotherExample}>
            {lesson.scenario.result.secondaryCta}
          </ProofLessonSecondaryAction>
        ),
        helperText: lesson.scenario.result.note,
      };
      break;
  }

  return (
    <WelcomeProofLessonStepLayout
      key={`${lesson.scenario.id}-${lesson.currentStep}`}
      isVisible={isVisible}
      currentStep={lesson.stepIndex + 1}
      totalSteps={lesson.totalSteps}
      progressLabel={progressLabel}
      eyebrow={stepView.eyebrow}
      title={stepView.title}
      description={stepView.description}
      content={stepView.content}
      primaryAction={stepView.primaryAction}
      secondaryAction={stepView.secondaryAction}
      helperText={stepView.helperText}
    />
  );
}
