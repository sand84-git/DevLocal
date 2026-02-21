/** Stagger 등장 애니메이션을 위한 CSS 클래스 */
export const STAGGER = "opacity-0 animate-fade-slide-up";

/** 인덱스 기반 animation-delay 스타일 생성 */
export function staggerDelay(
  index: number,
  base = 0,
  step = 80,
): React.CSSProperties {
  return { animationDelay: `${base + index * step}ms` };
}
