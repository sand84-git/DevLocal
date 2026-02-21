import { useEffect, useRef } from "react";
import { useAppStore } from "../store/useAppStore";
import type {
  NodeUpdateData,
  KoReviewReadyData,
  FinalReviewReadyData,
  KoReviewChunkData,
  TranslationChunkData,
  ReviewChunkData,
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

    /* ── 노드 수준 업데이트 ── */
    es.addEventListener("node_update", (e) => {
      const data: NodeUpdateData = JSON.parse(e.data);
      const s = store();
      s.setLogs(data.logs);

      if (data.step === "loading") {
        // Loading phase — 고정 진행률
        const loadingMap: Record<string, [number, string]> = {
          data_backup: [10, "Backing up data..."],
          context_glossary: [25, "Preparing glossary & context..."],
          ko_review: [50, "Reviewing Korean text..."],
        };
        const p = loadingMap[data.node];
        if (p) s.setProgress(p[0], p[1]);
      } else if (data.step === "translating") {
        // Translating phase — 라벨만 업데이트 (진행률은 chunk 이벤트가 담당)
        const labelMap: Record<string, string> = {
          translator: "Translator Agent working...",
          reviewer: "Reviewer Agent checking quality...",
          should_retry: "Retrying failed translations...",
        };
        const label = labelMap[data.node];
        if (label) {
          // reviewer 시작 시 최소 60% 보장 (translator 완료 의미)
          if (data.node === "reviewer") {
            s.setProgress(Math.max(s.progressPercent, 60), label);
          } else if (data.node === "should_retry") {
            s.setProgress(Math.max(s.progressPercent, 85), label);
          } else {
            s.setProgress(s.progressPercent, label);
          }
        }
      }
    });

    /* ── 원본 데이터 수신 (Loading 화면 테이블용) ── */
    es.addEventListener("original_data", (e) => {
      const data = JSON.parse(e.data);
      store().setOriginalRows(data.rows);
    });

    /* ── 한국어 검수 — 청크별 부분 결과 ── */
    es.addEventListener("ko_review_chunk", (e) => {
      const data: KoReviewChunkData = JSON.parse(e.data);
      const s = store();
      s.appendPartialKoResults(data.chunk_results);
      s.setChunkProgress(data.progress);
      const pct = Math.round(
        (data.progress.done / data.progress.total) * 100,
      );
      s.setProgress(
        pct,
        `Reviewing Korean... (${data.progress.done}/${data.progress.total})`,
      );
    });

    /* ── 번역 — 청크별 부분 결과 (전체의 0% → 60%) ── */
    es.addEventListener("translation_chunk", (e) => {
      const data: TranslationChunkData = JSON.parse(e.data);
      const s = store();
      s.appendPartialTranslations(data.chunk_results);
      s.setChunkProgress(data.progress);
      const rawPct = data.progress.done / data.progress.total;
      const scaledPct = Math.round(rawPct * 60); // 0-60% 범위
      const lang = data.progress.lang?.toUpperCase() ?? "";
      s.setProgress(
        scaledPct,
        `Translator Agent — ${lang} (${data.progress.done}/${data.progress.total})`,
      );
    });

    /* ── 검수 — 청크별 부분 결과 (전체의 60% → 95%) ── */
    es.addEventListener("review_chunk", (e) => {
      const data: ReviewChunkData = JSON.parse(e.data);
      const s = store();
      s.appendPartialReviews(data.chunk_results);
      s.setChunkProgress(data.progress);
      const rawPct = data.progress.total > 0
        ? data.progress.done / data.progress.total
        : 0;
      const scaledPct = 60 + Math.round(rawPct * 35); // 60-95% 범위
      s.setProgress(
        scaledPct,
        `Reviewer Agent — checking (${data.progress.done}/${data.progress.total})`,
      );
    });

    /* ── 한국어 검수 완료 → 항상 리뷰 화면 표시 (0건이어도 컨펌 필요) ── */
    es.addEventListener("ko_review_ready", (e) => {
      const data: KoReviewReadyData = JSON.parse(e.data);
      const s = store();
      s.setKoReviewResults(data.results);
      s.setTotalRows(data.count);
      s.setProgress(100, "Korean review complete");
      setTimeout(() => s.setCurrentStep("ko_review"), 1500);
    });

    /* ── 번역 검수 완료 → 600ms dwell 후 화면 전환 ── */
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
      setTimeout(() => s.setCurrentStep("final_review"), 600);
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
