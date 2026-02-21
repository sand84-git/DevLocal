import { useEffect, useRef } from "react";
import { useAppStore } from "../store/useAppStore";
import type {
  NodeUpdateData,
  KoReviewReadyData,
  FinalReviewReadyData,
} from "../types";

// LLM pricing (config/constants.py와 동일)
const LLM_PRICING = { input: 0.2 / 1_000_000, output: 0.5 / 1_000_000 };

/**
 * SSE 스트림 훅 — sessionId가 설정되면 연결, 전체 파이프라인 동안 유지
 * App.tsx 레벨에서 호출하여 화면 전환에도 연결이 유지되도록 함
 */
export function useSSE() {
  const sessionId = useAppStore((s) => s.sessionId);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const es = new EventSource(`/api/stream/${sessionId}`);
    esRef.current = es;
    const store = useAppStore.getState;

    es.addEventListener("node_update", (e) => {
      const data: NodeUpdateData = JSON.parse(e.data);
      const { setLogs, setProgress } = store();
      setLogs(data.logs);

      // 노드별 프로그레스 매핑 (loading phase + translating phase)
      const progressMap: Record<string, [number, string]> = {
        data_backup: [10, "Backing up data..."],
        context_glossary: [25, "Preparing glossary & context..."],
        ko_review: [50, "Reviewing Korean text..."],
        translator: [40, "Translating..."],
        reviewer: [70, "Reviewing translations..."],
        should_retry: [85, "Retrying failed translations..."],
      };
      const progress = progressMap[data.node];
      if (progress) {
        setProgress(progress[0], progress[1]);
      }
    });

    es.addEventListener("ko_review_ready", (e) => {
      const data: KoReviewReadyData = JSON.parse(e.data);
      const s = store();
      s.setKoReviewResults(data.results);
      s.setTotalRows(data.count);
      s.setProgress(100, "Korean review complete");
      s.setCurrentStep("ko_review");
    });

    es.addEventListener("final_review_ready", (e) => {
      const data: FinalReviewReadyData = JSON.parse(e.data);
      const s = store();
      s.setReviewResults(data.review_results);
      s.setFailedRows(data.failed_rows);
      if (data.cost) {
        const cost =
          data.cost.input_tokens * LLM_PRICING.input +
          data.cost.output_tokens * LLM_PRICING.output;
        s.setCostSummary({
          input_tokens: data.cost.input_tokens,
          output_tokens: data.cost.output_tokens,
          estimated_cost_usd: Math.round(cost * 10000) / 10000,
        });
      }
      s.setProgress(100, "Translation complete");
      s.setCurrentStep("final_review");
    });

    es.addEventListener("done", () => {
      store().setCurrentStep("done");
      es.close();
    });

    es.addEventListener("error", (e) => {
      if (e instanceof MessageEvent) {
        try {
          const data = JSON.parse(e.data);
          store().addLog(`[ERROR] ${data.message}`);
        } catch {
          // non-JSON error event
        }
      }
      es.close();
    });

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [sessionId]);

  return esRef;
}
