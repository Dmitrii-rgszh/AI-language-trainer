import { useEffect, useRef, useState } from "react";
import type { AppLocale } from "../../shared/i18n/locale";
import { apiClient } from "../../shared/api/client";
import avatarGirlSrc from "../../shared/assets/ai-tutor/avatar-girl.webp";
import { cn } from "../../shared/utils/cn";
import { TutorCard } from "./TutorCard";
import type { WelcomeProofLessonCoachCue } from "./welcomeAiTutorPrompts";

type WelcomeProofLessonCoachDockProps = {
  isVisible: boolean;
  locale: AppLocale;
  cue: WelcomeProofLessonCoachCue;
  message: string;
  replayCta: string;
  playKey: string;
};

const WELCOME_PRESENCE_VIDEO_REVISION = "presence-01-v2-forced";

function getPlaybackLabels(locale: AppLocale) {
  if (locale === "ru") {
    return {
      autoplayHint: "Если звук не стартовал автоматически, нажми «Послушать ещё раз».",
      idle: "Лиза рядом",
      speaking: "Лиза коротко объясняет",
    };
  }

  return {
    autoplayHint: "If audio did not start automatically, press “Hear it again”.",
    idle: "Liza is here",
    speaking: "Liza is guiding you",
  };
}

export function WelcomeProofLessonCoachDock({
  isVisible,
  locale,
  cue,
  message,
  replayCta,
  playKey,
}: WelcomeProofLessonCoachDockProps) {
  const [isVideoVisible, setIsVideoVisible] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackHint, setPlaybackHint] = useState<string | null>(null);
  const presenceVideoRef = useRef<HTMLVideoElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playedKeyRef = useRef<string | null>(null);
  const avatarAlt = locale === "ru" ? "Лиза" : "Liza";
  const labels = getPlaybackLabels(locale);
  const normalizedLocale = locale === "ru" ? "ru" : "en";
  const presenceVideoUrl = apiClient.getLiveAvatarPresenceVideoUrl(
    "verba_tutor",
    WELCOME_PRESENCE_VIDEO_REVISION,
  );
  const cueAudioUrl = apiClient.getWelcomeProofLessonCueAudioUrl(normalizedLocale, cue);

  useEffect(() => {
    return () => {
      presenceVideoRef.current?.pause();
      audioRef.current?.pause();
    };
  }, []);

  useEffect(() => {
    if (!isVisible) {
      presenceVideoRef.current?.pause();
      audioRef.current?.pause();
      setIsPlaying(false);
      setPlaybackHint(null);
      return;
    }

    void apiClient
      .preloadLiveAvatarPresenceVideo("verba_tutor", WELCOME_PRESENCE_VIDEO_REVISION)
      .catch(() => undefined);
    void apiClient
      .preloadWelcomeProofLessonCueAudio(normalizedLocale, cue)
      .catch(() => undefined);
  }, [cue, isVisible, normalizedLocale]);

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
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    const handlePlaying = () => {
      setIsPlaying(true);
      setPlaybackHint(null);
    };
    const handlePause = () => {
      if (!audio.ended && audio.currentTime > 0) {
        setIsPlaying(false);
      }
    };
    const handleEnded = () => {
      setIsPlaying(false);
    };
    const handleError = () => {
      setIsPlaying(false);
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

  async function playCue() {
    const audio = audioRef.current;
    if (!audio) {
      return false;
    }

    setPlaybackHint(null);
    setIsPlaying(false);
    audio.pause();
    if (audio.src !== cueAudioUrl) {
      audio.src = cueAudioUrl;
    }
    audio.currentTime = 0;
    audio.load();

    try {
      await audio.play();
      return true;
    } catch {
      setPlaybackHint(labels.autoplayHint);
      setIsPlaying(false);
      return false;
    }
  }

  useEffect(() => {
    if (!isVisible) {
      return;
    }
    if (playedKeyRef.current === playKey) {
      return;
    }

    playedKeyRef.current = playKey;
    void playCue();
  }, [cueAudioUrl, isVisible, playKey]);

  return (
    <div className="proof-lesson-coach-dock-row">
      <div className="proof-lesson-ai-cue proof-lesson-ai-cue--dock">
        <TutorCard
          label={avatarAlt}
          message={message}
          replayAction={(
            <button
              type="button"
              onClick={() => void playCue()}
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
                  isPlaying && "proof-lesson-ai-cue__status-dot--live",
                )}
                aria-hidden="true"
              />
              <span>{isPlaying ? labels.speaking : labels.idle}</span>
            </div>
          )}
          hint={playbackHint}
          isSpeaking={isPlaying}
          className="proof-lesson-tutor-card--dock"
          messageClassName="proof-lesson-tutor-card__utterance--dock"
          avatarStageClassName="proof-lesson-tutor-card__avatar-stage--dock"
          avatarStage={(
            <div
              className={cn(
                "proof-lesson-ai-avatar proof-lesson-ai-avatar--dock",
                isVideoVisible && "proof-lesson-ai-avatar--alive",
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
                )}
              />
              <div className="proof-lesson-ai-avatar__ambient-ring" aria-hidden="true" />
            </div>
          )}
        />
        <audio ref={audioRef} preload="auto" className="sr-only" />
      </div>
    </div>
  );
}
