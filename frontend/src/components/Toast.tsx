import { useEffect } from "react";
import { useToastStore, type Toast } from "../store/toastStore";

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, toast.duration);
    return () => clearTimeout(timer);
  }, [toast.duration, onDismiss]);

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="pointer-events-auto flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 shadow-lg animate-fade-slide-down max-w-sm"
    >
      <span
        className="material-symbols-outlined text-lg text-red-500 mt-0.5 shrink-0"
        aria-hidden="true"
      >
        error
      </span>
      <p className="flex-1 text-sm text-red-700 leading-relaxed">{toast.message}</p>
      <button
        type="button"
        onClick={onDismiss}
        className="shrink-0 text-red-400 hover:text-red-600 transition-colors"
        aria-label="닫기"
      >
        <span className="material-symbols-outlined text-lg" aria-hidden="true">
          close
        </span>
      </button>
    </div>
  );
}

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const removeToast = useToastStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[60] flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onDismiss={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );
}
