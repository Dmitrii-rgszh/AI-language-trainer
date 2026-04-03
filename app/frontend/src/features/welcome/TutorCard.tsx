import type { ReactNode } from "react";
import { cn } from "../../shared/utils/cn";

type TutorCardProps = {
  label: string;
  message: string;
  replayAction?: ReactNode;
  status?: ReactNode;
  hint?: ReactNode;
  stageStatus?: ReactNode;
  avatarStage: ReactNode;
  isSpeaking?: boolean;
  className?: string;
  messageClassName?: string;
  avatarStageClassName?: string;
};

export function TutorCard({
  label,
  message,
  replayAction,
  status,
  hint,
  stageStatus,
  avatarStage,
  isSpeaking = false,
  className,
  messageClassName,
  avatarStageClassName,
}: TutorCardProps) {
  return (
    <div
      className={cn(
        "proof-lesson-tutor-card",
        isSpeaking && "proof-lesson-tutor-card--speaking",
        className,
      )}
    >
      <div className="proof-lesson-tutor-card__message-column">
        <div className="proof-lesson-tutor-card__identity-row">
          <div className="proof-lesson-tutor-card__name-badge">{label}</div>
        </div>

        <p className={cn("proof-lesson-tutor-card__utterance", messageClassName)}>
          {message}
        </p>

        {replayAction ? (
          <div className="proof-lesson-tutor-card__replay-row">{replayAction}</div>
        ) : null}

        {status || hint ? (
          <div className="proof-lesson-tutor-card__state-stack">
            {status ? <div className="proof-lesson-tutor-card__state-row">{status}</div> : null}
            {hint ? <div className="proof-lesson-tutor-card__hint">{hint}</div> : null}
          </div>
        ) : null}
      </div>

      <div
        className={cn(
          "proof-lesson-tutor-card__avatar-stage",
          avatarStageClassName,
        )}
      >
        <div className="proof-lesson-tutor-card__avatar-shell">
          {avatarStage}
          {stageStatus ? (
            <div className="proof-lesson-tutor-card__stage-status">
              {stageStatus}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
