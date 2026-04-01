import type { CSSProperties } from "react";
import { livingDepthCommitmentConfig, getLivingDepthBackground } from "./livingBackgroundConfig";
import { useLivingBackgroundStateMachine } from "./useLivingBackgroundStateMachine";
import { useLivingDepthCommitment } from "./useLivingDepthCommitment";

type LivingBackgroundSystemProps = {
  routeSectionId: string;
};

type BackgroundLayerProps = {
  backgroundId: ReturnType<typeof getLivingDepthBackground>["id"];
  role: "previous" | "current" | "preview" | "next";
};

function BackgroundLayer({ backgroundId, role }: BackgroundLayerProps) {
  const background = getLivingDepthBackground(backgroundId);
  const preload = role === "preview" ? "metadata" : "auto";

  return (
    <div
      key={`${role}-${background.id}`}
      className={`living-depth-system__layer living-depth-system__layer--${role}`}
      data-background-id={background.id}
      data-depth-index={background.depthIndex}
    >
      <video
        className="living-depth-system__video"
        autoPlay
        muted
        loop
        playsInline
        preload={preload}
      >
        <source src={background.webmSrc} type="video/webm" />
        <source src={background.mp4Src} type="video/mp4" />
      </video>
    </div>
  );
}

export function LivingBackgroundSystem({ routeSectionId }: LivingBackgroundSystemProps) {
  const commitment = useLivingDepthCommitment(routeSectionId);
  const backgroundState = useLivingBackgroundStateMachine(routeSectionId, commitment);
  const renderLayers: Array<{ backgroundId: BackgroundLayerProps["backgroundId"]; role: BackgroundLayerProps["role"] }> =
    [];

  if (
    backgroundState.previousBackgroundId &&
    backgroundState.previousBackgroundId !== backgroundState.currentBackgroundId
  ) {
    renderLayers.push({
      backgroundId: backgroundState.previousBackgroundId,
      role: "previous",
    });
  }

  renderLayers.push({
    backgroundId: backgroundState.currentBackgroundId,
    role: "current",
  });

  if (
    backgroundState.previewBackgroundId &&
    backgroundState.previewBackgroundId !== backgroundState.currentBackgroundId &&
    backgroundState.previewBackgroundId !== backgroundState.nextBackgroundId &&
    backgroundState.previewBackgroundId !== backgroundState.previousBackgroundId
  ) {
    renderLayers.push({
      backgroundId: backgroundState.previewBackgroundId,
      role: "preview",
    });
  }

  if (
    backgroundState.nextBackgroundId &&
    backgroundState.nextBackgroundId !== backgroundState.currentBackgroundId
  ) {
    renderLayers.push({
      backgroundId: backgroundState.nextBackgroundId,
      role: "next",
    });
  }

  const style = {
    "--living-depth-transition-ms": `${
      backgroundState.reducedMotion
        ? livingDepthCommitmentConfig.reducedMotionTransitionMs
        : livingDepthCommitmentConfig.transitionMs
    }ms`,
    "--living-depth-stabilization-ms": `${
      backgroundState.reducedMotion
        ? livingDepthCommitmentConfig.reducedMotionStabilizationMs
        : livingDepthCommitmentConfig.stabilizationMs
    }ms`,
    "--living-depth-memory-ms": `${
      backgroundState.reducedMotion
        ? livingDepthCommitmentConfig.reducedMotionMemoryFadeMs
        : livingDepthCommitmentConfig.memoryFadeMs
    }ms`,
  } as CSSProperties;

  return (
    <div
      aria-hidden="true"
      className="living-depth-system"
      data-phase={backgroundState.phase}
      data-reduced-motion={backgroundState.reducedMotion ? "true" : "false"}
      data-has-preview={backgroundState.previewBackgroundId ? "true" : "false"}
      data-is-transitioning={backgroundState.isTransitioning ? "true" : "false"}
      style={style}
    >
      <div className="living-depth-system__fallback" />
      {renderLayers.map((layer) => (
        <BackgroundLayer
          key={`${layer.role}-${layer.backgroundId}`}
          backgroundId={layer.backgroundId}
          role={layer.role}
        />
      ))}
      <div className="living-depth-system__memory" />
      <div className="living-depth-system__bloom" />
      <div className="living-depth-system__veil" />
      <div className="living-depth-system__grain" />
    </div>
  );
}
