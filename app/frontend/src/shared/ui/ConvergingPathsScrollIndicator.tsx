import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type RefObject,
} from "react";
import { cn } from "../utils/cn";
import "./converging-paths-scroll-indicator.css";

export type ConvergingPathsScrollIndicatorTimings = {
  separationHoldMs: number;
  convergenceMs: number;
  directionBirthMs: number;
  settleMs: number;
};

export const defaultConvergingPathsScrollIndicatorTimings: ConvergingPathsScrollIndicatorTimings = {
  separationHoldMs: 760,
  convergenceMs: 860,
  directionBirthMs: 460,
  settleMs: 820,
};

type ConvergingPathsScrollIndicatorProps = {
  activeMessageIndex?: number;
  ariaLabel?: string;
  className?: string;
  color?: string;
  height?: number;
  intensity?: number;
  label?: string;
  messages?: readonly string[];
  onActivate?: () => void;
  opacity?: number;
  targetId?: string;
  targetRef?: RefObject<HTMLElement | null>;
  timings?: Partial<ConvergingPathsScrollIndicatorTimings>;
  width?: number;
};

const LEFT_PATH = "M 11 11 C 18 11.5 24 15.5 29 22 C 32 25.4 34.1 29 35.2 33";
const RIGHT_PATH = "M 61 11 C 54 11.5 48 15.5 43 22 C 40 25.4 37.9 29 36.8 33";

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function formatPercentage(value: number) {
  return `${Math.min(100, Math.max(0, value)).toFixed(3)}%`;
}

function sanitizeAnimationToken(value: string) {
  return value.replace(/[^a-zA-Z0-9_-]/g, "");
}

function resolveScrollTarget(
  trigger: HTMLButtonElement | null,
  targetRef?: RefObject<HTMLElement | null>,
  targetId?: string,
) {
  if (targetRef?.current) {
    return targetRef.current;
  }

  if (targetId) {
    const targetById = document.getElementById(targetId);
    if (targetById) {
      return targetById;
    }
  }

  const currentSection = trigger?.closest("section");
  if (currentSection?.nextElementSibling instanceof HTMLElement) {
    return currentSection.nextElementSibling;
  }

  return null;
}

function buildKeyframes(
  token: string,
  width: number,
  height: number,
  intensity: number,
  timings: ConvergingPathsScrollIndicatorTimings,
) {
  const totalMs =
    timings.separationHoldMs +
    timings.convergenceMs +
    timings.directionBirthMs +
    timings.settleMs;
  const holdStop = (timings.separationHoldMs / totalMs) * 100;
  const convergenceStop =
    ((timings.separationHoldMs + timings.convergenceMs) / totalMs) * 100;
  const birthStop =
    ((timings.separationHoldMs + timings.convergenceMs + timings.directionBirthMs) / totalMs) *
    100;

  const spreadX = (width * (0.08 + intensity * 0.06)).toFixed(2);
  const settleX = (Number(spreadX) * 0.92).toFixed(2);
  const convergeDrop = (height * (0.02 + intensity * 0.025)).toFixed(2);
  const birthDrop = (height * (0.11 + intensity * 0.05)).toFixed(2);
  const inwardNudge = (width * (0.015 + intensity * 0.008)).toFixed(2);
  const holdDash = (18 + intensity * 6).toFixed(2);
  const convergeDash = (4 - intensity * 2).toFixed(2);
  const birthDash = (-8 - intensity * 4).toFixed(2);

  return `
    @keyframes ${token}-left-group {
      0%,
      ${formatPercentage(holdStop)} {
        transform: translate3d(-${spreadX}px, 0px, 0px);
        opacity: 0.32;
      }

      ${formatPercentage(convergenceStop)} {
        transform: translate3d(0px, ${convergeDrop}px, 0px);
        opacity: 0.74;
      }

      ${formatPercentage(birthStop)} {
        transform: translate3d(-${inwardNudge}px, ${birthDrop}px, 0px);
        opacity: 0.84;
      }

      100% {
        transform: translate3d(-${settleX}px, 0px, 0px);
        opacity: 0.32;
      }
    }

    @keyframes ${token}-right-group {
      0%,
      ${formatPercentage(holdStop)} {
        transform: translate3d(${spreadX}px, 0px, 0px);
        opacity: 0.32;
      }

      ${formatPercentage(convergenceStop)} {
        transform: translate3d(0px, ${convergeDrop}px, 0px);
        opacity: 0.74;
      }

      ${formatPercentage(birthStop)} {
        transform: translate3d(${inwardNudge}px, ${birthDrop}px, 0px);
        opacity: 0.84;
      }

      100% {
        transform: translate3d(${settleX}px, 0px, 0px);
        opacity: 0.32;
      }
    }

    @keyframes ${token}-trail {
      0%,
      ${formatPercentage(holdStop)} {
        stroke-dasharray: 18 72;
        stroke-dashoffset: ${holdDash};
      }

      ${formatPercentage(convergenceStop)} {
        stroke-dasharray: 34 56;
        stroke-dashoffset: ${convergeDash};
      }

      ${formatPercentage(birthStop)} {
        stroke-dasharray: 48 42;
        stroke-dashoffset: ${birthDash};
      }

      100% {
        stroke-dasharray: 18 72;
        stroke-dashoffset: ${holdDash};
      }
    }

    @keyframes ${token}-aura {
      0%,
      ${formatPercentage(holdStop)} {
        transform: scale3d(0.72, 0.86, 1);
        opacity: 0.06;
      }

      ${formatPercentage(convergenceStop)} {
        transform: scale3d(0.96, 1, 1);
        opacity: 0.16;
      }

      ${formatPercentage(birthStop)} {
        transform: scale3d(1.08, 1.04, 1);
        opacity: 0.22;
      }

      100% {
        transform: scale3d(0.76, 0.88, 1);
        opacity: 0.06;
      }
    }
  `;
}

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

