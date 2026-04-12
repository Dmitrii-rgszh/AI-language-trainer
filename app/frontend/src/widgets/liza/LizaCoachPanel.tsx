import { useEffect, useRef, useState, type ReactNode } from "react";
import { apiClient } from "../../shared/api/client";
import type { AppLocale } from "../../shared/i18n/locale";
import avatarGirlSrc from "../../shared/assets/ai-tutor/avatar-girl.webp";
import { cn } from "../../shared/utils/cn";
import { TutorCard } from "../../features/welcome/TutorCard";

type LizaCoachRenderedSegment = {
  text: string;
  language: "ru" | "en";
};

type LizaCoachPresetSegment = {
  source: "preset";
  locale: "ru" | "en";
  kind: "intro" | "replay" | "clarity_intro" | "clarity_model";
  variant?: number;
  revision?: string;
};

export type LizaCoachPlaybackSegment =
  | LizaCoachRenderedSegment
  | LizaCoachPresetSegment;

type LizaCoachPanelProps = {
  isVisible?: boolean;
  locale: AppLocale;
  playKey: string;
  title?: string;
  message: string;
  spokenMessage?: string;
  spokenLanguage?: "ru" | "en";
  replayCta: string;
  primaryAction?: ReactNode;
  secondaryAction?: ReactNode;
  supportingText?: string;
  autoplaySegments?: LizaCoachPlaybackSegment[];
  replaySegments?: LizaCoachPlaybackSegment[];
  idleLabelOverride?: string;
  speakingLabelOverride?: string;
  allowAudioFallback?: boolean;
};

const LIZA_PANEL_PRESENCE_VIDEO_REVISION = "presence-01-v2-forced";

function isPresetSegment(
  segment: LizaCoachPlaybackSegment,
): segment is LizaCoachPresetSegment {
  return "source" in segment && segment.source === "preset";
}

function getPlaybackLabels(locale: AppLocale) {
  if (locale === "ru") {
    return {
      autoplayHint: "Если звук не стартовал автоматически, нажми «Послушать ещё раз».",
      idle: "Лиза рядом",
      loading: "Лиза готовит подсказку",
      speaking: "Лиза помогает с планом",
    };
  }

  return {
    autoplayHint: "If audio did not start automatically, press “Hear it again”.",
    idle: "Liza is here",
    loading: "Liza is preparing the guidance",
    speaking: "Liza is guiding your next step",
  };
}

