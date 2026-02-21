import { useEffect, useRef, useState } from "react";
import { useAppStore } from "./store/useAppStore";
import { useSSE } from "./hooks/useSSE";
import type { AppStep } from "./types";
import Header from "./components/Header";
import DataSourceScreen from "./screens/DataSourceScreen";
import KoReviewWorkspace from "./screens/KoReviewWorkspace";
import TranslationWorkspace from "./screens/TranslationWorkspace";
import DoneScreen from "./screens/DoneScreen";

function ScreenForStep({ step }: { step: AppStep }) {
  switch (step) {
    case "idle":
      return <DataSourceScreen />;
    case "loading":
    case "ko_review":
      return <KoReviewWorkspace />;
    case "translating":
    case "final_review":
      return <TranslationWorkspace />;
    case "done":
      return <DoneScreen />;
    default:
      return <DataSourceScreen />;
  }
}

// 같은 통합 컴포넌트 내 step 그룹 — 그룹 내 전환은 슬라이드 스킵
const KO_REVIEW_STEPS = new Set<AppStep>(["loading", "ko_review"]);
const TRANSLATION_STEPS = new Set<AppStep>(["translating", "final_review"]);

/**
 * 화면 전환 래퍼 — currentStep 변경 시:
 *  Phase 1 (exit):  현재 화면 fade-slide-left (400ms)
 *  Phase 2 (enter): 새 화면 fade-slide-right (400ms)
 *  단, 같은 그룹(KO_REVIEW_STEPS / TRANSLATION_STEPS) 내 전환은 in-place 처리 (슬라이드 스킵)
 */
function AnimatedScreen() {
  const currentStep = useAppStore((s) => s.currentStep);
  const [displayedStep, setDisplayedStep] = useState(currentStep);
  const [phase, setPhase] = useState<"idle" | "exit" | "enter">("idle");
  const prevStepRef = useRef(currentStep);

  useEffect(() => {
    if (currentStep === prevStepRef.current) return;
    const prev = prevStepRef.current;
    prevStepRef.current = currentStep;

    // 같은 통합 컴포넌트 내 전환 — 슬라이드 스킵
    const sameGroup =
      (KO_REVIEW_STEPS.has(prev) && KO_REVIEW_STEPS.has(currentStep)) ||
      (TRANSLATION_STEPS.has(prev) && TRANSLATION_STEPS.has(currentStep));
    if (sameGroup) {
      setDisplayedStep(currentStep);
      return;
    }

    // Exit phase
    setPhase("exit");

    const exitTimer = setTimeout(() => {
      setDisplayedStep(currentStep);
      setPhase("enter");

      const enterTimer = setTimeout(() => {
        setPhase("idle");
      }, 400);

      return () => clearTimeout(enterTimer);
    }, 400);

    return () => clearTimeout(exitTimer);
  }, [currentStep]);

  const animClass =
    phase === "exit"
      ? "animate-fade-slide-left"
      : phase === "enter"
        ? "animate-fade-slide-right"
        : "";

  return (
    <div
      className={`flex flex-1 flex-col overflow-hidden ${animClass}`}
      style={{ willChange: phase !== "idle" ? "transform, opacity" : "auto" }}
    >
      <ScreenForStep step={displayedStep} />
    </div>
  );
}

export default function App() {
  // SSE를 App 레벨에서 유지 — 화면 전환에도 연결 유지
  useSSE();

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-bg-page font-display text-text-main antialiased">
      <Header />
      <AnimatedScreen />
    </div>
  );
}
