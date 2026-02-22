import { useEffect, useRef, type ReactNode } from "react";

interface ConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string | ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "warning" | "danger";
}

export default function ConfirmModal({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirm & Proceed",
  cancelLabel = "Cancel",
  variant = "warning",
}: ConfirmModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  /* ESC 키로 닫기 */
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  const isWarning = variant === "warning";
  const iconBg = isWarning ? "bg-amber-100" : "bg-red-100";
  const iconColor = isWarning ? "text-amber-500" : "text-red-500";
  const iconName = isWarning ? "warning" : "delete";
  const confirmBg = isWarning
    ? "bg-primary hover:bg-primary-dark shadow-primary/30"
    : "bg-red-500 hover:bg-red-600 shadow-red-500/30";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in"
      onClick={(e) => {
        if (panelRef.current && !panelRef.current.contains(e.target as Node))
          onClose();
      }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />

      {/* Panel */}
      <div
        ref={panelRef}
        className="relative bg-white rounded-2xl shadow-xl p-8 max-w-md w-full mx-4 animate-fade-slide-up"
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-text-muted hover:text-text-main transition-colors"
        >
          <span className="material-symbols-outlined text-xl">close</span>
        </button>

        {/* Icon + Title */}
        <div className="flex items-start gap-4 mb-4">
          <div
            className={`flex-shrink-0 w-12 h-12 rounded-full ${iconBg} flex items-center justify-center`}
          >
            <span className={`material-symbols-outlined text-2xl ${iconColor}`}>
              {iconName}
            </span>
          </div>
          <div className="pt-1">
            <h3 className="text-lg font-bold text-text-main">{title}</h3>
          </div>
        </div>

        {/* Description */}
        <div className="text-sm text-text-muted leading-relaxed mb-8 ml-16">
          {description}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-lg border border-border-subtle text-text-muted hover:bg-surface-pale font-semibold text-sm transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`px-6 py-2.5 rounded-lg text-white font-bold text-sm transition-all shadow-lg ${confirmBg}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
