import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../shared/api/client";

type VoiceStyle = "neutral" | "coach";

export function useLessonAudio(onError: (message: string | null) => void) {
  const [isPlayingListening, setIsPlayingListening] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const currentAudioUrlRef = useRef<string | null>(null);

  useEffect(() => {
    return () => {
      audioRef.current?.pause();
      if (currentAudioUrlRef.current) {
        URL.revokeObjectURL(currentAudioUrlRef.current);
      }
    };
  }, []);

  async function playText(text: string, style: VoiceStyle = "neutral") {
    if (!text) {
      return;
    }

    onError(null);
    setIsPlayingListening(true);
    try {
      const audioBlob = await apiClient.synthesizeSpeech({
        text,
        language: "en",
        style,
      });
      if (currentAudioUrlRef.current) {
        URL.revokeObjectURL(currentAudioUrlRef.current);
      }
      const audioUrl = URL.createObjectURL(audioBlob);
      currentAudioUrlRef.current = audioUrl;
      if (!audioRef.current) {
        audioRef.current = new Audio();
      }
      audioRef.current.src = audioUrl;
      audioRef.current.onended = () => setIsPlayingListening(false);
      await audioRef.current.play();
    } catch (error) {
      setIsPlayingListening(false);
      onError(error instanceof Error ? error.message : "Listening playback failed");
    }
  }

  async function playListeningAudio(transcript: string | null) {
    if (!transcript) {
      return;
    }

    await playText(transcript, "neutral");
  }

  return {
    isPlayingListening,
    playListeningAudio,
    playText,
  };
}
