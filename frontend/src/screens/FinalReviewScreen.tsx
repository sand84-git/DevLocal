import { useMemo, useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { approveFinal, getDownloadUrl } from "../api/client";
import { highlightDiff } from "../utils/diffHighlight";
import { STAGGER, staggerDelay } from "../utils/stagger";
import ProgressSection from "../components/ProgressSection";
import Footer from "../components/Footer";

const PAGE_SIZE = 10;

export default function FinalReviewScreen() {
  const reviewResults = useAppStore((s) => s.reviewResults);
  const reviewDecisions = useAppStore((s) => s.reviewDecisions);
  const setReviewDecision = useAppStore((s) => s.setReviewDecision);
  const failedRows = useAppStore((s) => s.failedRows);
  const sessionId = useAppStore((s) => s.sessionId);
  const setCurrentStep = useAppStore((s) => s.setCurrentStep);
  const setTranslationsApplied = useAppStore((s) => s.setTranslationsApplied);
  const setCellsUpdated = useAppStore((s) => s.setCellsUpdated);
  const selectedLang = useAppStore((s) => s.selectedLang);
  const setSelectedLang = useAppStore((s) => s.setSelectedLang);

  const [page, setPage] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter by language
  const langItems = useMemo(
    () => reviewResults.filter((r) => r.lang === selectedLang),
    [reviewResults, selectedLang],
  );

  const availableLangs = useMemo(() => {
    const langs = new Set(reviewResults.map((r) => r.lang));
    return Array.from(langs);
  }, [reviewResults]);

  const totalPages = Math.max(1, Math.ceil(langItems.length / PAGE_SIZE));
  const pageItems = langItems.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE,
  );

  const decidedCount = Object.keys(reviewDecisions).length;

  const langFlags: Record<string, string> = {
    en: "\u{1F1FA}\u{1F1F8}",
    ja: "\u{1F1EF}\u{1F1F5}",
  };
  const langNames: Record<string, string> = {
    en: "English (US)",
    ja: "Japanese",
  };

  function handleApproveAllPage() {
    for (const item of pageItems) {
      if (!reviewDecisions[`${item.key}_${item.lang}`]) {
        setReviewDecision(`${item.key}_${item.lang}`, "accepted");
      }
    }
  }

  async function handleFinalApproval(decision: "approved" | "rejected") {
    if (!sessionId) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await approveFinal(sessionId, { decision });
      setTranslationsApplied(res.translations_applied ?? false);
      setCellsUpdated(res.updates_count ?? 0);
      setCurrentStep("done");
    } catch (e) {
      setError(
        `Final approval failed: ${e instanceof Error ? e.message : "Unknown error. Please try again."}`,
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-32">
        <div className="mx-auto max-w-[1400px] space-y-8">
          {/* Title */}
          <div className={`flex flex-col md:flex-row md:items-end justify-between gap-6 ${STAGGER}`} style={staggerDelay(0)}>
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
                Review AI-generated translations against the source (Korean).
                Confirm changes before exporting to game engine format.
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

          {/* Progress */}
          <div className={STAGGER} style={staggerDelay(1)}>
            <ProgressSection
              title="Overall Progress"
              total={reviewResults.length}
              percent={
                reviewResults.length > 0
                  ? Math.round((decidedCount / reviewResults.length) * 100)
                  : 0
              }
              done={decidedCount}
              pending={reviewResults.length - decidedCount}
              errors={failedRows.length}
            />
          </div>

          {/* Error banner */}
          {error && (
            <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <span className="material-symbols-outlined text-lg">error</span>
              {error}
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-400 hover:text-red-600"
              >
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>
          )}

          {/* Review table */}
          <div className={`flex flex-col min-h-[600px] ${STAGGER}`} style={staggerDelay(2)}>
            <div className="w-full bg-white border border-border-subtle rounded-xl overflow-hidden flex flex-col shadow-md h-full">
              {/* Toolbar */}
              <div className="p-4 border-b border-border-subtle bg-surface-pale/50 flex flex-wrap justify-between items-center gap-4">
                <div className="flex items-center gap-4">
                  {/* Language selector */}
                  <select
                    value={selectedLang}
                    onChange={(e) => {
                      setSelectedLang(e.target.value);
                      setPage(1);
                    }}
                    className="flex items-center gap-2 bg-white border border-border-subtle px-3 py-1.5 rounded-lg hover:border-primary transition-colors shadow-sm text-text-main font-bold text-sm"
                  >
                    {availableLangs.map((lang) => (
                      <option key={lang} value={lang}>
                        {langFlags[lang] || ""} {langNames[lang] || lang}
                      </option>
                    ))}
                  </select>

                  <div className="h-6 w-[1px] bg-border-subtle" />

                  <h3 className="text-text-main font-bold text-lg hidden sm:block">
                    Review Drafts
                  </h3>
                  <span className="bg-white px-2 py-0.5 rounded text-xs text-text-muted border border-border-subtle font-medium shadow-sm">
                    {langItems.length} Strings
                  </span>
                </div>

                <div className="flex gap-3 items-center">
                  {/* Pagination */}
                  <div className="flex items-center bg-white rounded-lg border border-border-subtle p-0.5 shadow-sm mr-2">
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

                  <button
                    onClick={handleApproveAllPage}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-light/50 border border-primary/20 text-primary-dark text-xs font-bold hover:bg-primary-light transition-colors shadow-sm uppercase tracking-wide"
                  >
                    <span className="material-symbols-outlined text-base">
                      done_all
                    </span>
                    Approve Page
                  </button>
                </div>
              </div>

              {/* Grid header */}
              <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-surface-pale border-b border-border-subtle text-xs font-bold text-text-muted uppercase tracking-wider sticky top-0 z-10">
                <div className="col-span-1">AI Note</div>
                <div className="col-span-3">Source (KR)</div>
                <div className="col-span-3">Previous Translation</div>
                <div className="col-span-4">New Translation (Draft)</div>
                <div className="col-span-1 text-center">Action</div>
              </div>

              {/* Rows */}
              <div className="overflow-y-auto custom-scrollbar flex-1 bg-white min-h-[500px]">
                {pageItems.map((item) => {
                  const decisionKey = `${item.key}_${item.lang}`;
                  const isUnchanged =
                    item.old_translation === item.translated;

                  return (
                    <div
                      key={decisionKey}
                      className={`grid grid-cols-12 gap-4 px-6 py-5 border-b border-surface-pale items-center hover:bg-surface-pale/30 transition-all duration-200 group ${
                        isUnchanged ? "opacity-45 hover:opacity-100" : ""
                      }`}
                    >
                      {/* AI Note */}
                      <div className="col-span-1">
                        <button
                          className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-semibold text-text-muted hover:text-primary hover:bg-primary-light/50 transition-all w-fit"
                          title={item.reason}
                        >
                          <span className="material-symbols-outlined text-lg">
                            chat_bubble
                          </span>
                          <span className="hidden xl:inline">View Note</span>
                        </button>
                      </div>

                      {/* Source KR */}
                      <div className="col-span-3 text-text-main text-sm font-medium leading-relaxed">
                        {item.original_ko}
                      </div>

                      {/* Previous Translation */}
                      <div className="col-span-3">
                        {item.old_translation ? (
                          <span className="text-diff-removed-text bg-diff-removed-bg/40 px-1.5 py-0.5 rounded text-sm leading-relaxed line-through decoration-diff-removed-text/40">
                            {item.old_translation}
                          </span>
                        ) : (
                          <span className="text-text-muted text-sm italic opacity-60">
                            No previous translation
                          </span>
                        )}
                      </div>

                      {/* New Translation — diff highlight */}
                      <div className="col-span-4 text-text-main text-sm leading-relaxed">
                        {item.old_translation && !isUnchanged ? (
                          <span className="bg-diff-added-bg text-diff-added-text px-1.5 py-0.5 rounded border border-diff-added-text/20 font-semibold">
                            {highlightDiff(
                              item.old_translation,
                              item.translated,
                            )}
                          </span>
                        ) : (
                          <span className="bg-diff-added-bg text-diff-added-text px-1.5 py-0.5 rounded border border-diff-added-text/20 font-semibold">
                            {item.translated}
                          </span>
                        )}
                      </div>

                      {/* Action */}
                      <div className="col-span-1 flex justify-center gap-2 opacity-40 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() =>
                            setReviewDecision(decisionKey, "accepted")
                          }
                          className={`w-9 h-9 flex items-center justify-center rounded-full transition-colors ${
                            reviewDecisions[decisionKey] === "accepted"
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
                            setReviewDecision(decisionKey, "rejected")
                          }
                          className={`w-9 h-9 flex items-center justify-center rounded-full transition-colors ${
                            reviewDecisions[decisionKey] === "rejected"
                              ? "bg-red-500 text-white"
                              : "bg-surface-pale text-text-muted hover:text-white hover:bg-red-500"
                          }`}
                        >
                          <span className="material-symbols-outlined text-xl">
                            close
                          </span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Footer */}
              <div className="p-3 bg-surface-pale/50 border-t border-border-subtle text-center text-xs text-text-muted font-medium">
                Showing {(page - 1) * PAGE_SIZE + 1}-
                {Math.min(page * PAGE_SIZE, langItems.length)} of{" "}
                {langItems.length} entries
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer
        onBack={() => setCurrentStep("ko_review")}
        onAction={() => handleFinalApproval("approved")}
        actionLabel={submitting ? "Processing..." : "Confirm & Next Step"}
        actionDisabled={submitting}
      />
    </>
  );
}
