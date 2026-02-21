import { useAppStore } from "../store/useAppStore";
import { useSSE } from "../hooks/useSSE";

export default function LoadingScreen() {
  const logs = useAppStore((s) => s.logs);
  const progressPercent = useAppStore((s) => s.progressPercent);
  const progressLabel = useAppStore((s) => s.progressLabel);

  // SSE 연결 활성화
  useSSE();

  return (
    <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-32">
      <div className="mx-auto max-w-4xl space-y-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-text-main">
            Loading & Analyzing...
          </h1>
          <p className="mt-2 text-sm text-text-muted">
            Backing up data, building glossary, and reviewing Korean text.
          </p>
        </div>

        {/* Progress */}
        <section className="rounded-xl border border-border-subtle bg-bg-surface p-8 shadow-soft">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-text-muted">
              {progressLabel || "Initializing..."}
            </span>
            <span className="text-2xl font-bold text-primary">
              {progressPercent}%
            </span>
          </div>
          <div className="relative w-full overflow-hidden rounded-full bg-slate-100 h-4">
            <div
              className="absolute top-0 left-0 h-full bg-primary rounded-full transition-all duration-500 shadow-[0_0_12px_rgba(14,165,233,0.4)]"
              style={{ width: `${progressPercent}%` }}
            >
              <div className="absolute inset-0 bg-white/20 animate-pulse" />
            </div>
          </div>
        </section>

        {/* Log terminal */}
        <section className="rounded-xl border border-border-subtle bg-slate-900 shadow-soft overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700">
            <span className="w-3 h-3 rounded-full bg-red-500" />
            <span className="w-3 h-3 rounded-full bg-yellow-500" />
            <span className="w-3 h-3 rounded-full bg-green-500" />
            <span className="ml-3 text-xs text-slate-400 font-mono">
              Processing Log
            </span>
          </div>
          <div className="p-4 h-64 overflow-y-auto custom-scrollbar font-mono text-xs text-green-400 leading-relaxed">
            {logs.length === 0 ? (
              <span className="text-slate-500">Waiting for events...</span>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="whitespace-pre-wrap">
                  <span className="text-slate-500 mr-2">
                    [{String(i + 1).padStart(3, "0")}]
                  </span>
                  {log}
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
