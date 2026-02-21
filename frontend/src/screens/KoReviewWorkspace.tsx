import { useEffect, useMemo, useRef, useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { approveKo, getDownloadUrl } from "../api/client";
import { useCountUp } from "../hooks/useCountUp";
import { highlightDiff } from "../utils/diffHighlight";
import Footer from "../components/Footer";

const PAGE_SIZE = 10;

/**
 * 통합 한국어 검수 화면 — LoadingScreen + KoReviewScreen 합본.
 * currentStep 기반으로 mode를 결정하고, loading → ko_review 전환 시
 * 페이지 이동 없이 in-place 트랜지션으로 처리.
 */
export default function KoReviewWorkspace() {
  /* ── Store ── */
  const currentStep = useAppStore((s) => s.currentStep);
  const sessionId = useAppStore((s) => s.sessionId);
  const setCurrentStep = useAppStore((s) => s.setCurrentStep);
  const progressPercent = useAppStore((s) => s.progressPercent);
  const progressLabel = useAppStore((s) => s.progressLabel);
  const originalRows = useAppStore((s) => s.originalRows);
  const partialKoResults = useAppStore((s) => s.partialKoResults);
  const koReviewResults = useAppStore((s) => s.koReviewResults);
  const koDecisions = useAppStore((s) => s.koDecisions);
  const setKoDecision = useAppStore((s) => s.setKoDecision);

  /* ── Local State ── */
  const [page, setPage] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [showIssuesOnly, setShowIssuesOnly] = useState(false);
  const [expandedNote, setExpandedNote] = useState<string | null>(null);

  /* ── Mode & Transition ── */
  const mode = currentStep === "ko_review" ? "review" : "loading";
  const prevModeRef = useRef(mode);
  const [transition, setTransition] = useState<
    "idle" | "exiting" | "entering"
  >("idle");

  useEffect(() => {
    if (prevModeRef.current === "loading" && mode === "review") {
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

  const showLoadingTitle = mode === "loading" || transition === "exiting";
  const showReviewTitle = mode === "review" && transition !== "exiting";
  const showStats = mode === "review" && transition !== "exiting";

  /* ── Row drip-feed animation ── */
  const doneKeysRef = useRef(new Set<string>());

  /* ── Derived — Review mode (카드 전환에 필요하므로 먼저 선언) ── */
  const issueItems = useMemo(
    () => koReviewResults.filter((r) => r.has_issue),
    [koReviewResults],
  );
  const decidedCount = Object.keys(koDecisions).length;
  const totalIssues = issueItems.length;

  /* ── Derived — Loading mode ── */
  const isComplete = progressPercent >= 100;

  const agentPhase = useMemo(() => {
    if (isComplete) return "complete" as const;
    if (partialKoResults.length > 0) return "reviewing" as const;
    return "init" as const;
  }, [isComplete, partialKoResults.length]);

  /* ── Progress card values (loading → review 전환) ── */
  const reviewPercent = totalIssues > 0
    ? Math.round((decidedCount / totalIssues) * 100) : 100;
  const cardPercent = mode === "review" && transition === "idle"
    ? reviewPercent : progressPercent;
  const animPct = useCountUp(cardPercent, 500);
  const cardLabel = mode === "review" && transition === "idle"
    ? `Review Progress — ${decidedCount}/${totalIssues} issues decided`
    : (progressLabel || "Initializing...");

  const cardComplete = mode === "review" ? reviewPercent >= 100 : isComplete;
  const barColor = cardComplete ? "bg-emerald-500" : "bg-primary";
  const barShadow = cardComplete
    ? "shadow-[0_0_12px_rgba(16,185,129,0.4)]"
    : "shadow-[0_0_12px_rgba(14,165,233,0.3)]";
  const pctColor = cardComplete ? "text-emerald-500" : "text-primary";

  // Map partial results by key for fast lookup (loading mode)
  const reviewMap = useMemo(() => {
    const m = new Map<
      string,
      { revised: string; comment: string; has_issue: boolean }
    >();
    for (const r of partialKoResults) {
      m.set(r.key, {
        revised: r.revised,
        comment: r.comment,
        has_issue: r.has_issue,
      });
    }
    return m;
  }, [partialKoResults]);

  /* ── Unified display items ── */
  const displayItems = useMemo(() => {
    if (mode === "loading") {
      return originalRows;
    }
    return showIssuesOnly ? issueItems : koReviewResults;
  }, [mode, originalRows, showIssuesOnly, issueItems, koReviewResults]);

  const totalPages = Math.max(1, Math.ceil(displayItems.length / PAGE_SIZE));
  const pageItems = displayItems.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE,
  );

  /* ── Handlers ── */
  async function handleApprove() {
    if (!sessionId) return;
    setSubmitting(true);
    try {
      await approveKo(sessionId, { decision: "approved" });
      setCurrentStep("translating");
    } catch {
      // TODO: error handling
    } finally {
      setSubmitting(false);
    }
  }

  /* ── Render ── */
  return (
    <>
      <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-32">
        <div className="mx-auto max-w-5xl space-y-6">
          {/* ═══ Title Area — cross-fade (no height collapse) ═══ */}
          <div className="relative min-h-[72px]">
            {/* Loading Title */}
            <div
              className={`transition-opacity duration-400 ease-out ${
                showLoadingTitle
                  ? "opacity-100"
                  : "opacity-0 pointer-events-none absolute inset-0"
              }`}
            >
              <div className="text-center">
                <h1 className="text-2xl font-bold text-text-main">
                  Loading & Analyzing...
                </h1>
                <p className="mt-2 text-sm text-text-muted">
                  Backing up data, building glossary, and reviewing Korean text.
                </p>
              </div>
            </div>

            {/* Review Title */}
            <div
              className={`transition-opacity duration-400 ease-out ${
                showReviewTitle
                  ? "opacity-100"
                  : "opacity-0 pointer-events-none absolute inset-0"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h1 className="text-2xl font-bold text-text-main">
                      Korean Language Review
                    </h1>
                    <span className="px-3 py-1 rounded-full bg-primary-light text-primary-dark text-xs font-bold border border-primary/20">
                      Step 2 of 5
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-text-muted">
                    Review original Korean strings for errors before starting
                    translation.
                  </p>
                </div>
                {sessionId && (
                  <a
                    href={getDownloadUrl(sessionId, "backup")}
                    className="inline-flex items-center gap-2 rounded-lg border border-border-subtle bg-white px-4 py-2 text-sm font-medium text-text-muted shadow-sm transition-colors hover:bg-slate-50 hover:text-text-main"
                  >
                    <span className="material-symbols-outlined text-lg">
                      download
                    </span>
                    Download CSV Backup
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* ═══ Progress Card (ALWAYS visible — never fades out) ═══ */}
          <section className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-soft animate-fade-slide-up">
            <div className="flex items-center justify-between mb-3">
              <span className={`text-sm font-medium text-text-muted ${!cardComplete ? "animate-breathe" : ""}`}>
                {cardLabel}
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
                style={{ width: `${cardPercent}%` }}
              />
              {cardPercent > 0 && cardPercent < 100 && (
                <div
                  className="absolute inset-0 animate-shimmer"
                  style={{
                    background:
                      "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.35) 50%, transparent 100%)",
                    width: `${cardPercent}%`,
                  }}
                />
              )}
              {cardComplete && (
                <div
                  className="absolute inset-0 animate-shimmer-once"
                  style={{
                    background:
                      "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.5) 50%, transparent 100%)",
                  }}
                />
              )}
            </div>

            {/* Unified collapsible: completion banner OR stats — single grid-collapse to avoid jitter */}
            <div
              className="grid transition-[grid-template-rows] duration-500 ease-out"
              style={{ gridTemplateRows: (isComplete || showStats) ? "1fr" : "0fr" }}
            >
              <div className="overflow-hidden">
                {showStats ? (
                  <div
                    className={`mt-4 pt-3 border-t border-border-subtle flex items-center gap-6 ${transition === "entering" ? "animate-section-fade-in" : ""}`}
                    style={
                      transition === "entering"
                        ? { animationDelay: "200ms" }
                        : undefined
                    }
                  >
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-emerald-500" />
                      <span className="text-xs font-semibold text-text-muted uppercase tracking-wide">
                        Done
                      </span>
                      <span className="text-sm font-bold text-text-main tabular-nums">
                        {decidedCount}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-amber-500" />
                      <span className="text-xs font-semibold text-text-muted uppercase tracking-wide">
                        Pending
                      </span>
                      <span className="text-sm font-bold text-text-main tabular-nums">
                        {Math.max(0, totalIssues - decidedCount)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-red-500" />
                      <span className="text-xs font-semibold text-text-muted uppercase tracking-wide">
                        Errors
                      </span>
                      <span className="text-sm font-bold text-text-main tabular-nums">
                        0
                      </span>
                    </div>
                  </div>
                ) : isComplete ? (
                  <div className="mt-4 pt-3 flex items-center gap-2 text-sm text-emerald-600 font-semibold animate-fade-slide-down">
                    <span className="material-symbols-outlined animate-bounce-in">
                      check_circle
                    </span>
                    Korean review complete — {partialKoResults.length} suggestions
                    found
                  </div>
                ) : null}
              </div>
            </div>
          </section>

          {/* ═══ Data Table ═══ */}
          {mode === "loading" && originalRows.length === 0 ? (
            /* Spinner before data arrives */
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <span className="material-symbols-outlined text-5xl text-primary animate-spin360">
                progress_activity
              </span>
              <p className="text-sm text-text-muted animate-breathe">
                Loading spreadsheet data...
              </p>
            </div>
          ) : (
            <section className="rounded-xl border border-border-subtle bg-bg-surface shadow-soft overflow-hidden animate-fade-slide-up">
              {/* Toolbar (review mode only) */}
              {mode === "review" && (
                <div className="border-b border-border-subtle bg-slate-50/50 p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white border border-border-subtle text-primary shadow-sm">
                        <span className="material-symbols-outlined text-lg">
                          table_rows
                        </span>
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-text-main">
                          Source Language (Korean) Review
                        </h3>
                        <p className="text-xs text-text-muted">
                          Review and fix original Korean strings before
                          translation begins.
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setShowIssuesOnly(!showIssuesOnly);
                        setPage(1);
                      }}
                      className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors border shadow-sm ${
                        showIssuesOnly
                          ? "bg-primary-light text-primary-dark border-primary/20"
                          : "bg-white text-text-muted border-border-subtle hover:bg-slate-50 hover:text-text-main"
                      }`}
                    >
                      <span className="material-symbols-outlined text-lg">
                        filter_list
                      </span>
                      Filter: Issues Only
                    </button>
                  </div>
                </div>
              )}

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border-subtle bg-slate-50/80">
                      <th className="px-4 py-3 text-left font-semibold text-text-muted w-[120px]">
                        AI Note
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-text-muted">
                        Original (Korean)
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-text-muted">
                        AI Suggested Fix
                      </th>
                      <th className="px-4 py-3 text-center font-semibold text-text-muted w-[100px]">
                        {mode === "review" ? "Action" : "Status"}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {mode === "loading"
                      ? /* ── Loading mode rows ── */
                        (pageItems as typeof originalRows).map((row) => {
                          const review = reviewMap.get(row.key);
                          const isDone = !!review;
                          const hasIssue = review?.has_issue ?? false;

                          // Drip-feed row animation
                          let showRowAnim = false;
                          if (isDone && !doneKeysRef.current.has(row.key)) {
                            doneKeysRef.current.add(row.key);
                            showRowAnim = true;
                          }

                          return (
                            <tr
                              key={row.key}
                              className={`border-b border-border-subtle transition-all duration-200 ${
                                isDone && !hasIssue
                                  ? "opacity-45 hover:opacity-100"
                                  : ""
                              } ${showRowAnim ? "animate-row-fade-in" : ""}`}
                            >
                              {/* AI Note */}
                              <td className="px-4 py-3">
                                {isDone && review?.comment ? (
                                  <div className="relative">
                                    <button
                                      onClick={() =>
                                        setExpandedNote(
                                          expandedNote === row.key
                                            ? null
                                            : row.key,
                                        )
                                      }
                                      className={`flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-semibold transition-all w-fit ${
                                        hasIssue
                                          ? "text-primary-dark bg-primary-light/50 border border-primary/10 hover:bg-primary-light"
                                          : "text-text-muted hover:text-primary hover:bg-primary-light/50"
                                      }`}
                                    >
                                      <span className="material-symbols-outlined text-lg">
                                        sticky_note_2
                                      </span>
                                    </button>
                                    {expandedNote === row.key && (
                                      <div className="absolute left-0 top-full mt-1 z-20 w-80 p-3 rounded-lg bg-white border border-border-subtle shadow-lg text-xs text-text-main leading-relaxed">
                                        {review.comment}
                                      </div>
                                    )}
                                  </div>
                                ) : isDone ? (
                                  <span className="text-gray-300 text-xs">
                                    &mdash;
                                  </span>
                                ) : null}
                              </td>

                              {/* Original (Korean) */}
                              <td className="px-4 py-3 text-text-main max-w-[250px]">
                                <span className="line-clamp-2">
                                  {row.korean}
                                </span>
                              </td>

                              {/* AI Suggested Fix */}
                              <td className="px-4 py-3 max-w-[250px]">
                                {isDone ? (
                                  hasIssue ? (
                                    <span className="text-emerald-700 line-clamp-2">
                                      {review!.revised}
                                    </span>
                                  ) : (
                                    <span className="text-gray-400 text-xs">
                                      No issues
                                    </span>
                                  )
                                ) : (
                                  <span className="text-gray-300">
                                    &mdash;
                                  </span>
                                )}
                              </td>

                              {/* Status */}
                              <td className="px-4 py-3 text-center">
                                {isDone ? (
                                  hasIssue ? (
                                    <span className="inline-flex items-center gap-1 rounded-full border border-amber-400 bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-600 animate-bounce-in">
                                      <span className="material-symbols-outlined text-sm">
                                        edit_note
                                      </span>
                                      Revised
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-600 animate-bounce-in">
                                      <span className="material-symbols-outlined text-sm">
                                        check
                                      </span>
                                      OK
                                    </span>
                                  )
                                ) : agentPhase === "complete" ? (
                                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-600 animate-bounce-in">
                                    <span className="material-symbols-outlined text-sm">
                                      check
                                    </span>
                                    OK
                                  </span>
                                ) : agentPhase === "reviewing" ? (
                                  <span className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary-light/50 px-2.5 py-0.5 text-xs font-medium text-primary animate-breathe">
                                    <span className="material-symbols-outlined text-sm animate-spin360">
                                      progress_activity
                                    </span>
                                    Reviewing
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-slate-400 animate-breathe">
                                    <span className="material-symbols-outlined text-sm">
                                      hourglass_empty
                                    </span>
                                    Pending
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })
                      : /* ── Review mode rows ── */
                        (pageItems as typeof koReviewResults).map((item) => {
                          const decision = koDecisions[item.key];
                          const isResolved = decision === "accepted";
                          const noIssue = !item.has_issue;

                          return (
                            <tr
                              key={item.key}
                              className={`group border-b border-border-subtle transition-all duration-200 ${
                                isResolved
                                  ? "bg-emerald-50/40"
                                  : noIssue
                                    ? "opacity-45 hover:opacity-100"
                                    : "hover:bg-slate-50"
                              }`}
                            >
                              {/* AI Note */}
                              <td className="px-4 py-3">
                                {isResolved ? (
                                  <div className="flex items-center justify-center gap-1.5 text-emerald-700 text-xs font-medium opacity-80">
                                    <span className="material-symbols-outlined text-base">
                                      check_circle
                                    </span>
                                    Resolved
                                  </div>
                                ) : item.comment ? (
                                  <div className="relative">
                                    <button
                                      onClick={() =>
                                        setExpandedNote(
                                          expandedNote === item.key
                                            ? null
                                            : item.key,
                                        )
                                      }
                                      className={`flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-semibold transition-all w-fit ${
                                        item.has_issue
                                          ? "text-primary-dark bg-primary-light/50 border border-primary/10 hover:bg-primary-light"
                                          : "text-text-muted hover:text-primary hover:bg-primary-light/50"
                                      }`}
                                    >
                                      <span className="material-symbols-outlined text-lg">
                                        sticky_note_2
                                      </span>
                                      <span className="hidden xl:inline">
                                        Note
                                      </span>
                                    </button>
                                    {expandedNote === item.key && (
                                      <div className="absolute left-0 top-full mt-1 z-20 w-80 p-3 rounded-lg bg-white border border-border-subtle shadow-lg text-xs text-text-main leading-relaxed">
                                        {item.comment}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-gray-300 text-xs">
                                    &mdash;
                                  </span>
                                )}
                              </td>

                              {/* Original (Korean) */}
                              <td
                                className={`px-4 py-3 ${
                                  isResolved
                                    ? "text-slate-400 line-through decoration-slate-300"
                                    : "text-text-main"
                                }`}
                              >
                                {item.original}
                              </td>

                              {/* AI Suggested Fix — diff highlight */}
                              <td className="px-4 py-3">
                                {item.has_issue ? (
                                  <span className="text-text-main">
                                    {highlightDiff(item.original, item.revised)}
                                  </span>
                                ) : (
                                  <span className="text-gray-400 text-xs">
                                    No changes
                                  </span>
                                )}
                              </td>

                              {/* Action */}
                              <td className="px-4 py-3">
                                {isResolved ? (
                                  <div className="flex justify-center">
                                    <span className="flex items-center gap-1 text-xs font-bold text-emerald-600 bg-white border border-emerald-100 rounded-lg px-3 py-1 shadow-sm">
                                      Accepted
                                    </span>
                                  </div>
                                ) : (
                                  <div className="flex justify-center gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
                                    <button
                                      onClick={() =>
                                        setKoDecision(item.key, "rejected")
                                      }
                                      className="rounded-md p-1.5 text-text-muted hover:bg-red-50 hover:text-red-600 transition-colors"
                                      title="Reject"
                                    >
                                      <span className="material-symbols-outlined text-xl">
                                        close
                                      </span>
                                    </button>
                                    <button
                                      onClick={() =>
                                        setKoDecision(item.key, "accepted")
                                      }
                                      className="rounded-md p-1.5 text-primary hover:bg-primary-light hover:text-primary-dark transition-colors"
                                      title="Accept"
                                    >
                                      <span className="material-symbols-outlined text-xl">
                                        check
                                      </span>
                                    </button>
                                  </div>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-5 py-3 border-t border-border-subtle bg-slate-50/50">
                  <span className="text-xs text-text-muted">
                    Showing {(page - 1) * PAGE_SIZE + 1}&ndash;
                    {Math.min(page * PAGE_SIZE, displayItems.length)} of{" "}
                    {displayItems.length}
                    {mode === "review" && showIssuesOnly
                      ? " issues"
                      : " items"}
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-2.5 py-1 rounded text-xs font-medium text-text-muted hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      Prev
                    </button>
                    {Array.from(
                      { length: Math.min(totalPages, 7) },
                      (_, i) => {
                        const p = i + 1;
                        return (
                          <button
                            key={p}
                            onClick={() => setPage(p)}
                            className={`w-7 h-7 rounded text-xs font-medium ${
                              p === page
                                ? "bg-primary text-white"
                                : "text-text-muted hover:bg-slate-100"
                            }`}
                          >
                            {p}
                          </button>
                        );
                      },
                    )}
                    <button
                      onClick={() =>
                        setPage((p) => Math.min(totalPages, p + 1))
                      }
                      disabled={page === totalPages}
                      className="px-2.5 py-1 rounded text-xs font-medium text-text-muted hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </section>
          )}
        </div>
      </main>

      {/* ═══ Footer ═══ */}
      {(mode === "review" || isComplete) && (
        <Footer
          onBack={() => setCurrentStep("idle")}
          onAction={mode === "review" ? handleApprove : undefined}
          actionLabel={
            mode === "review"
              ? (submitting ? "Processing..." : "Confirm & Next Step")
              : "Preparing review..."
          }
          actionDisabled={mode !== "review" || submitting}
        />
      )}
    </>
  );
}
