import { useAppStore } from "../store/useAppStore";
import StepIndicator from "./StepIndicator";

export default function Header() {
  const currentStep = useAppStore((s) => s.currentStep);
  const sseStatus = useAppStore((s) => s.sseStatus);

  const statusConfig = {
    connected: { dot: "bg-emerald-500 animate-dot-pulse", label: "Connected" },
    reconnecting: { dot: "bg-amber-400 animate-breathe", label: "Reconnecting..." },
    disconnected: { dot: "bg-slate-300", label: "Disconnected" },
  };
  const status = statusConfig[sseStatus];

  return (
    <header className="flex h-20 items-center justify-between border-b border-border-subtle bg-bg-surface px-8 shadow-sm shrink-0 z-30">
      {/* Logo */}
      <div className="flex items-center gap-3 min-w-[240px]">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-white shadow-md shadow-primary/20">
          <span className="material-symbols-outlined text-2xl">translate</span>
        </div>
        <div>
          <h2 className="text-base font-bold text-text-main tracking-tight leading-none">
            Game Localization
          </h2>
          <span className="text-xs text-text-muted font-medium">
            Automated Workflow
          </span>
        </div>
      </div>

      {/* Step indicator */}
      <StepIndicator currentStep={currentStep} />

      {/* Right side: connection status */}
      <div className="min-w-[240px] flex justify-end">
        {currentStep !== "idle" && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 rounded-lg border border-border-subtle">
            <span className={`w-2 h-2 rounded-full ${status.dot}`} />
            <span className="text-xs font-medium text-text-muted">
              {status.label}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
