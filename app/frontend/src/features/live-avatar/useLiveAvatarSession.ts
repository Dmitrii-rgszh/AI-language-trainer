import { useEffect, useMemo, useRef, useState } from "react";
import { ApiError, apiClient } from "../../shared/api/client";
import type {
  LiveAvatarConfig,
  LiveAvatarFallbackResponse,
  LiveAvatarStatus,
} from "../../shared/types/live-avatar";
import { LiveAvatarRtcClient } from "../../rtc/live-avatar-client";

type LiveAvatarConnectionState =
  | "idle"
  | "connecting"
  | "connected"
  | "microphone_active"
  | "listening"
  | "processing"
  | "thinking"
  | "speaking"
  | "fallback_mode"
  | "reconnecting"
  | "connection_error";

const DEFAULT_STATUS_LABELS: Record<LiveAvatarConnectionState, string> = {
  idle: "Подключение не начато",
  connecting: "Подключение…",
  connected: "Соединение установлено",
  microphone_active: "Микрофон активен",
  listening: "Слушаю…",
  processing: "Обрабатываю…",
  thinking: "Обрабатываю…",
  speaking: "Лиза отвечает…",
  fallback_mode: "Fallback mode",
  reconnecting: "Переподключение…",
  connection_error: "Ошибка соединения",
};

