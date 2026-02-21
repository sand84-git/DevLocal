import { useEffect, useMemo, useRef, useState } from "react";
import { useAppStore } from "../store/useAppStore";
import {
  cancelTranslation,
  approveFinal,
  getDownloadUrl,
} from "../api/client";
import { useCountUp } from "../hooks/useCountUp";
import { highlightDiff } from "../utils/diffHighlight";
import Footer from "../components/Footer";

const PAGE_SIZE = 10;

/**
 * 통합 번역 화면 — TranslatingScreen + FinalReviewScreen 합본.
 * currentStep 기반으로 mode를 결정하고, translating → review 전환 시
 * 페이지 이동 없이 in-place 트랜지션으로 처리.
 */
export default function TranslationWorkspace() {
  /* ── Store ── */
  const currentStep = useAppStore((s) => s.currentStep);
  const sessionId = useAppStore((s) => s.sessionId);
  const setCurrentStep = useAppStore((s) => s.setCurrentStep);
  const progressPercent = useAppStore((s) => s.progressPercent);
  const progressLabel = useAppStore((s) => s.progressLabel);
  const originalRows = useAppStore((s) => s.originalRows);
  const partialTranslations = useAppStore((s) => s.partialTranslations);
  const partialReviews = useAppStore((s) => s.partialReviews);
  const reviewResults = useAppStore((s) => s.reviewResults);
  const reviewDecisions = useAppStore((s) => s.reviewDecisions);
  const setReviewDecision = useAppStore((s) => s.setReviewDecision);
  const selectedLang = useAppStore((s) => s.selectedLang);
  const setSelectedLang = useAppStore((s) => s.setSelectedLang);
  const costSummary = useAppStore((s) => s.costSummary);
  const setTranslationsApplied = useAppStore((s) => s.setTranslationsApplied);
  const setCellsUpdated = useAppStore((s) => s.setCellsUpdated);

  /* ── Local State ── */
  const [page, setPage] = useState(1);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [expandedNote, setExpandedNote] = useState<string | null>(null);

  /* ── Mode & Transition ── */
  const mode = currentStep === "final_review" ? "review" : "translating";
  const prevModeRef = useRef(mode);
  const [transition, setTransition] = useState<
    "idle" | "exiting" | "entering"
  >("idle");

  useEffect(() => {
    if (prevModeRef.current === "translating" && mode === "review") {
      setPage(1);
      setExpandedNote(null);
      setTransition("exiting");
      const t1 = setTimeout(() => setTransition("entering"), 400);
      const t2 = setTimeout(() => setTransition("idle"), 800);
      prevModeRef.current = mode;
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
      };
    }
    prevModeRef.current = mode;
  }, [mode]);

  const showProgress = mode === "translating" || transition === "exiting";
  const showReviewHeader = mode === "review" && transition !== "exiting";

  /* ── Row drip-feed animation ── */
  const doneKeysRef = useRef(new Set<string>());

  /* ── Derived ── */
  const isComplete = progressPercent >= 100;
  const animPct = useCountUp(progressPercent, 500);

  const agentPhase: "init" | "translator" | "reviewer" | "complete" =
    isComplete
      ? "complete"
      : progressLabel.includes("Translator") ||
          progressLabel.includes("Retrying")
        ? "translator"
        : progressLabel.includes("Reviewer")
          ? "reviewer"
          : "init";

  const availableLangs = useMemo(() => {
    if (mode === "review") {
      return Array.from(new Set(reviewResults.map((r) => r.lang)));
    }
    const s = new Set<string>();
    for (const t of partialTranslations) s.add(t.lang);
    return Array.from(s).sort();
  }, [mode, reviewResults, partialTranslations]);

  const activeLang = availableLangs.includes(selectedLang)
    ? selectedLang
    : (availableLangs[0] ?? "en");

  useEffect(() => {
    if (activeLang !== selectedLang) setSelectedLang(activeLang);
  }, [activeLang, selectedLang, setSelectedLang]);

  const translationMap = useMemo(() => {
    const m = new Map<string, string>();
    for (const t of partialTranslations) {
      if (t.lang === activeLang) m.set(t.key, t.translated);
    }
    return m;
  }, [partialTranslations, activeLang]);

  const reviewMap = useMemo(() => {
    const m = new Map<string, { reason: string; old_translation: string }>();
    for (const r of partialReviews) {
      if (r.lang === activeLang)
        m.set(r.key, { reason: r.reason, old_translation: r.old_translation });
    }
    return m;
  }, [partialReviews, activeLang]);

  /* ── Unified Rows ── */
  type RowStatus = "translating" | "translated" | "reviewing" | "reviewed";

  const unifiedRows = useMemo(() => {
    if (mode === "review") {
      return reviewResults
        .filter((r) => r.lang === activeLang)
        .map((r) => ({
          key: r.key,
          lang: r.lang,
          original_ko: r.original_ko,
          old_translation: r.old_translation,
          translated: r.translated,
          reason: r.reason,
          isDone: true,
          hasChange: r.old_translation !== r.translated,
          rowStatus: "reviewed" as RowStatus,
        }));
    }
    return originalRows.map((row) => {
      const translated = translationMap.get(row.key);
      const review = reviewMap.get(row.key);
      const isDone = translated !== undefined;
      const hasReview = review !== undefined;
      const hasChange =
        isDone && review ? review.old_translation !== translated : false;

      let rowStatus: RowStatus;
      if (!isDone) {
        rowStatus =
          agentPhase === "reviewer" || agentPhase === "complete"
            ? "translated"
            : "translating";
      } else if (hasReview || agentPhase === "complete") {
        rowStatus = "reviewed";
      } else if (agentPhase === "reviewer") {
        rowStatus = "reviewing";
      } else {
        rowStatus = "translated";
      }

      return {
        key: row.key,
        lang: activeLang,
        original_ko: row.korean,
        old_translation: review?.old_translation ?? "",
        translated: translated ?? "",
        reason: review?.reason ?? "",
        isDone,
        hasChange,
        rowStatus,
      };
    });
  }, [mode, reviewResults, originalRows, translationMap, reviewMap, activeLang, agentPhase]);

  const totalPages = Math.max(1, Math.ceil(unifiedRows.length / PAGE_SIZE));
  const pageRows = unifiedRows.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE,
  );

  const changedCount = useMemo(
    () =>
      reviewResults.filter((r) => r.old_translation !== r.translated).length,
    [reviewResults],
  );
  const unchangedCount = reviewResults.length - changedCount;

  const barColor = isComplete ? "bg-emerald-500" : "bg-primary";
  const barShadow = isComplete
    ? "shadow-[0_0_12px_rgba(16,185,129,0.4)]"
    : "shadow-[0_0_12px_rgba(14,165,233,0.3)]";
  const pctColor = isComplete ? "text-emerald-500" : "text-primary";

  /* ── Handlers ── */
  async function handleCancel() {
    if (!sessionId) return;
    setCancelError(null);
    try {
      await cancelTranslation(sessionId);
      setCurrentStep("ko_review");
    } catch (e) {
      setCancelError(
        `Cancel failed: ${e instanceof Error ? e.message : "Unknown error"}`,
      );
    }
  }

  async function handleFinalApproval(decision: "approved" | "rejected") {
    if (!sessionId) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await approveFinal(sessionId, { decision });
      setTranslationsApplied(res.translations_applied ?? false);
      setCellsUpdated(res.updates_count ?? 0);
      setCurrentStep("done");
    } catch (e) {
      setSubmitError(
        `Final approval failed: ${e instanceof Error ? e.message : "Unknown error"}`,
      );
    } finally {
      setSubmitting(false);
    }
  }

  function handleApproveAllPage() {
    for (const row of pageRows) {
      const dk = `${row.key}_${row.lang}`;
      if (!reviewDecisions[dk]) setReviewDecision(dk, "accepted");
    }
  }

  const error = cancelError || submitError;

  /* ── Render ── */
  return (
    <>
      <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-32">
        <div
          className={`mx-auto space-y-6 transition-[max-width] duration-500 ${
            mode === "review" ? "max-w-[1400px]" : "max-w-5xl"
          }`}
        >
          {/* ═══ Progress Section (translating) ═══ */}
          {showProgress && (
            <div
              className={`space-y-4 ${transition === "exiting" ? "animate-section-fade-out" : ""}`}
            >
              <div className="text-center animate-fade-in">
                <h1 className="text-2xl font-bold text-text-main">
                  Translating...
                </h1>
                <p className="mt-2 text-sm text-text-muted">
                  AI is translating your content. This may take a few minutes.
                </p>
              </div>

              {/* Progress bar */}
              <section className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-soft animate-fade-slide-up">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-text-muted animate-breathe">
                    {progressLabel || "Initializing..."}
                  </span>
                  <span
                    className={`text-2xl font-bold tabular-nums ${pctColor}`}
                  >
                    {animPct}%
                  </span>
                </div>
                <div className="relative w-full overflow-hidden rounded-full bg-slate-100 h-3.5">
                  <div
                    className={`absolute top-0 left-0 h-full rounded-full transition-all duration-700 ease-out ${barColor} ${barShadow}`}
                    style={{ width: `${progressPercent}%` }}
                  />
                  {progressPercent > 0 && progressPercent < 100 && (
                    <div
                      className="absolute inset-0 animate-shimmer"
                      style={{
                        background:
                          "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.35) 50%, transparent 100%)",
                        width: `${progressPercent}%`,
                      }}
                    />
                  )}
                  {isComplete && (
                    <div
                      className="absolute inset-0 animate-shimmer-once"
                      style={{
                        background:
                          "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.5) 50%, transparent 100%)",
                      }}
                    />
                  )}
                </div>
              </section>

              {/* Agent pipeline indicator */}
              {agentPhase !== "init" && (
                <div className="flex items-center justify-center gap-3 animate-fade-in">
                  {/* Translator */}
                  <div
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-500 ${
                      agentPhase === "translator"
                        ? "border-primary bg-primary-light/60 shadow-sm"
                        : agentPhase === "reviewer" ||
                            agentPhase === "complete"
                          ? "border-emerald-200 bg-emerald-50/60"
                          : "border-border-subtle bg-slate-50"
                    }`}
                  >
                    <span
                      className={`material-symbols-outlined text-lg ${
                        agentPhase === "translator"
                          ? "text-primary animate-spin360"
                          : agentPhase === "reviewer" ||
                              agentPhase === "complete"
                            ? "text-emerald-500"
                            : "text-text-muted"
                      }`}
                    >
                      {agentPhase === "translator"
                        ? "progress_activity"
                        : agentPhase === "reviewer" ||
                            agentPhase === "complete"
                          ? "check_circle"
                          : "circle"}
                    </span>
                    <span
                      className={`text-xs font-semibold ${
                        agentPhase === "translator"
                          ? "text-primary-dark"
                          : agentPhase === "reviewer" ||
                              agentPhase === "complete"
                            ? "text-emerald-600"
                            : "text-text-muted"
                      }`}
                    >
                      Translator
                    </span>
                  </div>

                  <span
                    className={`material-symbols-outlined text-lg transition-colors duration-500 ${
                      agentPhase === "reviewer" || agentPhase === "complete"
                        ? "text-emerald-400"
                        : "text-slate-300"
                    }`}
                  >
                    arrow_forward
                  </span>

                  {/* Reviewer */}
                  <div
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-500 ${
                      agentPhase === "reviewer"
                        ? "border-primary bg-primary-light/60 shadow-sm"
                        : agentPhase === "complete"
                          ? "border-emerald-200 bg-emerald-50/60"
                          : "border-border-subtle bg-slate-50"
                    }`}
                  >
                    <span
                      className={`material-symbols-outlined text-lg ${
                        agentPhase === "reviewer"
                          ? "text-primary animate-spin360"
                          : agentPhase === "complete"
                            ? "text-emerald-500"
                            : "text-text-muted"
                      }`}
                    >
                      {agentPhase === "reviewer"
                        ? "progress_activity"
                        : agentPhase === "complete"
                          ? "check_circle"
                          : "circle"}
                    </span>
                    <span
                      className={`text-xs font-semibold ${
                        agentPhase === "reviewer"
                          ? "text-primary-dark"
                          : agentPhase === "complete"
                            ? "text-emerald-600"
                            : "text-text-muted"
                      }`}
                    >
                      Reviewer
                    </span>
                  </div>

                  <span
                    className={`material-symbols-outlined text-lg transition-colors duration-500 ${
                      agentPhase === "complete"
                        ? "text-emerald-400"
                        : "text-slate-300"
                    }`}
                  >
                    arrow_forward
                  </span>

                  {/* Complete */}
                  <div
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-500 ${
                      agentPhase === "complete"
                        ? "border-emerald-200 bg-emerald-50/60 shadow-sm"
                        : "border-border-subtle bg-slate-50"
                    }`}
                  >
                    <span
                      className={`material-symbols-outlined text-lg ${
                        agentPhase === "complete"
                          ? "text-emerald-500"
                          : "text-text-muted"
                      }`}
                    >
                      {agentPhase === "complete" ? "check_circle" : "circle"}
                    </span>
                    <span
                      className={`text-xs font-semibold ${
                        agentPhase === "complete"
                          ? "text-emerald-600"
                          : "text-text-muted"
                      }`}
                    >
                      Complete
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ═══ Review Header (review mode) ═══ */}
          {showReviewHeader && (
            <div
              className={`space-y-6 ${transition === "entering" ? "animate-section-fade-in" : ""}`}
            >
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <h1 className="text-3xl font-bold text-text-main tracking-tight">
                      Translation Review
                    </h1>
                    <span className="px-3 py-1 rounded-full bg-primary-light text-primary-dark text-xs font-bold border border-primary/20">
                      Step 4 of 5
                    </span>
                  </div>
                  <p className="text-text-muted text-base max-w-2xl">
                    Review AI-generated translations against the source
                    (Korean). Confirm changes before exporting to game engine
                    format.
                  </p>
                </div>
                {sessionId && (
                  <a
                    href={getDownloadUrl(sessionId, "translation_report")}
                    className="hidden md:flex items-center gap-2 px-4 py-2.5 rounded-lg border border-border-subtle bg-white hover:bg-surface-pale text-text-muted hover:text-primary transition-colors font-semibold text-sm shadow-sm h-10"
                  >
                    <span className="material-symbols-outlined text-xl">
                      download
                    </span>
                    Download CSV Backup
                  </a>
                )}
              </div>

              {/* Summary cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-soft">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="material-symbols-outlined text-lg text-primary">
                      translate
                    </span>
                    <span className="text-xs font-medium text-text-muted">
                      Total Strings
                    </span>
                  </div>
                  <span className="text-2xl font-bold text-text-main tabular-nums">
                    {reviewResults.length}
                  </span>
                </div>
                <div className="rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-soft">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="material-symbols-outlined text-lg text-emerald-500">
                      swap_horiz
                    </span>
                    <span className="text-xs font-medium text-text-muted">
                      Changed
                    </span>
                  </div>
                  <span className="text-2xl font-bold text-emerald-600 tabular-nums">
                    {changedCount}
                  </span>
                </div>
                <div className="rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-soft">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="material-symbols-outlined text-lg text-slate-400">
                      horizontal_rule
                    </span>
                    <span className="text-xs font-medium text-text-muted">
                      Unchanged
                    </span>
                  </div>
                  <span className="text-2xl font-bold text-slate-400 tabular-nums">
                    {unchangedCount}
                  </span>
                </div>
                <div className="rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-soft">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="material-symbols-outlined text-lg text-amber-500">
                      paid
                    </span>
                    <span className="text-xs font-medium text-text-muted">
                      Est. Cost
                    </span>
                  </div>
                  <span className="text-2xl font-bold text-text-main tabular-nums">
                    ${costSummary?.estimated_cost_usd?.toFixed(4) ?? "\u2014"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* ═══ Error Banner ═══ */}
          {error && (
            <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 animate-fade-slide-down">
              <span className="material-symbols-outlined text-lg animate-shake">
                error
              </span>
              {error}
              <button
                onClick={() => {
                  setCancelError(null);
                  setSubmitError(null);
                }}
                className="ml-auto text-red-400 hover:text-red-600"
              >
                <span className="material-symbols-outlined text-lg">
                  close
                </span>
              </button>
            </div>
          )}

          {/* ═══ Data Table ═══ */}
          {mode === "translating" && originalRows.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <span className="material-symbols-outlined text-5xl text-primary animate-spin360">
                progress_activity
              </span>
              <p className="text-sm text-text-muted animate-breathe">
                Preparing translation...
              </p>
            </div>
          ) : (
            <div className="flex flex-col min-h-[500px] animate-fade-slide-up">
              <div className="w-full bg-white border border-border-subtle rounded-xl overflow-hidden flex flex-col shadow-md h-full">
                {/* Toolbar */}
                <div className="p-4 border-b border-border-subtle bg-surface-pale/50 flex flex-wrap justify-between items-center gap-4">
                  <div className="flex items-center gap-4">
                    {/* Language tabs */}
                    {availableLangs.length > 0 && (
                      <div className="flex items-center gap-1">
                        <span className="text-xs font-medium text-text-muted mr-2">
                          Language:
                        </span>
                        {availableLangs.map((lang) => (
                          <button
                            key={lang}
                            onClick={() => {
                              setSelectedLang(lang);
                              setPage(1);
                            }}
                            className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                              lang === activeLang
                                ? "bg-primary text-white shadow-sm"
                                : "text-text-muted hover:bg-slate-100"
                            }`}
                          >
                            {lang.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    )}

                    <div className="h-6 w-[1px] bg-border-subtle" />

                    {mode === "review" ? (
                      <>
                        <h3 className="text-text-main font-bold text-lg hidden sm:block">
                          Review Drafts
                        </h3>
                        <span className="bg-white px-2 py-0.5 rounded text-xs text-text-muted border border-border-subtle font-medium shadow-sm">
                          {unifiedRows.length} Strings
                        </span>
                      </>
                    ) : (
                      <span className="text-xs text-text-muted tabular-nums">
                        {translationMap.size}/{originalRows.length} translated
                      </span>
                    )}
                  </div>

                  <div className="flex gap-3 items-center">
                    {/* Pagination */}
                    <div className="flex items-center bg-white rounded-lg border border-border-subtle p-0.5 shadow-sm">
                      <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page <= 1}
                        className="w-8 h-8 flex items-center justify-center rounded text-text-muted hover:text-primary hover:bg-surface-pale transition-colors disabled:opacity-30"
                      >
                        <span className="material-symbols-outlined text-xl">
                          chevron_left
                        </span>
                      </button>
                      <span className="text-sm text-text-main font-bold px-3 min-w-[80px] text-center">
                        {page} / {totalPages}
                      </span>
                      <button
                        onClick={() =>
                          setPage((p) => Math.min(totalPages, p + 1))
                        }
                        disabled={page >= totalPages}
                        className="w-8 h-8 flex items-center justify-center rounded text-text-muted hover:text-primary hover:bg-surface-pale transition-colors disabled:opacity-30"
                      >
                        <span className="material-symbols-outlined text-xl">
                          chevron_right
                        </span>
                      </button>
                    </div>

                    {/* Approve All (review mode) */}
                    {mode === "review" && (
                      <button
                        onClick={handleApproveAllPage}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-light/50 border border-primary/20 text-primary-dark text-xs font-bold hover:bg-primary-light transition-colors shadow-sm uppercase tracking-wide"
                      >
                        <span className="material-symbols-outlined text-base">
                          done_all
                        </span>
                        Approve Page
                      </button>
                    )}
                  </div>
                </div>

                {/* Completion banner (translating, 100%) */}
                {mode === "translating" && isComplete && (
                  <div className="flex items-center gap-3 px-5 py-3 bg-emerald-50 border-b border-emerald-200 animate-fade-slide-down">
                    <span className="material-symbols-outlined text-emerald-600 animate-bounce-in">
                      check_circle
                    </span>
                    <span className="text-sm font-semibold text-emerald-700">
                      Translation complete — moving to review
                    </span>
                  </div>
                )}

                {/* Grid header */}
                <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-surface-pale border-b border-border-subtle text-xs font-bold text-text-muted uppercase tracking-wider sticky top-0 z-10">
                  <div className="col-span-1">AI Note</div>
                  <div className="col-span-3">Source (KR)</div>
                  <div className="col-span-3">Previous Translation</div>
                  <div className="col-span-4">New Translation</div>
                  <div className="col-span-1 text-center">
                    {mode === "review" ? "Action" : "Status"}
                  </div>
                </div>

                {/* Rows */}
                <div className="overflow-y-auto custom-scrollbar flex-1 bg-white min-h-[400px]">
                  {pageRows.map((row) => {
                    const rowKey = `${row.key}_${row.lang}`;
                    const isUnchanged = row.isDone && !row.hasChange;

                    // Drip-feed row animation (translating mode only)
                    let showRowAnim = false;
                    if (mode === "translating" && row.isDone) {
                      if (!doneKeysRef.current.has(rowKey)) {
                        doneKeysRef.current.add(rowKey);
                        showRowAnim = true;
                      }
                    }

                    return (
                      <div
                        key={rowKey}
                        className={`grid grid-cols-12 gap-4 px-6 py-5 border-b border-surface-pale items-center hover:bg-surface-pale/30 transition-all duration-200 group ${
                          isUnchanged ? "opacity-45 hover:opacity-100" : ""
                        } ${showRowAnim ? "animate-row-fade-in" : ""}`}
                      >
                        {/* AI Note */}
                        <div className="col-span-1 relative">
                          {row.reason ? (
                            <>
                              <button
                                onClick={() =>
                                  setExpandedNote(
                                    expandedNote === rowKey ? null : rowKey,
                                  )
                                }
                                className={`flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-semibold transition-all w-fit ${
                                  row.hasChange
                                    ? "text-primary-dark bg-primary-light/50 border border-primary/10 hover:bg-primary-light"
                                    : "text-text-muted hover:text-primary hover:bg-primary-light/50"
                                }`}
                              >
                                <span className="material-symbols-outlined text-lg">
                                  sticky_note_2
                                </span>
                                {mode === "review" && (
                                  <span className="hidden xl:inline">Note</span>
                                )}
                              </button>
                              {expandedNote === rowKey && (
                                <div className="absolute left-0 top-full mt-1 z-20 w-80 p-3 rounded-lg bg-white border border-border-subtle shadow-lg text-xs text-text-main leading-relaxed">
                                  {row.reason}
                                </div>
                              )}
                            </>
                          ) : row.isDone ? (
                            <span className="text-gray-300 text-xs">
                              &mdash;
                            </span>
                          ) : null}
                        </div>

                        {/* Source KR */}
                        <div className="col-span-3 text-text-main text-sm font-medium leading-relaxed">
                          <span className="line-clamp-2">
                            {row.original_ko}
                          </span>
                        </div>

                        {/* Previous Translation */}
                        <div className="col-span-3">
                          {row.old_translation ? (
                            isUnchanged ? (
                              <span className="text-text-muted text-sm leading-relaxed line-clamp-2">
                                {row.old_translation}
                              </span>
                            ) : (
                              <span className="text-diff-removed-text bg-diff-removed-bg/40 px-1.5 py-0.5 rounded text-sm leading-relaxed line-through decoration-diff-removed-text/40 line-clamp-2">
                                {row.old_translation}
                              </span>
                            )
                          ) : row.isDone ? (
                            <span className="text-text-muted text-sm italic opacity-60">
                              No previous translation
                            </span>
                          ) : (
                            <span className="text-gray-300">&mdash;</span>
                          )}
                        </div>

                        {/* New Translation */}
                        <div className="col-span-4 text-sm leading-relaxed">
                          {row.isDone ? (
                            row.hasChange && row.old_translation ? (
                              <span className="text-text-main line-clamp-2">
                                {highlightDiff(
                                  row.old_translation,
                                  row.translated,
                                )}
                              </span>
                            ) : (
                              <span
                                className={
                                  row.hasChange
                                    ? "text-text-main"
                                    : "text-text-muted"
                                }
                              >
                                <span className="line-clamp-2">
                                  {row.translated}
                                </span>
                              </span>
                            )
                          ) : (
                            <span className="text-gray-300">&mdash;</span>
                          )}
                        </div>

                        {/* Action / Status */}
                        <div className="col-span-1 flex justify-center">
                          {mode === "review" ? (
                            <div className="flex gap-2 opacity-40 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() =>
                                  setReviewDecision(rowKey, "accepted")
                                }
                                className={`w-9 h-9 flex items-center justify-center rounded-full transition-colors ${
                                  reviewDecisions[rowKey] === "accepted"
                                    ? "bg-primary text-white"
                                    : "bg-surface-pale text-text-muted hover:text-white hover:bg-primary"
                                }`}
                              >
                                <span className="material-symbols-outlined text-xl">
                                  check
                                </span>
                              </button>
                              <button
                                onClick={() =>
                                  setReviewDecision(rowKey, "rejected")
                                }
                                className={`w-9 h-9 flex items-center justify-center rounded-full transition-colors ${
                                  reviewDecisions[rowKey] === "rejected"
                                    ? "bg-red-500 text-white"
                                    : "bg-surface-pale text-text-muted hover:text-white hover:bg-red-500"
                                }`}
                              >
                                <span className="material-symbols-outlined text-xl">
                                  close
                                </span>
                              </button>
                            </div>
                          ) : row.rowStatus === "translating" ? (
                            <span className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary-light/50 px-2.5 py-0.5 text-xs font-medium text-primary animate-breathe">
                              <span className="material-symbols-outlined text-sm animate-spin360">
                                progress_activity
                              </span>
                              Translating
                            </span>
                          ) : row.rowStatus === "translated" ? (
                            <span className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary-light px-2.5 py-0.5 text-xs font-medium text-primary-dark">
                              <span className="material-symbols-outlined text-sm">
                                check
                              </span>
                              Translated
                            </span>
                          ) : row.rowStatus === "reviewing" ? (
                            <span className="inline-flex items-center gap-1 rounded-full border border-amber-400 bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-600 animate-breathe">
                              <span className="material-symbols-outlined text-sm animate-spin360">
                                progress_activity
                              </span>
                              Reviewing
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-600">
                              <span className="material-symbols-outlined text-sm">
                                check
                              </span>
                              Reviewed
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Table footer */}
                <div className="p-3 bg-surface-pale/50 border-t border-border-subtle text-center text-xs text-text-muted font-medium">
                  Showing{" "}
                  {Math.min((page - 1) * PAGE_SIZE + 1, unifiedRows.length)}-
                  {Math.min(page * PAGE_SIZE, unifiedRows.length)} of{" "}
                  {unifiedRows.length} entries
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ═══ Footer ═══ */}
      {mode === "translating" ? (
        <Footer
          showCancel
          onCancel={handleCancel}
          actionLabel="Translating..."
          actionDisabled
        />
      ) : (
        <Footer
          onBack={() => setCurrentStep("ko_review")}
          onAction={() => handleFinalApproval("approved")}
          actionLabel={submitting ? "Processing..." : "Confirm & Next Step"}
          actionDisabled={submitting}
        />
      )}
    </>
  );
}
