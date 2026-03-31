import { createBrowserRouter, Navigate } from "react-router-dom";
import { ActivityPage } from "../pages/ActivityPage";
import { DashboardPage } from "../pages/DashboardPage";
import { GrammarPage } from "../pages/GrammarPage";
import { LessonRunnerPage } from "../pages/LessonRunnerPage";
import { LessonResultsPage } from "../pages/LessonResultsPage";
import { MistakesPage } from "../pages/MistakesPage";
import { OnboardingPage } from "../pages/OnboardingPage";
import { ProfessionPage } from "../pages/ProfessionPage";
import { ProgressPage } from "../pages/ProgressPage";
import { PronunciationPage } from "../pages/PronunciationPage";
import { SettingsPage } from "../pages/SettingsPage";
import { SpeakingPage } from "../pages/SpeakingPage";
import { VocabularyPage } from "../pages/VocabularyPage";
import { WelcomePage } from "../pages/WelcomePage";
import { WritingPage } from "../pages/WritingPage";
import { routes } from "../shared/constants/routes";
import { AppShell } from "../widgets/AppShell";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to={routes.welcome} replace /> },
      { path: routes.welcome, element: <WelcomePage /> },
      { path: routes.onboarding, element: <OnboardingPage /> },
      { path: routes.dashboard, element: <DashboardPage /> },
      { path: routes.activity, element: <ActivityPage /> },
      { path: routes.vocabulary, element: <VocabularyPage /> },
      { path: routes.lessonRunner, element: <LessonRunnerPage /> },
      { path: routes.lessonResults, element: <LessonResultsPage /> },
      { path: routes.grammar, element: <GrammarPage /> },
      { path: routes.speaking, element: <SpeakingPage /> },
      { path: routes.pronunciation, element: <PronunciationPage /> },
      { path: routes.writing, element: <WritingPage /> },
      { path: routes.profession, element: <ProfessionPage /> },
      { path: routes.mistakes, element: <MistakesPage /> },
      { path: routes.progress, element: <ProgressPage /> },
      { path: routes.settings, element: <SettingsPage /> },
    ],
  },
]);
