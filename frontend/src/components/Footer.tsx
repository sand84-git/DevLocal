import { useAppStore } from "../store/useAppStore";

interface FooterProps {
  onBack?: () => void;
  onAction?: () => void;
  actionLabel?: string;
  actionIcon?: string;
  actionDisabled?: boolean;
  showCancel?: boolean;
  onCancel?: () => void;
  showExport?: boolean;
  onExport?: () => void;
}

export default function Footer({
  onBack,
  onAction,
  actionLabel = "Next Step",
  actionIcon = "arrow_forward",
  actionDisabled = false,
  showCancel = false,
  onCancel,
  showExport = false,
  onExport,
}: FooterProps) {
  const currentStep = useAppStore((s) => s.currentStep);
  const mode = useAppStore((s) => s.mode);

  const isIdle = currentStep === "idle";

  return (
    <div className="h-20 border-t border-border-subtle bg-bg-surface px-8 shadow-[0_-4px_20px_-2px_rgba(0,0,0,0.05)] z-20 flex items-center justify-center shrink-0">
      <div className="w-full flex max-w-6xl items-center justify-between">
        {/* Left: Back or Cancel */}
        {showCancel ? (
          <button
            onClick={onCancel}
            className="px-6 py-2.5 text-text-muted hover:text-text-main font-semibold text-sm transition-colors"
          >
            Cancel
          </button>
        ) : (
          <button
            onClick={onBack}
            disabled={isIdle}
            className={`rounded-lg px-6 py-2.5 text-sm font-medium transition-colors h-11 flex items-center gap-2 ${
              isIdle
                ? "text-slate-300 cursor-not-allowed"
                : "text-text-muted hover:bg-slate-50 hover:text-text-main"
            }`}
          >
            <span className="material-symbols-outlined text-lg">
              arrow_back
            </span>
            Back
          </button>
        )}

        {/* Right: Controls */}
        <div className="flex items-center gap-4">
          {/* Scope radio (disabled after idle) */}
          <div
            className={`flex items-center gap-3 px-4 py-1.5 bg-slate-50 rounded-lg border border-border-subtle ${
              !isIdle ? "opacity-70" : ""
            }`}
          >
            <span className="text-xs font-semibold text-text-muted uppercase tracking-wide mr-1">
              Scope:
            </span>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="translation_scope"
                checked={mode === "A"}
                disabled={!isIdle}
                readOnly={!isIdle}
                className="w-4 h-4 text-primary border-slate-300 focus:ring-primary"
              />
              <span className="text-sm font-medium text-text-muted">
                전체 번역
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="translation_scope"
                checked={mode === "B"}
                disabled={!isIdle}
                readOnly={!isIdle}
                className="w-4 h-4 text-primary border-slate-300 focus:ring-primary"
              />
              <span className="text-sm font-medium text-text-muted">
                신규 번역
              </span>
            </label>
          </div>

          <div className="h-8 w-px bg-border-subtle" />

          {/* Folder button */}
          <button
            className="flex items-center justify-center rounded-lg border border-border-subtle bg-white p-2.5 text-text-muted hover:bg-slate-50 hover:border-slate-300 hover:text-text-main transition-all shadow-sm h-11 w-11"
            title="Open Folder"
          >
            <span className="material-symbols-outlined text-xl">
              folder_open
            </span>
          </button>

          {/* Export button (step 5) */}
          {showExport && (
            <button
              onClick={onExport}
              className="px-6 py-2.5 bg-white border border-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition-colors shadow-sm text-sm"
            >
              Export JSON
            </button>
          )}

          {/* Main action button */}
          <button
            onClick={onAction}
            disabled={actionDisabled}
            className="group flex items-center gap-2 rounded-lg bg-primary px-8 py-2.5 text-sm font-bold text-white hover:bg-primary-dark transition-all shadow-lg shadow-primary/30 h-11 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLabel}
            <span className="material-symbols-outlined text-lg transition-transform group-hover:translate-x-1">
              {actionIcon}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
