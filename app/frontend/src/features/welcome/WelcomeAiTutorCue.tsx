import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import type { AppLocale } from "../../shared/i18n/locale";
import { ApiError, apiClient } from "../../shared/api/client";
import { useAppStore } from "../../shared/store/app-store";
import avatarGirlSrc from "../../shared/assets/ai-tutor/avatar-girl.webp";
import { cn } from "../../shared/utils/cn";
import { TutorCard } from "./TutorCard";

type WelcomeAiTutorCueProps = {
  isVisible: boolean;
  locale: AppLocale;
  label: string;
  message: string;
  spokenMessage?: string;
  replayCta: string;
};

const AI_TUTOR_SPEAKER = "Daisy Studious";
const WELCOME_TUTOR_VIDEO_WAIT_MS = 12000;
const WELCOME_TUTOR_REPLAY_VIDEO_WAIT_MS = 18000;

function getPlaybackLabels(locale: AppLocale) {
  if (locale === "ru") {
    return {
      autoplayHint: "Если звук не стартовал автоматически, нажми «Послушать ещё раз».",
      loading: "Лиза готовит задание...",
      warming: "Первый запуск прогревает видео-аватар. Это может занять несколько секунд.",
      playing: "Лиза озвучивает задание",
    };
  }

  return {
    autoplayHint: "If audio did not start automatically, press “Hear it again”.",
    loading: "Liza is preparing the prompt...",
    warming: "The first launch is warming up the avatar video. This can take a few seconds.",
    playing: "Liza is saying the prompt",
  };
}

