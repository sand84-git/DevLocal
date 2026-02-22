import { useState, useEffect, useRef } from "react";
import { useAppStore } from "../store/useAppStore";
import { connectSheet, startPipeline, getConfig, saveConfig } from "../api/client";
import Footer from "../components/Footer";

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
  const [showHelp, setShowHelp] = useState(false);
  const [copied, setCopied] = useState(false);
  const helpRef = useRef<HTMLDivElement>(null);

  const botEmail = useAppStore((s) => s.botEmail);

  // Load saved config on mount
  useEffect(() => {
    getConfig()
      .then((cfg) => {
        if (cfg.saved_url && !sheetUrl) {
          setSheetUrl(cfg.saved_url);
        }
        if (cfg.saved_sheet) {
          setSelectedSheet(cfg.saved_sheet);
        }
        if (cfg.bot_email) {
          setBotEmail(cfg.bot_email);
        }
      })
      .catch(() => {});
  }, []);

  // Close help popover on outside click
  useEffect(() => {
    if (!showHelp) return;
    function handleMouseDown(e: MouseEvent) {
      if (helpRef.current && !helpRef.current.contains(e.target as Node)) {
        setShowHelp(false);
      }
    }
    document.addEventListener("mousedown", handleMouseDown);
    return () => document.removeEventListener("mousedown", handleMouseDown);
  }, [showHelp]);

  async function handleConnect() {
    if (!sheetUrl.trim()) return;
    setConnecting(true);
    setError("");
    try {
      const res = await connectSheet({ sheet_url: sheetUrl });
      setSheetNames(res.sheet_names);
      setBotEmail(res.bot_email);
      if (res.sheet_names.length > 0) {
        // 이전 선택 탭이 있고 목록에 포함되면 유지, 아니면 첫 번째 선택
        if (!selectedSheet || !res.sheet_names.includes(selectedSheet)) {
          setSelectedSheet(res.sheet_names[0]);
        }
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
      // 설정 영속 저장 (시트 URL + 선택된 탭)
      saveConfig({ saved_url: sheetUrl, saved_sheet: selectedSheet }).catch(() => {});
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
      <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-32 flex flex-col items-center justify-center relative bg-gradient-mesh">
        {/* Decorative background blobs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
          <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-100 rounded-full mix-blend-multiply filter blur-[80px] opacity-70 animate-blob" />
          <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-sky-100 rounded-full mix-blend-multiply filter blur-[80px] opacity-70 animate-blob animation-delay-2000" />
        </div>

        <div className="w-full max-w-2xl space-y-8">
          {/* Title section — above card */}
          <div className="text-center space-y-3 mb-8">
            <h3 className="text-3xl md:text-4xl font-bold text-text-main tracking-tight">
              Data Source Configuration
            </h3>
            <p className="text-text-muted text-base max-w-lg mx-auto leading-relaxed">
              Connect your master Google Sheet to seamlessly sync and automate
              your localization workflow.
            </p>
          </div>

          {/* Main card — glassmorphism */}
          <section className="rounded-2xl border border-white/50 bg-white/80 backdrop-blur-xl p-8 md:p-10 shadow-soft ring-1 ring-slate-900/5 animate-fade-slide-up">
            <div className="grid grid-cols-1 gap-8">
              {/* Google Sheet URL */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <label className="block text-sm font-semibold text-text-main">
                    Google Sheet URL
                  </label>
                  <div className="relative" ref={helpRef}>
                    <button
                      onClick={() => setShowHelp(!showHelp)}
                      className={`text-xs font-medium transition-colors duration-200 flex items-center gap-1 group ${
                        showHelp
                          ? "text-primary-dark"
                          : "text-primary hover:text-primary-dark"
                      }`}
                    >
                      Need help?{" "}
                      <span className="material-symbols-outlined text-sm group-hover:translate-x-0.5 transition-transform">
                        arrow_forward
                      </span>
                    </button>
                    {showHelp && (
                      <div className="absolute right-0 top-full mt-2 z-20 w-80 p-4 rounded-lg bg-white border border-border-subtle shadow-lg text-left animate-fade-slide-down">
                        <p className="text-xs font-semibold text-text-main mb-2">
                          Share your sheet with this email:
                        </p>
                        <div className="flex items-center gap-2 bg-slate-50 rounded-lg p-2.5 ring-1 ring-inset ring-slate-200">
                          <span className="text-xs text-text-main font-mono break-all flex-1">
                            {botEmail || "Loading..."}
                          </span>
                          <button
                            onClick={async () => {
                              if (!botEmail) return;
                              await navigator.clipboard.writeText(botEmail);
                              setCopied(true);
                              setTimeout(() => setCopied(false), 1500);
                            }}
                            className="shrink-0 p-1.5 rounded-md text-text-muted hover:text-primary hover:bg-primary/5 transition-colors duration-200"
                            title="Copy"
                          >
                            <span className="material-symbols-outlined text-base">
                              {copied ? "check" : "content_copy"}
                            </span>
                          </button>
                        </div>
                        <p className="text-[11px] text-text-muted mt-2 leading-relaxed">
                          Add as <strong>Editor</strong> in Google Sheets sharing settings.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                <div className="group relative flex rounded-xl bg-white ring-1 ring-inset ring-slate-200 focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2 shadow-sm transition-all duration-200 hover:ring-slate-300">
                  <div className="flex items-center pl-4 border-r border-slate-100 pr-3 bg-slate-50 rounded-l-xl">
                    <img
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuCUTqR4611swIA4vQeI__WyiAAbdng68ytwlBVg0LUOxyEVpLnOeYFifEtfXArHcrWhXg51tjJLt4F3idymF3-vNCwgv0gu5cR_PdO0VtpNgxwdUTFVSfF_z16U33SHbM1xrP5Wd_RMPShKEUXu9jpybl21XKiHuCYosPvZz5-XnkBankOR0q9OW9UqM3nte6ncfz_LOndztvFBksYyw8jyWPxRdS60e4xi04GtCfu34hkVyKJ-Gsgb6iMmGaxaULvp1AfYnMwGFQ"
                      alt="Sheets"
                      className="h-6 w-6"
                    />
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
                    className="block w-full border-0 bg-transparent py-4 pl-4 text-text-main placeholder:text-slate-400 focus:ring-0 sm:text-sm sm:leading-6 rounded-r-xl"
                  />
                  <div className="flex items-center pr-2">
                    <button
                      onClick={handleConnect}
                      disabled={connecting}
                      className="p-2 text-text-muted hover:text-primary rounded-lg hover:bg-primary/5 transition-colors duration-200"
                    >
                      <span className="material-symbols-outlined text-xl">
                        {connecting ? "sync" : "content_paste"}
                      </span>
                    </button>
                  </div>
                </div>

                {/* Status / Info */}
                {connecting ? (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="material-symbols-outlined text-sm text-primary animate-spin360">
                      progress_activity
                    </span>
                    <span className="text-primary font-medium">
                      Connecting...
                    </span>
                  </div>
                ) : sheetNames.length > 0 ? (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="material-symbols-outlined text-sm text-emerald-500">
                      check_circle
                    </span>
                    <span className="text-emerald-600 font-medium">
                      Connected — {sheetNames.length} tab
                      {sheetNames.length > 1 ? "s" : ""} found
                    </span>
                  </div>
                ) : (
                  <div className="flex items-start gap-2 text-xs text-text-muted bg-blue-50/50 p-2 rounded-lg border border-blue-100/50">
                    <span className="material-symbols-outlined text-sm text-primary mt-0.5">
                      info
                    </span>
                    <span>
                      Ensure the sheet is shared with the service account email
                      before proceeding.
                    </span>
                  </div>
                )}
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
                      className="block w-full rounded-xl border-0 bg-white py-3.5 pl-4 pr-10 text-text-main ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-primary sm:text-sm sm:leading-6 shadow-sm appearance-none transition-all duration-200 hover:ring-slate-300"
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
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-4 text-text-muted">
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
                    <div className="relative w-full">
                      <input
                        type="number"
                        value={rowStart || ""}
                        onChange={(e) => setRowStart(Number(e.target.value))}
                        placeholder="1"
                        className="block w-full rounded-xl border-0 bg-white py-3.5 px-3 text-center text-text-main ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-primary sm:text-sm sm:leading-6 shadow-sm transition-all hover:ring-slate-300 placeholder:text-slate-400"
                      />
                    </div>
                    <span className="text-slate-300 font-medium text-lg">
                      -
                    </span>
                    <div className="relative w-full">
                      <div className="group relative">
                        <input
                          type="number"
                          value={rowEnd || ""}
                          onChange={(e) => {
                            const v = Number(e.target.value);
                            setRowEnd(v);
                            setRowLimit(v > 0 ? v - rowStart : 0);
                          }}
                          placeholder="&#8734;"
                          className="block w-full rounded-xl border-0 bg-white py-3.5 px-3 text-center text-text-main ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-primary sm:text-sm sm:leading-6 shadow-sm transition-all hover:ring-slate-300 placeholder:text-slate-400"
                        />
                        <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                          Empty = Auto-detect
                          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Error message */}
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2 animate-fade-slide-down">
                <span className="material-symbols-outlined text-lg animate-shake">
                  error
                </span>
                {error}
              </div>
            )}
          </section>
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
