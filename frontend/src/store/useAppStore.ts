import { create } from "zustand";
import type {
  AppStep,
  KoReviewItem,
  ReviewItem,
  FailedRow,
  CostSummary,
  OriginalRow,
  TranslationChunkItem,
  ChunkProgress,
} from "../types";

interface AppState {
  /* ── Connection ── */
  sheetUrl: string;
  sheetNames: string[];
  botEmail: string;
  selectedSheet: string;
  mode: "A" | "B";
  rowLimit: number;

  /* ── Session ── */
  sessionId: string | null;
  currentStep: AppStep;
  previousStep: AppStep | null;

  /* ── KR Review (HITL 1) ── */
  koReviewResults: KoReviewItem[];
  koDecisions: Record<string, "accepted" | "rejected">;

  /* ── Translation / Review (HITL 2) ── */
  reviewResults: ReviewItem[];
  reviewDecisions: Record<string, "accepted" | "rejected">;
  failedRows: FailedRow[];
  selectedLang: string;
  reviewPage: number;

  /* ── Chunk Streaming (실시간 진행) ── */
  originalRows: OriginalRow[];
  partialKoResults: KoReviewItem[];
  partialTranslations: TranslationChunkItem[];
  partialReviews: ReviewItem[];
  chunkProgress: ChunkProgress | null;

  /* ── Metrics ── */
  costSummary: CostSummary | null;
  totalRows: number;
  cellsUpdated: number;

  /* ── Logs ── */
  logs: string[];
  progressPercent: number;
  progressLabel: string;

  /* ── Done ── */
  translationsApplied: boolean;

  /* ── Actions ── */
  setSheetUrl: (url: string) => void;
  setSheetNames: (names: string[]) => void;
  setBotEmail: (email: string) => void;
  setSelectedSheet: (name: string) => void;
  setMode: (mode: "A" | "B") => void;
  setRowLimit: (limit: number) => void;
  setSessionId: (id: string | null) => void;
  setCurrentStep: (step: AppStep) => void;
  setKoReviewResults: (results: KoReviewItem[]) => void;
  setKoDecision: (key: string, decision: "accepted" | "rejected") => void;
  setReviewResults: (results: ReviewItem[]) => void;
  setReviewDecision: (key: string, decision: "accepted" | "rejected") => void;
  setFailedRows: (rows: FailedRow[]) => void;
  setSelectedLang: (lang: string) => void;
  setReviewPage: (page: number) => void;
  setOriginalRows: (rows: OriginalRow[]) => void;
  appendPartialKoResults: (results: KoReviewItem[]) => void;
  appendPartialTranslations: (results: TranslationChunkItem[]) => void;
  appendPartialReviews: (results: ReviewItem[]) => void;
  setChunkProgress: (progress: ChunkProgress | null) => void;
  setCostSummary: (cost: CostSummary | null) => void;
  setTotalRows: (n: number) => void;
  setCellsUpdated: (n: number) => void;
  addLog: (log: string) => void;
  setLogs: (logs: string[]) => void;
  setProgress: (percent: number, label: string) => void;
  setTranslationsApplied: (applied: boolean) => void;
  reset: () => void;
}

const initialState = {
  sheetUrl: "",
  sheetNames: [] as string[],
  botEmail: "",
  selectedSheet: "",
  mode: "A" as const,
  rowLimit: 0,
  sessionId: null as string | null,
  currentStep: "idle" as AppStep,
  previousStep: null as AppStep | null,
  koReviewResults: [] as KoReviewItem[],
  koDecisions: {} as Record<string, "accepted" | "rejected">,
  reviewResults: [] as ReviewItem[],
  reviewDecisions: {} as Record<string, "accepted" | "rejected">,
  failedRows: [] as FailedRow[],
  selectedLang: "en",
  reviewPage: 1,
  originalRows: [] as OriginalRow[],
  partialKoResults: [] as KoReviewItem[],
  partialTranslations: [] as TranslationChunkItem[],
  partialReviews: [] as ReviewItem[],
  chunkProgress: null as ChunkProgress | null,
  costSummary: null as CostSummary | null,
  totalRows: 0,
  cellsUpdated: 0,
  logs: [] as string[],
  progressPercent: 0,
  progressLabel: "",
  translationsApplied: false,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  setSheetUrl: (url) => set({ sheetUrl: url }),
  setSheetNames: (names) => set({ sheetNames: names }),
  setBotEmail: (email) => set({ botEmail: email }),
  setSelectedSheet: (name) => set({ selectedSheet: name }),
  setMode: (mode) => set({ mode }),
  setRowLimit: (limit) => set({ rowLimit: limit }),
  setSessionId: (id) => set({ sessionId: id }),
  setCurrentStep: (step) =>
    set((s) => ({ currentStep: step, previousStep: s.currentStep })),
  setKoReviewResults: (results) => set({ koReviewResults: results }),
  setKoDecision: (key, decision) =>
    set((s) => ({ koDecisions: { ...s.koDecisions, [key]: decision } })),
  setReviewResults: (results) => set({ reviewResults: results }),
  setReviewDecision: (key, decision) =>
    set((s) => ({
      reviewDecisions: { ...s.reviewDecisions, [key]: decision },
    })),
  setFailedRows: (rows) => set({ failedRows: rows }),
  setSelectedLang: (lang) => set({ selectedLang: lang }),
  setReviewPage: (page) => set({ reviewPage: page }),
  setOriginalRows: (rows) => set({ originalRows: rows }),
  appendPartialKoResults: (results) =>
    set((s) => ({ partialKoResults: [...s.partialKoResults, ...results] })),
  appendPartialTranslations: (results) =>
    set((s) => ({ partialTranslations: [...s.partialTranslations, ...results] })),
  appendPartialReviews: (results) =>
    set((s) => ({ partialReviews: [...s.partialReviews, ...results] })),
  setChunkProgress: (progress) => set({ chunkProgress: progress }),
  setCostSummary: (cost) => set({ costSummary: cost }),
  setTotalRows: (n) => set({ totalRows: n }),
  setCellsUpdated: (n) => set({ cellsUpdated: n }),
  addLog: (log) => set((s) => ({ logs: [...s.logs, log] })),
  setLogs: (logs) => set({ logs }),
  setProgress: (percent, label) =>
    set({ progressPercent: percent, progressLabel: label }),
  setTranslationsApplied: (applied) => set({ translationsApplied: applied }),
  reset: () => set(initialState),
}));
