import type { Lesson } from "../../entities/lesson/model";

function normalizeText(value: string) {
  return value.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ");
}

function countKeywordMatches(responseText: string, keywords: string[]) {
  const normalizedResponse = normalizeText(responseText);
  return keywords.filter((keyword) => normalizedResponse.includes(normalizeText(keyword))).length;
}

type ListeningQuestionRule = {
  prompt: string;
  acceptableAnswers: string[];
};

function parseListeningQuestionRule(value: unknown): ListeningQuestionRule | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const prompt = "prompt" in value && typeof value.prompt === "string" ? value.prompt : null;
  const acceptableAnswers =
    "acceptable_answers" in value && Array.isArray(value.acceptable_answers)
      ? value.acceptable_answers.filter((item): item is string => typeof item === "string")
      : [];

  if (!prompt || acceptableAnswers.length === 0) {
    return null;
  }

  return { prompt, acceptableAnswers };
}

function extractListeningQuestionSets(block: Lesson["blocks"][number]) {
  const variants = Array.isArray(block.payload.audio_variants) ? block.payload.audio_variants : [];
  const parsedVariants = variants
    .map((variant) => {
      if (!variant || typeof variant !== "object") {
        return null;
      }

      const transcript = "transcript" in variant && typeof variant.transcript === "string" ? variant.transcript : null;
      const label = "label" in variant && typeof variant.label === "string" ? variant.label : "Audio variant";
      const questions =
        "questions" in variant && Array.isArray(variant.questions)
          ? variant.questions
              .map(parseListeningQuestionRule)
              .filter((item: ListeningQuestionRule | null): item is ListeningQuestionRule => item !== null)
          : [];

      if (!transcript || questions.length === 0) {
        return null;
      }

      return {
        label,
        transcript,
        questions,
      };
    })
    .filter(
      (
        item: { label: string; transcript: string; questions: ListeningQuestionRule[] } | null,
      ): item is { label: string; transcript: string; questions: ListeningQuestionRule[] } => item !== null,
    );

  if (parsedVariants.length > 0) {
    return parsedVariants;
  }

  const fallbackQuestions = Array.isArray(block.payload.questions)
    ? block.payload.questions
        .filter((item): item is string => typeof item === "string")
        .map((prompt) => ({ prompt, acceptableAnswers: [] as string[] }))
    : [];
  const fallbackAnswers = Array.isArray(block.payload.answer_key)
    ? block.payload.answer_key.filter((item): item is string => typeof item === "string")
    : Array.isArray(block.payload.answerKey)
      ? block.payload.answerKey.filter((item): item is string => typeof item === "string")
      : [];

  if (fallbackQuestions.length === 0 && fallbackAnswers.length === 0) {
    return [];
  }

  return [
    {
      label: "Primary audio",
      transcript: typeof block.payload.transcript === "string" ? block.payload.transcript : "",
      questions:
        fallbackQuestions.length > 0
          ? fallbackQuestions.map((question, index) => ({
              prompt: question.prompt,
              acceptableAnswers: fallbackAnswers[index] ? [fallbackAnswers[index]] : fallbackAnswers,
            }))
          : [{ prompt: "Listening answer", acceptableAnswers: fallbackAnswers }],
    },
  ];
}

function extractReadingQuestionSet(block: Lesson["blocks"][number]) {
  const questionRules = Array.isArray(block.payload.questions)
    ? block.payload.questions
        .map((item) => {
          if (typeof item === "string") {
            return { prompt: item, acceptableAnswers: [] as string[] };
          }
          return parseListeningQuestionRule(item);
        })
        .filter((item): item is ListeningQuestionRule => item !== null)
    : [];
  const fallbackAnswers = Array.isArray(block.payload.answer_key)
    ? block.payload.answer_key.filter((item): item is string => typeof item === "string")
    : Array.isArray(block.payload.answerKey)
      ? block.payload.answerKey.filter((item): item is string => typeof item === "string")
      : [];

  if (questionRules.length > 0) {
    return questionRules.map((question, index) => ({
      prompt: question.prompt,
      acceptableAnswers:
        question.acceptableAnswers.length > 0
          ? question.acceptableAnswers
          : fallbackAnswers[index]
            ? [fallbackAnswers[index]]
            : fallbackAnswers,
    }));
  }

  if (fallbackAnswers.length === 0) {
    return [];
  }

  return [{ prompt: "Reading answer", acceptableAnswers: fallbackAnswers }];
}

function scoreListeningResponse(
  block: Lesson["blocks"][number],
  responseText: string,
  transcriptRevealed: boolean,
  baseScore: number,
) {
  const variants = extractListeningQuestionSets(block);
  if (variants.length === 0) {
    return Math.max(25, Math.min(95, Math.round(baseScore - (transcriptRevealed ? 12 : 0))));
  }

  const bestCoverage = variants.reduce((best, variant) => {
    const matchedQuestions = variant.questions.filter((question) => {
      if (question.acceptableAnswers.length === 0) {
        return false;
      }
      return countKeywordMatches(responseText, question.acceptableAnswers) > 0;
    }).length;
    const coverage = matchedQuestions / variant.questions.length;
    return Math.max(best, coverage);
  }, 0);

  const coverageScore = 42 + bestCoverage * 48;
  const completenessBoost = responseText.trim().length > 0 ? Math.min(8, responseText.trim().split(/\s+/).length) : 0;
  const revealPenalty = transcriptRevealed ? 12 : 0;

  return Math.max(25, Math.min(95, Math.round(Math.max(baseScore - 8, coverageScore + completenessBoost) - revealPenalty)));
}

function scoreReadingResponse(block: Lesson["blocks"][number], responseText: string, baseScore: number) {
  const questionRules = extractReadingQuestionSet(block);
  if (questionRules.length === 0) {
    return Math.max(30, Math.min(95, Math.round(baseScore)));
  }

  const matchedQuestions = questionRules.filter((question) => {
    if (question.acceptableAnswers.length === 0) {
      return false;
    }
    return countKeywordMatches(responseText, question.acceptableAnswers) > 0;
  }).length;
  const coverage = matchedQuestions / questionRules.length;
  const coverageScore = 45 + coverage * 44;
  const completenessBoost = responseText.trim().length > 0 ? Math.min(10, responseText.trim().split(/\s+/).length) : 0;

  return Math.max(30, Math.min(95, Math.round(Math.max(baseScore - 4, coverageScore + completenessBoost))));
}

export function buildBlockScore(params: {
  lessonType: Lesson["lessonType"];
  block: Lesson["blocks"][number];
  responseText: string;
  explicitScore?: number;
  transcriptRevealed?: boolean;
}) {
  const { lessonType, block, responseText, explicitScore, transcriptRevealed = false } = params;
  if (typeof explicitScore === "number") {
    return explicitScore;
  }

  const trimmedResponse = responseText.trim();
  const wordCount = trimmedResponse.split(/\s+/).filter(Boolean).length;
  const baseScore = trimmedResponse.length === 0 ? 45 : Math.min(92, 52 + wordCount * 3);

  if (block.blockType === "listening_block") {
    return scoreListeningResponse(block, trimmedResponse, transcriptRevealed, baseScore);
  }
  if (block.blockType === "reading_block") {
    return scoreReadingResponse(block, trimmedResponse, baseScore);
  }

  if (lessonType !== "diagnostic") {
    return Math.max(55, baseScore);
  }
  if (block.blockType === "writing_block") {
    return Math.min(95, baseScore + 3);
  }
  return baseScore;
}
