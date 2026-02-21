import { useEffect, useRef } from "react";
import { useAppStore } from "../store/useAppStore";
import type {
  NodeUpdateData,
  KoReviewReadyData,
  FinalReviewReadyData,
} from "../types";

/**
 * SSE 스트림 훅 — sessionId가 있으면 /api/stream/{sessionId}에 연결
 */
export function useSSE() {
  const sessionId = useAppStore((s) => s.sessionId);
  const currentStep = useAppStore((s) => s.currentStep);
  const setCurrentStep = useAppStore((s) => s.setCurrentStep);
  const setKoReviewResults = useAppStore((s) => s.setKoReviewResults);
  const setReviewResults = useAppStore((s) => s.setReviewResults);
  const setFailedRows = useAppStore((s) => s.setFailedRows);
  const setCostSummary = useAppStore((s) => s.setCostSummary);
  const addLog = useAppStore((s) => s.addLog);
  const setProgress = useAppStore((s) => s.setProgress);
  const setTotalRows = useAppStore((s) => s.setTotalRows);

  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!sessionId || currentStep !== "loading") return;

    const es = new EventSource(`/api/stream/${sessionId}`);
    esRef.current = es;

    es.addEventListener("node_update", (e) => {
      const data: NodeUpdateData = JSON.parse(e.data);
      for (const log of data.logs) {
        addLog(log);
      }

      // 노드별 프로그레스 매핑
      const nodeProgressMap: Record<string, [number, string]> = {
        data_backup: [10, "Backing up data..."],
        context_glossary: [25, "Preparing glossary & context..."],
        ko_review: [50, "Reviewing Korean text..."],
      };
      const progress = nodeProgressMap[data.node];
      if (progress) {
        setProgress(progress[0], progress[1]);
      }
    });

    es.addEventListener("ko_review_ready", (e) => {
      const data: KoReviewReadyData = JSON.parse(e.data);
      setKoReviewResults(data.results);
      setTotalRows(data.count);
      setProgress(100, "Korean review complete");
      setCurrentStep("ko_review");
    });

    es.addEventListener("final_review_ready", (e) => {
      const data: FinalReviewReadyData = JSON.parse(e.data);
      setReviewResults(data.review_results);
      setFailedRows(data.failed_rows);
      if (data.cost) {
        setCostSummary({
          input_tokens: data.cost.input_tokens,
          output_tokens: data.cost.output_tokens,
          estimated_cost_usd: 0,
        });
      }
      setProgress(100, "Translation complete");
      setCurrentStep("final_review");
    });

    es.addEventListener("done", () => {
      setCurrentStep("done");
      es.close();
    });

    es.addEventListener("error", (e) => {
      if (e instanceof MessageEvent) {
        const data = JSON.parse(e.data);
        addLog(`[ERROR] ${data.message}`);
      }
      es.close();
    });

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [
    sessionId,
    currentStep,
    setCurrentStep,
    setKoReviewResults,
    setReviewResults,
    setFailedRows,
    setCostSummary,
    addLog,
    setProgress,
    setTotalRows,
  ]);

  return esRef;
}
