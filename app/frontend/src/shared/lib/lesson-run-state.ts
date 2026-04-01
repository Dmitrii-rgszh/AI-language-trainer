import type { Lesson, LessonRunState } from "../../entities/lesson/model";

export interface HydratedLessonRunState {
  lesson: Lesson;
  activeLessonRunId: string;
  selectedBlockIndex: number;
  blockResponses: Record<string, string>;
  blockScores: Record<string, number>;
}

export function hydrateLessonRunState(lessonRun: LessonRunState): HydratedLessonRunState {
  const blockResponses = Object.fromEntries(
    lessonRun.blockRuns
      .map((blockRun) => [blockRun.blockId, blockRun.userResponse ?? blockRun.transcript ?? ""])
      .filter((entry) => entry[1].trim().length > 0),
  );
  const blockScores = Object.fromEntries(
    lessonRun.blockRuns
      .filter((blockRun) => typeof blockRun.score === "number")
      .map((blockRun) => [blockRun.blockId, blockRun.score as number]),
  );
  const firstIncompleteIndex = lessonRun.lesson.blocks.findIndex((block) => {
    const blockRun = lessonRun.blockRuns.find((item) => item.blockId === block.id);
    return blockRun?.status !== "completed";
  });

  return {
    lesson: lessonRun.lesson,
    activeLessonRunId: lessonRun.runId,
    selectedBlockIndex: firstIncompleteIndex >= 0 ? firstIncompleteIndex : lessonRun.lesson.blocks.length - 1,
    blockResponses,
    blockScores,
  };
}
