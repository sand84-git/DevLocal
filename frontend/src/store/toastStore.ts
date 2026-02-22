import { create } from "zustand";

export interface Toast {
  id: string;
  message: string;
  type: "error";
  duration: number;
}

interface ToastState {
  toasts: Toast[];
  addToast: (message: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

const MAX_TOASTS = 3;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  addToast: (message, duration = 5000) =>
    set((state) => {
      const toast: Toast = {
        id: crypto.randomUUID(),
        message,
        type: "error",
        duration,
      };
      const next = [...state.toasts, toast];
      // FIFO: 최대 3개 유지
      return { toasts: next.length > MAX_TOASTS ? next.slice(-MAX_TOASTS) : next };
    }),

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}));
