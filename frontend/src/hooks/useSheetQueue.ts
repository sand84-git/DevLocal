import { useEffect, useRef } from "react";
import { useAppStore } from "../store/useAppStore";
import { startPipeline } from "../api/client";

/**
 * All Sheets 모드 시 시트 큐를 관리하는 훅.
 * 한 시트의 번역이 "done"에 도달하면 2초 후 다음 시트를 자동 시작.
 * App.tsx 레벨에서 호출.
 */
export function useSheetQueue() {
  const currentStep = useAppStore((s) => s.currentStep);
  const allSheetsMode = useAppStore((s) => s.allSheetsMode);
  const sheetQueue = useAppStore((s) => s.sheetQueue);
  const currentSheetIndex = useAppStore((s) => s.currentSheetIndex);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    if (currentStep !== "done" || !allSheetsMode) return;
    if (currentSheetIndex + 1 >= sheetQueue.length) return;

    timerRef.current = setTimeout(async () => {
      const s = useAppStore.getState();
      const nextSheet = sheetQueue[currentSheetIndex + 1];
      s.advanceSheetQueue();
      s.resetTranslationState();
      s.setCurrentStep("loading");

      try {
        const res = await startPipeline({
          sheet_url: s.sheetUrl,
          sheet_name: nextSheet,
          mode: s.mode,
          target_languages: ["en", "ja"],
          row_limit: 0,
        });
        s.setSessionId(res.session_id);
      } catch {
        s.setCurrentStep("idle");
        s.setAllSheetsMode(false);
      }
    }, 2000);

    return () => clearTimeout(timerRef.current);
  }, [currentStep, allSheetsMode, currentSheetIndex, sheetQueue]);
}