export function LizaCoachPanel({
  isVisible = true,
  locale,
  playKey,
  title,
  message,
  spokenMessage,
  spokenLanguage,
  replayCta,
  primaryAction,
  secondaryAction,
  supportingText,
  autoplaySegments,
  replaySegments,
  idleLabelOverride,
  speakingLabelOverride,
  allowAudioFallback = true,
}: LizaCoachPanelProps) {
  const [isVideoVisible, setIsVideoVisible] = useState(false);
  const [isClipVisible, setIsClipVisible] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [playbackHint, setPlaybackHint] = useState<string | null>(null);
  const presenceVideoRef = useRef<HTMLVideoElement | null>(null);
  const clipVideoRef = useRef<HTMLVideoElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const clipObjectUrlRef = useRef<string | null>(null);
  const playedKeyRef = useRef<string | null>(null);
  const avatarAlt = locale === "ru" ? "Лиза" : "Liza";
  const labels = getPlaybackLabels(locale);
  const resolvedSpokenLanguage = spokenLanguage ?? (locale === "ru" ? "ru" : "en");
  const resolvedSpokenMessage = spokenMessage?.trim() || message;
  const resolvedAutoplaySegments =
    autoplaySegments?.filter((segment) =>
      isPresetSegment(segment) ? true : segment.text.trim().length > 0,
    ) ?? [];
  const resolvedReplaySegments =
    replaySegments?.filter((segment) =>
      isPresetSegment(segment) ? true : segment.text.trim().length > 0,
    ) ?? [];
  const idleLabel = idleLabelOverride ?? labels.idle;
  const speakingLabel = speakingLabelOverride ?? labels.speaking;
  const hasExplicitSegments =
    resolvedAutoplaySegments.length > 0 || resolvedReplaySegments.length > 0;
  const presenceVideoUrl = apiClient.getLiveAvatarPresenceVideoUrl(
    "verba_tutor",
    LIZA_PANEL_PRESENCE_VIDEO_REVISION,
  );
  const cacheSignature = [
    "global-liza-coach",
    resolvedSpokenLanguage,
    playKey,
    resolvedSpokenMessage,
    resolvedAutoplaySegments
      .map((segment) =>
        isPresetSegment(segment)
          ? `preset:${segment.locale}:${segment.kind}:${segment.variant ?? 0}:${segment.revision ?? ""}`
          : `${segment.language}:${segment.text}`,
      )
      .join("|"),
    resolvedReplaySegments
      .map((segment) =>
        isPresetSegment(segment)
          ? `preset:${segment.locale}:${segment.kind}:${segment.variant ?? 0}:${segment.revision ?? ""}`
          : `${segment.language}:${segment.text}`,
      )
      .join("|"),
  ].join(":");

  useEffect(() => {
    return () => {
      presenceVideoRef.current?.pause();
      clipVideoRef.current?.pause();
      audioRef.current?.pause();
      if (clipObjectUrlRef.current) {
        URL.revokeObjectURL(clipObjectUrlRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!isVisible) {
      presenceVideoRef.current?.pause();
      clipVideoRef.current?.pause();
      audioRef.current?.pause();
      setIsClipVisible(false);
      setIsPlaying(false);
      setIsLoading(false);
      setPlaybackHint(null);
      return;
    }

    void apiClient
      .preloadLiveAvatarPresenceVideo("verba_tutor", LIZA_PANEL_PRESENCE_VIDEO_REVISION)
      .catch(() => undefined);
    if (!hasExplicitSegments) {
      void apiClient
        .prefetchWelcomeTutorClip({
          text: resolvedSpokenMessage,
          language: resolvedSpokenLanguage,
          avatarKey: "verba_tutor",
          cacheSignature,
        })
        .catch(() => undefined);
    }
    for (const [index, segment] of resolvedAutoplaySegments.entries()) {
      if (isPresetSegment(segment)) {
        void apiClient
          .prefetchWelcomeTutorPresetClip({
            locale: segment.locale,
            kind: segment.kind,
            variant: segment.variant ?? 0,
            revision: segment.revision,
          })
          .catch(() => undefined);
      } else {
        void apiClient
          .prefetchWelcomeTutorClip({
            text: segment.text,
            language: segment.language,
            avatarKey: "verba_tutor",
            cacheSignature: `${cacheSignature}:auto:${index}`,
          })
          .catch(() => undefined);
      }
    }
    for (const [index, segment] of resolvedReplaySegments.entries()) {
      if (isPresetSegment(segment)) {
        void apiClient
          .prefetchWelcomeTutorPresetClip({
            locale: segment.locale,
            kind: segment.kind,
            variant: segment.variant ?? 0,
            revision: segment.revision,
          })
          .catch(() => undefined);
      } else {
        void apiClient
          .prefetchWelcomeTutorClip({
            text: segment.text,
            language: segment.language,
            avatarKey: "verba_tutor",
            cacheSignature: `${cacheSignature}:replay:${index}`,
          })
          .catch(() => undefined);
      }
    }
  }, [
    cacheSignature,
    isVisible,
    hasExplicitSegments,
    resolvedAutoplaySegments,
    resolvedReplaySegments,
    resolvedSpokenLanguage,
    resolvedSpokenMessage,
  ]);

  useEffect(() => {
    const video = presenceVideoRef.current;
    if (!video || !isVisible) {
      return;
    }

    let cancelled = false;

    const showVideo = () => {
      if (cancelled) {
        return;
      }
      setIsVideoVisible(true);
      video.muted = true;
      video.defaultMuted = true;
      video.loop = true;
      video.playsInline = true;
      void video.play().catch(() => undefined);
    };

    const handleError = () => {
      if (!cancelled) {
        setIsVideoVisible(false);
      }
    };

    video.addEventListener("loadeddata", showVideo, { once: true });
    video.addEventListener("canplay", showVideo, { once: true });
    video.addEventListener("playing", showVideo);
    video.addEventListener("error", handleError, { once: true });

    video.load();
    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      showVideo();
    }

    return () => {
      cancelled = true;
      video.removeEventListener("loadeddata", showVideo);
      video.removeEventListener("canplay", showVideo);
      video.removeEventListener("playing", showVideo);
      video.removeEventListener("error", handleError);
    };
  }, [isVisible, presenceVideoUrl]);

  useEffect(() => {
    const clipVideo = clipVideoRef.current;
    if (!clipVideo) {
      return;
    }

    const handlePlaying = () => {
      setIsClipVisible(true);
      setIsPlaying(true);
      setIsLoading(false);
      setPlaybackHint(null);
    };
    const handlePause = () => {
      if (clipVideo.ended || clipVideo.currentTime <= 0) {
        return;
      }
      setIsPlaying(false);
    };
    const handleEnded = () => {
      setIsClipVisible(false);
      setIsPlaying(false);
      setIsLoading(false);
    };
    const handleError = () => {
      setIsClipVisible(false);
      setIsPlaying(false);
      setIsLoading(false);
      setPlaybackHint(labels.autoplayHint);
    };

    clipVideo.addEventListener("playing", handlePlaying);
    clipVideo.addEventListener("pause", handlePause);
    clipVideo.addEventListener("ended", handleEnded);
    clipVideo.addEventListener("error", handleError);

    return () => {
      clipVideo.removeEventListener("playing", handlePlaying);
      clipVideo.removeEventListener("pause", handlePause);
      clipVideo.removeEventListener("ended", handleEnded);
      clipVideo.removeEventListener("error", handleError);
    };
  }, [labels.autoplayHint]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    const handlePlaying = () => {
      setIsPlaying(true);
      setIsLoading(false);
      setPlaybackHint(null);
    };
    const handlePause = () => {
      if (audio.ended || audio.currentTime <= 0) {
        return;
      }
      setIsPlaying(false);
    };
    const handleEnded = () => {
      setIsPlaying(false);
      setIsLoading(false);
    };
    const handleError = () => {
      setIsPlaying(false);
      setIsLoading(false);
      setPlaybackHint(labels.autoplayHint);
    };

    audio.addEventListener("playing", handlePlaying);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    return () => {
      audio.removeEventListener("playing", handlePlaying);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
    };
  }, [labels.autoplayHint]);

  async function playAudioFallback() {
    const audio = audioRef.current;
    if (!audio) {
      return false;
    }

    try {
      const audioBlob = await apiClient.synthesizeSpeech({
        text: resolvedSpokenMessage,
        language: resolvedSpokenLanguage,
        speaker: "Daisy Studious",
        style: "warm",
      });
      const audioUrl = URL.createObjectURL(audioBlob);
      if (clipObjectUrlRef.current) {
        URL.revokeObjectURL(clipObjectUrlRef.current);
      }
      clipObjectUrlRef.current = audioUrl;
      audio.pause();
      audio.src = audioUrl;
      audio.currentTime = 0;
      audio.load();
      await audio.play();
      return true;
    } catch {
      setPlaybackHint(labels.autoplayHint);
      setIsClipVisible(false);
      setIsPlaying(false);
      setIsLoading(false);
      return false;
    }
  }

  async function playRenderedSegment(
    segment: LizaCoachRenderedSegment,
    nextCacheSignature: string,
  ) {
    const clipVideo = clipVideoRef.current;
    if (!clipVideo) {
      return false;
    }

    try {
      const clipBlob = await apiClient.renderWelcomeTutorClip({
        text: segment.text,
        language: segment.language,
        avatarKey: "verba_tutor",
        cacheSignature: nextCacheSignature,
      });
      const clipUrl = URL.createObjectURL(clipBlob);
      if (clipObjectUrlRef.current) {
        URL.revokeObjectURL(clipObjectUrlRef.current);
      }
      clipObjectUrlRef.current = clipUrl;

      clipVideo.pause();
      setIsClipVisible(false);
      clipVideo.muted = false;
      clipVideo.defaultMuted = false;
      clipVideo.src = clipUrl;
      clipVideo.currentTime = 0;
      clipVideo.load();
      await clipVideo.play();
      await new Promise<void>((resolve, reject) => {
        const handleEnded = () => {
          cleanup();
          resolve();
        };
        const handleError = () => {
          cleanup();
          reject(new Error("clip-playback-error"));
        };
        const cleanup = () => {
          clipVideo.removeEventListener("ended", handleEnded);
          clipVideo.removeEventListener("error", handleError);
        };

        clipVideo.addEventListener("ended", handleEnded, { once: true });
        clipVideo.addEventListener("error", handleError, { once: true });
      });
      return true;
    } catch {
      setIsClipVisible(false);
      return false;
    }
  }

  async function playPresetSegment(segment: LizaCoachPresetSegment) {
    const clipVideo = clipVideoRef.current;
    if (!clipVideo) {
      return false;
    }

    try {
      const clipBlob = await apiClient.getWelcomeTutorPresetClip({
        locale: segment.locale,
        kind: segment.kind,
        variant: segment.variant ?? 0,
        revision: segment.revision,
      });
      const clipUrl = URL.createObjectURL(clipBlob);
      if (clipObjectUrlRef.current) {
        URL.revokeObjectURL(clipObjectUrlRef.current);
      }
      clipObjectUrlRef.current = clipUrl;

      clipVideo.pause();
      setIsClipVisible(false);
      clipVideo.muted = false;
      clipVideo.defaultMuted = false;
      clipVideo.src = clipUrl;
      clipVideo.currentTime = 0;
      clipVideo.load();
      await clipVideo.play();
      await new Promise<void>((resolve, reject) => {
        const handleEnded = () => {
          cleanup();
          resolve();
        };
        const handleError = () => {
          cleanup();
          reject(new Error("preset-playback-error"));
        };
        const cleanup = () => {
          clipVideo.removeEventListener("ended", handleEnded);
          clipVideo.removeEventListener("error", handleError);
        };

        clipVideo.addEventListener("ended", handleEnded, { once: true });
        clipVideo.addEventListener("error", handleError, { once: true });
      });
      return true;
    } catch {
      setIsClipVisible(false);
      return false;
    }
  }

  async function playCue(mode: "auto" | "replay" = "auto") {
    const clipVideo = clipVideoRef.current;
    setPlaybackHint(null);
    setIsPlaying(false);
    setIsLoading(true);

    const selectedSegments =
      mode === "replay" && resolvedReplaySegments.length > 0
        ? resolvedReplaySegments
        : resolvedAutoplaySegments;

    if (selectedSegments.length > 0) {
      for (const [index, segment] of selectedSegments.entries()) {
        const success = isPresetSegment(segment)
          ? await playPresetSegment(segment)
          : await playRenderedSegment(segment, `${cacheSignature}:${mode}:${index}`);
        if (!success) {
          setPlaybackHint(labels.autoplayHint);
          setIsLoading(false);
          return allowAudioFallback ? playAudioFallback() : false;
        }
      }
      setIsLoading(false);
      return true;
    }

    if (!clipVideo) {
      return allowAudioFallback ? playAudioFallback() : false;
    }

    const success = await playRenderedSegment(
      {
        text: resolvedSpokenMessage,
        language: resolvedSpokenLanguage,
      },
      cacheSignature,
    );
    if (!success) {
      setPlaybackHint(labels.autoplayHint);
      setIsLoading(false);
      return allowAudioFallback ? playAudioFallback() : false;
    }
    return true;
  }

  useEffect(() => {
    if (!isVisible) {
      return;
    }
    if (playedKeyRef.current === playKey) {
      return;
    }

    playedKeyRef.current = playKey;
    void playCue("auto");
  }, [isVisible, playKey]);

  return (
    <div className="liza-coach-panel">
      {title ? <div className="liza-coach-panel__eyebrow">{title}</div> : null}
      <TutorCard
        label={avatarAlt}
        message={message}
        replayAction={(
          <button
            type="button"
            onClick={() => void playCue("replay")}
            className="proof-lesson-ai-cue__replay"
          >
            {replayCta}
          </button>
        )}
        status={(
          <div className="proof-lesson-ai-cue__status">
            <span
              className={cn(
                "proof-lesson-ai-cue__status-dot",
                (isPlaying || isLoading) && "proof-lesson-ai-cue__status-dot--live",
              )}
              aria-hidden="true"
            />
            <span>{isPlaying ? speakingLabel : isLoading ? labels.loading : idleLabel}</span>
          </div>
        )}
        hint={playbackHint}
        isSpeaking={isPlaying}
        className="proof-lesson-tutor-card--dock liza-coach-panel__card"
        messageClassName="proof-lesson-tutor-card__utterance--dock liza-coach-panel__message"
        avatarStageClassName="proof-lesson-tutor-card__avatar-stage--dock liza-coach-panel__avatar-stage"
        avatarStage={(
          <div
            className={cn(
              "proof-lesson-ai-avatar proof-lesson-ai-avatar--dock",
              "liza-coach-panel__avatar",
              isVideoVisible && "proof-lesson-ai-avatar--alive",
              isClipVisible && "proof-lesson-ai-avatar--video",
              isPlaying && "proof-lesson-ai-avatar--speaking",
            )}
          >
            <img
              src={avatarGirlSrc}
              alt={avatarAlt}
              className={cn(
                "proof-lesson-ai-avatar__image",
                isVideoVisible && "is-hidden",
              )}
              draggable={false}
              decoding="async"
            />
            <video
              ref={presenceVideoRef}
              src={presenceVideoUrl}
              autoPlay
              loop
              playsInline
              preload="auto"
              muted
              className={cn(
                "proof-lesson-ai-avatar__idle",
                isVideoVisible && "is-visible",
                isClipVisible && "is-covered",
              )}
            />
            <video
              ref={clipVideoRef}
              playsInline
              preload="auto"
              crossOrigin="anonymous"
              className={cn(
                "proof-lesson-ai-avatar__video",
                isClipVisible && "is-visible",
              )}
            />
            <div className="proof-lesson-ai-avatar__ambient-ring" aria-hidden="true" />
          </div>
        )}
      />
      {primaryAction || secondaryAction ? (
        <div className="liza-coach-panel__actions">
          {primaryAction ? <div className="liza-coach-panel__primary-action">{primaryAction}</div> : null}
          {secondaryAction ? <div className="liza-coach-panel__secondary-action">{secondaryAction}</div> : null}
        </div>
      ) : null}
      {supportingText ? (
        <div className="liza-coach-panel__supporting-text">{supportingText}</div>
      ) : null}
      <audio ref={audioRef} preload="auto" className="sr-only" />
    </div>
  );
}
