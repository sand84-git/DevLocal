# 프론트엔드 (React) 상세

## 디자인 시스템
- Stitch 기반 — Sky Blue (#0ea5e9) + Inter 폰트 + Material Symbols Outlined
- 디자인 토큰: `frontend/src/index.css` (@theme 블록)
- 상세 규칙: `memory/ui-design-rules.md` (색상/타이포/그림자/컴포넌트)

## 화면 흐름
`idle → loading → ko_review → translating → final_review → done`

## 통합 워크스페이스 패턴
- `KoReviewWorkspace`: loading + ko_review를 하나의 화면에서 처리 (프로그레스 → 테이블 전환)
- `TranslationWorkspace`: translating + final_review를 하나의 화면에서 처리 (파이프라인 → 검수 전환)
- 같은 워크스페이스 내 전환 시 애니메이션 스킵 (자연스러운 UX)

## 스텝 인디케이터
5단계: Load → KR Review → Translating → Multi-Review → Complete

## SSE 실시간 업데이트
- 연결: `EventSource(/api/stream/{sessionId})` → `useSSE.ts` 훅 → Zustand 상태 갱신
- 드립피드: 청크 결과를 150ms 간격으로 항목별 전송 (부드러운 테이블 채워짐)
- 자동 재연결: 5회까지 지수 백오프 (1~16초)
- 세션 복원: 재연결 시 `getSessionState()` 호출로 상태 동기화

## HITL UX
- ko_review: Accept/Reject → POST `/api/approve-ko`
- final_review: Accept/Reject → POST `/api/approve-final`
- 번역 취소: POST `/api/cancel/{sessionId}` → 그래프 재생성 → ko_review 복귀

## 기타 기능
- **All Sheets 모드**: 전체 시트를 자동 순차 처리 (`useSheetQueue` 훅, 2초 딜레이)
- **Settings 모달**: Glossary 편집 (언어별) + 게임 시놉시스 + 톤앤매너 + 시트별 커스텀 프롬프트
- **네비게이션 가드**: 작업 진행 중 브라우저 새로고침/닫기 방지 (beforeunload)
