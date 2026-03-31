export interface VocabularyItem {
  id: string;
  word: string;
  translation: string;
  context: string;
  category: string;
  sourceModule?: string;
  reviewReason?: string;
  learnedStatus: "new" | "active" | "mastered";
  repetitionStage: number;
}
