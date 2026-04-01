import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../shared/api/client";

type UsePronunciationAssessmentOptions = {
  onTranscript: (blockId: string, value: string) => void;
  onScore: (blockId: string, value: number) => void;
  onError: (message: string | null) => void;
};

export function usePronunciationAssessment(options: UsePronunciationAssessmentOptions) {
  const { onTranscript, onScore, onError } = options;
  const [isRecordingPronunciation, setIsRecordingPronunciation] = useState(false);
  const [isAssessingPronunciation, setIsAssessingPronunciation] = useState(false);
  const [pronunciationTarget, setPronunciationTarget] = useState<string | null>(null);
  const activeBlockIdRef = useRef<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    return () => {
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function startPronunciationRecording(target: string, blockId: string) {
    onError(null);
    activeBlockIdRef.current = blockId;
    setPronunciationTarget(target);
    recordedChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };
      mediaRecorder.start();
      setIsRecordingPronunciation(true);
    } catch (error) {
      onError(error instanceof Error ? error.message : "Microphone access failed");
    }
  }

  async function stopPronunciationRecordingAndAssess() {
    const mediaRecorder = mediaRecorderRef.current;
    const blockId = activeBlockIdRef.current;
    if (!mediaRecorder || !pronunciationTarget || !blockId) {
      return;
    }

    setIsAssessingPronunciation(true);
    const recordedBlob = await new Promise<Blob>((resolve) => {
      mediaRecorder.onstop = () => {
        resolve(new Blob(recordedChunksRef.current, { type: mediaRecorder.mimeType || "audio/webm" }));
      };
      mediaRecorder.stop();
    });
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;
    mediaRecorderRef.current = null;
    setIsRecordingPronunciation(false);

    try {
      const assessment = await apiClient.assessPronunciation({
        targetText: pronunciationTarget,
        audio: recordedBlob,
      });
      onTranscript(blockId, assessment.transcript);
      onScore(blockId, assessment.score);
    } catch (error) {
      onError(error instanceof Error ? error.message : "Pronunciation scoring failed");
    } finally {
      activeBlockIdRef.current = null;
      setIsAssessingPronunciation(false);
      setPronunciationTarget(null);
    }
  }

  return {
    isAssessingPronunciation,
    isRecordingPronunciation,
    pronunciationTarget,
    startPronunciationRecording,
    stopPronunciationRecordingAndAssess,
  };
}
