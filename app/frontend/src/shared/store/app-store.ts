import { create } from "zustand";
import { createLessonActions } from "./app-store-lesson";
import { createSessionActions } from "./app-store-session";
import { createInitialAppStoreState } from "./app-store.state";
import type { AppState } from "./app-store.types";

export const useAppStore = create<AppState>((set, get) => ({
  ...createInitialAppStoreState(),
  ...createSessionActions(set, get),
  ...createLessonActions(set, get),
}));

export type { AppState } from "./app-store.types";
