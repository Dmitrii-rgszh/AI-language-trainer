import { useEffect, useRef, useState } from "react";
import type { AppLocale } from "../../shared/i18n/locale";
import avatarGirlSrc from "../../shared/assets/ai-tutor/avatar-girl.webp";
import { useLiveAvatarSession } from "../live-avatar/useLiveAvatarSession";
import { cn } from "../../shared/utils/cn";

type WelcomeStreamingAvatarCueProps = {
  isVisible: boolean;
  locale: AppLocale;
  label: string;
  message: string;
  spokenMessage?: string;
  replayCta: string;
};

function getPlaybackLabels(locale: AppLocale) {
  if (locale === "ru") {
    return {
      autoplayHint: "Если звук не стартовал автоматически, нажми «Послушать ещё раз».",
      connecting: "Подключаю живого аватара...",
      ready: "Лиза готова к live-демо.",
      speaking: "Лиза говорит вживую...",
    };
  }

  return {
    autoplayHint: "If audio did not start automatically, press “Hear it again”.",
    connecting: "Connecting the live avatar...",
    ready: "Liza is ready for the live demo.",
    speaking: "Liza is speaking live...",
  };
}

export function WelcomeStreamingAvatarCue({
  isVisible,
  locale,
  label,
  message,
  spokenMessage,
  replayCta,
}: WelcomeStreamingAvatarCueProps) {
  const labels = getPlaybackLabels(locale);
  const avatarAlt = locale === "ru" ? "Лиза" : "Liza";
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const spokenPromptKeyRef = useRef<string | null>(null);
  const {
    canConnect,
    connect,
    connectionState,
    disconnect,
    error,
    isBootstrapping,
    isConnected,
    remoteStream,
    speakText,
    statusDetail,
  } = useLiveAvatarSession();
  const [playbackHint, setPlaybackHint] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const livePrompt = (spokenMessage || message).trim();
  const promptKey = `${locale}:${livePrompt}`;
  const language = locale === "ru" ? "ru" : "en";

  async function startMediaPlayback() {
    const video = videoRef.current;
    const audio = audioRef.current;
    const audioStream = audio?.srcObject instanceof MediaStream ? audio.srcObject : null;

    if (video) {
      try {
        await video.play();
      } catch {
        setPlaybackHint(labels.autoplayHint);
      }
    }

    if (audio && audioStream && audioStream.getAudioTracks().length > 0) {
      try {
        await audio.play();
        setPlaybackHint(null);
      } catch {
        setPlaybackHint(labels.autoplayHint);
      }
    }
  }

  useEffect(() => {
    if (!isVisible) {
      spokenPromptKeyRef.current = null;
      setPlaybackHint(null);
      setIsPlaying(false);
      void disconnect();
      return;
    }

    if (canConnect && !isConnected && connectionState !== "connecting") {
      void connect({ captureMicrophone: false });
    }
  }, [canConnect, connect, connectionState, disconnect, isConnected, isVisible]);

  useEffect(() => {
    if (!isVisible || !isConnected) {
      return;
    }
    if (spokenPromptKeyRef.current === promptKey) {
      return;
    }
    spokenPromptKeyRef.current = promptKey;
    setPlaybackHint(null);
    speakText(livePrompt, language);
  }, [isConnected, isVisible, language, livePrompt, promptKey, speakText]);

  useEffect(() => {
    const video = videoRef.current;
    const audio = audioRef.current;
    if (!video || !audio) {
      return;
    }

    if (!remoteStream) {
      video.pause();
      video.srcObject = null;
      audio.pause();
      audio.srcObject = null;
      return;
    }

    const nextVideoStream = new MediaStream(remoteStream.getVideoTracks());
    const nextAudioStream = new MediaStream(remoteStream.getAudioTracks());
    video.srcObject = nextVideoStream;
    audio.srcObject = nextAudioStream;
    video.onplaying = () => setIsPlaying(true);
    video.onpause = () => setIsPlaying(false);
    video.onended = () => setIsPlaying(false);

    const syncPlayback = () => {
      void startMediaPlayback();
    };

    video.onloadedmetadata = syncPlayback;
    audio.onloadedmetadata = syncPlayback;
    for (const track of nextVideoStream.getTracks()) {
      track.onunmute = syncPlayback;
    }
    for (const track of nextAudioStream.getTracks()) {
      track.onunmute = syncPlayback;
    }
    void startMediaPlayback();

    return () => {
      video.onloadedmetadata = null;
      video.onplaying = null;
      video.onpause = null;
      video.onended = null;
      audio.onloadedmetadata = null;
      for (const track of nextVideoStream.getTracks()) {
        track.onunmute = null;
      }
      for (const track of nextAudioStream.getTracks()) {
        track.onunmute = null;
      }
    };
  }, [labels.autoplayHint, remoteStream]);

  const isBusy =
    isBootstrapping ||
    connectionState === "connecting" ||
    connectionState === "processing" ||
    connectionState === "thinking" ||
    connectionState === "speaking";
  const statusLabel =
    connectionState === "speaking"
      ? labels.speaking
      : connectionState === "connecting" || isBootstrapping
        ? labels.connecting
        : statusDetail || labels.ready;

  const handleReplay = () => {
    spokenPromptKeyRef.current = null;
    setPlaybackHint(null);
    if (!isConnected) {
      void connect({ captureMicrophone: false });
      return;
    }
    void startMediaPlayback();
    speakText(livePrompt, language);
  };

  return (
    <div className="proof-lesson-ai-cue">
      <div className="proof-lesson-surface proof-lesson-surface--warm proof-lesson-ai-cue__stage">
        <div className="proof-lesson-ai-cue__copy">
          <div className="proof-lesson-ai-cue__label">{label}</div>
          <p className="proof-lesson-ai-cue__message">{message}</p>

          <div className="proof-lesson-ai-cue__footer">
            <div className="proof-lesson-ai-cue__status">
              <span
                className={cn(
                  "proof-lesson-ai-cue__status-dot",
                  (isBusy || isPlaying) && "proof-lesson-ai-cue__status-dot--live",
                )}
                aria-hidden="true"
              />
              <span>{error || statusLabel}</span>
            </div>

            {playbackHint ? <div className="proof-lesson-ai-cue__hint">{playbackHint}</div> : null}

            <button
              type="button"
              onClick={handleReplay}
              className="proof-lesson-ai-cue__replay"
            >
              {replayCta}
            </button>
          </div>
        </div>

        <div className="proof-lesson-ai-cue__visual">
          <div
            className={cn(
              "proof-lesson-ai-avatar",
              (isPlaying || connectionState === "speaking") && "proof-lesson-ai-avatar--speaking",
              remoteStream && "proof-lesson-ai-avatar--video",
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
              ref={videoRef}
              autoPlay
              playsInline
              preload="auto"
              muted
              className={cn(
                "proof-lesson-ai-avatar__video",
                remoteStream && "is-visible",
              )}
            />
            <audio ref={audioRef} autoPlay preload="auto" className="sr-only" />
            <div className="proof-lesson-ai-avatar__ambient-ring" aria-hidden="true" />
          </div>
        </div>
      </div>
    </div>
  );
}
