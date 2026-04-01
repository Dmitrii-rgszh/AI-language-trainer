import type { LessonBlock } from "../../entities/lesson/model";

export type ListeningVariant = {
  id?: string;
  label?: string;
  transcript?: string;
  questions?: Array<{ prompt?: string; acceptable_answers?: string[] }>;
};

export function getListeningVariants(block: LessonBlock): ListeningVariant[] {
  return Array.isArray(block.payload.audio_variants)
    ? block.payload.audio_variants.filter((item): item is ListeningVariant => Boolean(item && typeof item === "object"))
    : [];
}

export function getListeningBlockState(block: LessonBlock, selectedVariantIndex: number) {
  const listeningVariants = getListeningVariants(block);
  const selectedListeningVariant = listeningVariants[selectedVariantIndex] ?? listeningVariants[0] ?? null;
  const listeningTranscript =
    selectedListeningVariant && typeof selectedListeningVariant.transcript === "string"
      ? selectedListeningVariant.transcript
      : typeof block.payload.transcript === "string"
        ? block.payload.transcript
        : null;
  const listeningQuestions =
    selectedListeningVariant && Array.isArray(selectedListeningVariant.questions)
      ? selectedListeningVariant.questions
          .filter(
            (
              item,
            ): item is {
              prompt: string;
              acceptable_answers?: string[];
            } => Boolean(item && typeof item === "object" && typeof item.prompt === "string"),
          )
          .map((item) => item.prompt)
      : Array.isArray(block.payload.questions)
        ? block.payload.questions.filter((item): item is string => typeof item === "string")
        : [];

  return {
    listeningVariants,
    selectedListeningVariant,
    listeningTranscript,
    listeningQuestions,
  };
}

export function getPronunciationTargets(block: LessonBlock): string[] {
  return [
    ...((block.payload.phraseDrills as string[] | undefined) ?? []),
    ...((block.payload.phrase_drills as string[] | undefined) ?? []),
  ].filter(Boolean);
}
