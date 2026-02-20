# UI Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** app.py의 UI를 Warm & Minimalist 스타일로 전면 리디자인 (비즈니스 로직 변경 없음)

**Architecture:** 커스텀 HTML 스텝 인디케이터 + 고급 CSS를 적용한 Streamlit 네이티브 UI. UI 렌더링 헬퍼를 `utils/ui_components.py`로 분리하여 app.py를 깔끔하게 유지.

**Tech Stack:** Streamlit, CSS3 (애니메이션 포함), HTML5

---

### Task 1: UI 헬퍼 모듈 생성

**Files:**
- Create: `utils/ui_components.py`

**Step 1: `utils/ui_components.py` 작성**

스텝 인디케이터, 카드 헤더, CSS 주입을 위한 헬퍼 함수 모듈 생성.

```python
"""UI 컴포넌트 헬퍼 — 커스텀 HTML 렌더링"""

import streamlit as st


def inject_custom_css():
    """전체 커스텀 CSS 주입"""
    st.markdown("""
<style>
    /* ── 전역 ── */
    .stApp {
        background-color: #F6F5F0;
    }

    /* ── 사이드바 ── */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E8E6E1;
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2C2C2C !important;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #C85A32;
    }

    /* ── 텍스트 ── */
    h1, h2, h3, p, span, label {
        color: #2C2C2C !important;
    }

    /* ── 버튼 ── */
    .stButton > button[kind="primary"] {
        background-color: #C85A32;
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #B04E2A;
        box-shadow: 0 4px 12px rgba(200, 90, 50, 0.3);
        transform: translateY(-1px);
    }
    .stButton > button:not([kind="primary"]) {
        border-radius: 12px;
        border: 1px solid #D5D3CE;
        color: #2C2C2C;
        font-weight: 500;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #C85A32;
        color: #C85A32;
        background-color: #FFF5F0;
    }

    /* ── 다운로드 버튼 ── */
    .stDownloadButton > button {
        border-radius: 12px;
        border: 1px solid #C85A32;
        color: #C85A32;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stDownloadButton > button:hover {
        background-color: #FFF5F0;
    }

    /* ── Progress bar ── */
    .stProgress > div > div {
        background-color: #C85A32;
    }

    /* ── 구분선 ── */
    hr {
        border: none;
        border-top: 1px solid #E8E6E1;
        margin: 1.5rem 0;
    }

    /* ── 카드 ── */
    .dl-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 0;
        margin: 1rem 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        overflow: hidden;
    }
    .dl-card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #F0EDE8;
        border-left: 4px solid #C85A32;
    }
    .dl-card-header .icon {
        font-size: 1.3rem;
    }
    .dl-card-header .title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2C2C2C;
    }
    .dl-card-header .badge {
        margin-left: auto;
        background: #FFF5F0;
        color: #C85A32;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .dl-card-body {
        padding: 1.5rem;
    }

    /* ── 스텝 인디케이터 ── */
    .step-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1.2rem 2rem;
        background: #FFFFFF;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        margin-bottom: 1.5rem;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .step-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .step-circle.done {
        background-color: #E8F5E9;
        color: #2E7D32;
    }
    .step-circle.active {
        background-color: #C85A32;
        color: white;
        animation: pulse 2s ease-in-out infinite;
    }
    .step-circle.pending {
        background-color: #F0EDE8;
        color: #9E9E9E;
    }
    .step-label {
        font-size: 0.85rem;
        font-weight: 600;
    }
    .step-label.done { color: #2E7D32; }
    .step-label.active { color: #C85A32; }
    .step-label.pending { color: #9E9E9E; }
    .step-connector {
        width: 60px;
        height: 2px;
        margin: 0 12px;
        flex-shrink: 0;
    }
    .step-connector.done { background-color: #2E7D32; }
    .step-connector.active { background: linear-gradient(90deg, #2E7D32, #C85A32); }
    .step-connector.pending { background-color: #E0E0E0; }

    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(200, 90, 50, 0.4); }
        50% { box-shadow: 0 0 0 8px rgba(200, 90, 50, 0); }
    }

    /* ── 완료 화면 ── */
    .done-header {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    .done-header .checkmark {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .done-header h2 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2E7D32 !important;
    }
    .done-header p {
        color: #757575 !important;
        font-size: 0.95rem;
    }

    /* ── 연결 뱃지 ── */
    .connection-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .connection-badge.success {
        background: #E8F5E9;
        color: #2E7D32;
    }
    .connection-badge.error {
        background: #FFEBEE;
        color: #C62828;
    }

    /* ── 앱 헤더 ── */
    .app-header {
        text-align: center;
        padding: 0.5rem 0 1rem;
    }
    .app-header h1 {
        font-size: 1.6rem;
        font-weight: 800;
        color: #2C2C2C !important;
        margin-bottom: 0.2rem;
    }
    .app-header .subtitle {
        font-size: 0.85rem;
        color: #9E9E9E !important;
    }

    /* ── 사이드바 로고 ── */
    .sidebar-logo {
        text-align: center;
        padding: 0.5rem 0 1rem;
        border-bottom: 1px solid #F0EDE8;
        margin-bottom: 1rem;
    }
    .sidebar-logo .name {
        font-size: 1.3rem;
        font-weight: 800;
        color: #C85A32 !important;
    }
    .sidebar-logo .version {
        font-size: 0.75rem;
        color: #9E9E9E !important;
    }

    /* ── 데이터프레임 ── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


def render_step_indicator(current_step: str):
    """3단계 프로그레스 인디케이터 렌더링"""
    steps = [
        {"label": "한국어 검수", "key": "step1"},
        {"label": "번역 / 검수", "key": "step2"},
        {"label": "최종 승인", "key": "step3"},
    ]

    # current_step → 각 스텝 상태 매핑
    step_map = {
        "idle":         ["pending", "pending", "pending"],
        "loading":      ["active",  "pending", "pending"],
        "ko_review":    ["done",    "pending", "pending"],
        "translating":  ["done",    "active",  "pending"],
        "final_review": ["done",    "done",    "active"],
        "done":         ["done",    "done",    "done"],
    }
    states = step_map.get(current_step, ["pending", "pending", "pending"])

    def circle(state, num):
        if state == "done":
            return f'<div class="step-circle done">&#10003;</div>'
        elif state == "active":
            return f'<div class="step-circle active">{num}</div>'
        else:
            return f'<div class="step-circle pending">{num}</div>'

    def connector(prev_state, curr_state):
        if prev_state == "done" and curr_state == "done":
            cls = "done"
        elif prev_state == "done" and curr_state == "active":
            cls = "active"
        else:
            cls = "pending"
        return f'<div class="step-connector {cls}"></div>'

    html_parts = []
    for i, (step, state) in enumerate(zip(steps, states)):
        if i > 0:
            html_parts.append(connector(states[i - 1], state))
        html_parts.append(
            f'<div class="step-item">'
            f'  {circle(state, i + 1)}'
            f'  <span class="step-label {state}">{step["label"]}</span>'
            f'</div>'
        )

    html = f'<div class="step-indicator">{"".join(html_parts)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_card_start(icon: str, title: str, badge: str = ""):
    """카드 시작 (헤더 + body 시작)"""
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    st.markdown(
        f'<div class="dl-card">'
        f'  <div class="dl-card-header">'
        f'    <span class="icon">{icon}</span>'
        f'    <span class="title">{title}</span>'
        f'    {badge_html}'
        f'  </div>'
        f'  <div class="dl-card-body">',
        unsafe_allow_html=True,
    )


def render_card_end():
    """카드 끝"""
    st.markdown('</div></div>', unsafe_allow_html=True)


def render_sidebar_logo():
    """사이드바 로고"""
    st.markdown(
        '<div class="sidebar-logo">'
        '  <div class="name">DevLocal</div>'
        '  <div class="version">v1.0</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_connection_badge(connected: bool, sheet_count: int = 0):
    """시트 연결 상태 뱃지"""
    if connected:
        st.markdown(
            f'<span class="connection-badge success">&#10003; 연결됨 &middot; {sheet_count}개 시트</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="connection-badge error">&#10007; 미연결</span>',
            unsafe_allow_html=True,
        )


def render_app_header():
    """메인 영역 앱 헤더"""
    st.markdown(
        '<div class="app-header">'
        '  <h1>게임 로컬라이징 자동화 툴</h1>'
        '  <span class="subtitle">AI 기반 다국어 번역 &middot; 검수 &middot; 자동화</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_done_header():
    """완료 화면 헤더"""
    st.markdown(
        '<div class="done-header">'
        '  <div class="checkmark">&#10003;</div>'
        '  <h2>작업 완료</h2>'
        '  <p>모든 번역 및 검수가 성공적으로 완료되었습니다.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
```

