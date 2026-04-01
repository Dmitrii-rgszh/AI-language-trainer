import { useEffect, useRef, useState, type MutableRefObject } from "react";
import {
  livingDepthCommitmentConfig,
  resolveLivingDepthBackgroundId,
} from "./livingBackgroundConfig";
import type {
  LivingBackgroundMachineState,
  LivingDepthCommitmentState,
} from "./livingBackgroundTypes";

function usePrefersReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updatePreference = () => {
      setPrefersReducedMotion(mediaQuery.matches);
    };

    updatePreference();
    mediaQuery.addEventListener("change", updatePreference);

    return () => {
      mediaQuery.removeEventListener("change", updatePreference);
    };
  }, []);

  return prefersReducedMotion;
}

export function useLivingBackgroundStateMachine(
  routeSectionId: string,
  commitment: LivingDepthCommitmentState,
) {
  const reducedMotion = usePrefersReducedMotion();
  const [state, setState] = useState<LivingBackgroundMachineState>(() => ({
    currentSectionId: routeSectionId,
    currentBackgroundId: resolveLivingDepthBackgroundId(routeSectionId),
    nextBackgroundId: null,
    previewBackgroundId: null,
    previousBackgroundId: null,
    pendingSectionId: null,
    committedSectionId: routeSectionId,
    isTransitioning: false,
    phase: "idle",
    reducedMotion: false,
  }));

  const stateRef = useRef(state);
  const cooldownUntilRef = useRef(0);
  const transitionStepTimerRef = useRef<number | null>(null);
  const settleTimerRef = useRef<number | null>(null);
  const memoryTimerRef = useRef<number | null>(null);
  const queuedSectionIdRef = useRef<string | null>(null);
  const processTimerRef = useRef<number | null>(null);

  function clearTimer(timerRef: MutableRefObject<number | null>) {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }

  function flushTransitionTimers() {
    clearTimer(transitionStepTimerRef);
    clearTimer(settleTimerRef);
    clearTimer(memoryTimerRef);
    clearTimer(processTimerRef);
  }

  function startTransition(sectionId: string) {
    const nextBackgroundId = resolveLivingDepthBackgroundId(sectionId);
    const previousBackgroundId = stateRef.current.currentBackgroundId;

    if (nextBackgroundId === previousBackgroundId) {
      setState((currentState) => {
        const nextState = {
          ...currentState,
          currentSectionId: sectionId,
          committedSectionId: sectionId,
          pendingSectionId: null,
          previewBackgroundId: null,
          phase: "idle" as const,
          reducedMotion,
        };
        stateRef.current = nextState;
        return nextState;
      });
      return;
    }

    flushTransitionTimers();

    setState((currentState) => {
      const nextState: LivingBackgroundMachineState = {
        ...currentState,
        nextBackgroundId,
        previewBackgroundId: nextBackgroundId,
        previousBackgroundId,
        pendingSectionId: sectionId,
        committedSectionId: sectionId,
        isTransitioning: true,
        phase: reducedMotion ? "stabilizing" : "transition",
        reducedMotion,
      };
      stateRef.current = nextState;
      return nextState;
    });

    const swapDelay = reducedMotion
      ? livingDepthCommitmentConfig.reducedMotionTransitionMs
      : livingDepthCommitmentConfig.transitionMs;
    const stabilizeDelay = reducedMotion
      ? livingDepthCommitmentConfig.reducedMotionStabilizationMs
      : livingDepthCommitmentConfig.stabilizationMs;
    const memoryDelay = reducedMotion
      ? livingDepthCommitmentConfig.reducedMotionMemoryFadeMs
      : livingDepthCommitmentConfig.memoryFadeMs;

    transitionStepTimerRef.current = window.setTimeout(() => {
      setState((currentState) => {
        const nextState: LivingBackgroundMachineState = {
          ...currentState,
          currentSectionId: sectionId,
          currentBackgroundId: nextBackgroundId,
          phase: "stabilizing",
          reducedMotion,
        };
        stateRef.current = nextState;
        return nextState;
      });
    }, swapDelay);

    settleTimerRef.current = window.setTimeout(() => {
      cooldownUntilRef.current = performance.now() + livingDepthCommitmentConfig.cooldownMs;
      setState((currentState) => {
        const nextState: LivingBackgroundMachineState = {
          ...currentState,
          nextBackgroundId: null,
          previewBackgroundId: null,
          pendingSectionId: null,
          isTransitioning: false,
          phase: "idle",
          reducedMotion,
        };
        stateRef.current = nextState;
        return nextState;
      });

      if (queuedSectionIdRef.current) {
        const queuedSectionId = queuedSectionIdRef.current;
        queuedSectionIdRef.current = null;
        processQueuedSection(queuedSectionId);
      }
    }, swapDelay + stabilizeDelay);

    memoryTimerRef.current = window.setTimeout(() => {
      setState((currentState) => {
        if (currentState.previousBackgroundId !== previousBackgroundId) {
          return currentState;
        }

        const nextState: LivingBackgroundMachineState = {
          ...currentState,
          previousBackgroundId: null,
          reducedMotion,
        };
        stateRef.current = nextState;
        return nextState;
      });
    }, swapDelay + memoryDelay);
  }

  function processQueuedSection(sectionId: string) {
    clearTimer(processTimerRef);

    if (stateRef.current.isTransitioning) {
      queuedSectionIdRef.current = sectionId;
      return;
    }

    const waitMs = Math.max(0, cooldownUntilRef.current - performance.now());
    if (waitMs > 0) {
      queuedSectionIdRef.current = sectionId;
      processTimerRef.current = window.setTimeout(() => {
        const queuedSectionId = queuedSectionIdRef.current;
        if (!queuedSectionId) {
          return;
        }

        queuedSectionIdRef.current = null;
        startTransition(queuedSectionId);
      }, waitMs);
      return;
    }

    startTransition(sectionId);
  }

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    setState((currentState) => {
      if (currentState.reducedMotion === reducedMotion) {
        return currentState;
      }

      const nextState = {
        ...currentState,
        reducedMotion,
      };
      stateRef.current = nextState;
      return nextState;
    });
  }, [reducedMotion]);

  useEffect(() => {
    if (stateRef.current.isTransitioning) {
      return;
    }

    const previewBackgroundId = resolveLivingDepthBackgroundId(commitment.bloomSectionId);
    const nextPreviewBackgroundId =
      commitment.bloomSectionId &&
      previewBackgroundId !== stateRef.current.currentBackgroundId
        ? previewBackgroundId
        : null;

    setState((currentState) => {
      const nextPhase = nextPreviewBackgroundId ? "bloom" : "idle";
      if (
        currentState.previewBackgroundId === nextPreviewBackgroundId &&
        currentState.pendingSectionId === commitment.bloomSectionId &&
        currentState.phase === nextPhase &&
        currentState.committedSectionId === commitment.committedSectionId
      ) {
        return currentState;
      }

      const nextState: LivingBackgroundMachineState = {
        ...currentState,
        previewBackgroundId: nextPreviewBackgroundId,
        pendingSectionId: commitment.bloomSectionId,
        committedSectionId: commitment.committedSectionId,
        phase: nextPhase,
        reducedMotion,
      };
      stateRef.current = nextState;
      return nextState;
    });
  }, [commitment.bloomSectionId, commitment.committedSectionId, reducedMotion, state.isTransitioning]);

  useEffect(() => {
    const targetSectionId = commitment.committedSectionId || routeSectionId;
    const targetBackgroundId = resolveLivingDepthBackgroundId(targetSectionId);

    if (targetBackgroundId === stateRef.current.currentBackgroundId) {
      setState((currentState) => {
        if (
          currentState.currentSectionId === targetSectionId &&
          currentState.committedSectionId === targetSectionId
        ) {
          return currentState;
        }

        const nextState: LivingBackgroundMachineState = {
          ...currentState,
          currentSectionId: targetSectionId,
          committedSectionId: targetSectionId,
          reducedMotion,
        };
        stateRef.current = nextState;
        return nextState;
      });
      return;
    }

    queuedSectionIdRef.current = targetSectionId;
    processQueuedSection(targetSectionId);
  }, [commitment.committedSectionId, commitment.commitVersion, routeSectionId, reducedMotion]);

  useEffect(() => {
    return () => {
      flushTransitionTimers();
    };
  }, []);

  return state;
}
