import { useEffect } from "react";

/**
 * 작업 중 브라우저 새로고침/탭 닫기 방지 — beforeunload 이벤트 핸들러.
 * active=true일 때만 이벤트를 등록합니다.
 */
export function useNavigationGuard(active: boolean) {
  useEffect(() => {
    if (!active) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [active]);
}
