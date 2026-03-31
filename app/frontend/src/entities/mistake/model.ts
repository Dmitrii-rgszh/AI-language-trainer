export type MistakeCategory =
  | "grammar"
  | "pronunciation"
  | "vocabulary"
  | "speaking"
  | "writing"
  | "profession";

export interface Mistake {
  id: string;
  category: MistakeCategory;
  subtype: string;
  sourceModule: string;
  originalText: string;
  correctedText: string;
  explanation: string;
  repetitionCount: number;
  lastSeenAt: string;
}

export interface WeakSpot {
  id: string;
  title: string;
  category: MistakeCategory;
  recommendation: string;
}