**Step 2: 문법 검증**

Run: `python3 -c "import ast; ast.parse(open('utils/ui_components.py').read()); print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add utils/ui_components.py
git commit -m "feat: add UI component helpers for redesign"
```

---

### Task 2: app.py CSS 교체 및 사이드바 리디자인

**Files:**
- Modify: `app.py` (lines 37-96: CSS 섹션, lines 132-189: 사이드바 섹션)

**Step 1: CSS 섹션 교체**

기존 `st.markdown("""<style>...</style>""")` 블록(37-96행)을 삭제하고, `inject_custom_css()` 호출로 대체.

```python
from utils.ui_components import (
    inject_custom_css,
    render_step_indicator,
    render_card_start,
    render_card_end,
    render_sidebar_logo,
    render_connection_badge,
    render_app_header,
    render_done_header,
)

# 기존 CSS 블록 대신:
inject_custom_css()
```

**Step 2: 사이드바 리디자인**

기존 사이드바 코드를 아래로 교체:

```python
with st.sidebar:
    render_sidebar_logo()

    # ── 시트 연결 ──
    st.markdown("## 시트 연결")
    sheet_url = st.text_input(
        "구글 시트 URL",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        label_visibility="collapsed",
    )

    sheet_names = []
    if sheet_url:
        try:
            if st.session_state.spreadsheet is None or st.session_state.get("_last_url") != sheet_url:
                with st.spinner("시트 연결 중..."):
                    st.session_state.spreadsheet = connect_to_sheet(sheet_url)
                    st.session_state._last_url = sheet_url
            sheet_names = get_worksheet_names(st.session_state.spreadsheet)
            render_connection_badge(True, len(sheet_names))
        except Exception as e:
            render_connection_badge(False)
            st.error(f"연결 실패: {e}")

    selected_sheet = st.selectbox(
        "작업 대상 시트",
        options=sheet_names,
        disabled=not sheet_names,
    )

    st.divider()

    # ── 번역 설정 ──
    st.markdown("## 번역 설정")
    target_langs = st.multiselect(
        "타겟 언어",
        options=list(SUPPORTED_LANGUAGES.keys()),
        default=list(SUPPORTED_LANGUAGES.keys()),
        format_func=lambda x: f"{x.upper()} ({SUPPORTED_LANGUAGES[x]})",
    )

    mode = st.radio(
        "작업 모드",
        options=["A", "B"],
        format_func=lambda x: "모드 A (전체 번역/검수)" if x == "A" else "모드 B (빈칸 번역)",
        horizontal=True,
        help="A: 기존 번역 유무와 상관없이 전체 재번역\nB: 빈칸만 번역 (비용 절감)",
    )

    row_limit = st.number_input(
        "테스트 행 수 제한 (0 = 전체)",
        min_value=0,
        max_value=1000,
        value=0,
        help="테스트 시 처리할 최대 행 수를 지정합니다. 0이면 전체 처리.",
    )

    st.divider()

    start_button = st.button(
        "작업 시작",
        type="primary",
        disabled=(not sheet_url or not selected_sheet or not target_langs),
        use_container_width=True,
    )
```

