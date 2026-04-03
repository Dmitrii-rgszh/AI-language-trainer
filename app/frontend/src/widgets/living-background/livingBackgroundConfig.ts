import { routes } from "../../shared/constants/routes";
import type { LivingBackgroundAsset, LivingBackgroundId, LivingDepthCommitmentConfig } from "./livingBackgroundTypes";

const LIVING_DEPTH_ASSET_BASE_PATH = "";

export const livingDepthBackgrounds: LivingBackgroundAsset[] = [
  {
    id: "background-1",
    webmSrc: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-1.webm`,
    mp4Src: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-1.mp4`,
    depthIndex: 1,
  },
  {
    id: "background-2",
    webmSrc: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-2.webm`,
    mp4Src: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-2.mp4`,
    depthIndex: 2,
  },
  {
    id: "background-3",
    webmSrc: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-3.webm`,
    mp4Src: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-3.mp4`,
    depthIndex: 3,
  },
  {
    id: "background-4",
    webmSrc: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-4.webm`,
    mp4Src: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-4.mp4`,
    depthIndex: 4,
  },
  {
    id: "background-5",
    webmSrc: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-5.webm`,
    mp4Src: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-5.mp4`,
    depthIndex: 5,
  },
  {
    id: "background-6",
    webmSrc: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-6.webm`,
    mp4Src: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-6.mp4`,
    depthIndex: 6,
  },
  {
    id: "background-7",
    webmSrc: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-7.webm`,
    mp4Src: `${LIVING_DEPTH_ASSET_BASE_PATH}/background-7.mp4`,
    depthIndex: 7,
  },
];

export const livingDepthSectionIds = {
  routeDefault: "route-default",
  routeWelcome: "route-welcome",
  routeOnboarding: "route-onboarding",
  routeDashboard: "route-dashboard",
  routeActivity: "route-activity",
  routeVocabulary: "route-vocabulary",
  routeLessonRunner: "route-lesson-runner",
  routeLessonResults: "route-lesson-results",
  routeGrammar: "route-grammar",
  routeSpeaking: "route-speaking",
  routePronunciation: "route-pronunciation",
  routeWriting: "route-writing",
  routeProfession: "route-profession",
  routeMistakes: "route-mistakes",
  routeProgress: "route-progress",
  routeSettings: "route-settings",
  dashboardHero: "dashboard-hero",
  dashboardRoadmap: "dashboard-roadmap",
  dashboardResume: "dashboard-resume",
  dashboardActions: "dashboard-actions",
  dashboardLoop: "dashboard-loop",
  dashboardSignals: "dashboard-signals",
  dashboardActivity: "dashboard-activity",
  progressDiagnostic: "progress-diagnostic",
  progressOverview: "progress-overview",
  progressPronunciation: "progress-pronunciation",
  progressHistory: "progress-history",
  progressSignals: "progress-signals",
  activityOverview: "activity-overview",
  activityLoop: "activity-loop",
  activitySignals: "activity-signals",
  activityHistory: "activity-history",
} as const;

const routeSectionByPath: Record<string, string> = {
  [routes.welcome]: livingDepthSectionIds.routeWelcome,
  [routes.welcomeClassic]: livingDepthSectionIds.routeWelcome,
  [routes.liveAvatar]: livingDepthSectionIds.routeWelcome,
  [routes.onboarding]: livingDepthSectionIds.routeOnboarding,
  [routes.dashboard]: livingDepthSectionIds.routeDashboard,
  [routes.activity]: livingDepthSectionIds.routeActivity,
  [routes.vocabulary]: livingDepthSectionIds.routeVocabulary,
  [routes.lessonRunner]: livingDepthSectionIds.routeLessonRunner,
  [routes.lessonResults]: livingDepthSectionIds.routeLessonResults,
  [routes.grammar]: livingDepthSectionIds.routeGrammar,
  [routes.speaking]: livingDepthSectionIds.routeSpeaking,
  [routes.pronunciation]: livingDepthSectionIds.routePronunciation,
  [routes.writing]: livingDepthSectionIds.routeWriting,
  [routes.profession]: livingDepthSectionIds.routeProfession,
  [routes.mistakes]: livingDepthSectionIds.routeMistakes,
  [routes.progress]: livingDepthSectionIds.routeProgress,
  [routes.settings]: livingDepthSectionIds.routeSettings,
};

export const livingDepthSectionBackgroundMap: Record<string, LivingBackgroundId> = {
  [livingDepthSectionIds.routeDefault]: "background-1",
  [livingDepthSectionIds.routeWelcome]: "background-1",
  [livingDepthSectionIds.routeOnboarding]: "background-2",
  [livingDepthSectionIds.routeDashboard]: "background-2",
  [livingDepthSectionIds.routeActivity]: "background-5",
  [livingDepthSectionIds.routeVocabulary]: "background-4",
  [livingDepthSectionIds.routeLessonRunner]: "background-7",
  [livingDepthSectionIds.routeLessonResults]: "background-7",
  [livingDepthSectionIds.routeGrammar]: "background-3",
  [livingDepthSectionIds.routeSpeaking]: "background-5",
  [livingDepthSectionIds.routePronunciation]: "background-6",
  [livingDepthSectionIds.routeWriting]: "background-7",
  [livingDepthSectionIds.routeProfession]: "background-7",
  [livingDepthSectionIds.routeMistakes]: "background-7",
  [livingDepthSectionIds.routeProgress]: "background-4",
  [livingDepthSectionIds.routeSettings]: "background-2",
  [livingDepthSectionIds.dashboardHero]: "background-2",
  [livingDepthSectionIds.dashboardRoadmap]: "background-3",
  [livingDepthSectionIds.dashboardResume]: "background-3",
  [livingDepthSectionIds.dashboardActions]: "background-4",
  [livingDepthSectionIds.dashboardLoop]: "background-5",
  [livingDepthSectionIds.dashboardSignals]: "background-6",
  [livingDepthSectionIds.dashboardActivity]: "background-7",
  [livingDepthSectionIds.progressDiagnostic]: "background-3",
  [livingDepthSectionIds.progressOverview]: "background-4",
  [livingDepthSectionIds.progressPronunciation]: "background-6",
  [livingDepthSectionIds.progressHistory]: "background-5",
  [livingDepthSectionIds.progressSignals]: "background-7",
  [livingDepthSectionIds.activityOverview]: "background-3",
  [livingDepthSectionIds.activityLoop]: "background-4",
  [livingDepthSectionIds.activitySignals]: "background-6",
  [livingDepthSectionIds.activityHistory]: "background-7",
};

export const livingDepthCommitmentConfig: LivingDepthCommitmentConfig = {
  candidateVisibilityThreshold: 0.22,
  bloomVisibilityThreshold: 0.42,
  commitVisibilityThreshold: 0.6,
  dwellTimeMs: 1600,
  bloomDelayMs: 260,
  scrollVelocityThreshold: 0.12,
  fastScrollVelocityThreshold: 0.85,
  scrollSettleMs: 180,
  desktopCursorIdleMs: 1000,
  desktopPointerMovementThresholdPx: 18,
  mobilePostScrollStabilizationMs: 260,
  cooldownMs: 900,
  routeNavigationCommitDelayMs: 260,
  transitionMs: 1500,
  stabilizationMs: 700,
  memoryFadeMs: 1900,
  reducedMotionTransitionMs: 260,
  reducedMotionStabilizationMs: 220,
  reducedMotionMemoryFadeMs: 320,
};

const livingDepthBackgroundById = new Map(livingDepthBackgrounds.map((background) => [background.id, background]));

export function getLivingDepthRouteSectionId(pathname: string) {
  return routeSectionByPath[pathname] ?? livingDepthSectionIds.routeDefault;
}

export function resolveLivingDepthBackgroundId(sectionId: string | null | undefined) {
  if (!sectionId) {
    return livingDepthSectionBackgroundMap[livingDepthSectionIds.routeDefault];
  }

  return (
    livingDepthSectionBackgroundMap[sectionId] ??
    livingDepthSectionBackgroundMap[livingDepthSectionIds.routeDefault]
  );
}

export function getLivingDepthBackground(backgroundId: LivingBackgroundId) {
  return livingDepthBackgroundById.get(backgroundId) ?? livingDepthBackgrounds[0];
}
