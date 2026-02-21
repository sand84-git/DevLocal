import { useEffect, useRef, useState } from "react";
import { useAppStore } from "./store/useAppStore";
import { useSSE } from "./hooks/useSSE";
import type { AppStep } from "./types";
import Header from "./components/Header";
import DataSourceScreen from "./screens/DataSourceScreen";
import LoadingScreen from "./screens/LoadingScreen";
import KoReviewScreen from "./screens/KoReviewScreen";
import TranslatingScreen from "./screens/TranslatingScreen";
import FinalReviewScreen from "./screens/FinalReviewScreen";
import DoneScreen from "./screens/DoneScreen";

function ScreenForStep({ step }: { step: AppStep }) {
  switch (step) {
    case "idle":
      return <DataSourceScreen />;
    case "loading":
      return <LoadingScreen />;
    case "ko_review":
      return <KoReviewScreen />;
    case "translating":
      return <TranslatingScreen />;
    case "final_review":
      return <FinalReviewScreen />;
    case "done":
      return <DoneScreen />;
    default:
      return <DataSourceScreen />;
  }
}

/**
 * 화면 전환 래퍼 — currentStep 변경 시:
 *  Phase 1 (exit):  현재 화면 fade-slide-left (400ms)
 *  Phase 2 (enter): 새 화면 fade-slide-right (400ms)
 */
function AnimatedScreen() {
  const currentStep = useAppStore((s) => s.currentStep);
  const [displayedStep, setDisplayedStep] = useState(currentStep);
  const [phase, setPhase] = useState<"idle" | "exit" | "enter">("idle");
  const prevStepRef = useRef(currentStep);

  useEffect(() => {
    if (currentStep === prevStepRef.current) return;
    prevStepRef.current = currentStep;

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