**Step 3: 메인 헤더 + 스텝 인디케이터 교체**

기존 `st.title(...)` + 봇 이메일 섹션을 교체:

```python
# ── 메인 영역 ──
render_app_header()

# 봇 이메일 안내
try:
    bot_email = get_bot_email()
    if bot_email:
        st.info(
            f"시트 [공유] 버튼에서 **편집자**로 초대: `{bot_email}`"
        )
except Exception:
    pass

# 스텝 인디케이터
render_step_indicator(st.session_state.current_step)
```

**Step 4: 문법 검증**

Run: `python3 -c "import ast; ast.parse(open('app.py').read()); print('OK')"`
Expected: OK

**Step 5: 시각 확인**

Run: 브라우저에서 localhost:8501 새로고침 → 사이드바 로고, 연결 뱃지, 스텝 인디케이터 확인

**Step 6: Commit**

```bash
git add app.py
git commit -m "feat: redesign sidebar and add step indicator"
```

---

### Task 3: 백업 카드 + HITL 1 카드 리디자인

**Files:**
- Modify: `app.py` (lines 321-466: 백업 + HITL 1 섹션)

**Step 1: 백업 카드 교체**

기존 `<div class="card">` 래핑을 `render_card_start/end`로 교체:

```python
if st.session_state.backup_csv:
    _sheet = st.session_state.get('_last_sheet', '')
    _rows = len(st.session_state.df) if st.session_state.df is not None else 0
    render_card_start("📦", "원본 백업", f"{_sheet} · {_rows}행")
    st.warning("아래 파일은 **작업 시작 전 원본 데이터**입니다. 반드시 다운로드하세요!")
    st.download_button(
        label=f"📥 {st.session_state.backup_filename} 다운로드",
        data=st.session_state.backup_csv,
        file_name=st.session_state.backup_filename,
        mime="text/csv",
        use_container_width=True,
    )
    render_card_end()
```