export function WelcomeAiTutorCue({
  isVisible,
  locale,
  label,
  message,
  spokenMessage,
  replayCta,
}: WelcomeAiTutorCueProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackHint, setPlaybackHint] = useState<string | null>(null);
  const [renderMode, setRenderMode] = useState<"video" | "audio">("audio");
  const [videoPlaybackKey, setVideoPlaybackKey] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const currentAudioUrlRef = useRef<string | null>(null);
  const currentVideoUrlRef = useRef<string | null>(null);
  const preparedAudioKeyRef = useRef<string | null>(null);
  const preparedAudioPromiseRef = useRef<Promise<string> | null>(null);
  const preparedVideoBlobRef = useRef<Blob | null>(null);
  const preparedVideoKeyRef = useRef<string | null>(null);
  const preparedVideoPromiseRef = useRef<Promise<Blob> | null>(null);
  const autoPlayKeyRef = useRef<string | null>(null);
  const playbackRequestRef = useRef(0);
  const labels = getPlaybackLabels(locale);
  const avatarAlt = locale === "ru" ? "Лиза" : "Liza";
  const livePrompt = (spokenMessage || message).trim();
  const providers = useAppStore((state) => state.providers);
  const ttsProvider = providers.find((provider) => provider.type === "tts");
  const ttsCacheSignature = ttsProvider
    ? `${ttsProvider.key}|${ttsProvider.details}`
    : "tts-provider-pending";

  function stopCurrentPlayback() {
    audioRef.current?.pause();
    videoRef.current?.pause();
    setIsPlaying(false);
  }

  useEffect(() => {
    return () => {
      stopCurrentPlayback();
      audioRef.current = null;
      videoRef.current = null;

      if (currentAudioUrlRef.current) {
        URL.revokeObjectURL(currentAudioUrlRef.current);
      }
      if (currentVideoUrlRef.current) {
        URL.revokeObjectURL(currentVideoUrlRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (isVisible) {
      void ensureAudioSource().catch(() => undefined);
      void ensureVideoSource().catch(() => undefined);
      return;
    }

    stopCurrentPlayback();
    setIsLoading(false);
    setPlaybackHint(null);
  }, [isVisible]);

  useEffect(() => {
    if (!isVisible) {
      return;
    }

    const autoPlayKey = `${locale}:${livePrompt}:${ttsCacheSignature}`;
    if (autoPlayKeyRef.current === autoPlayKey) {
      return;
    }

    autoPlayKeyRef.current = autoPlayKey;
    void playTutorCue("auto");
  }, [isVisible, locale, livePrompt, ttsCacheSignature]);

  function ensureAudioElement() {
    if (audioRef.current) {
      return audioRef.current;
    }

    const audio = new Audio();
    audio.preload = "auto";
    audio.onended = () => setIsPlaying(false);
    audio.onpause = () => setIsPlaying(false);
    audioRef.current = audio;
    return audio;
  }

  function buildVideoSourceKey() {
    return `${locale}:${livePrompt}:${ttsCacheSignature}`;
  }

  async function ensureAudioSource() {
    const sourceKey = buildVideoSourceKey();
    if (preparedAudioKeyRef.current === sourceKey && currentAudioUrlRef.current) {
      return currentAudioUrlRef.current;
    }

    if (preparedAudioKeyRef.current === sourceKey && preparedAudioPromiseRef.current) {
      return preparedAudioPromiseRef.current;
    }

    if (currentAudioUrlRef.current) {
      URL.revokeObjectURL(currentAudioUrlRef.current);
      currentAudioUrlRef.current = null;
    }

    preparedAudioKeyRef.current = sourceKey;
    preparedAudioPromiseRef.current = apiClient
      .synthesizeSpeech({
        text: livePrompt,
        language: locale === "ru" ? "ru" : "en",
        speaker: AI_TUTOR_SPEAKER,
        style: "warm",
      })
      .then((audioBlob) => {
        const audioUrl = URL.createObjectURL(audioBlob);
        currentAudioUrlRef.current = audioUrl;
        return audioUrl;
      })
      .finally(() => {
        preparedAudioPromiseRef.current = null;
      });

    return preparedAudioPromiseRef.current;
  }

  async function ensureVideoSource() {
    const sourceKey = buildVideoSourceKey();
    if (preparedVideoKeyRef.current === sourceKey && preparedVideoBlobRef.current) {
      return preparedVideoBlobRef.current;
    }

    if (preparedVideoKeyRef.current === sourceKey && preparedVideoPromiseRef.current) {
      return preparedVideoPromiseRef.current;
    }

    preparedVideoBlobRef.current = null;

    preparedVideoKeyRef.current = sourceKey;
    preparedVideoPromiseRef.current = apiClient
      .renderWelcomeTutorClip({
        text: livePrompt,
        language: locale === "ru" ? "ru" : "en",
        avatarKey: "verba_tutor",
        cacheSignature: ttsCacheSignature,
      })
      .then((videoBlob) => {
        preparedVideoBlobRef.current = videoBlob;
        return videoBlob;
      })
      .finally(() => {
        preparedVideoPromiseRef.current = null;
      });

    return preparedVideoPromiseRef.current;
  }

  function isCurrentPlaybackRequest(requestId: number) {
    return playbackRequestRef.current === requestId;
  }

  function hasPreparedVideoSource() {
    return (
      preparedVideoKeyRef.current === buildVideoSourceKey() &&
      Boolean(preparedVideoBlobRef.current)
    );
  }

  function hasPreparedAudioSource() {
    return (
      preparedAudioKeyRef.current === buildVideoSourceKey() &&
      Boolean(currentAudioUrlRef.current)
    );
  }

  function isVideoPreparingForCurrentCue() {
    return (
      preparedVideoKeyRef.current === buildVideoSourceKey() &&
      Boolean(preparedVideoPromiseRef.current)
    );
  }

  async function waitForVideoCanPlay(video: HTMLVideoElement) {
    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      return;
    }

    await new Promise<void>((resolve, reject) => {
      const handleReady = () => {
        cleanup();
        resolve();
      };
      const handleError = () => {
        cleanup();
        reject(new Error("Tutor video could not be loaded."));
      };
      const cleanup = () => {
        video.removeEventListener("loadeddata", handleReady);
        video.removeEventListener("canplay", handleReady);
        video.removeEventListener("error", handleError);
      };

      video.addEventListener("loadeddata", handleReady, { once: true });
      video.addEventListener("canplay", handleReady, { once: true });
      video.addEventListener("error", handleError, { once: true });
    });
  }

  async function resolveVideoElement(forceRemount: boolean) {
    if (forceRemount) {
      flushSync(() => {
        setVideoPlaybackKey((current) => current + 1);
      });
      await Promise.resolve();
    }

    const video = videoRef.current;
    if (!video) {
      throw new Error("Tutor video element is not ready");
    }

    return video;
  }

  async function playNarration(requestId: number) {
    const audio = ensureAudioElement();
    const audioUrl = await ensureAudioSource();
    if (!isCurrentPlaybackRequest(requestId)) {
      return;
    }

    videoRef.current?.pause();
    audio.pause();
    if (audio.src !== audioUrl) {
      audio.src = audioUrl;
    }
    try {
      audio.currentTime = 0;
    } catch {
      // Ignore harmless seek errors while the element is preparing.
    }
    setRenderMode("audio");
    if (!isCurrentPlaybackRequest(requestId)) {
      return;
    }
    await audio.play();
    if (isCurrentPlaybackRequest(requestId)) {
      setIsPlaying(true);
    }
  }

  async function loadVideoSource(
    video: HTMLVideoElement,
    videoUrl: string,
    forceReload = false,
  ) {
    const shouldReloadSource =
      forceReload ||
      video.src !== videoUrl ||
      video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA;

    video.pause();

    if (shouldReloadSource) {
      video.removeAttribute("src");
      video.load();
      video.src = videoUrl;
      video.load();
      await waitForVideoCanPlay(video);
    }

    try {
      video.currentTime = 0;
    } catch {
      // Some browsers can briefly reject seeking before metadata is ready.
    }
  }

  async function playMuseTalkVideo(requestId: number, forceReload = false) {
    const video = await resolveVideoElement(forceReload);

    const videoBlob = await ensureVideoSource();
    if (!isCurrentPlaybackRequest(requestId)) {
      return;
    }

    if (currentVideoUrlRef.current) {
      URL.revokeObjectURL(currentVideoUrlRef.current);
      currentVideoUrlRef.current = null;
    }

    const videoUrl = URL.createObjectURL(videoBlob);
    currentVideoUrlRef.current = videoUrl;
    audioRef.current?.pause();
    await loadVideoSource(video, videoUrl, forceReload);
    if (!isCurrentPlaybackRequest(requestId)) {
      return;
    }
    video.onplaying = () => setIsPlaying(true);
    video.onended = () => setIsPlaying(false);
    video.onpause = () => setIsPlaying(false);
    video.muted = false;
    setRenderMode("video");
    await video.play();
    if (isCurrentPlaybackRequest(requestId)) {
      setIsPlaying(true);
    }
  }

  async function playMuseTalkVideoWithTimeout(
    requestId: number,
    timeoutMs: number,
    forceReload = false,
  ) {
    await Promise.race([
      playMuseTalkVideo(requestId, forceReload),
      new Promise<never>((_, reject) => {
        window.setTimeout(() => {
          if (isCurrentPlaybackRequest(requestId)) {
            const timeoutError = new Error("Tutor video is still warming up.");
            timeoutError.name = "TutorVideoTimeoutError";
            reject(timeoutError);
          }
        }, timeoutMs);
      }),
    ]);
  }

  async function playTutorCue(trigger: "auto" | "manual" = "manual") {
    const initialRequestId = playbackRequestRef.current + 1;
    playbackRequestRef.current = initialRequestId;
    setPlaybackHint(null);
    setIsLoading(true);
    stopCurrentPlayback();

    try {
      if (trigger === "manual") {
        if (hasPreparedAudioSource() && !hasPreparedVideoSource() && !isVideoPreparingForCurrentCue()) {
          await playNarration(initialRequestId);
          return;
        }

        if (hasPreparedVideoSource()) {
          try {
            await playMuseTalkVideo(initialRequestId, true);
            return;
          } catch {
            const fallbackRequestId = playbackRequestRef.current + 1;
            playbackRequestRef.current = fallbackRequestId;
            await playNarration(fallbackRequestId);
            return;
          }
        }
      }

      await playMuseTalkVideoWithTimeout(
        initialRequestId,
        trigger === "manual"
          ? WELCOME_TUTOR_REPLAY_VIDEO_WAIT_MS
          : WELCOME_TUTOR_VIDEO_WAIT_MS,
        trigger === "manual",
      );
      return;
    } catch (error) {
      const blockedAutoplay =
        error instanceof Error &&
        (error.name === "NotAllowedError" || error.message.includes("play"));
      const videoTimedOut =
        error instanceof Error && error.name === "TutorVideoTimeoutError";

      if (videoTimedOut) {
        const fallbackRequestId = playbackRequestRef.current + 1;
        playbackRequestRef.current = fallbackRequestId;

        try {
          await playNarration(fallbackRequestId);
          return;
        } catch (fallbackError) {
          const fallbackBlocked =
            fallbackError instanceof Error &&
            (fallbackError.name === "NotAllowedError" ||
              fallbackError.message.includes("play"));
          if (trigger === "manual") {
            setPlaybackHint(labels.loading);
            setIsPlaying(false);
            if (!fallbackBlocked) {
              setRenderMode("audio");
            }
            return;
          }
          setPlaybackHint(labels.warming);
          setIsPlaying(false);
          if (!fallbackBlocked) {
            setRenderMode("audio");
          }
          return;
        }
      }

      if (!blockedAutoplay && error instanceof ApiError) {
        try {
          await playNarration(initialRequestId);
          return;
        } catch (fallbackError) {
          const fallbackBlocked =
            fallbackError instanceof Error &&
            (fallbackError.name === "NotAllowedError" ||
              fallbackError.message.includes("play"));
          if (fallbackBlocked) {
            setPlaybackHint(labels.autoplayHint);
            setIsPlaying(false);
            return;
          }

          setPlaybackHint(labels.autoplayHint);
          setIsPlaying(false);
          return;
        }
      }

      if (blockedAutoplay) {
        setPlaybackHint(labels.autoplayHint);
        setIsPlaying(false);
        return;
      }

      try {
        await playNarration(initialRequestId);
      } catch (fallbackError) {
        const fallbackBlocked =
          fallbackError instanceof Error &&
          (fallbackError.name === "NotAllowedError" ||
            fallbackError.message.includes("play"));
        setPlaybackHint(labels.autoplayHint);
        setIsPlaying(false);
        if (!fallbackBlocked) {
          setRenderMode("audio");
        }
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="proof-lesson-ai-cue">
      <TutorCard
        label={label}
        message={message}
        replayAction={
          <button
            type="button"
            onClick={() => void playTutorCue("manual")}
            className="proof-lesson-ai-cue__replay"
          >
            {replayCta}
          </button>
        }
        status={
          isLoading || isPlaying ? (
            <div className="proof-lesson-ai-cue__status">
              <span
                className={cn(
                  "proof-lesson-ai-cue__status-dot",
                  (isLoading || isPlaying) && "proof-lesson-ai-cue__status-dot--live",
                )}
                aria-hidden="true"
              />
              <span>{isLoading ? labels.loading : labels.playing}</span>
            </div>
          ) : null
        }
        hint={playbackHint}
        isSpeaking={isPlaying}
        avatarStage={
          <div
            className={cn(
              "proof-lesson-ai-avatar",
              isPlaying && "proof-lesson-ai-avatar--speaking",
              renderMode === "video" && "proof-lesson-ai-avatar--video",
            )}
          >
            <img
              src={avatarGirlSrc}
              alt={avatarAlt}
              className="proof-lesson-ai-avatar__image"
              draggable={false}
              decoding="async"
            />
            <video
              key={videoPlaybackKey}
              ref={videoRef}
              playsInline
              preload="auto"
              muted={false}
              className={cn(
                "proof-lesson-ai-avatar__video",
                renderMode === "video" && "is-visible",
              )}
            />
            <div className="proof-lesson-ai-avatar__ambient-ring" aria-hidden="true" />
          </div>
        }
      />
    </div>
  );
}
