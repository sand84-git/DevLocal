# UI 전면 개편 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Stitch 디자인 레퍼런스 기반으로 Streamlit UI를 전면 개편 — 사이드바 제거, Full-Width, Sky Blue 테마, 5단계 스텝 인디케이터

**Architecture:** 기존 `ui_components.py`의 CSS 토큰과 HTML 컴포넌트를 전면 교체하고, `app.py`의 사이드바 로직을 메인 영역 카드로 이동. 백엔드(agents/, config/, utils/validation.py 등)는 변경 없음.

**Tech Stack:** Streamlit, CSS Custom Properties, Inter font, HTML/CSS (unsafe_allow_html), Material Symbols

---

## Phase 1: Visual Shell — 전체 UI 골격 (가장 먼저 확인)

> 목표: 모든 동작 검증 이전에, 새 디자인의 전체 레이아웃을 눈으로 확인할 수 있는 상태를 만든다.
> 이 단계에서는 기능 연결 없이 순수 CSS + HTML 마크업만 작업한다.

### Task 1-1: CSS 디자인 토큰 전면 교체

**Files:**
- Modify: `utils/ui_components.py:1-715` (CSS 전체)

**Step 1:** `inject_custom_css()` 내부 CSS를 전면 교체
- `:root` 변수: Warm Green → Sky Blue 토큰으로 교체
- 폰트: `DM Sans` → `Inter`
- 그림자: `none` → `0 4px 20px -2px rgba(0,0,0,0.05)`
- 사이드바 관련 CSS 전체 삭제 (70줄+)
- 새 컴포넌트 CSS 추가: 헤더, 5단계 스텝, 하단 Footer, 세그먼트 컨트롤

**교체할 핵심 토큰:**
```css
:root {
    --primary: #0ea5e9;
    --primary-dark: #0284c7;
    --primary-light: #e0f2fe;
    --bg-page: #f8fafc;
    --bg-surface: #ffffff;
    --border-subtle: #e2e8f0;
    --text-main: #1e293b;
    --text-muted: #64748b;
    --success: #10b981;
    --success-light: #d1fae5;
    --warning: #f59e0b;
    --warning-light: #fef3c7;
    --error: #ef4444;
    --error-light: #fee2e2;
    --diff-added: #dcfce7;
    --diff-removed: #fee2e2;
}
```

### Task 1-2: 헤더 + 5단계 스텝 인디케이터

**Files:**
- Modify: `utils/ui_components.py` — `render_step_indicator()` 재작성 + 새 `render_header()` 추가

**변경 사항:**
- 3단계 → 5단계: Load, KR Review, Translating, Multi-Review, Complete
- 원형 아이콘 + 연결선 (Stitch 스타일: `w-8 h-8 rounded-full` + 가로 2px 라인)
- Material Symbols 아이콘 사용: check, chat_bubble, g_translate, checklist, check_circle
- 프로그레스바는 기존 방식 유지 (인디케이터 하단 통합)
- `render_header()`: 로고 + 앱 타이틀 + 스텝 인디케이터를 하나의 헤더 바로 통합

**step_map 변경:**
```python
step_map = {
    "idle": [0, 0, 0, 0, 0],      # 모두 pending
    "loading": [1, 0, 0, 0, 0],    # Load active
    "ko_review": [2, 1, 0, 0, 0],  # Load done, KR active
    "translating": [2, 2, 1, 0, 0], # Load+KR done, Trans active
    "final_review": [2, 2, 2, 1, 0], # +Trans done, Review active
    "done": [2, 2, 2, 2, 2],       # 모두 done
}
# 0=pending, 1=active, 2=done
```

### Task 1-3: app.py 사이드바 제거 + Full-Width 셸

**Files:**
- Modify: `app.py:227-370` (사이드바 블록 → 메인 영역 스텁)

**변경 사항:**
- `with st.sidebar:` 블록 전체 제거
- `st.set_page_config(layout="wide")` 유지
- 메인 영역 최상단에 `render_header()` 호출
- 각 화면 상태에 임시 플레이스홀더 마크업 배치:
  - idle: "Data Source Configuration" 카드 셸 (빈 카드)
  - ko_review: "Korean Review" 카드 셸
  - translating: "Translating..." 카드 셸
  - final_review: "Translation Review" 카드 셸
  - done: "Complete" 카드 셸
- 하단 Footer 렌더 함수 호출

### Task 1-4: 하단 Footer 컴포넌트

**Files:**
- Modify: `utils/ui_components.py` — 새 `render_footer()` 추가

