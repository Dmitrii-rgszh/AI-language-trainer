import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import type { AppLocale } from "../../shared/i18n/locale";
import { apiClient } from "../../shared/api/client";
import avatarGirlSrc from "../../shared/assets/ai-tutor/avatar-girl.webp";
import { cn } from "../../shared/utils/cn";
import { TutorCard } from "./TutorCard";
import {
  getWelcomeAiTutorIntroVariants,
  getWelcomeAiTutorReplayPrompt,
} from "./welcomeAiTutorPrompts";

type WelcomeAiTutorCueProps = {
  isVisible: boolean;
  locale: AppLocale;
  label: string;
  message: string;
  spokenMessage?: string;
  replayCta: string;
  showReplayAction?: boolean;
  showStaticFallback?: boolean;
  onIntroPlaybackStart?: () => void;
  onIntroPlaybackComplete?: () => void;
};

export type WelcomeAiTutorCueHandle = {
  playIntro: () => Promise<boolean>;
  playReplay: () => Promise<boolean>;
};

const WELCOME_PRESENCE_VIDEO_REVISION = "presence-master-01-v2-generated";
const INTRO_VARIANT_STORAGE_KEY = "welcome-ai-tutor-intro-variant";

function getPlaybackLabels(locale: AppLocale) {
  if (locale === "ru") {
    return {
      autoplayHint: "Если звук не стартовал автоматически, нажми «Повторить ещё раз».",
      playing: "Лиза озвучивает задание",
    };
  }

  return {
    autoplayHint: "If audio did not start automatically, press “Hear it again”.",
    playing: "Liza is saying the prompt",
  };
}

function getNextIntroVariantIndex(variantCount: number) {
  try {
    const currentValue = Number(window.sessionStorage.getItem(INTRO_VARIANT_STORAGE_KEY) || "0");
    const normalizedCurrent = Number.isFinite(currentValue) ? currentValue : 0;
    const nextValue = (normalizedCurrent + 1) % variantCount;
    window.sessionStorage.setItem(INTRO_VARIANT_STORAGE_KEY, String(nextValue));
    return normalizedCurrent % variantCount;
  } catch {
    return 0;
  }
}

