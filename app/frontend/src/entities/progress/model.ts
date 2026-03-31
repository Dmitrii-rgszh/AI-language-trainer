export interface SkillProgress {
  label: string;
  score: number;
}

export interface LessonHistoryItem {
  id: string;
  title: string;
  lessonType: string;
  completedAt: string;
  score: number;
}

export interface ProgressSnapshot {
  id: string;
  grammarScore: number;
  speakingScore: number;
  listeningScore: number;
  pronunciationScore: number;
  writingScore: number;
  professionScore: number;
  regulationScore: number;
  streak: number;
  dailyGoalMinutes: number;
  minutesCompletedToday: number;
  history: LessonHistoryItem[];
}