**구현:**
- CSS: `position: sticky; bottom: 0;` + 배경/그림자
- 좌: Back 버튼 슬롯
- 우: 주요 액션 버튼 슬롯
- Streamlit에서는 `st.markdown()` + 별도 `st.columns()`로 구현 (sticky CSS)

### Task 1-5: 시각 확인

**Run:** `/Users/annmini/Library/Python/3.9/bin/streamlit run app.py`

**확인 항목:**
- [ ] 페이지 배경 #f8fafc (쿨 그레이) 적용
- [ ] Inter 폰트 로드 확인
- [ ] 헤더에 로고 + 5단계 스텝 인디케이터 표시
- [ ] 사이드바 완전히 사라짐
- [ ] 각 화면 상태별 플레이스홀더 카드 보임
- [ ] 카드에 그림자 + 둥근 모서리 적용
- [ ] 하단 Footer 영역 표시

### Phase 1 완료 체크리스트
- [ ] **시각**: 새 테마(Sky Blue + Inter) 전체 적용
- [ ] **레이아웃**: 사이드바 없음, Full-Width
- [ ] **스텝**: 5단계 인디케이터 올바른 상태 표시 (idle=모두 pending)
- [ ] **구조**: 에러 없이 앱 로드
- [ ] **버그**: `inject_custom_css()` 중복 호출 없음
- [ ] **버그**: 기존 `render_*` 함수 참조 에러 없음

---

## Phase 2: Data Source Configuration 카드 기능 연결

> 목표: 사이드바에 있던 모든 설정을 메인 영역 카드에 통합하고 작업 시작이 동작하도록 한다.

### Task 2-1: Data Source Configuration 카드 UI

**Files:**
- Modify: `utils/ui_components.py` — 새 `render_data_source_card()` 추가
- Modify: `app.py` — idle 화면에서 호출

**구현:**
- Section 1 헤더: 번호 원형(①) + "Data Source Configuration" + Connected 배지
- Row 1: Google Sheet URL (text_input) | Sheet Tab (selectbox) | Row Range (number_input × 2)
- Row 2: Translation Mode (세그먼트 컨트롤 — st.radio horizontal) | Target Languages (multiselect)
- Advanced (st.expander): Row Limit, Backup Folder

**Streamlit 위젯 매핑:**
```
Google Sheet URL  → st.text_input (3-col grid, col-span 6)
Sheet Tab         → st.selectbox (col-span 3)
Row Range         → st.number_input × 2 (col-span 3)
Mode              → st.radio(horizontal=True, options=["Full","New Only"])
Target Languages  → st.multiselect
Row Limit         → st.number_input (Advanced 내)
Backup Folder     → st.text_input (Advanced 내)
```

### Task 2-2: 시트 연결 로직 이동

**Files:**
- Modify: `app.py` — sidebar에서 main으로 이동

**변경 사항:**
- URL 입력 → 자동 연결 (기존 `connect_to_sheet` 로직 그대로)
- Connected 배지: `render_connection_badge()` → Data Source 카드 헤더 내 인라인
- 시트 탭 목록 로드 → selectbox 옵션으로 전달
- `_save_config()` 로직 유지

### Task 2-3: Start 버튼 + Footer 연결

**Files:**
- Modify: `app.py` — Footer 영역에 Start 버튼 배치

**변경 사항:**
- idle 상태: Footer 우측에 "Start Translation →" 버튼
- 기존 `start_button` 로직 그대로 유지 (graph.stream 시작)
- mode 값: `"A"` (Full) / `"B"` (New Only) 매핑

### Task 2-4: 검증

**Run:** streamlit run app.py

### Phase 2 완료 체크리스트
- [ ] **기능**: 시트 URL 입력 → 자동 연결 + Connected 배지
- [ ] **기능**: 시트 탭 드롭다운 정상 로드
- [ ] **기능**: Translation Mode 선택 (Full/New Only)
- [ ] **기능**: Target Languages 선택/해제
- [ ] **기능**: Start 버튼 클릭 → loading 시작 → ko_review 도달
- [ ] **기능**: Advanced 접이식 (Row Limit, Backup Folder) 동작
- [ ] **기능**: URL 영속 저장 (.app_config.json) 정상
- [ ] **시각**: 카드 레이아웃이 Stitch 디자인과 유사
- [ ] **버그**: mode="A"/"B" 매핑 정확 (session_state 확인)
- [ ] **버그**: 연결 실패 시 에러 표시 정상

---

## Phase 3: KR Review 화면 개편

> 목표: 한국어 검수 화면을 Stitch 디자인의 테이블 형태로 개편하고 HITL 1 동작 유지.

### Task 3-1: KR Review 테이블 UI

