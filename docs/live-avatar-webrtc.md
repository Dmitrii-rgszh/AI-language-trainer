# Live Avatar WebRTC

MVP live-режим переводит AI-аватара из сценария `render file -> show file` в сценарий `WebRTC session -> stream audio/video back to browser`.

## Что входит в v1

- signaling по `WebSocket`
- server-side `aiortc` peer connection
- захват микрофона в браузере
- server-side endpoint detection
- `STT -> dialogue -> Qwen3-TTS clone -> MuseTalk live`
- возврат audio/video как live media stream
- fallback render mode через обычный MuseTalk clip

## Ключевые backend-модули

- `backend/app/api/routes/live_avatar.py`
  HTTP и WebSocket API для live-режима.
- `backend/app/services/live_avatar_service/service.py`
  orchestration, readiness, fallback render.
- `backend/app/live_avatar/rtc/session.py`
  lifecycle одной live-сессии, inbound audio, outbound media.
- `backend/app/live_avatar/rtc/tracks.py`
  server-side audio/video tracks для WebRTC.
- `backend/app/live_avatar/rtc/ice.py`
  сборка ICE/STUN/TURN конфигурации.
- `backend/app/live_avatar/audio/utterance_recorder.py`
  простая VAD/endpoint detection логика.
- `backend/app/live_avatar/dialogue/service.py`
  отдельный dialogue/LLM слой.
- `backend/app/live_avatar/tts/qwen3/engine.py`
  адаптер Qwen3-TTS для clone voice profile.
- `backend/app/live_avatar/lipsync/musetalk/engine.py`
  адаптер MuseTalk live-sidecar.

## Ключевые frontend-модули

- `app/frontend/src/rtc/live-avatar-client.ts`
  браузерный WebRTC client и signaling.
- `app/frontend/src/features/live-avatar/useLiveAvatarSession.ts`
  session state, reconnect, fallback.
- `app/frontend/src/features/live-avatar/LiveAvatarScreen.tsx`
  live UI и статусы.
- `app/frontend/src/pages/LiveAvatarPage.tsx`
  страница `/live-avatar`.

## Runtime sidecars

- `backend/scripts/qwen_tts_sidecar.py`
  локальный Qwen3-TTS runtime.
- `backend/scripts/musetalk_live_sidecar.py`
  live MuseTalk sidecar, который отдаёт кадры потоком.

## Основные API

- `GET /api/live-avatar/config`
- `GET /api/live-avatar/status`
- `WS /api/live-avatar/ws`
- `POST /api/live-avatar/fallback-render`
- `GET /api/live-avatar/fallback-render/{clip_id}`

## Важные env-переменные

- `LIVE_AVATAR_ENABLED`
- `WEBRTC_STUN_URLS`
- `WEBRTC_TURN_URLS`
- `WEBRTC_TURN_USERNAME`
- `WEBRTC_TURN_PASSWORD`
- `QWEN_TTS_MODEL`
- `QWEN_TTS_DEVICE`
- `QWEN_TTS_MODE`
- `QWEN_TTS_STREAMING_ENABLED`
- `QWEN_TTS_REF_AUDIO_PATH`
- `QWEN_TTS_REF_TEXT`
- `QWEN_TTS_WARMUP`
- `QWEN_TTS_SAMPLE_RATE`
- `MUSE_TALK_LIVE_ENABLED`
- `MUSE_TALK_LIVE_BASE_URL`
- `MUSE_TALK_FPS`
- `MUSE_TALK_FRAME_BUFFER`
- `MUSE_TALK_WARMUP`
- `STT_PROVIDER`
- `LLM_PROVIDER`

## Локальный запуск

1. Подготовить runtimes:
   - `backend/scripts/setup_qwen_tts_runtime.ps1`
   - `backend/scripts/setup_musetalk_runtime.ps1`
2. Положить reference voice и transcript.
3. Запустить `run_local_app.bat`.
4. Открыть `http://127.0.0.1:5173/live-avatar`.

## Что проверять в UI

- статус `Подключение…`
- статус `Соединение установлено`
- статус `Микрофон активен`
- статусы `Слушаю… -> Обрабатываю… -> Лиза отвечает…`
- появление live video/audio stream
- fallback render как резервный сценарий

## Ограничения v1

- endpoint detection пока server-side и сравнительно простая
- barge-in пока не реализован
- RTCDataChannel пока не используется как основной transport событий
- adaptive buffering и dynamic quality downgrade пока не реализованы
- TURN предусмотрен конфигом, но локально основная схема рассчитана на STUN/direct setup
