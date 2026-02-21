import { useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { connectSheet, startPipeline, getConfig } from "../api/client";
import Footer from "../components/Footer";
import { useEffect } from "react";

export default function DataSourceScreen() {
  const sheetUrl = useAppStore((s) => s.sheetUrl);
  const setSheetUrl = useAppStore((s) => s.setSheetUrl);
  const sheetNames = useAppStore((s) => s.sheetNames);
  const setSheetNames = useAppStore((s) => s.setSheetNames);
  const setBotEmail = useAppStore((s) => s.setBotEmail);
  const selectedSheet = useAppStore((s) => s.selectedSheet);
  const setSelectedSheet = useAppStore((s) => s.setSelectedSheet);
  const mode = useAppStore((s) => s.mode);
  const setRowLimit = useAppStore((s) => s.setRowLimit);
  const setSessionId = useAppStore((s) => s.setSessionId);
  const setCurrentStep = useAppStore((s) => s.setCurrentStep);

  const [rowStart, setRowStart] = useState(0);
  const [rowEnd, setRowEnd] = useState(0);
  const [connecting, setConnecting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load saved config on mount
  useEffect(() => {
    getConfig()
      .then((cfg) => {
        if (cfg.saved_url && !sheetUrl) {
          setSheetUrl(cfg.saved_url);
        }
      })
      .catch(() => {});
  }, []);

  async function handleConnect() {
    if (!sheetUrl.trim()) return;
    setConnecting(true);
    setError("");
    try {
      const res = await connectSheet({ sheet_url: sheetUrl });
      setSheetNames(res.sheet_names);
      setBotEmail(res.bot_email);
      if (res.sheet_names.length > 0) {
        setSelectedSheet(res.sheet_names[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connection failed");
    } finally {
      setConnecting(false);
    }
  }

  async function handleLoad() {
    if (!selectedSheet) return;
    setLoading(true);
    setError("");
    // 낙관적 전환 — API 응답 전에 즉시 loading 화면으로 이동
    setCurrentStep("loading");
    try {
      const res = await startPipeline({
        sheet_url: sheetUrl,
        sheet_name: selectedSheet,
        mode,
        target_languages: ["en", "ja"],
        row_limit: rowEnd > 0 ? rowEnd - rowStart : 0,
      });
      setSessionId(res.session_id);
    } catch (e) {
      // 실패 시 idle로 복귀
      setCurrentStep("idle");
      setError(e instanceof Error ? e.message : "Failed to start");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-32 flex flex-col items-center justify-center">
        <div className="w-full max-w-3xl space-y-6">
          <section className="rounded-xl border border-border-subtle bg-bg-surface p-8 shadow-soft">
            <div className="mb-8">
              <h3 className="text-xl font-bold text-text-main">
                Data Source Configuration
              </h3>
              <p className="text-text-muted text-sm mt-1">
                Connect your Google Sheet to start the localization process.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-8">
              {/* Google Sheet URL */}
              <div className="space-y-4">
                <div className="flex justify-between">
                  <label className="block text-sm font-semibold text-text-main">
                    Google Sheet URL
                  </label>
                  <a
                    href="#"
                    className="text-sm text-primary hover:text-primary-dark hover:underline flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-sm">
                      help
                    </span>
                    Help
                  </a>
                </div>
                <div className="flex rounded-lg bg-white ring-1 ring-inset ring-border-subtle focus-within:ring-2 focus-within:ring-primary shadow-sm transition-all hover:ring-slate-300">
                  <div className="flex items-center pl-3">
                    <span className="material-symbols-outlined text-text-muted text-xl">
                      table_chart
                    </span>
                  </div>
                  <input
                    type="text"
                    value={sheetUrl}
                    onChange={(e) => setSheetUrl(e.target.value)}
                    onBlur={() => {
                      if (sheetUrl.trim() && sheetNames.length === 0)
                        handleConnect();
                    }}
                    placeholder="https://docs.google.com/spreadsheets/d/..."
                    className="block w-full border-0 bg-transparent py-3 pl-3 text-text-main placeholder:text-slate-400 focus:ring-0 sm:text-sm sm:leading-6"
                  />
                  <div className="flex items-center pr-2">
                    <button
                      onClick={handleConnect}
                      disabled={connecting}
                      className="p-1.5 text-text-muted hover:text-primary rounded-md hover:bg-slate-50 transition-colors"
                    >
                      <span className="material-symbols-outlined text-xl">
                        {connecting ? "sync" : "content_paste"}
                      </span>
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs mt-2">
                  {connecting ? (
                    <>
                      <span className="material-symbols-outlined text-sm text-primary animate-spin360">
                        progress_activity
                      </span>
                      <span className="text-primary font-medium">Connecting...</span>
                    </>
                  ) : sheetNames.length > 0 ? (
                    <>
                      <span className="material-symbols-outlined text-sm text-emerald-500">
                        check_circle
                      </span>
                      <span className="text-emerald-600 font-medium">
                        Connected — {sheetNames.length} tab{sheetNames.length > 1 ? "s" : ""} found
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-sm text-text-muted">
                        info
                      </span>
                      <span className="text-text-muted">
                        Make sure the sheet is shared with the service account.
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Sheet Tab + Row Range */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-text-main">
                    Sheet Tab Name
                  </label>
                  <div className="relative">
                    <select
                      value={selectedSheet}
                      onChange={(e) => setSelectedSheet(e.target.value)}
                      disabled={sheetNames.length === 0}
                      className="block w-full rounded-lg border-0 bg-white py-3 pl-3 pr-10 text-text-main ring-1 ring-inset ring-border-subtle focus:ring-2 focus:ring-primary sm:text-sm sm:leading-6 shadow-sm appearance-none transition-all hover:ring-slate-300"
                    >
                      {sheetNames.length === 0 ? (
                        <option value="">Select a tab...</option>
                      ) : (
                        sheetNames.map((n) => (
                          <option key={n} value={n}>
                            {n}
                          </option>
                        ))
                      )}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-text-muted">
                      <span className="material-symbols-outlined">
                        expand_more
                      </span>
                    </div>
                  </div>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-text-main">
                    Row Range
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="number"
                      value={rowStart || ""}
                      onChange={(e) => setRowStart(Number(e.target.value))}
                      placeholder="Start"
                      className="block w-full rounded-lg border-0 bg-white py-3 px-3 text-center text-text-main ring-1 ring-inset ring-border-subtle focus:ring-2 focus:ring-primary sm:text-sm sm:leading-6 shadow-sm transition-all hover:ring-slate-300 placeholder:text-slate-400"
                    />
                    <span className="text-text-muted font-medium">-</span>
                    <input
                      type="number"
                      value={rowEnd || ""}
                      onChange={(e) => {
                        const v = Number(e.target.value);
                        setRowEnd(v);
                        setRowLimit(v > 0 ? v - rowStart : 0);
                      }}
                      placeholder="End"
                      className="block w-full rounded-lg border-0 bg-white py-3 px-3 text-center text-text-main ring-1 ring-inset ring-border-subtle focus:ring-2 focus:ring-primary sm:text-sm sm:leading-6 shadow-sm transition-all hover:ring-slate-300 placeholder:text-slate-400"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Error message */}
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-700">
                {error}
              </div>
            )}
          </section>

          {/* Tip */}
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex gap-3 text-sm text-blue-800">
            <span className="material-symbols-outlined text-blue-600 shrink-0">
              tips_and_updates
            </span>
            <div>
              <p className="font-semibold mb-1">Tip</p>
              <p className="opacity-90">
                Leaving the end row empty will automatically detect the last row
                containing data.
              </p>
            </div>
          </div>
        </div>
      </main>

      <Footer
        onAction={handleLoad}
        actionLabel={loading ? "Loading..." : "Load Data"}
        actionIcon={loading ? "sync" : "arrow_forward"}
        actionDisabled={!selectedSheet || loading}
      />
    </>
  );
}
