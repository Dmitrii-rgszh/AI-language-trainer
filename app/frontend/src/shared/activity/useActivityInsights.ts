import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type {
  ListeningAttempt,
  ListeningTrend,
  PronunciationTrend,
  SpeakingAttempt,
} from "../types/app-data";

type UseActivityInsightsOptions = {
  errorMessage: string;
  includeListeningHistory?: boolean;
};

export function useActivityInsights(options: UseActivityInsightsOptions) {
  const { errorMessage, includeListeningHistory = false } = options;
  const [speakingAttempts, setSpeakingAttempts] = useState<SpeakingAttempt[]>([]);
  const [pronunciationTrend, setPronunciationTrend] = useState<PronunciationTrend | null>(null);
  const [listeningAttempts, setListeningAttempts] = useState<ListeningAttempt[]>([]);
  const [listeningTrend, setListeningTrend] = useState<ListeningTrend | null>(null);
  const [activityError, setActivityError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadActivityInsights() {
      try {
        const [attempts, pronunciation, listening, listeningHistory] = await Promise.all([
          apiClient.getSpeakingAttempts(),
          apiClient.getPronunciationTrends(),
          apiClient.getListeningTrends(),
          includeListeningHistory ? apiClient.getListeningHistory() : Promise.resolve([] as ListeningAttempt[]),
        ]);

        if (!isMounted) {
          return;
        }

        setSpeakingAttempts(attempts);
        setPronunciationTrend(pronunciation);
        setListeningTrend(listening);
        setListeningAttempts(listeningHistory);
        setActivityError(null);
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setActivityError(error instanceof Error ? error.message : errorMessage);
      }
    }

    void loadActivityInsights();

    return () => {
      isMounted = false;
    };
  }, [errorMessage, includeListeningHistory]);

  return {
    activityError,
    listeningAttempts,
    listeningTrend,
    pronunciationTrend,
    speakingAttempts,
  };
}