export const WelcomeAiTutorCue = forwardRef<WelcomeAiTutorCueHandle, WelcomeAiTutorCueProps>(function WelcomeAiTutorCue({
  isVisible,
  locale,
  label,
  message,
  replayCta,
  showReplayAction = true,
  showStaticFallback = true,
  onIntroPlaybackStart,
  onIntroPlaybackComplete,
}: WelcomeAiTutorCueProps, ref) {
  const [isVideoVisible, setIsVideoVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isClipVisible, setIsClipVisible] = useState(false);
  const [playbackHint, setPlaybackHint] = useState<string | null>(null);
  const presenceVideoRef = useRef<HTMLVideoElement | null>(null);
  const clipVideoRef = useRef<HTMLVideoElement | null>(null);
  const introClipUrlRef = useRef<string | null>(null);
  const replayClipUrlRef = useRef<string | null>(null);
  const activePlaybackModeRef = useRef<"intro" | "replay" | null>(null);
  const selectedIntroIndexRef = useRef(0);
  const introClipPreloadPromiseRef = useRef<Promise<string | null> | null>(null);
  const replayClipPreloadPromiseRef = useRef<Promise<string | null> | null>(null);
  const avatarAlt = locale === "ru" ? "Лиза" : "Liza";
  const labels = getPlaybackLabels(locale);
  const replayPrompt = getWelcomeAiTutorReplayPrompt(locale);
  const introVariants = useMemo(
    () => getWelcomeAiTutorIntroVariants(locale),
    [locale],
  );
  const presenceVideoUrl = apiClient.getLiveAvatarPresenceVideoUrl(
    "verba_tutor",
    WELCOME_PRESENCE_VIDEO_REVISION,
  );

  useEffect(() => {
    return () => {
      presenceVideoRef.current?.pause();
      clipVideoRef.current?.pause();
      if (introClipUrlRef.current) {
        URL.revokeObjectURL(introClipUrlRef.current);
        introClipUrlRef.current = null;
      }
      if (replayClipUrlRef.current) {
        URL.revokeObjectURL(replayClipUrlRef.current);
        replayClipUrlRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!isVisible) {
      presenceVideoRef.current?.pause();
      clipVideoRef.current?.pause();
      setIsVideoVisible(false);
      setIsClipVisible(false);
      setIsPlaying(false);
      setIsLoading(false);
      setPlaybackHint(null);
      activePlaybackModeRef.current = null;
      return;
    }

    selectedIntroIndexRef.current = getNextIntroVariantIndex(introVariants.length);
    if (introClipUrlRef.current) {
      URL.revokeObjectURL(introClipUrlRef.current);
      introClipUrlRef.current = null;
    }
    introClipPreloadPromiseRef.current = null;
    void apiClient
      .preloadLiveAvatarPresenceVideo("verba_tutor", WELCOME_PRESENCE_VIDEO_REVISION)
      .catch(() => undefined);
    void preloadReplayClip().catch(() => undefined);
    void preloadSelectedIntroClip().catch(() => undefined);
  }, [introVariants.length, isVisible]);

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

    const watchdog = window.setInterval(() => {
      if (!cancelled && video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA && video.paused) {
        void video.play().catch(() => undefined);
      }
    }, 500);

    return () => {
      cancelled = true;
      window.clearInterval(watchdog);
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
      if (activePlaybackModeRef.current === "intro") {
        onIntroPlaybackStart?.();
      }
    };

    const handleEnded = () => {
      setIsClipVisible(false);
      setIsPlaying(false);
      setIsLoading(false);
      if (activePlaybackModeRef.current === "intro") {
        onIntroPlaybackComplete?.();
      }
      activePlaybackModeRef.current = null;
    };

    const handlePause = () => {
      if (clipVideo.ended || clipVideo.currentTime <= 0) {
        return;
      }
      setIsPlaying(false);
    };

    const handleError = () => {
      setIsClipVisible(false);
      setIsPlaying(false);
      setIsLoading(false);
      setPlaybackHint(labels.autoplayHint);
      activePlaybackModeRef.current = null;
    };

    clipVideo.addEventListener("playing", handlePlaying);
    clipVideo.addEventListener("ended", handleEnded);
    clipVideo.addEventListener("pause", handlePause);
    clipVideo.addEventListener("error", handleError);

    return () => {
      clipVideo.removeEventListener("playing", handlePlaying);
      clipVideo.removeEventListener("ended", handleEnded);
      clipVideo.removeEventListener("pause", handlePause);
      clipVideo.removeEventListener("error", handleError);
    };
  }, [labels.autoplayHint]);

  useImperativeHandle(ref, () => ({
    playIntro: () => playPrompt("intro"),
    playReplay: () => playPrompt("replay"),
  }));

  async function preloadSelectedIntroClip() {
    if (introClipUrlRef.current) {
      return introClipUrlRef.current;
    }

    if (!introClipPreloadPromiseRef.current) {
      const selectedVariant = introVariants[selectedIntroIndexRef.current] ? selectedIntroIndexRef.current : 0;
      introClipPreloadPromiseRef.current = apiClient
        .getWelcomeTutorPresetClip({
          locale: locale === "ru" ? "ru" : "en",
          kind: "intro",
          variant: selectedVariant,
        })
        .then((blob) => {
          const nextUrl = URL.createObjectURL(blob);
          introClipUrlRef.current = nextUrl;
          return nextUrl;
        });
    }

    return introClipPreloadPromiseRef.current;
  }

  async function preloadReplayClip() {
    if (replayClipUrlRef.current) {
      return replayClipUrlRef.current;
    }

    if (!replayClipPreloadPromiseRef.current) {
      replayClipPreloadPromiseRef.current = apiClient
        .getWelcomeTutorPresetClip({
          locale: locale === "ru" ? "ru" : "en",
          kind: "replay",
          variant: 0,
        })
        .then((blob) => {
          const nextUrl = URL.createObjectURL(blob);
          replayClipUrlRef.current = nextUrl;
          return nextUrl;
        });
    }

    return replayClipPreloadPromiseRef.current;
  }

  async function playPrompt(mode: "intro" | "replay"): Promise<boolean> {
    const clipVideo = clipVideoRef.current;
    if (!clipVideo) {
      return false;
    }

    setPlaybackHint(null);
    setIsLoading(true);
    setIsPlaying(false);
    activePlaybackModeRef.current = mode;

    try {
      const nextUrl =
        mode === "intro"
          ? await preloadSelectedIntroClip()
          : await preloadReplayClip();

      if (!nextUrl) {
        setPlaybackHint(labels.autoplayHint);
        activePlaybackModeRef.current = null;
        return false;
      }

      clipVideo.pause();
      setIsClipVisible(false);
      clipVideo.muted = false;
      clipVideo.defaultMuted = false;
      if (clipVideo.src !== nextUrl) {
        clipVideo.src = nextUrl;
      }
      clipVideo.currentTime = 0;
      clipVideo.load();
      await clipVideo.play();
      return true;
    } catch {
      setPlaybackHint(labels.autoplayHint);
      setIsClipVisible(false);
      setIsPlaying(false);
      setIsLoading(false);
      activePlaybackModeRef.current = null;
      return false;
    }
  }

  return (
    <div className="proof-lesson-ai-cue">
      <TutorCard
        label={label}
        message={message}
        replayAction={showReplayAction ? (
          <button
            type="button"
            onClick={() => void playPrompt("replay")}
            className="proof-lesson-ai-cue__replay"
          >
            {replayCta}
          </button>
        ) : undefined}
        status={
          isPlaying ? (
            <div className="proof-lesson-ai-cue__status">
              <span
                className={cn(
                  "proof-lesson-ai-cue__status-dot",
                  isPlaying && "proof-lesson-ai-cue__status-dot--live",
                )}
                aria-hidden="true"
              />
              <span>{labels.playing}</span>
            </div>
          ) : null
        }
        hint={playbackHint}
        isSpeaking={isPlaying}
        avatarStage={
          <div
            className={cn(
              "proof-lesson-ai-avatar",
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
                (!showStaticFallback || isVideoVisible) && "is-hidden",
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
              className={cn("proof-lesson-ai-avatar__video", isClipVisible && "is-visible")}
            />
            <div className="proof-lesson-ai-avatar__ambient-ring" aria-hidden="true" />
          </div>
        }
      />
    </div>
  );
});
