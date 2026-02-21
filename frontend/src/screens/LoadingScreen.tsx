import { useMemo, useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { useCountUp } from "../hooks/useCountUp";

const PAGE_SIZE = 10;

export default function LoadingScreen() {
  const progressPercent = useAppStore((s) => s.progressPercent);
  const progressLabel = useAppStore((s) => s.progressLabel);
  const originalRows = useAppStore((s) => s.originalRows);
  const partialKoResults = useAppStore((s) => s.partialKoResults);

  const [page, setPage] = useState(1);

  const isComplete = progressPercent >= 100;
  const animPct = useCountUp(progressPercent, 500);

  // Map partial results by key for fast lookup
  const reviewMap = useMemo(() => {
    const m = new Map<string, { revised: string; comment: string; has_issue: boolean }>();
    for (const r of partialKoResults) {
      m.set(r.key, { revised: r.revised, comment: r.comment, has_issue: r.has_issue });
    }
    return m;
  }, [partialKoResults]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(originalRows.length / PAGE_SIZE));
  const pagedRows = originalRows.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE,
  );

  const barColor = isComplete ? "bg-emerald-500" : "bg-primary";
  const barShadow = isComplete
    ? "shadow-[0_0_12px_rgba(16,185,129,0.4)]"
    : "shadow-[0_0_12px_rgba(14,165,233,0.3)]";
  const pctColor = isComplete ? "text-emerald-500" : "text-primary";

  return (
    <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-32">
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Title */}
        <div className="text-center animate-fade-in">
          <h1 className="text-2xl font-bold text-text-main">
            Loading & Analyzing...
          </h1>
          <p className="mt-2 text-sm text-text-muted">
            Backing up data, building glossary, and reviewing Korean text.
          </p>
        </div>

        {/* Progress bar */}
        <section className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-soft animate-fade-slide-up">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-text-muted animate-breathe">
              {progressLabel || "Initializing..."}
            </span>
            <span className={`text-2xl font-bold tabular-nums ${pctColor}`}>
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

        {/* Content area */}
        {originalRows.length === 0 ? (
          /* Spinner before data arrives */
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <span className="material-symbols-outlined text-5xl text-primary animate-spin-360">
              progress_activity
            </span>
            <p className="text-sm text-text-muted animate-breathe">
              Loading spreadsheet data...
            </p>
          </div>
        ) : (
          /* Live review table */
          <section className="rounded-xl border border-border-subtle bg-bg-surface shadow-soft overflow-hidden animate-fade-slide-up">
            {/* Completion banner */}
            {isComplete && (
              <div className="flex items-center gap-3 px-5 py-3 bg-emerald-50 border-b border-emerald-200 animate-fade-slide-down">
                <span className="material-symbols-outlined text-emerald-600 animate-bounce-in">
                  check_circle
                </span>
                <span className="text-sm font-semibold text-emerald-700">
                  Korean review complete — {partialKoResults.length} suggestions found
                </span>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-subtle bg-slate-50/80">
                    <th className="px-4 py-3 text-left font-semibold text-text-muted w-[140px]">
                      Key
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-text-muted">
                      Korean (ko)
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-text-muted">
                      AI Review
                    </th>
                    <th className="px-4 py-3 text-center font-semibold text-text-muted w-[90px]">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {pagedRows.map((row) => {
                    const review = reviewMap.get(row.key);
                    const isDone = !!review;
                    const hasIssue = review?.has_issue ?? false;

                    return (
                      <tr
                        key={row.key}
                        className={`border-b border-border-subtle transition-all duration-200 ${
                          isDone && !hasIssue
                            ? "opacity-45 hover:opacity-100"
                            : ""
                        }`}
                      >
                        <td className="px-4 py-3 font-mono text-xs text-text-muted truncate max-w-[140px]">
                          {row.key}
                        </td>
                        <td className="px-4 py-3 text-text-main max-w-[250px]">
                          <span className="line-clamp-2">{row.korean}</span>
                        </td>
                        <td className="px-4 py-3 max-w-[250px]">
                          {isDone ? (
                            hasIssue ? (
                              <span className="text-emerald-700 line-clamp-2">
                                {review.revised}
                              </span>
                            ) : (
                              <span className="text-gray-400 text-xs">
                                No issues
                              </span>
                            )
                          ) : (
                            <span className="text-gray-300">—</span>
                          )}
                        </td>
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
                          ) : !isComplete ? (
                            <span className="text-xs text-gray-400 animate-breathe">
                              Pending
                            </span>
                          ) : null}
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
                  Showing {(page - 1) * PAGE_SIZE + 1}–
                  {Math.min(page * PAGE_SIZE, originalRows.length)} of{" "}
                  {originalRows.length}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-2.5 py-1 rounded text-xs font-medium text-text-muted hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    Prev
                  </button>
                  {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
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
                  })}
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
  );
}
