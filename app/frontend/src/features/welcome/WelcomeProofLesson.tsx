import { useEffect, useRef, useState, type ReactNode } from "react";
import type { AppLocale } from "../../shared/i18n/locale";
import { Button } from "../../shared/ui/Button";
import { cn } from "../../shared/utils/cn";
import {
  WelcomeAiTutorCue,
  type WelcomeAiTutorCueHandle,
} from "./WelcomeAiTutorCue";
import { useWelcomeProofLesson } from "./useWelcomeProofLesson";
import { WelcomeProofLessonStepLayout } from "./WelcomeProofLessonStepLayout";
import {
  getWelcomeProofLessonCoachPrompt,
  type WelcomeProofLessonCoachCue,
} from "./welcomeAiTutorPrompts";
import {
  LizaCoachPanel,
  type LizaCoachPlaybackSegment,
} from "../../widgets/liza/LizaCoachPanel";
import type { WelcomeProofLessonRuntime } from "./useWelcomeProofLessonRuntime";

const WELCOME_TUTOR_CLARITY_PRESET_REVISION = "welcome-presets-v7-stable-coach";

type WelcomeProofLessonProps = {
  isVisible: boolean;
  locale: AppLocale;
  runtime: WelcomeProofLessonRuntime;
  onRetryRuntime: () => void;
};

type WelcomeProofLessonStepView = {
  eyebrow: string;
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
  autoStopLabel?: string | null;
  autoStopProgress?: number | null;
};

