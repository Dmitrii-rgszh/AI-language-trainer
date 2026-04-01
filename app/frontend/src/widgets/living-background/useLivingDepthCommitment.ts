import { useEffect, useRef, useState } from "react";
import { livingDepthCommitmentConfig, resolveLivingDepthBackgroundId } from "./livingBackgroundConfig";
import type { LivingDepthCommitmentState } from "./livingBackgroundTypes";

type ObservedSection = {
  id: string;
  element: HTMLElement;
  fallback: boolean;
  visibility: number;
};

type SectionSnapshot = {
  id: string;
  fallback: boolean;
  ratio: number;
  score: number;
};

const SECTION_SELECTOR = "[data-living-depth-section]";

function computeVisibleRatio(element: HTMLElement) {
  const rect = element.getBoundingClientRect();
  const viewportHeight = window.innerHeight || 1;
  const visiblePx = Math.max(0, Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0));

  if (rect.height <= 0) {
    return 0;
  }

  return Math.max(0, Math.min(1, visiblePx / rect.height));
}

function computeSectionScore(element: HTMLElement, ratio: number, fallback: boolean) {
  const rect = element.getBoundingClientRect();
  const viewportHeight = window.innerHeight || 1;
  const center = rect.top + rect.height / 2;
  const centerOffset = Math.abs(center - viewportHeight / 2);
  const centeredness = 1 - Math.min(1, centerOffset / viewportHeight);
  const fallbackPenalty = fallback ? 0.24 : 0;

  return ratio * 0.72 + centeredness * 0.28 - fallbackPenalty;
}

function isFinePointerDevice() {
  return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
}

function collectSnapshots(sections: Map<string, ObservedSection>) {
  const snapshots: SectionSnapshot[] = [];

  for (const section of sections.values()) {
    if (!section.element.isConnected) {
      continue;
    }

    const ratio = Math.max(section.visibility, computeVisibleRatio(section.element));
    const score = computeSectionScore(section.element, ratio, section.fallback);

    if (ratio <= 0.01) {
      continue;
    }

    snapshots.push({
      id: section.id,
      fallback: section.fallback,
      ratio,
      score,
    });
  }

  return snapshots.sort((left, right) => right.score - left.score);
}

function selectCandidate(
  snapshots: SectionSnapshot[],
  routeSectionId: string,
) {
  if (snapshots.length === 0) {
    return null;
  }

  const prominentNonFallback = snapshots.find(
    (snapshot) =>
      !snapshot.fallback &&
      snapshot.ratio >= livingDepthCommitmentConfig.candidateVisibilityThreshold,
  );

  if (prominentNonFallback) {
    return prominentNonFallback;
  }

  const routeSnapshot = snapshots.find((snapshot) => snapshot.id === routeSectionId);
  return snapshots[0] ?? routeSnapshot ?? null;
}

