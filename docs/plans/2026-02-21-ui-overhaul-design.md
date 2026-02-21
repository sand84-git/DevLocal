# UI 전면 개편 디자인 문서

## 개요
Stitch 디자인 레퍼런스 기반으로 기존 Streamlit UI를 전면 개편.
핵심 기능(LangGraph 8노드, HITL 2단계, 실시간 스트리밍)은 그대로 유지.

## 전략
- Approach A: Streamlit 유지 + Stitch를 디자인 레퍼런스로 활용
- 사이드바 완전 제거 → Full-Width 레이아웃
- 모든 설정을 메인 영역 Data Source 카드에 통합

## 레이아웃 구조

### Header (고정 상단)
- 로고: 🌐 Game Localization Tool
- 스텝 인디케이터: 5단계 (Load → KR Review → Translating → Multi-Review → Complete)
- 원형 아이콘 + 연결선 방식 (Stitch 디자인 참조)

### Main Content (화면 상태별)

**idle — Data Source Configuration**
- Row 1: Google Sheet URL | Sheet Tab | Row Range
- Row 2: Translation Mode (Full/New Only 세그먼트) | Target Languages (체크박스)
- Advanced (접이식): Row Limit, Backup Folder
- Footer: [Start Translation →]

**ko_review — 한국어 검수**
- 테이블: AI Comment | Original (Korean) | AI Suggested Fix | Action
- 카테고리 배지: Typo(빨강), Grammar(주황), Spacing(파랑), Style(보라)
- 페이지네이션 (Showing X of Y)
- Footer: [Back] [Skip → 원본 유지] [Approve & Translate →]

**translating — 번역 진행**
- 스텝 인디케이터 내부 프로그레스바
- 실행 로그 터미널
- Footer: [Cancel — 한국어 검수로 돌아가기]

**final_review — 번역 검수**
- Overall Progress 바 + 메트릭 (Done/Pending/Errors)
- 테이블: Key ID | Source (KR) | Previous | New Translation | Action
- Diff 하이라이팅 (초록: 추가, 빨강: 삭제)
- Footer: [Back] [Reject — 원복] [Apply to Sheet →]

**done — 완료**
- 체크마크 + 메트릭 그리드 (번역건수, 실패, 토큰, 비용)
- 다운로드 버튼 4개 (백업CSV, 번역리포트, 실패행, 로그)
- Footer: [New Task →]

### Footer (하단 고정)
- 좌: Back 버튼
- 우: 주요 액션 버튼 (단계별 변경)

## 디자인 토큰

| 토큰 | 값 | 용도 |
|------|---|------|
| --primary | #0ea5e9 | 메인 액센트 (Sky Blue) |
| --primary-dark | #0284c7 | 호버/강조 |
| --primary-light | #e0f2fe | 배지 배경 |
| --bg-page | #f8fafc | 페이지 배경 |
| --bg-surface | #ffffff | 카드 배경 |
| --border-subtle | #e2e8f0 | 보더 |
| --text-main | #1e293b | 메인 텍스트 |
| --text-muted | #64748b | 보조 텍스트 |
| --success | #10b981 | 성공 |
| --warning | #f59e0b | 경고 |
| --error | #ef4444 | 오류 |
| --diff-added | #dcfce7 | Diff 추가 배경 |
| --diff-removed | #fee2e2 | Diff 삭제 배경 |
| Font | Inter 400-700 | 전체 |
| Shadow | 0 4px 20px -2px rgba(0,0,0,0.05) | 카드 |
| Radius | 12px (카드), 8px (인풋), 9999px (배지) | |

## 변경 대상 파일
- `utils/ui_components.py` — CSS + 모든 HTML 컴포넌트 전면 재작성
- `app.py` — 사이드바 제거, Full-Width 레이아웃, 설정 카드 이동
- `utils/diff_report.py` — DataFrame 스타일 색상 정렬 (부분)
- `utils/sheets.py` — 셀 하이라이트 색상 정렬 (부분)

## 변경하지 않는 파일 (백엔드 무변경)
- agents/graph.py, state.py, prompts.py
- agents/nodes/* (translator, reviewer, writer, data_backup, context_glossary)
- config/constants.py, config/glossary.py
- utils/validation.py, utils/cost_tracker.py
