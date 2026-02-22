import { useState, useEffect } from "react";
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
  const projectName = useAppStore((s) => s.projectName);
  const setProjectName = useAppStore((s) => s.setProjectName);
  const allSheetsMode = useAppStore((s) => s.allSheetsMode);
  const setAllSheetsMode = useAppStore((s) => s.setAllSheetsMode);
  const setSheetQueue = useAppStore((s) => s.setSheetQueue);

  const [rowStart, setRowStart] = useState(0);
  const [rowEnd, setRowEnd] = useState(0);
  const [connecting, setConnecting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [synopsis, setSynopsis] = useState("");

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
        if (cfg.game_synopsis) {
          setSynopsis(cfg.game_synopsis);
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
      if (res.project_name) setProjectName(res.project_name);
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
    if (allSheetsMode) {
      // All Sheets 모드: 시트 큐 세팅 후 첫 시트로 시작
      setSheetQueue([...sheetNames]);
      await startSheet(sheetNames[0]);
      saveConfig({ saved_url: sheetUrl, saved_sheet: "__ALL_SHEETS__" }).catch(() => {});
    } else {
      if (!selectedSheet) return;
      await startSheet(selectedSheet);
      saveConfig({ saved_url: sheetUrl, saved_sheet: selectedSheet }).catch(() => {});
    }
  }

  async function startSheet(sheetName: string) {
    setLoading(true);
    setError("");
    setCurrentStep("loading");
    try {
      const res = await startPipeline({
        sheet_url: sheetUrl,
        sheet_name: sheetName,
        mode,
        target_languages: ["en", "ja"],
        row_limit: allSheetsMode ? 0 : rowEnd > 0 ? rowEnd - rowStart : 0,
      });
      setSessionId(res.session_id);
    } catch (e) {
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
          {/* Title section — crossfade, fixed height, no jitter */}
          <div className="relative mb-8 h-32">
            {/* Default state */}
            <div className={`absolute inset-0 flex flex-col items-center justify-center text-center transition-all duration-500 ease-out ${
              projectName ? "opacity-0 -translate-y-3 pointer-events-none" : "opacity-100 translate-y-0"
            }`}>
              <h3 className="text-3xl md:text-4xl font-bold text-text-main tracking-tight">
                Data Source Configuration
              </h3>
              <p className="text-text-muted text-base max-w-lg mx-auto leading-relaxed mt-2">
                Connect your master Google Sheet to seamlessly sync and
                automate your localization workflow.
              </p>
            </div>
            {/* Project loaded state */}
            <div className={`absolute inset-0 flex flex-col items-center justify-center text-center transition-all duration-500 ease-out ${
              projectName ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3 pointer-events-none"
            }`}>
              <h3 className="text-3xl md:text-4xl font-bold text-text-main tracking-tight">
                <span className="text-primary">'{projectName}'</span> loaded
              </h3>
              {synopsis && (
                <p className="text-text-muted text-sm max-w-md mx-auto leading-relaxed mt-2 line-clamp-3">
                  {synopsis}
                </p>
              )}
            </div>
          </div>

          {/* Main card — glassmorphism */}
          <section className="rounded-2xl border border-white/50 bg-white/80 backdrop-blur-xl p-8 md:p-10 shadow-soft ring-1 ring-slate-900/5 animate-fade-slide-up">
            <div className="grid grid-cols-1 gap-8">
              {/* Google Sheet URL */}
              <div className="space-y-4">
                <label className="block text-sm font-semibold text-text-main">
                  Google Sheet URL
                </label>
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
                      value={allSheetsMode ? "__ALL_SHEETS__" : selectedSheet}
                      onChange={(e) => {
                        const val = e.target.value;
                        if (val === "__ALL_SHEETS__") {
                          setAllSheetsMode(true);
                          setSelectedSheet(sheetNames[0] || "");
                        } else {
                          setAllSheetsMode(false);
                          setSelectedSheet(val);
                        }
                      }}
                      disabled={sheetNames.length === 0}
                      className="block w-full rounded-xl border-0 bg-white py-3.5 pl-4 pr-10 text-text-main ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-primary sm:text-sm sm:leading-6 shadow-sm appearance-none transition-all duration-200 hover:ring-slate-300"
                    >
                      {sheetNames.length === 0 ? (
                        <option value="">Select a tab...</option>
                      ) : (
                        <>
                          <option value="__ALL_SHEETS__">
                            All Sheets ({sheetNames.length} tabs)
                          </option>
                          {sheetNames.map((n) => (
                            <option key={n} value={n}>
                              {n}
                            </option>
                          ))}
                        </>
                      )}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-4 text-text-muted">
                      <span className="material-symbols-outlined">
                        expand_more
                      </span>
                    </div>
                  </div>
                </div>
                <div className={allSheetsMode ? "opacity-50 pointer-events-none" : ""}>
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
                        disabled={allSheetsMode}
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
                          disabled={allSheetsMode}
                          className="block w-full rounded-xl border-0 bg-white py-3.5 px-3 text-center text-text-main ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-primary sm:text-sm sm:leading-6 shadow-sm transition-all hover:ring-slate-300 placeholder:text-slate-400 placeholder:text-2xl"
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
        actionDisabled={(!selectedSheet && !allSheetsMode) || loading}
      />
    </>
  );
}