**Files:**
- Modify: `utils/ui_components.py` — 새 `render_ko_review_table()` 추가
- Modify: `app.py:583-665` — ko_review 화면 재작성

**구현:**
- 카드 헤더: ② Source Language (Korean) Review + "N issues" 배지
- 기존 `st.dataframe(style_ko_diff())` → 커스텀 HTML 테이블
- 컬럼: Original (Korean) | AI Suggested Fix | Category Badge
- 카테고리 배지 CSS: Typo(rose), Grammar(amber), Spacing(blue), Style(purple)
- Approve/Reject 버튼은 Footer에 배치

**주의:** 현재 `ko_review_results`에는 카테고리 필드가 없음 → 배지는 일단 "수정" 단일 배지로 통일하고, 향후 AI 분류 추가 시 확장 가능하도록 구조만 준비.

### Task 3-2: HITL 1 버튼 연결

**Files:**
- Modify: `app.py` — Footer에 Approve/Skip 버튼

**변경 사항:**
- Footer 좌: "Back" (idle로 돌아가기)
- Footer 우: "Skip → 원본 유지" + "Approve & Translate →"
- 기존 `btn_approve`/`btn_reject` 로직 그대로 연결
- ko_count == 0 자동 승인 로직 유지

### Task 3-3: 검증

### Phase 3 완료 체크리스트
- [ ] **기능**: 수정 제안 N건 → 테이블에 올바르게 표시
- [ ] **기능**: 0건 → 자동 승인 → translating 직행
- [ ] **기능**: Approve 클릭 → translating 전환
- [ ] **기능**: Skip 클릭 → 원본 유지 + translating 전환
- [ ] **기능**: CSV 다운로드 버튼 동작
- [ ] **시각**: 테이블 스타일이 Stitch 디자인과 유사
- [ ] **시각**: 배지 색상 올바름
- [ ] **버그**: 빈 DataFrame 시 크래시 없음
- [ ] **버그**: st.rerun() 정상 동작 (무한 루프 없음)

---

## Phase 4: Translating + Final Review 화면 개편

> 목표: 번역 진행 스트리밍 UI와 최종 검수 테이블을 새 디자인으로 교체.

### Task 4-1: Translating 화면

**Files:**
- Modify: `app.py:667-735` — translating 화면 재작성

**변경 사항:**
- 스텝 인디케이터: "Translating" 활성 + 프로그레스바 (기존 방식 유지)
- 로그 터미널: 새 디자인 토큰 적용 (`render_log_terminal` CSS 변경은 Phase 1에서 완료)
- Cancel 버튼: Footer에 배치 ("Cancel — 한국어 검수로 돌아가기")
- `_run_translation_streaming()` 함수는 변경 없음

### Task 4-2: Final Review 화면 — Progress Bar + 테이블

**Files:**
- Modify: `utils/ui_components.py` — 새 `render_progress_bar()` + `render_translation_table()` 추가
- Modify: `app.py:737-888` — final_review 화면 재작성

**구현:**
- Overall Progress 카드: 프로그레스바 + Done/Pending/Errors 메트릭
- 번역 테이블: Key ID | Source (KR) | Previous Translation | New Translation | Action
- Diff 하이라이팅: 변경 텍스트에 초록 배경 (`--diff-added`)
- Failed rows 별도 섹션 유지 (기존 st.warning + st.dataframe)
- Footer: "Reject — 원복" + "Apply to Sheet →"

### Task 4-3: HITL 2 + Writer 연결

**변경 사항:**
- 기존 `btn_approve`/`btn_reject` 로직을 Footer 버튼에 연결
- `batch_update_sheet` + `batch_format_cells` 호출 그대로 유지
- Tool_Status 원복 로직 유지

### Task 4-4: 검증

### Phase 4 완료 체크리스트
- [ ] **기능**: 번역 스트리밍 실시간 로그 표시
- [ ] **기능**: 프로그레스바 실시간 업데이트
- [ ] **기능**: Cancel → 한국어 검수로 복귀
- [ ] **기능**: Final Review 테이블에 번역 결과 표시
- [ ] **기능**: Apply → 시트 업데이트 + done 전환
- [ ] **기능**: Reject → Tool_Status 원복 + done 전환
- [ ] **기능**: Failed rows 표시 + CSV 다운로드
- [ ] **시각**: Progress 바 스타일 (Sky Blue)
- [ ] **시각**: Diff 하이라이팅 (초록/빨강)
- [ ] **버그**: 스트리밍 중 UI 멈춤/깨짐 없음
- [ ] **버그**: Cancel 후 그래프 재생성 정상
- [ ] **버그**: 빈 review_results 시 크래시 없음

