import { routes } from "./routes";

export const navigationItems = [
  { label: "Onboarding", to: routes.onboarding },
  { label: "Dashboard", to: routes.dashboard },
  { label: "Activity", to: routes.activity },
  { label: "Vocabulary", to: routes.vocabulary },
  { label: "Lesson Runner", to: routes.lessonRunner },
  { label: "Grammar", to: routes.grammar },
  { label: "Speaking", to: routes.speaking },
  { label: "Pronunciation", to: routes.pronunciation },
  { label: "Writing", to: routes.writing },
  { label: "Profession", to: routes.profession },
  { label: "My Mistakes", to: routes.mistakes },
  { label: "Progress", to: routes.progress },
  { label: "Settings", to: routes.settings },
] as const;
