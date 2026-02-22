import { useAppStore } from "../store/useAppStore";

interface FooterProps {
  onBack?: () => void;
  onAction?: () => void;
  actionLabel?: string;
  actionIcon?: string;
  actionDisabled?: boolean;
  actionCompleted?: boolean;
  showCancel?: boolean;
  onCancel?: () => void;
  showExport?: boolean;
  onExport?: () => void;
  showDiscard?: boolean;
  onDiscard?: () => void;
}

export default function Footer({
  onBack,
  onAction,
  actionLabel = "Next Step",
  actionIcon = "arrow_forward",
  actionDisabled = false,
  actionCompleted = false,
  showCancel = false,
  onCancel,
  showExport = false,
  onExport,
  showDiscard = false,
  onDiscard,
}: FooterProps) {
  const currentStep = useAppStore((s) => s.currentStep);
  const mode = useAppStore((s) => s.mode);
  const setMode = useAppStore((s) => s.setMode);

  const isIdle = currentStep === "idle";

  return (
    <div className="h-24 border-t border-slate-100 bg-white/90 backdrop-blur-md px-8 shadow-[0_-4px_30px_-4px_rgba(0,0,0,0.03)] z-20 flex items-center justify-center shrink-0">
      <div className="w-full flex max-w-5xl items-center justify-between">
        {/* Left: Back or Cancel */}
        {showCancel ? (
          <button
            onClick={onCancel}
            className="px-6 py-2.5 text-text-muted hover:text-text-main font-semibold text-sm transition-colors duration-200"
          >
            Cancel
          </button>
        ) : (
          <button
            onClick={onBack}
            disabled={isIdle}
            className={`rounded-xl px-6 py-2.5 text-sm font-medium transition-colors duration-200 flex items-center gap-2 ${
              isIdle
                ? "text-slate-300 cursor-not-allowed select-none"
                : "text-text-muted hover:bg-slate-50 hover:text-text-main"
            }`}
          >
            <span className="material-symbols-outlined text-lg">
              arrow_back
            </span>
            Back
          </button>
        )}

        {/* Discard button (Back 옆) */}
        {showDiscard && (
          <button
            onClick={onDiscard}
            className="flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-sm font-medium text-red-500 hover:bg-red-50 hover:text-red-600 transition-colors duration-200"
            title="Discard all changes"
          >
            <span className="material-symbols-outlined text-lg">delete</span>
            Discard
          </button>
        )}

        {/* Right: Controls */}
        <div className="flex items-center gap-6">
          {/* Scope pill toggle */}
          <div
            className={`flex items-center bg-slate-100/80 rounded-xl p-1.5 border border-slate-200 shadow-inner ${
              !isIdle ? "opacity-70 pointer-events-none" : ""
            }`}
          >
            <label className="relative flex cursor-pointer rounded-lg px-4 py-2 text-sm font-semibold text-slate-500 hover:text-text-main transition-all duration-200 has-[:checked]:bg-white has-[:checked]:text-primary has-[:checked]:shadow-sm">
              <input
                type="radio"
                name="translation_scope"
                checked={mode === "A"}
                disabled={!isIdle}
                onChange={() => setMode("A")}
                className="sr-only"
              />
              <span className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">
                  playlist_add_check
                </span>
                All
              </span>
            </label>
            <label className="relative flex cursor-pointer rounded-lg px-4 py-2 text-sm font-semibold text-slate-500 hover:text-text-main transition-all duration-200 has-[:checked]:bg-white has-[:checked]:text-primary has-[:checked]:shadow-sm">
              <input
                type="radio"
                name="translation_scope"
                checked={mode === "B"}
                disabled={!isIdle}
                onChange={() => setMode("B")}
                className="sr-only"
              />
              <span className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">
                  new_releases
                </span>
                New
              </span>
            </label>
          </div>

          <div className="h-8 w-px bg-slate-200" />

          {/* Folder button */}
          <button
            className="flex items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 hover:bg-slate-50 hover:border-slate-300 hover:text-primary transition-all duration-200 shadow-sm h-12 w-12 group"
            title="Select Folder"
          >
            <span className="material-symbols-outlined text-2xl group-hover:scale-110 transition-transform">
              folder_open
            </span>
          </button>

          {/* Export button (step 5) */}
          {showExport && (
            <button
              onClick={onExport}
              className="px-6 py-2.5 bg-white border border-slate-300 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 transition-colors duration-200 shadow-sm text-sm"
            >
              Export JSON
            </button>
          )}

          {/* Main action button */}
          <button
            onClick={onAction}
            disabled={actionDisabled}
            className={`group flex items-center gap-3 rounded-xl px-8 py-3 text-base font-bold text-white transition-all duration-200 active:scale-[0.98] ring-offset-2 focus:ring-2 ring-primary disabled:opacity-50 disabled:cursor-not-allowed ${
              actionCompleted
                ? "bg-emerald-500 hover:bg-emerald-600 shadow-lg shadow-emerald-500/30"
                : "bg-gradient-to-r from-primary to-primary-dark hover:shadow-lg hover:shadow-primary/30"
            }`}
          >
            {actionLabel}
            <span className="material-symbols-outlined text-xl transition-transform group-hover:translate-x-1">
              {actionIcon}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