export function useLiveAvatarSession() {
  const clientRef = useRef<LiveAvatarRtcClient | null>(null);
  const connectOptionsRef = useRef<{ captureMicrophone?: boolean }>({ captureMicrophone: true });
  const reconnectTimerRef = useRef<number | null>(null);
  const [config, setConfig] = useState<LiveAvatarConfig | null>(null);
  const [status, setStatus] = useState<LiveAvatarStatus | null>(null);
  const [connectionState, setConnectionState] = useState<LiveAvatarConnectionState>("idle");
  const [statusDetail, setStatusDetail] = useState(DEFAULT_STATUS_LABELS.idle);
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null);
  const [userTranscript, setUserTranscript] = useState("");
  const [assistantText, setAssistantText] = useState("");
  const [fallbackInput, setFallbackInput] = useState("");
  const [fallbackVideoUrl, setFallbackVideoUrl] = useState<string | null>(null);
  const [fallbackResult, setFallbackResult] = useState<LiveAvatarFallbackResponse | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [isFallbackRendering, setIsFallbackRendering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadConfig() {
      setIsBootstrapping(true);
      try {
        const [nextConfig, nextStatus] = await Promise.all([
          apiClient.getLiveAvatarConfig(),
          apiClient.getLiveAvatarStatus(),
        ]);
        if (cancelled) {
          return;
        }
        setConfig(nextConfig);
        setStatus(nextStatus);
        setConnectionState(nextStatus.ready ? "idle" : "connection_error");
        setStatusDetail(nextStatus.details || DEFAULT_STATUS_LABELS.idle);
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError instanceof Error ? fetchError.message : "Не удалось загрузить live avatar конфиг.");
          setConnectionState("connection_error");
          setStatusDetail(DEFAULT_STATUS_LABELS.connection_error);
        }
      } finally {
        if (!cancelled) {
          setIsBootstrapping(false);
        }
      }
    }

    void loadConfig();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      void clientRef.current?.disconnect();
    };
  }, []);

  useEffect(() => {
    return () => {
      if (fallbackVideoUrl) {
        URL.revokeObjectURL(fallbackVideoUrl);
      }
    };
  }, [fallbackVideoUrl]);

  const canConnect = Boolean(config?.enabled && status?.ready);

  const connect = async (options?: { captureMicrophone?: boolean }) => {
    if (!config) {
      return;
    }
    connectOptionsRef.current = options ?? connectOptionsRef.current;

    if (reconnectTimerRef.current !== null) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    setError(null);
    setConnectionState("connecting");
    setStatusDetail(DEFAULT_STATUS_LABELS.connecting);

    const client = new LiveAvatarRtcClient(config, {
      onAssistantText: (text) => {
        setAssistantText(text);
      },
      onDisconnected: (wasManual) => {
        setRemoteStream(null);
        if (wasManual) {
          setConnectionState("idle");
          setStatusDetail(DEFAULT_STATUS_LABELS.idle);
          return;
        }
        setConnectionState("reconnecting");
        setStatusDetail(DEFAULT_STATUS_LABELS.reconnecting);
        reconnectTimerRef.current = window.setTimeout(() => {
          reconnectTimerRef.current = null;
          void connect(connectOptionsRef.current);
        }, 1500);
      },
      onError: (message) => {
        setError(message);
        setConnectionState("connection_error");
        setStatusDetail(message || DEFAULT_STATUS_LABELS.connection_error);
      },
      onRemoteStream: (stream) => {
        setRemoteStream(stream);
      },
      onStatus: (nextStatus, detail) => {
        const typedStatus = (nextStatus as LiveAvatarConnectionState) || "connected";
        setConnectionState(typedStatus in DEFAULT_STATUS_LABELS ? typedStatus : "connected");
        setStatusDetail(detail || DEFAULT_STATUS_LABELS.connected);
      },
      onUserTranscript: (text) => {
        setUserTranscript(text);
        setFallbackInput((current) => current || text);
      },
    });

    try {
      await client.connect(options);
      connectOptionsRef.current = client.getConnectOptions();
      clientRef.current = client;
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : "Не удалось установить live-соединение.");
      setConnectionState("connection_error");
      setStatusDetail(DEFAULT_STATUS_LABELS.connection_error);
    }
  };

  const disconnect = async () => {
    if (reconnectTimerRef.current !== null) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    await clientRef.current?.disconnect();
    clientRef.current = null;
    setRemoteStream(null);
    setConnectionState("idle");
    setStatusDetail(DEFAULT_STATUS_LABELS.idle);
  };

  const forceEndTurn = () => {
    clientRef.current?.forceEndTurn();
  };

  const speakText = (text: string, language = "ru") => {
    clientRef.current?.speakText(text, language);
  };

  const runFallbackRender = async () => {
    const userText = fallbackInput.trim() || userTranscript.trim();
    if (!userText) {
      setError("Нужен текст последней реплики для fallback render.");
      return;
    }

    setIsFallbackRendering(true);
    setError(null);
    setConnectionState("fallback_mode");
    setStatusDetail(DEFAULT_STATUS_LABELS.fallback_mode);
    try {
      const result = await apiClient.renderLiveAvatarFallback({
        userText,
        language: "ru",
        avatarKey: config?.defaultAvatarKey ?? "verba_tutor",
      });
      const clipBlob = await apiClient.getLiveAvatarFallbackClip(result.clipId);
      if (fallbackVideoUrl) {
        URL.revokeObjectURL(fallbackVideoUrl);
      }
      const videoUrl = URL.createObjectURL(clipBlob);
      setFallbackVideoUrl(videoUrl);
      setFallbackResult(result);
      setAssistantText(result.assistantText);
    } catch (fallbackError) {
      const message =
        fallbackError instanceof ApiError
          ? `Fallback render failed: ${fallbackError.status}`
          : fallbackError instanceof Error
            ? fallbackError.message
            : "Fallback render failed.";
      setError(message);
      setConnectionState("connection_error");
      setStatusDetail(message);
    } finally {
      setIsFallbackRendering(false);
    }
  };

  const isConnected = useMemo(
    () => ["connected", "microphone_active", "listening", "processing", "thinking", "speaking", "fallback_mode"].includes(connectionState),
    [connectionState],
  );

  return {
    assistantText,
    canConnect,
    config,
    connect,
    connectionState,
    disconnect,
    error,
    fallbackInput,
    fallbackResult,
    fallbackVideoUrl,
    forceEndTurn,
    isBootstrapping,
    isConnected,
    isFallbackRendering,
    remoteStream,
    runFallbackRender,
    setFallbackInput,
    speakText,
    status,
    statusDetail,
    userTranscript,
  };
}
