import { useMemo, useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { approveKo, getDownloadUrl } from "../api/client";
import ProgressSection from "../components/ProgressSection";
import Footer from "../components/Footer";

const PAGE_SIZE = 10;

export default function KoReviewScreen() {
  const koReviewResults = useAppStore((s) => s.koReviewResults);
  const koDecisions = useAppStore((s) => s.koDecisions);
  const setKoDecision = useAppStore((s) => s.setKoDecision);
  const sessionId = useAppStore((s) => s.sessionId);
  const setCurrentStep = useAppStore((s) => s.setCurrentStep);

  const [page, setPage] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [showIssuesOnly, setShowIssuesOnly] = useState(false);

  const issueItems = useMemo(
    () => koReviewResults.filter((r) => r.has_issue),
    [koReviewResults],
  );

  const displayItems = showIssuesOnly ? issueItems : koReviewResults;
  const totalPages = Math.max(1, Math.ceil(displayItems.length / PAGE_SIZE));
  const pageItems = displayItems.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE,
  );

  const decidedCount = Object.keys(koDecisions).length;
  const totalIssues = issueItems.length;

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

  return (
    <>
      <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-32">
        <div className="mx-auto max-w-6xl space-y-6">
          {/* Title row */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-text-main">
                Korean Language Review
              </h1>
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

          {/* Progress */}
          <ProgressSection
            title="Korean Review Progress"
            total={koReviewResults.length}
            percent={
              totalIssues > 0
                ? Math.round((decidedCount / totalIssues) * 100)
                : 100
            }
            done={decidedCount}
            pending={Math.max(0, totalIssues - decidedCount)}
            errors={0}
          />

          {/* Table section */}
          <section className="flex flex-col rounded-xl border border-border-subtle bg-bg-surface shadow-soft overflow-hidden">
            {/* Table header */}
            <div className="border-b border-border-subtle bg-slate-50/50 p-6">
              <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white border border-border-subtle text-primary shadow-sm">
                    <span className="material-symbols-outlined text-lg">
                      table_rows
                    </span>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-text-main">
                      Source Language (Korean) Review
                    </h3>
                    <p className="text-sm text-text-muted">
                      Review and fix original Korean strings before translation
                      begins.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
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
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-text-main">
                <thead className="bg-slate-50 text-xs uppercase text-text-muted font-semibold border-b border-border-subtle">
                  <tr>
                    <th className="px-6 py-4 w-40" scope="col">
                      AI Comment
                    </th>
                    <th className="px-6 py-4" scope="col">
                      Original (Korean)
                    </th>
                    <th className="px-6 py-4" scope="col">
                      AI Suggested Fix
                    </th>
                    <th className="px-6 py-4 text-center w-32" scope="col">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle bg-white">
                  {pageItems.map((item) => {
                    const decision = koDecisions[item.key];
                    const isResolved = decision === "accepted";

                    return (
                      <tr
                        key={item.key}
                        className={`group transition-colors ${
                          isResolved
                            ? "bg-emerald-50/40"
                            : "hover:bg-slate-50"
                        }`}
                      >
                        {/* AI Comment */}
                        <td className="px-6 py-4">
                          {isResolved ? (
                            <div className="flex items-center justify-center gap-1.5 text-emerald-700 text-xs font-medium opacity-80">
                              <span className="material-symbols-outlined text-base">
                                check_circle
                              </span>
                              Resolved
                            </div>
                          ) : (
                            <button
                              className="flex items-center gap-2 text-primary-dark hover:text-primary text-xs font-medium bg-primary-light/50 px-2.5 py-1.5 rounded-lg border border-primary/10 hover:bg-primary-light w-full justify-center"
                              title={item.comment}
                            >
                              <span className="material-symbols-outlined text-base">
                                sticky_note_2
                              </span>
                              View Note
                            </button>
                          )}
                        </td>

                        {/* Original */}
                        <td
                          className={`px-6 py-4 ${
                            isResolved
                              ? "text-slate-400 line-through decoration-slate-300"
                              : "text-text-main"
                          }`}
                        >
                          {item.original}
                        </td>

                        {/* Suggested Fix */}
                        <td className="px-6 py-4">
                          <span className="text-primary-dark font-medium">
                            {item.revised}
                          </span>
                        </td>

                        {/* Action */}
                        <td className="px-6 py-4">
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
            <div className="border-t border-border-subtle bg-slate-50 p-4 flex items-center justify-between">
              <p className="text-sm text-text-muted">
                Showing {(page - 1) * PAGE_SIZE + 1}-
                {Math.min(page * PAGE_SIZE, displayItems.length)} of{" "}
                {displayItems.length} issues
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1.5 rounded-lg bg-white border border-border-subtle text-sm text-text-muted hover:text-primary hover:border-primary disabled:opacity-50 transition-all shadow-sm"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 rounded-lg bg-white border border-border-subtle text-sm text-text-muted hover:text-primary hover:border-primary disabled:opacity-50 transition-all shadow-sm"
                >
                  Next
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>

      <Footer
        onBack={() => setCurrentStep("idle")}
        onAction={handleApprove}
        actionLabel={submitting ? "Processing..." : "Confirm & Next Step"}
        actionDisabled={submitting}
      />
    </>
  );
}
