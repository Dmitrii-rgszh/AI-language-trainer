export type LivingBackgroundId =
  | "background-1"
  | "background-2"
  | "background-3"
  | "background-4"
  | "background-5"
  | "background-6"
  | "background-7";

export type LivingBackgroundPhase = "idle" | "bloom" | "transition" | "stabilizing";

export type LivingBackgroundAsset = {
  id: LivingBackgroundId;
  webmSrc: string;
  mp4Src: string;
  depthIndex: number;
};

export type LivingDepthCommitmentConfig = {
  candidateVisibilityThreshold: number;
  bloomVisibilityThreshold: number;
  commitVisibilityThreshold: number;
  dwellTimeMs: number;
  bloomDelayMs: number;
  scrollVelocityThreshold: number;
  fastScrollVelocityThreshold: number;
  scrollSettleMs: number;
  desktopCursorIdleMs: number;
  desktopPointerMovementThresholdPx: number;
  mobilePostScrollStabilizationMs: number;
  cooldownMs: number;
  routeNavigationCommitDelayMs: number;
  transitionMs: number;
  stabilizationMs: number;
  memoryFadeMs: number;
  reducedMotionTransitionMs: number;
  reducedMotionStabilizationMs: number;
  reducedMotionMemoryFadeMs: number;
};

export type LivingDepthCommitmentState = {
  candidateSectionId: string | null;
  bloomSectionId: string | null;
  committedSectionId: string;
  commitVersion: number;
};

export type LivingBackgroundMachineState = {
  currentSectionId: string;
  currentBackgroundId: LivingBackgroundId;
  nextBackgroundId: LivingBackgroundId | null;
  previewBackgroundId: LivingBackgroundId | null;
  previousBackgroundId: LivingBackgroundId | null;
  pendingSectionId: string | null;
  committedSectionId: string;
  isTransitioning: boolean;
  phase: LivingBackgroundPhase;
  reducedMotion: boolean;
};