**Step 2: HITL 1 카드 교체**

```python
if st.session_state.current_step == "ko_review":
    ko_count = len(st.session_state.ko_report_df) if st.session_state.ko_report_df is not None and not st.session_state.ko_report_df.empty else 0
    render_card_start("✏️", "한국어 사전 검수", f"수정 제안 {ko_count}건" if ko_count else "")

    if ko_count > 0:
        st.dataframe(st.session_state.ko_report_df, use_container_width=True)
        st.download_button(
            label="📥 한국어 변경 리포트 (CSV)",
            data=st.session_state.ko_report_csv,
            file_name="ko_review_report.csv",
            mime="text/csv",
        )
    else:
        st.success("수정 제안 없음 — 원본 한국어가 양호합니다.")

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        # ... 승인 버튼 (기존 로직 그대로) ...
    with col2:
        # ... 반려 버튼 (기존 로직 그대로) ...

    render_card_end()
```

버튼 핸들러 내부 로직(graph.invoke, batch_update_sheet 등)은 **일체 변경하지 않음**.

**Step 3: 문법 검증 + 시각 확인**

Run: `python3 -c "import ast; ast.parse(open('app.py').read()); print('OK')"`
브라우저 새로고침 → 백업 카드 확인

**Step 4: Commit**

```bash
git add app.py
git commit -m "feat: redesign backup and ko_review cards"
```

---

### Task 4: HITL 2 카드 + 완료 화면 + 로그 리디자인

**Files:**
- Modify: `app.py` (lines 468-583: HITL 2 + 완료 + 로그)

**Step 1: HITL 2 카드 교체**

