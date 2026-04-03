import type { LiveAvatarConfig } from "../shared/types/live-avatar";

type LiveAvatarClientCallbacks = {
  onAssistantText: (text: string) => void;
  onDisconnected: (wasManual: boolean) => void;
  onError: (message: string) => void;
  onRemoteStream: (stream: MediaStream) => void;
  onStatus: (status: string, detail: string) => void;
  onUserTranscript: (text: string) => void;
};

function buildWebSocketUrl(signalingPath: string) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${signalingPath}`;
}

function mapIceServers(config: LiveAvatarConfig) {
  return config.iceServers.map((server) => ({
    urls: server.urls,
    username: server.username ?? undefined,
    credential: server.credential ?? undefined,
  }));
}

export class LiveAvatarRtcClient {
  private callbacks: LiveAvatarClientCallbacks;
  private config: LiveAvatarConfig;
  private captureMicrophone = true;
  private localStream: MediaStream | null = null;
  private manualClose = false;
  private peerConnection: RTCPeerConnection | null = null;
  private remoteStream = new MediaStream();
  private websocket: WebSocket | null = null;

  constructor(config: LiveAvatarConfig, callbacks: LiveAvatarClientCallbacks) {
    this.config = config;
    this.callbacks = callbacks;
  }

  async connect(options?: { captureMicrophone?: boolean }) {
    this.manualClose = false;
    this.remoteStream = new MediaStream();
    const captureMicrophone = options?.captureMicrophone ?? true;
    this.captureMicrophone = captureMicrophone;
    let localStream: MediaStream | null = null;
    if (captureMicrophone) {
      localStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          autoGainControl: true,
          echoCancellation: true,
          noiseSuppression: true,
        },
        video: false,
      });
      this.localStream = localStream;
    } else {
      this.localStream = null;
    }

    const websocket = await this.openWebSocket();
    const peerConnection = new RTCPeerConnection({
      iceServers: mapIceServers(this.config),
    });

    peerConnection.onicecandidate = (event) => {
      if (!event.candidate || !this.websocket) {
        return;
      }
      this.websocket.send(
        JSON.stringify({
          type: "ice-candidate",
          candidate: {
            candidate: event.candidate.candidate,
            sdpMid: event.candidate.sdpMid,
            sdpMLineIndex: event.candidate.sdpMLineIndex,
          },
        }),
      );
    };

    peerConnection.ontrack = (event) => {
      for (const track of event.streams[0]?.getTracks() ?? [event.track]) {
        const alreadyPresent = this.remoteStream.getTracks().some((existingTrack) => existingTrack.id === track.id);
        if (!alreadyPresent) {
          this.remoteStream.addTrack(track);
        }
      }
      this.callbacks.onRemoteStream(new MediaStream(this.remoteStream.getTracks()));
    };

    peerConnection.onconnectionstatechange = () => {
      if (peerConnection.connectionState === "failed" || peerConnection.connectionState === "disconnected") {
        this.callbacks.onError("Ошибка WebRTC-соединения.");
      }
    };

    peerConnection.addTransceiver("audio", { direction: "recvonly" });
    peerConnection.addTransceiver("video", { direction: "recvonly" });

    if (localStream) {
      for (const track of localStream.getTracks()) {
        peerConnection.addTrack(track, localStream);
      }
    }

    this.websocket = websocket;
    this.peerConnection = peerConnection;

    const offer = await peerConnection.createOffer({
      offerToReceiveAudio: true,
      offerToReceiveVideo: true,
    });
    await peerConnection.setLocalDescription(offer);
    websocket.send(JSON.stringify({ type: "offer", sdp: offer.sdp }));
  }

  getConnectOptions() {
    return { captureMicrophone: this.captureMicrophone };
  }

  async disconnect() {
    this.manualClose = true;
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify({ type: "disconnect" }));
    }
    this.cleanup();
  }

  forceEndTurn() {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify({ type: "force-end-turn" }));
    }
  }

  speakText(text: string, language = "ru") {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(
        JSON.stringify({
          type: "speak-text",
          text,
          language,
        }),
      );
    }
  }

  private async openWebSocket() {
    const websocket = new WebSocket(this.config.signalingUrl || buildWebSocketUrl(this.config.signalingPath));

    await new Promise<void>((resolve, reject) => {
      const handleOpen = () => {
        cleanup();
        resolve();
      };
      const handleError = () => {
        cleanup();
        reject(new Error("WebSocket signaling failed to open."));
      };
      const cleanup = () => {
        websocket.removeEventListener("open", handleOpen);
        websocket.removeEventListener("error", handleError);
      };
      websocket.addEventListener("open", handleOpen, { once: true });
      websocket.addEventListener("error", handleError, { once: true });
    });

    websocket.onmessage = (event) => {
      void this.handleMessage(event.data);
    };
    websocket.onclose = () => {
      const wasManual = this.manualClose;
      this.cleanup();
      this.callbacks.onDisconnected(wasManual);
    };

    return websocket;
  }

  private async handleMessage(rawMessage: string) {
    const message = JSON.parse(rawMessage) as {
      type?: string;
      sdp?: string;
      candidate?: RTCIceCandidateInit;
      detail?: string;
      status?: string;
      text?: string;
    };

    switch (message.type) {
      case "answer":
        if (!this.peerConnection || !message.sdp) {
          return;
        }
        await this.peerConnection.setRemoteDescription({
          type: "answer",
          sdp: message.sdp,
        });
        return;
      case "ice-candidate":
        if (!this.peerConnection || !message.candidate) {
          return;
        }
        await this.peerConnection.addIceCandidate(message.candidate);
        return;
      case "status":
        this.callbacks.onStatus(message.status ?? "status", message.detail ?? "");
        return;
      case "session-ready":
        this.callbacks.onStatus("connecting", "Подключение…");
        return;
      case "user-transcript":
        this.callbacks.onUserTranscript(message.text ?? "");
        return;
      case "assistant-text":
        this.callbacks.onAssistantText(message.text ?? "");
        return;
      default:
        return;
    }
  }

  private cleanup() {
    this.peerConnection?.close();
    this.peerConnection = null;

    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.close();
    }
    this.websocket = null;

    for (const track of this.localStream?.getTracks() ?? []) {
      track.stop();
    }
    this.localStream = null;

    for (const track of this.remoteStream.getTracks()) {
      track.stop();
      this.remoteStream.removeTrack(track);
    }
  }
}