export function ConvergingPathsScrollIndicator({
  activeMessageIndex = 0,
  ariaLabel,
  className,
  color,
  height = 36,
  intensity = 0.92,
  label,
  messages,
  onActivate,
  opacity = 0.9,
  targetId,
  targetRef,
  timings,
  width = 68,
}: ConvergingPathsScrollIndicatorProps) {
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const prefersReducedMotion = usePrefersReducedMotion();
  const animationToken = sanitizeAnimationToken(useId());
  const mergedTimings = {
    ...defaultConvergingPathsScrollIndicatorTimings,
    ...timings,
  };
  const cycleMs =
    mergedTimings.separationHoldMs +
    mergedTimings.convergenceMs +
    mergedTimings.directionBirthMs +
    mergedTimings.settleMs;
  const resolvedLabel =
    label ??
    messages?.[clamp(activeMessageIndex, 0, Math.max(0, (messages?.length ?? 1) - 1))] ??
    "";

  const keyframes = useMemo(
    () =>
      buildKeyframes(
        animationToken,
        width,
        height,
        clamp(intensity, 0.35, 1.2),
        mergedTimings,
      ),
    [animationToken, height, intensity, mergedTimings, width],
  );

  const rootStyle = {
    "--converging-scroll-width": width.toString(),
    "--converging-scroll-height": height.toString(),
    "--converging-scroll-opacity": opacity.toString(),
    "--converging-scroll-color": color ?? "rgba(29, 42, 56, 0.58)",
  } as CSSProperties;

  const sharedAnimationStyle = {
    animationDuration: `${cycleMs}ms`,
    animationIterationCount: "infinite",
    animationTimingFunction: "linear",
    animationFillMode: "both",
  } as CSSProperties;

  const handleActivate = () => {
    onActivate?.();

    const target = resolveScrollTarget(triggerRef.current, targetRef, targetId);
    if (!target) {
      return;
    }

    target.scrollIntoView({
      behavior: prefersReducedMotion ? "auto" : "smooth",
      block: "start",
    });
  };

  return (
    <button
      ref={triggerRef}
      type="button"
      className={cn("converging-scroll-indicator", className)}
      style={rootStyle}
      onClick={handleActivate}
      aria-label={ariaLabel ?? resolvedLabel}
      data-reduced-motion={prefersReducedMotion ? "true" : "false"}
    >
      <style>{keyframes}</style>

      <span className="converging-scroll-indicator__label">{resolvedLabel}</span>

      <span className="converging-scroll-indicator__stage" aria-hidden="true">
        <span
          className="converging-scroll-indicator__aura"
          style={{
            ...sharedAnimationStyle,
            animationName: `${animationToken}-aura`,
          }}
        />

        <svg
          className="converging-scroll-indicator__svg"
          viewBox="0 0 72 40"
          role="presentation"
          focusable="false"
        >
          <g
            className="converging-scroll-indicator__path-group"
            style={{
              ...sharedAnimationStyle,
              animationName: `${animationToken}-left-group`,
            }}
          >
            <path
              className="converging-scroll-indicator__path converging-scroll-indicator__path--echo"
              d={LEFT_PATH}
              style={{
                ...sharedAnimationStyle,
                animationName: `${animationToken}-trail`,
              }}
            />
            <path
              className="converging-scroll-indicator__path converging-scroll-indicator__path--core"
              d={LEFT_PATH}
              style={{
                ...sharedAnimationStyle,
                animationName: `${animationToken}-trail`,
              }}
            />
          </g>

          <g
            className="converging-scroll-indicator__path-group"
            style={{
              ...sharedAnimationStyle,
              animationName: `${animationToken}-right-group`,
            }}
          >
            <path
              className="converging-scroll-indicator__path converging-scroll-indicator__path--echo"
              d={RIGHT_PATH}
              style={{
                ...sharedAnimationStyle,
                animationName: `${animationToken}-trail`,
              }}
            />
            <path
              className="converging-scroll-indicator__path converging-scroll-indicator__path--core"
              d={RIGHT_PATH}
              style={{
                ...sharedAnimationStyle,
                animationName: `${animationToken}-trail`,
              }}
            />
          </g>
        </svg>
      </span>
    </button>
  );
}
