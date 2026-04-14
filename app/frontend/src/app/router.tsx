import { createBrowserRouter, Navigate } from "react-router-dom";
import { routes } from "../shared/constants/routes";
import { WelcomePage } from "../pages/WelcomePage";
import { WelcomeClassicPage } from "../pages/WelcomeClassicPage";
import { AppShell } from "../widgets/AppShell";
import { RouteErrorScreen } from "./RouteErrorScreen";

function lazyPage<T extends Record<string, unknown>>(load: () => Promise<T>, exportName: keyof T) {
  return async () => {
    const module = await load();
    return { Component: module[exportName] as React.ComponentType };
  };
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    errorElement: <RouteErrorScreen />,
    children: [
      { index: true, element: <Navigate to={routes.welcome} replace /> },
      { path: routes.welcome, element: <WelcomePage /> },
      { path: routes.welcomeClassic, element: <WelcomeClassicPage /> },
      { path: routes.liveAvatar, lazy: lazyPage(() => import("../pages/LiveAvatarPage"), "LiveAvatarPage") },
      { path: routes.onboarding, lazy: lazyPage(() => import("../pages/OnboardingPage"), "OnboardingPage") },
      { path: routes.dashboard, lazy: lazyPage(() => import("../pages/DashboardPage"), "DashboardPage") },
      { path: routes.dailyLoop, lazy: lazyPage(() => import("../pages/DailyLoopPage"), "DailyLoopPage") },
      { path: routes.activity, lazy: lazyPage(() => import("../pages/ActivityPage"), "ActivityPage") },
      { path: routes.vocabulary, lazy: lazyPage(() => import("../pages/VocabularyPage"), "VocabularyPage") },
      { path: routes.lessonRunner, lazy: lazyPage(() => import("../pages/LessonRunnerPage"), "LessonRunnerPage") },
      { path: routes.lessonResults, lazy: lazyPage(() => import("../pages/LessonResultsPage"), "LessonResultsPage") },
      { path: routes.grammar, lazy: lazyPage(() => import("../pages/GrammarPage"), "GrammarPage") },
      { path: routes.speaking, lazy: lazyPage(() => import("../pages/SpeakingPage"), "SpeakingPage") },
      { path: routes.pronunciation, lazy: lazyPage(() => import("../pages/PronunciationPage"), "PronunciationPage") },
      { path: routes.writing, lazy: lazyPage(() => import("../pages/WritingPage"), "WritingPage") },
      { path: routes.profession, lazy: lazyPage(() => import("../pages/ProfessionPage"), "ProfessionPage") },
      { path: routes.mistakes, lazy: lazyPage(() => import("../pages/MistakesPage"), "MistakesPage") },
      { path: routes.progress, lazy: lazyPage(() => import("../pages/ProgressPage"), "ProgressPage") },
      { path: routes.settings, lazy: lazyPage(() => import("../pages/SettingsPage"), "SettingsPage") },
    ],
  },
]);
