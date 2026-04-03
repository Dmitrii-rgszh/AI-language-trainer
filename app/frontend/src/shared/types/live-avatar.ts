export interface LiveAvatarIceServer {
  urls: string[];
  username?: string | null;
  credential?: string | null;
}

export interface LiveAvatarConfig {
  enabled: boolean;
  signalingPath: string;
  signalingUrl: string;
  defaultAvatarKey: string;
  defaultVoiceProfileId: string;
  fallbackModeAvailable: boolean;
  iceServers: LiveAvatarIceServer[];
  details: string;
}

export interface LiveAvatarStatus {
  enabled: boolean;
  ready: boolean;
  mode: "live" | "fallback" | "disabled";
  details: string;
}

export interface LiveAvatarFallbackResponse {
  transcript: string;
  assistantText: string;
  clipId: string;
  clipUrl: string;
}