```python
if st.session_state.current_step == "final_review":
    review_count = len(st.session_state.translation_report_df) if st.session_state.translation_report_df is not None and not st.session_state.translation_report_df.empty else 0
    fail_count = len(st.session_state.graph_result.get("failed_rows", [])) if st.session_state.graph_result else 0
    render_card_start("🔍", "최종 번역 검토", f"변경 {review_count}건 · 실패 {fail_count}건")

    if review_count > 0:
        st.dataframe(st.session_state.translation_report_df, use_container_width=True)
        st.download_button(
            label="📥 번역 변경 리포트 (CSV)",
            data=st.session_state.translation_report_csv,
            file_name="translation_diff_report.csv",
            mime="text/csv",
        )
    else:
        st.info("변경 사항 없음")

    # 검수실패 행 표시
    if fail_count > 0:
        st.warning(f"검수 실패: {fail_count}건 — 아래 행은 3회 재시도 후에도 검증 통과 실패")
        failed_df = pd.DataFrame(st.session_state.graph_result.get("failed_rows", []))
        st.dataframe(failed_df, use_container_width=True)

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        # ... 승인 버튼 (기존 로직 그대로) ...
    with col2:
        # ... 반려 버튼 (기존 로직 그대로) ...

    render_card_end()
```

**Step 2: 완료 화면 교체**

```python
if st.session_state.current_step == "done":
    render_card_start("", "")  # 헤더 없는 카드 — 아래에서 커스텀 헤더 사용
    # 실제로는 render_card_start 대신 직접 div:
    st.markdown('<div class="dl-card"><div class="dl-card-body">', unsafe_allow_html=True)

    render_done_header()

    # 비용 요약
    if st.session_state.cost_summary:
        from config.constants import LLM_PRICING
        summary = st.session_state.cost_summary
        input_t = summary.get("input_tokens", 0)
        output_t = summary.get("output_tokens", 0)
        cost = (input_t * LLM_PRICING["input"]) + (output_t * LLM_PRICING["output"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Input 토큰", f"{input_t:,}")
        col2.metric("Output 토큰", f"{output_t:,}")
        col3.metric("예상 비용", f"${cost:.4f}")

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    if st.button("새 작업 시작", use_container_width=True):
        # ... 기존 초기화 로직 그대로 ...

    st.markdown('</div></div>', unsafe_allow_html=True)
```

**Step 3: 로그 섹션 — Progress bar를 스텝 인디케이터 아래로 이동 (이미 render_step_indicator에서 상태 표현)**

```python
# 기존 progress bar 제거 (스텝 인디케이터가 대체)
# if st.session_state.current_step == "translating":
#     st.progress(0.5, text="번역 및 검수 진행 중...")

# 로그는 그대로 유지하되 카드로 감싸기
if st.session_state.logs:
    with st.expander("📋 실행 로그", expanded=False):
        log_text = "\n".join(st.session_state.logs)
        st.text_area("로그", value=log_text, height=300, disabled=True, label_visibility="collapsed")
```

**Step 4: 문법 검증 + 시각 확인**

Run: `python3 -c "import ast; ast.parse(open('app.py').read()); print('OK')"`
브라우저 새로고침 → HITL 2, 완료 화면, 로그 확인

**Step 5: Commit**

```bash
git add app.py
git commit -m "feat: redesign final review, done screen, and logs"
```

---

### Task 5: 최종 시각 검증 및 미세 조정

**Files:**
- Modify: `app.py`, `utils/ui_components.py` (필요 시)

**Step 1: 전체 플로우 시각 점검**

브라우저에서 다음 화면들을 하나씩 확인:
1. idle 상태 (초기 화면) — 스텝 인디케이터 모두 회색
2. 시트 URL 입력 → 연결 뱃지 초록
3. 작업 시작 → 백업 카드 표시
4. ko_review → HITL 1 카드 + 스텝 1 완료 표시
5. (가능하면) translating → 스텝 2 활성
6. done → 완료 화면 + 통계

**Step 2: CSS 미세 조정**

시각 점검 결과 발견된 간격/색상/크기 이슈를 `utils/ui_components.py`의 CSS에서 수정.

**Step 3: 최종 Commit**

```bash
git add app.py utils/ui_components.py
git commit -m "style: fine-tune UI spacing and colors"
```
