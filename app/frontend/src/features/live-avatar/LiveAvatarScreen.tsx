import { useEffect, useRef } from "react";
import { Card } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { useLiveAvatarSession } from "./useLiveAvatarSession";

function StatusBadge({ label }: { label: string }) {
  return (
    <div className="rounded-full border border-white/70 bg-white/80 px-3 py-1 text-xs font-[700] tracking-[-0.01em] text-slate-700">
      {label}
    </div>
  );
}

export function LiveAvatarScreen() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const {
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
    statusDetail,
    userTranscript,
  } = useLiveAvatarSession();

  useEffect(() => {
    const videoElement = videoRef.current;
    if (!videoElement) {
      return;
    }

    if (fallbackVideoUrl) {
      videoElement.srcObject = null;
      videoElement.src = fallbackVideoUrl;
      void videoElement.play().catch(() => undefined);
      return;
    }

    if (!remoteStream) {
      videoElement.srcObject = null;
      videoElement.removeAttribute("src");
      videoElement.load();
      return;
    }

    videoElement.src = "";
    videoElement.srcObject = remoteStream;

    const ensurePlayback = () => {
      void videoElement.play().catch(() => undefined);
    };

    videoElement.onloadedmetadata = ensurePlayback;
    for (const track of remoteStream.getTracks()) {
      track.onunmute = ensurePlayback;
    }
    ensurePlayback();

    return () => {
      videoElement.onloadedmetadata = null;
      for (const track of remoteStream.getTracks()) {
        track.onunmute = null;
      }
    };
  }, [fallbackVideoUrl, remoteStream]);

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow="Live Avatar"
        title="WebRTC avatar conversation"
        description="Живой режим держит открытый peer connection, принимает ваш микрофон на backend, а ответ отдаёт назад голосом клона и lip sync-потоком. Если live путь недоступен, можно сразу переключиться на fallback render."
      />

      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.95fr]">
        <Card className="space-y-4 overflow-hidden">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge label="WebRTC" />
            <StatusBadge label="Qwen3-TTS clone" />
            <StatusBadge label="MuseTalk live" />
            <StatusBadge label={connectionState.replace(/_/g, " ")} />
          </div>

          <div className="relative overflow-hidden rounded-[30px] border border-white/70 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.92),rgba(226,239,237,0.78)_58%,rgba(204,222,220,0.88))] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.88)]">
            <div className="absolute inset-x-0 top-0 h-28 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.86),transparent_72%)]" />
            <video
              ref={videoRef}
              playsInline
              autoPlay
              controls={Boolean(fallbackVideoUrl)}
              className="relative z-[1] aspect-square w-full rounded-[24px] bg-[#e8efe9] object-cover shadow-[0_18px_45px_rgba(122,146,150,0.18)]"
            />
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-[24px] bg-sand/75 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">Runtime</div>
              <div className="mt-2 text-sm leading-6 text-slate-700">{statusDetail}</div>
            </div>
            <div className="rounded-[24px] bg-white/70 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">Session</div>
              <div className="mt-2 text-sm leading-6 text-slate-700">
                {isBootstrapping
                  ? "Подгружаю live-конфиг и ICE-настройки…"
                  : config?.details ?? "Конфиг live-режима недоступен."}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button onClick={() => void connect()} disabled={!canConnect || isBootstrapping || isConnected}>
              Подключиться
            </Button>
            <Button variant="secondary" onClick={() => void disconnect()} disabled={!isConnected}>
              Отключиться
            </Button>
            <Button variant="ghost" onClick={forceEndTurn} disabled={!isConnected}>
              Завершить реплику
            </Button>
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">Диалог</div>
            <div className="rounded-[22px] bg-white/72 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">Вы сказали</div>
              <div className="mt-2 min-h-[72px] text-sm leading-6 text-slate-700">
                {userTranscript || "Пока нет распознанной реплики."}
              </div>
            </div>
            <div className="rounded-[22px] bg-sand/75 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">Ответ Лизы</div>
              <div className="mt-2 min-h-[88px] text-sm leading-6 text-slate-700">
                {assistantText || "Ответ появится после завершения вашей реплики."}
              </div>
            </div>
          </Card>

          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">Fallback render</div>
            <div className="text-sm leading-6 text-slate-600">
              Если live-поток недоступен, можно собрать обычный ролик как резервный сценарий и сразу воспроизвести его здесь же.
            </div>
            <textarea
              value={fallbackInput}
              onChange={(event) => setFallbackInput(event.target.value)}
              placeholder="Текст последней реплики для fallback render"
              className="min-h-[120px] w-full rounded-[22px] border border-white/70 bg-white/78 px-4 py-3 text-sm text-slate-700 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] outline-none transition-colors focus:border-teal-400"
            />
            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" onClick={() => void runFallbackRender()} disabled={isFallbackRendering}>
                {isFallbackRendering ? "Рендерю…" : "Запустить fallback render"}
              </Button>
            </div>
            {fallbackResult ? (
              <div className="rounded-[22px] bg-white/72 p-4 text-sm leading-6 text-slate-700">
                <div className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">Fallback clip</div>
                <div className="mt-2">Clip ID: {fallbackResult.clipId}</div>
                <div>Ответ: {fallbackResult.assistantText}</div>
              </div>
            ) : null}
          </Card>

          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">Статусы UX</div>
            <div className="grid gap-2">
              {[
                "Подключение…",
                "Соединение установлено",
                "Микрофон активен",
                "Слушаю…",
                "Обрабатываю…",
                "Лиза отвечает…",
                "Ошибка соединения",
                "Переподключение…",
                "Fallback mode",
              ].map((label) => (
                <div
                  key={label}
                  className="rounded-full border border-white/65 bg-white/74 px-4 py-2 text-sm text-slate-700"
                >
                  {label}
                </div>
              ))}
            </div>
            {error ? <div className="rounded-[20px] bg-[#fff1ef] p-4 text-sm text-[#b94f38]">{error}</div> : null}
          </Card>
        </div>
      </div>
    </div>
  );
}