---

## Phase 5: Done 화면 + 색상 정렬 + 마무리

> 목표: 완료 화면 개편, 전체 색상 팔레트 일관성 정렬, E2E 워크플로 검증.

### Task 5-1: Done 화면 개편

**Files:**
- Modify: `app.py:890-990` — done 화면 재작성
- Modify: `utils/ui_components.py` — `render_done_header()` 업데이트

**구현:**
- 체크마크 아이콘: Sky Blue primary 색상으로 변경
- 메트릭 그리드: 새 디자인 토큰 (이미 Phase 1에서 CSS 변경)
- 다운로드 버튼 4개: 새 버튼 스타일
- "New Task →" Footer 버튼
- 적용 취소 시 다른 메시지 + 아이콘

### Task 5-2: diff_report.py 색상 정렬

**Files:**
- Modify: `utils/diff_report.py:44-63`

**변경:**
```python
# Before
"background-color: #FFEBEE"  # Warm red
"background-color: #E8F5E9"  # Warm green

# After
"background-color: #fee2e2"  # --diff-removed (새 토큰)
"background-color: #dcfce7"  # --diff-added (새 토큰)
```

### Task 5-3: sheets.py 하이라이트 색상 정렬

**Files:**
- Modify: `utils/sheets.py:127-131`

**변경:**
```python
# Before
HIGHLIGHT_COLORS = {
    "translation": {"red": 1.0, "green": 0.976, "blue": 0.769},
    "review_failed": {"red": 1.0, "green": 0.922, "blue": 0.933},
    "completed": {"red": 0.89, "green": 0.949, "blue": 0.992},
}

# After — Sky Blue 팔레트에 맞춤
HIGHLIGHT_COLORS = {
    "translation": {"red": 0.878, "green": 0.961, "blue": 0.996},  # #E0F5FE primary-light
    "review_failed": {"red": 0.996, "green": 0.886, "blue": 0.886},  # #FEE2E2 diff-removed
    "completed": {"red": 0.863, "green": 0.988, "blue": 0.906},  # #DCFCE7 diff-added
}
```

### Task 5-4: 미사용 함수/CSS 정리

**Files:**
- Modify: `utils/ui_components.py`
- Modify: `app.py`

**삭제 대상:**
- `render_sidebar_logo()` — 사이드바 제거됨
- `render_saved_url()` — 사이드바 전용이었음
- `render_app_header()` — `render_header()`로 대체
- 사이드바 관련 CSS 전체 (Phase 1에서 이미 삭제했으면 확인)
- `app.py`의 `render_sidebar_logo`, `render_saved_url` import 제거

### Task 5-5: E2E 워크플로 검증

**Run:** streamlit run app.py

### Phase 5 완료 체크리스트 (E2E)
- [ ] **E2E**: idle → URL 입력 → 연결 → 시트 선택 → 모드 선택 → Start
- [ ] **E2E**: loading → 프로그레스 → ko_review 도달
- [ ] **E2E**: ko_review → 0건 자동승인 / N건 테이블 표시 → Approve
- [ ] **E2E**: translating → 로그 스트리밍 → final_review 도달
- [ ] **E2E**: final_review → 테이블 표시 → Apply → done
- [ ] **E2E**: done → 메트릭 + 다운로드 4개 → New Task → idle
- [ ] **E2E**: Cancel 플로우 (translating → ko_review 복귀)
- [ ] **E2E**: Reject 플로우 (final_review → Tool_Status 원복 → done)
- [ ] **색상**: diff_report 하이라이트 새 팔레트 확인
- [ ] **색상**: sheets.py 셀 하이라이트 새 팔레트 확인
- [ ] **정리**: 미사용 함수/import 없음
- [ ] **정리**: 콘솔 에러/경고 없음 (urllib3 제외)

---

## 수정 파일 요약

| 파일 | Phase | 변경 범위 |
|------|-------|----------|
| `utils/ui_components.py` | 1-5 | CSS 전면 교체 + 컴포넌트 추가/수정/삭제 |
| `app.py` | 1-5 | 사이드바 제거, 레이아웃 재구성, 전 화면 UI 교체 |
| `utils/diff_report.py` | 5 | 색상 4줄 변경 |
| `utils/sheets.py` | 5 | HIGHLIGHT_COLORS 3줄 변경 |

## 변경하지 않는 파일
- `agents/graph.py`, `agents/state.py`, `agents/prompts.py`
- `agents/nodes/*` (translator, reviewer, writer, data_backup, context_glossary)
- `config/constants.py`, `config/glossary.py`
- `utils/validation.py`, `utils/cost_tracker.py`