export function useLivingDepthCommitment(routeSectionId: string) {
  const [state, setState] = useState<LivingDepthCommitmentState>({
    candidateSectionId: routeSectionId,
    bloomSectionId: null,
    committedSectionId: routeSectionId,
    commitVersion: 0,
  });

  const stateRef = useRef(state);
  const sectionsRef = useRef(new Map<string, ObservedSection>());
  const observerRef = useRef<IntersectionObserver | null>(null);
  const mutationObserverRef = useRef<MutationObserver | null>(null);
  const evaluateFrameRef = useRef<number | null>(null);
  const refreshFrameRef = useRef<number | null>(null);
  const routeCommitTimerRef = useRef<number | null>(null);
  const candidateSectionRef = useRef(routeSectionId);
  const committedSectionRef = useRef(routeSectionId);
  const candidateSinceRef = useRef(0);
  const lastScrollYRef = useRef(0);
  const lastScrollTimeRef = useRef(0);
  const lastScrollAtRef = useRef(0);
  const scrollVelocityRef = useRef(0);
  const lastPointerMoveAtRef = useRef(0);
  const lastPointerPositionRef = useRef<{ x: number; y: number } | null>(null);
  const finePointerRef = useRef(false);

  function publish(nextState: LivingDepthCommitmentState) {
    const currentState = stateRef.current;
    if (
      currentState.candidateSectionId === nextState.candidateSectionId &&
      currentState.bloomSectionId === nextState.bloomSectionId &&
      currentState.committedSectionId === nextState.committedSectionId &&
      currentState.commitVersion === nextState.commitVersion
    ) {
      return;
    }

    stateRef.current = nextState;
    setState(nextState);
  }

  function scheduleEvaluate() {
    if (evaluateFrameRef.current !== null) {
      return;
    }

    evaluateFrameRef.current = window.requestAnimationFrame(() => {
      evaluateFrameRef.current = null;

      const now = performance.now();
      const snapshots = collectSnapshots(sectionsRef.current);
      const candidate = selectCandidate(snapshots, routeSectionId);
      const nextCandidateId = candidate?.id ?? routeSectionId;

      if (nextCandidateId !== candidateSectionRef.current) {
        candidateSectionRef.current = nextCandidateId;
        candidateSinceRef.current = now;
      }

      const candidateBackgroundId = resolveLivingDepthBackgroundId(nextCandidateId);
      const committedBackgroundId = resolveLivingDepthBackgroundId(committedSectionRef.current);
      const timeSinceScroll = now - lastScrollAtRef.current;
      const decayedVelocity =
        timeSinceScroll > livingDepthCommitmentConfig.scrollSettleMs
          ? scrollVelocityRef.current *
            Math.max(
              0,
              1 - (timeSinceScroll - livingDepthCommitmentConfig.scrollSettleMs) / 320,
            )
          : scrollVelocityRef.current;
      const isFastScrolling =
        decayedVelocity >= livingDepthCommitmentConfig.fastScrollVelocityThreshold;
      const isScrollSettled =
        !isFastScrolling &&
        timeSinceScroll >= livingDepthCommitmentConfig.scrollSettleMs &&
        decayedVelocity <= livingDepthCommitmentConfig.scrollVelocityThreshold;
      const isPointerCalm =
        !finePointerRef.current ||
        now - lastPointerMoveAtRef.current >= livingDepthCommitmentConfig.desktopCursorIdleMs;
      const motionQualified = finePointerRef.current
        ? isScrollSettled && isPointerCalm
        : isScrollSettled &&
          timeSinceScroll >= livingDepthCommitmentConfig.mobilePostScrollStabilizationMs;
      const dwellMs = now - candidateSinceRef.current;
      const canBloom =
        candidate &&
        candidateBackgroundId !== committedBackgroundId &&
        candidate.ratio >= livingDepthCommitmentConfig.bloomVisibilityThreshold &&
        dwellMs >= livingDepthCommitmentConfig.bloomDelayMs &&
        !isFastScrolling;
      const canCommit =
        candidate &&
        candidateBackgroundId !== committedBackgroundId &&
        candidate.ratio >= livingDepthCommitmentConfig.commitVisibilityThreshold &&
        dwellMs >= livingDepthCommitmentConfig.dwellTimeMs &&
        motionQualified;

      if (canCommit && candidate && candidate.id !== committedSectionRef.current) {
        committedSectionRef.current = candidate.id;
        publish({
          candidateSectionId: nextCandidateId,
          bloomSectionId: null,
          committedSectionId: candidate.id,
          commitVersion: stateRef.current.commitVersion + 1,
        });
        return;
      }

      publish({
        candidateSectionId: nextCandidateId,
        bloomSectionId: canBloom && candidate ? candidate.id : null,
        committedSectionId: committedSectionRef.current,
        commitVersion: stateRef.current.commitVersion,
      });
    });
  }

  function refreshSections() {
    if (!observerRef.current) {
      return;
    }

    const nextSections = new Map<string, ObservedSection>();

    document.querySelectorAll<HTMLElement>(SECTION_SELECTOR).forEach((element) => {
      const id = element.dataset.livingDepthSection?.trim();
      if (!id) {
        return;
      }

      const fallback = element.dataset.livingDepthFallback === "true";
      const existing = sectionsRef.current.get(id);
      const tracked =
        existing && existing.element === element
          ? { ...existing, fallback }
          : {
              id,
              element,
              fallback,
              visibility: existing?.visibility ?? 0,
            };

      nextSections.set(id, tracked);

      if (!existing || existing.element !== element) {
        observerRef.current?.observe(element);
      }
    });

    for (const existing of sectionsRef.current.values()) {
      if (nextSections.get(existing.id)?.element !== existing.element) {
        observerRef.current?.unobserve(existing.element);
      }
    }

    sectionsRef.current = nextSections;
    scheduleEvaluate();
  }

  function scheduleRefresh() {
    if (refreshFrameRef.current !== null) {
      return;
    }

    refreshFrameRef.current = window.requestAnimationFrame(() => {
      refreshFrameRef.current = null;
      refreshSections();
    });
  }

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    finePointerRef.current = isFinePointerDevice();
    const now = performance.now();
    candidateSinceRef.current = now;
    lastScrollYRef.current = window.scrollY;
    lastScrollTimeRef.current = now;
    lastScrollAtRef.current = now;
    lastPointerMoveAtRef.current = now - livingDepthCommitmentConfig.desktopCursorIdleMs;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const element = entry.target as HTMLElement;
          const id = element.dataset.livingDepthSection?.trim();
          if (!id) {
            continue;
          }

          const existing = sectionsRef.current.get(id);
          if (existing) {
            existing.visibility = entry.intersectionRatio;
          }
        }

        scheduleEvaluate();
      },
      {
        threshold: [0, 0.08, 0.16, 0.24, 0.36, 0.48, 0.6, 0.72, 0.84, 1],
      },
    );

    mutationObserverRef.current = new MutationObserver(() => {
      scheduleRefresh();
    });
    mutationObserverRef.current.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["data-living-depth-section", "data-living-depth-fallback"],
    });

    const onScroll = () => {
      const timestamp = performance.now();
      const nextScrollY = window.scrollY;
      const deltaY = Math.abs(nextScrollY - lastScrollYRef.current);
      const deltaTime = Math.max(timestamp - lastScrollTimeRef.current, 16);

      scrollVelocityRef.current = deltaY / deltaTime;
      lastScrollYRef.current = nextScrollY;
      lastScrollTimeRef.current = timestamp;
      lastScrollAtRef.current = timestamp;
      scheduleEvaluate();
    };

    const onResize = () => {
      scheduleEvaluate();
    };

    const onPointerMove = (event: PointerEvent) => {
      if (!finePointerRef.current) {
        return;
      }

      const previousPosition = lastPointerPositionRef.current;
      lastPointerPositionRef.current = { x: event.clientX, y: event.clientY };

      if (!previousPosition) {
        return;
      }

      const distance = Math.hypot(
        event.clientX - previousPosition.x,
        event.clientY - previousPosition.y,
      );

      if (distance >= livingDepthCommitmentConfig.desktopPointerMovementThresholdPx) {
        lastPointerMoveAtRef.current = performance.now();
        scheduleEvaluate();
      }
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    scheduleRefresh();

    return () => {
      observerRef.current?.disconnect();
      mutationObserverRef.current?.disconnect();
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("pointermove", onPointerMove);

      if (evaluateFrameRef.current !== null) {
        window.cancelAnimationFrame(evaluateFrameRef.current);
      }
      if (refreshFrameRef.current !== null) {
        window.cancelAnimationFrame(refreshFrameRef.current);
      }
      if (routeCommitTimerRef.current !== null) {
        window.clearTimeout(routeCommitTimerRef.current);
      }
    };
  }, [routeSectionId]);

  useEffect(() => {
    const now = performance.now();
    candidateSectionRef.current = routeSectionId;
    committedSectionRef.current = stateRef.current.committedSectionId;
    candidateSinceRef.current = now;

    publish({
      candidateSectionId: routeSectionId,
      bloomSectionId: null,
      committedSectionId: stateRef.current.committedSectionId,
      commitVersion: stateRef.current.commitVersion,
    });

    if (routeCommitTimerRef.current !== null) {
      window.clearTimeout(routeCommitTimerRef.current);
    }

    routeCommitTimerRef.current = window.setTimeout(() => {
      if (committedSectionRef.current === routeSectionId) {
        publish({
          candidateSectionId: routeSectionId,
          bloomSectionId: null,
          committedSectionId: routeSectionId,
          commitVersion: stateRef.current.commitVersion,
        });
        return;
      }

      committedSectionRef.current = routeSectionId;
      publish({
        candidateSectionId: routeSectionId,
        bloomSectionId: null,
        committedSectionId: routeSectionId,
        commitVersion: stateRef.current.commitVersion + 1,
      });
    }, livingDepthCommitmentConfig.routeNavigationCommitDelayMs);

    scheduleRefresh();

    return () => {
      if (routeCommitTimerRef.current !== null) {
        window.clearTimeout(routeCommitTimerRef.current);
      }
    };
  }, [routeSectionId]);

  return state;
}