type ProofLessonAdviceListProps = {
  items: string[];
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
    resultEyebrow: "Итог",
    resultDescription:
      "Одна живая ситуация уже превратилась в рабочий шаблон. Дальше сохраним этот старт в твоём профиле и соберём личный трек.",
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
    resultEyebrow: "Result",
    resultDescription:
      "One live situation already became a working pattern. Next we save this start in your profile and build a personal track around it.",
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
  autoStopLabel,
  autoStopProgress,
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
        {autoStopLabel ? (
          <div className="proof-lesson-voice-autostop">
            <div className="proof-lesson-voice-autostop__label">{autoStopLabel}</div>
            <div className="proof-lesson-voice-autostop__track" aria-hidden="true">
              <div
                className="proof-lesson-voice-autostop__bar"
                style={{ width: `${Math.max(0, Math.min(100, (autoStopProgress ?? 0) * 100))}%` }}
              />
            </div>
          </div>
        ) : null}
      </ProofLessonSurface>

      {value.trim() ? (
        <ProofLessonSurface tone="warm">
          <ProofLessonSectionLabel>{previewLabel}</ProofLessonSectionLabel>
          <div className="proof-lesson-preview-text">{value.trim()}</div>
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

function ProofLessonAdviceList({ items }: ProofLessonAdviceListProps) {
  return (
    <div className="proof-lesson-advice-list" role="list">
      {items.slice(0, 3).map((item, index) => (
        <div key={`${index}-${item}`} className="proof-lesson-advice-list__item" role="listitem">
          <span className="proof-lesson-advice-list__index" aria-hidden="true">
            {index + 1}
          </span>
          <p className="proof-lesson-advice-list__text">{item}</p>
        </div>
      ))}
    </div>
  );
}

export function WelcomeProofLesson({
  isVisible,
  locale,
  runtime,
  onRetryRuntime,
}: WelcomeProofLessonProps) {
  const lesson = useWelcomeProofLesson(locale);
  const [hasSituationIntroCompleted, setHasSituationIntroCompleted] = useState(false);
  const [isSituationIntroLoading, setIsSituationIntroLoading] = useState(false);
  const [isSituationIntroPlaying, setIsSituationIntroPlaying] = useState(false);
  const situationCueRef = useRef<WelcomeAiTutorCueHandle | null>(null);
  const showsProgress = lesson.currentStep !== "intro";
  const progressTotalSteps = Math.max(1, lesson.totalSteps - 1);
  const progressCurrentStep = showsProgress
    ? Math.min(progressTotalSteps, Math.max(1, lesson.stepIndex))
    : 0;
  const progressLabel = showsProgress
    ? locale === "ru"
      ? `${progressCurrentStep} из ${progressTotalSteps}`
      : `${progressCurrentStep} of ${progressTotalSteps}`
    : "";
  const copy = proofLessonStepCopy[locale];
  const voiceProcessingLabel =
    locale === "ru" ? "Распознаём и разбираем твою фразу..." : "Recognizing and analyzing your phrase...";
  const voiceListeningLabel =
    locale === "ru" ? "Слушаю. Начни говорить..." : "Listening. Start speaking...";
  const voiceDetectedLabel =
    locale === "ru"
      ? "Фразу услышала. Остановлю запись после 3 секунд тишины..."
      : "I heard the phrase. I will stop after 3 seconds of silence...";
  const naturalMatchDescription =
    locale === "ru"
      ? "Ты уже сказал именно ту фразу, которая звучит естественно и вежливо. Ниже коротко закрепим, почему она хороша."
      : "You already said the natural and polite version. Below is a short explanation of why it works well.";
  const naturalMatchLabel =
    locale === "ru" ? "Отлично, это уже хороший вариант" : "Great, this is already a strong version";
  const naturalMatchHint =
    locale === "ru" ? "Совпадает с рекомендуемой формулировкой." : "It matches the recommended phrasing.";
  const coachReplayCta =
    locale === "ru" ? "Послушать ещё раз" : "Hear it again";
  const manualStopLabel =
    locale === "ru" ? "Остановить вручную" : "Stop manually";
  const autoStopHelperText =
    locale === "ru"
      ? "После фразы запись остановится сама, когда услышит паузу."
      : "After your phrase, the recording stops on its own when it hears a pause.";
  const feedbackAdviceItems = [
    lesson.feedback.explanationPrimary,
    lesson.feedback.explanationSecondary,
  ].filter(Boolean);
  const trailingSilenceSeconds =
    lesson.voiceTrailingSilenceRemainingMs !== null
      ? Math.max(0.3, Math.ceil(lesson.voiceTrailingSilenceRemainingMs / 100) / 10)
      : null;
  const trailingSilenceProgress =
    lesson.voiceTrailingSilenceRemainingMs !== null
      ? lesson.voiceTrailingSilenceRemainingMs / 3000
      : null;
  const autoStopLabel =
    trailingSilenceSeconds !== null
      ? locale === "ru"
        ? `Автостоп через ${trailingSilenceSeconds.toFixed(1)} с`
        : `Auto-stop in ${trailingSilenceSeconds.toFixed(1)}s`
      : null;
  const clarityModelPhrase = lesson.scenario.languageTargets.firstAttemptImproved;
  const clarityCoachMessage =
    locale === "ru"
      ? `Слушай, как Лиза произносит фразу: ${clarityModelPhrase}`
      : `Listen to how Liza says the phrase: ${clarityModelPhrase}`;
  const clarityCoachReplayCta =
    locale === "ru" ? "Послушать фразу ещё раз" : "Hear the phrase again";
  const clarityCoachSpeakingLabel =
    locale === "ru" ? "Лиза произносит фразу" : "Liza is saying the phrase";
  const resultCoachMessage =
    locale === "ru"
      ? "Ты уже почувствовал, как Verba превращает живую фразу в понятный навык. Теперь сохраним этот старт в твоём профиле и соберём личный трек."
      : "You already felt how Verba turns one live phrase into a usable skill. Next we save this start in your profile and build a personal track around it.";
  const resultJourneyTitle =
    locale === "ru" ? "Что будет дальше" : "What happens next";
  const resultJourneySteps =
    locale === "ru"
      ? [
          "Создадим твой аккаунт и сохраним этот первый результат",
          "Лиза уточнит твою цель, уровень и желаемый формат обучения",
          "Сразу соберём личный стартовый трек вместо общего курса",
        ]
      : [
          "We create your account and save this first result",
          "Liza clarifies your goal, level, and preferred learning format",
          "Right away, we build a personal starter track instead of a generic course",
        ];

  function buildCoachDock(
    cue: WelcomeProofLessonCoachCue,
    overrides?: {
      message?: string;
      replayCta?: string;
      autoplaySegments?: LizaCoachPlaybackSegment[];
      replaySegments?: LizaCoachPlaybackSegment[];
      playbackText?: string;
      playbackLanguage?: "ru" | "en";
      speakingLabelOverride?: string;
      idleLabelOverride?: string;
    },
  ) {
    return (
      <div className="proof-lesson-coach-dock-row">
        <LizaCoachPanel
          isVisible={isVisible}
          locale={locale}
          message={overrides?.message ?? getWelcomeProofLessonCoachPrompt(locale, cue)}
          spokenMessage={overrides?.playbackText}
          spokenLanguage={overrides?.playbackLanguage}
          replayCta={overrides?.replayCta ?? coachReplayCta}
          playKey={`${lesson.scenario.id}:${lesson.currentStep}:${cue}`}
          autoplaySegments={overrides?.autoplaySegments}
          replaySegments={overrides?.replaySegments}
          speakingLabelOverride={overrides?.speakingLabelOverride}
          idleLabelOverride={overrides?.idleLabelOverride}
          allowAudioFallback={false}
        />
      </div>
    );
  }

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
              ? voiceProcessingLabel
              : lesson.isVoiceRecording
                ? lesson.voiceActivityState === "speech_detected"
                  ? voiceDetectedLabel
                  : voiceListeningLabel
                : lesson.scenario.firstAttempt.voiceStartCta
          }
          previewLabel={lesson.scenario.firstAttempt.saidLabel}
          autoStopLabel={
            lesson.isVoiceRecording && lesson.voiceActivityState === "speech_detected"
              ? autoStopLabel
              : null
          }
          autoStopProgress={trailingSilenceProgress}
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
      {buildCoachDock("retry")}

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
              ? voiceProcessingLabel
              : lesson.isVoiceRecording
                ? lesson.voiceActivityState === "speech_detected"
                  ? voiceDetectedLabel
                  : voiceListeningLabel
                : lesson.scenario.retry.voiceStartCta
          }
          previewLabel={lesson.scenario.retry.saidLabel}
          autoStopLabel={
            lesson.isVoiceRecording && lesson.voiceActivityState === "speech_detected"
              ? autoStopLabel
              : null
          }
          autoStopProgress={trailingSilenceProgress}
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
  const situationPrompt =
    lesson.scenario.situation.coachSpokenPrompt ??
    lesson.scenario.situation.coachPrompt;
  const situationPreviewMessage =
    locale === "ru"
      ? "Прослушай короткое задание от Лизы, а потом ответь, как бы ты сказал это по-английски."
      : "Listen to Liza’s short prompt first, then answer how you would say it in English.";

  useEffect(() => {
    if (lesson.currentStep !== "situation") {
      setHasSituationIntroCompleted(false);
      setIsSituationIntroLoading(false);
      setIsSituationIntroPlaying(false);
    }
  }, [lesson.currentStep, lesson.scenario.id]);

  async function playSituationIntro() {
    if (!situationCueRef.current || isSituationIntroPlaying || isSituationIntroLoading) {
      return;
    }

    setIsSituationIntroLoading(true);
    const started = await situationCueRef.current.playIntro();
    if (!started) {
      setIsSituationIntroLoading(false);
      setIsSituationIntroPlaying(false);
    }
  }

  switch (lesson.currentStep) {
    case "intro":
      stepView = {
        eyebrow: copy.introEyebrow,
        title: lesson.scenario.intro.title,
        description: lesson.scenario.intro.description,
        cardClassName: "proof-lesson-card--intro",
        content: (
          <div className="proof-lesson-stack">
            <ProofLessonTrustBadge>
              {lesson.scenario.intro.microCopy}
            </ProofLessonTrustBadge>

            <ProofLessonSurface tone={runtime.phase === "ready" ? "accent" : "warm"}>
              <ProofLessonSectionLabel accent>
                {runtime.title}
              </ProofLessonSectionLabel>
              <p className="proof-lesson-supporting-copy mt-4">
                {runtime.description}
              </p>
              {runtime.detail ? (
                <p className="proof-lesson-supporting-copy mt-3 text-coral">
                  {runtime.detail}
                </p>
              ) : null}
            </ProofLessonSurface>
          </div>
        ),
        primaryAction: (
          runtime.phase === "error" ? (
            <Button
              type="button"
              onClick={onRetryRuntime}
              className="proof-lesson-primary-button"
            >
              {locale === "ru" ? "Подготовить живой урок ещё раз" : "Prepare the live lesson again"}
            </Button>
          ) : (
            <Button
              type="button"
              onClick={lesson.startLesson}
              disabled={!runtime.canStart}
              className="proof-lesson-primary-button"
            >
              {runtime.phase === "preparing"
                ? locale === "ru"
                  ? "Лиза подготавливает урок..."
                  : "Liza is preparing the lesson..."
                : lesson.scenario.intro.cta}
            </Button>
          )
        ),
      };
      break;
    case "situation":
      stepView = {
        eyebrow: lesson.scenario.situation.label,
        title: lesson.scenario.situation.title,
        cardClassName: "proof-lesson-card--scene",
        stepClassName: "proof-lesson-step--scene",
        contentClassName: "proof-lesson-step__content--scene",
        content: (
          <div className="proof-lesson-stack">
            <WelcomeAiTutorCue
              ref={(value) => {
                situationCueRef.current = value;
              }}
              isVisible={isVisible}
              locale={locale}
              label={lesson.scenario.situation.coachLabel}
              message={hasSituationIntroCompleted ? situationPrompt : situationPreviewMessage}
              spokenMessage={situationPrompt}
              replayCta={lesson.scenario.situation.coachReplayCta}
              showReplayAction={hasSituationIntroCompleted}
              showStaticFallback={false}
              onIntroPlaybackStart={() => {
                setIsSituationIntroLoading(false);
                setIsSituationIntroPlaying(true);
              }}
              onIntroPlaybackComplete={() => {
                setIsSituationIntroLoading(false);
                setIsSituationIntroPlaying(false);
                setHasSituationIntroCompleted(true);
              }}
            />

            {lesson.isAttemptActive ? attemptContent : null}
          </div>
        ),
        primaryAction: (
          !hasSituationIntroCompleted ? (
            <Button
              type="button"
              onClick={() => void playSituationIntro()}
              disabled={isSituationIntroPlaying || isSituationIntroLoading}
              className="proof-lesson-primary-button"
            >
              {isSituationIntroLoading
                ? locale === "ru"
                  ? "Загружаем задание..."
                  : "Loading the prompt..."
                : isSituationIntroPlaying
                ? locale === "ru"
                  ? "Лиза говорит..."
                  : "Liza is speaking..."
                : locale === "ru"
                  ? "Прослушать задание"
                  : "Listen to the prompt"}
            </Button>
          ) : lesson.isAttemptActive &&
            lesson.attemptInputMode === "voice" &&
            lesson.voiceInputEnabled &&
            !lesson.isVoiceRecording &&
            !lesson.isVoiceProcessing ? (
            <Button
              type="button"
              onClick={() => void lesson.startVoiceRecording("attempt")}
              className="proof-lesson-primary-button"
            >
              {lesson.scenario.firstAttempt.voiceStartCta}
            </Button>
          ) : !lesson.isAttemptActive ? (
            <Button
              type="button"
              onClick={() => void lesson.beginVoiceFirstAttempt()}
              className="proof-lesson-primary-button"
            >
              {lesson.scenario.situation.primaryCta}
            </Button>
          ) : undefined
        ),
        secondaryAction: !hasSituationIntroCompleted ? undefined : !lesson.isAttemptActive ? (
          <ProofLessonSecondaryAction
            onClick={() => lesson.beginFirstAttempt("text")}
          >
            {lesson.scenario.situation.secondaryCta}
          </ProofLessonSecondaryAction>
        ) : lesson.attemptInputMode === "voice" &&
          lesson.voiceInputEnabled &&
          lesson.isVoiceRecording ? (
          <ProofLessonSecondaryAction
            onClick={() => void lesson.stopVoiceRecording()}
          >
            {manualStopLabel}
          </ProofLessonSecondaryAction>
        ) : lesson.attemptInputMode === "voice" && lesson.voiceInputEnabled ? (
          <ProofLessonSecondaryAction
            onClick={() => lesson.beginFirstAttempt("text")}
          >
            {lesson.scenario.firstAttempt.fallbackCta}
          </ProofLessonSecondaryAction>
        ) : lesson.attemptInputMode === "text" && lesson.voiceInputEnabled ? (
          <ProofLessonSecondaryAction
            onClick={() => void lesson.beginVoiceFirstAttempt()}
          >
            {lesson.scenario.situation.primaryCta}
          </ProofLessonSecondaryAction>
        ) : undefined,
        helperText:
          lesson.isAttemptActive &&
          lesson.attemptInputMode === "voice" &&
          lesson.voiceInputEnabled &&
          lesson.isVoiceRecording
            ? autoStopHelperText
            : undefined,
      };
      break;
    case "feedback":
      stepView = {
        eyebrow: copy.feedbackEyebrow,
        title: lesson.feedback.title,
        description: lesson.feedback.isAlreadyNatural
          ? naturalMatchDescription
          : copy.feedbackDescription,
        content: (
          <div className="proof-lesson-stack">
            {buildCoachDock("feedback")}

            {lesson.feedback.isAlreadyNatural ? (
              <ProofLessonSurface tone="accent">
                <ProofLessonSectionLabel accent>
                  {naturalMatchLabel}
                </ProofLessonSectionLabel>
                <div className="proof-lesson-key-text">
                  {lesson.feedback.userVersion}
                </div>
                <p className="proof-lesson-supporting-copy mt-5">
                  {naturalMatchHint}
                </p>
              </ProofLessonSurface>
            ) : (
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
            )}

            <ProofLessonSurface tone="warm">
              <ProofLessonAdviceList items={feedbackAdviceItems} />
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
            {buildCoachDock("clarity", {
              message: clarityCoachMessage,
              replayCta: clarityCoachReplayCta,
              autoplaySegments: [
                {
                  source: "preset",
                  locale: locale === "ru" ? "ru" : "en",
                  kind: "clarity_intro",
                  revision: WELCOME_TUTOR_CLARITY_PRESET_REVISION,
                },
                {
                  source: "preset",
                  locale: locale === "ru" ? "ru" : "en",
                  kind: "clarity_model",
                  revision: WELCOME_TUTOR_CLARITY_PRESET_REVISION,
                },
              ],
              replaySegments: [
                {
                  source: "preset",
                  locale: locale === "ru" ? "ru" : "en",
                  kind: "clarity_model",
                  revision: WELCOME_TUTOR_CLARITY_PRESET_REVISION,
                },
              ],
              speakingLabelOverride: clarityCoachSpeakingLabel,
            })}

            <ProofLessonSurface tone="accent" className="max-w-[24rem]">
              <div className="proof-lesson-key-text">
                {lesson.clarityStatusLabel}
              </div>
            </ProofLessonSurface>

            <ProofLessonSurface>
              <ProofLessonSectionLabel>
                {lesson.scenario.clarity.hintsTitle}
              </ProofLessonSectionLabel>
              <div className="mt-4">
                <ProofLessonAdviceList items={lesson.clarityHints} />
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
          ) : lesson.retryInputMode === "voice" &&
            lesson.voiceInputEnabled &&
            !lesson.isVoiceRecording &&
            !lesson.isVoiceProcessing ? (
            <Button
              type="button"
              onClick={() => void lesson.startVoiceRecording("retry")}
              className="proof-lesson-primary-button"
            >
              {lesson.scenario.retry.voiceStartCta}
            </Button>
          ) : undefined,
        secondaryAction:
          lesson.retryInputMode === null ? (
            <ProofLessonSecondaryAction
              onClick={() => lesson.beginRetry("text")}
            >
              {lesson.scenario.retry.secondaryCta}
            </ProofLessonSecondaryAction>
          ) : lesson.retryInputMode === "voice" &&
            lesson.voiceInputEnabled &&
            lesson.isVoiceRecording ? (
            <ProofLessonSecondaryAction
              onClick={() => void lesson.stopVoiceRecording()}
            >
              {manualStopLabel}
            </ProofLessonSecondaryAction>
          ) : lesson.retryInputMode === "voice" && lesson.voiceInputEnabled ? (
            <ProofLessonSecondaryAction
              onClick={() => lesson.beginRetry("text")}
            >
              {lesson.scenario.retry.fallbackCta}
            </ProofLessonSecondaryAction>
          ) : undefined,
        helperText:
          lesson.retryInputMode === "voice" &&
          lesson.voiceInputEnabled &&
          lesson.isVoiceRecording
            ? autoStopHelperText
            : undefined,
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
            {buildCoachDock("result", {
              message: resultCoachMessage,
            })}

            <ProofLessonAdviceList items={lesson.scenario.result.points} />

            <ProofLessonSurface>
              <div className="grid gap-5 md:grid-cols-2">
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
                  <p className="proof-lesson-supporting-copy mt-3">
                    {lesson.scenario.result.comment}
                  </p>
                </div>
              </div>
            </ProofLessonSurface>

            <ProofLessonSurface tone="warm">
              <ProofLessonSectionLabel accent>
                {resultJourneyTitle}
              </ProofLessonSectionLabel>
              <div className="mt-4">
                <ProofLessonAdviceList items={resultJourneySteps} />
              </div>
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
      isVisible={isVisible}
      currentStep={progressCurrentStep}
      totalSteps={progressTotalSteps}
      progressLabel={progressLabel}
      showProgress={showsProgress}
      stepKey={`${lesson.scenario.id}-${lesson.currentStep}`}
      eyebrow={stepView.eyebrow}
      title={stepView.title}
      description={stepView.description}
      content={stepView.content}
      contentClassName={stepView.contentClassName}
      cardClassName={stepView.cardClassName}
      stepClassName={stepView.stepClassName}
      primaryAction={stepView.primaryAction}
      secondaryAction={stepView.secondaryAction}
      helperText={stepView.helperText}
    />
  );
}
