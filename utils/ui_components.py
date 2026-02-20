"""UI 컴포넌트 헬퍼 — 모던 SaaS 디자인 시스템 (Indigo + Dark Sidebar)"""

import html as html_module
import streamlit as st


def inject_custom_css():
    """전체 커스텀 CSS 주입 — 모던 SaaS 스타일"""
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ══════════════════════════════════════════
       Design Tokens
       ══════════════════════════════════════════ */
    :root {
        --bg-main: #F8FAFC;
        --bg-card: #FFFFFF;
        --bg-sidebar: #0F172A;
        --bg-sidebar-hover: rgba(255,255,255,0.05);
        --bg-sidebar-active: rgba(99,102,241,0.12);

        --accent: #6366F1;
        --accent-hover: #4F46E5;
        --accent-light: #EEF2FF;
        --accent-glow: rgba(99,102,241,0.25);

        --success: #10B981;
        --success-light: #ECFDF5;
        --warning: #F59E0B;
        --warning-light: #FFFBEB;
        --error: #EF4444;
        --error-light: #FEF2F2;

        --text-primary: #0F172A;
        --text-secondary: #475569;
        --text-muted: #94A3B8;
        --text-sidebar: #CBD5E1;
        --text-sidebar-muted: #64748B;

        --border: #E2E8F0;
        --border-light: #F1F5F9;

        --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.06), 0 2px 4px -2px rgba(0,0,0,0.04);

        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 14px;
        --radius-xl: 20px;
    }

    /* ══════════════════════════════════════════
       Global
       ══════════════════════════════════════════ */
    .stApp {
        background-color: var(--bg-main);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary) !important;
    }

    /* ══════════════════════════════════════════
       Dark Sidebar
       ══════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        border-right: 1px solid rgba(255,255,255,0.04);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.8rem;
    }

    /* Sidebar text overrides */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-sidebar) !important;
    }
    [data-testid="stSidebar"] .sidebar-section-title {
        font-size: 0.68rem;
        font-weight: 600;
        color: var(--text-sidebar-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
        padding-bottom: 0;
        border-bottom: none;
    }

    /* Sidebar text input */
    [data-testid="stSidebar"] .stTextInput input {
        background-color: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: var(--radius-md);
        color: #E2E8F0 !important;
        font-size: 0.85rem;
    }
    [data-testid="stSidebar"] .stTextInput input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-glow);
    }
    [data-testid="stSidebar"] .stTextInput input::placeholder {
        color: var(--text-sidebar-muted) !important;
    }

    /* Sidebar selectbox */
    [data-testid="stSidebar"] [data-baseweb="select"] {
        border-radius: var(--radius-md);
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.1);
        color: #E2E8F0 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div:hover {
        border-color: rgba(255,255,255,0.2);
    }

    /* Sidebar multiselect */
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div {
        background-color: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.1);
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background-color: var(--accent) !important;
        color: white !important;
        border-radius: var(--radius-sm) !important;
    }

    /* Sidebar radio */
    [data-testid="stSidebar"] .stRadio label {
        color: var(--text-sidebar) !important;
    }

    /* Sidebar number input */
    [data-testid="stSidebar"] .stNumberInput input {
        background-color: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.1);
        color: #E2E8F0 !important;
        border-radius: var(--radius-md);
    }

    /* Sidebar divider */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.06);
        margin: 0.8rem 0;
    }

    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
        border: none;
        color: white !important;
        width: 100%;
    }
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
        background: rgba(255,255,255,0.04);
        border-color: rgba(255,255,255,0.1);
        color: var(--text-sidebar) !important;
        font-size: 0.8rem;
    }
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {
        background: rgba(99,102,241,0.12);
        border-color: var(--accent);
        color: #A5B4FC !important;
    }

    /* Sidebar expander */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        color: var(--text-sidebar) !important;
        font-size: 0.8rem;
    }

    /* ══════════════════════════════════════════
       Buttons — Main Area
       ══════════════════════════════════════════ */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
        border: none;
        border-radius: var(--radius-md);
        color: white !important;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.55rem 1.4rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 1px 3px rgba(99,102,241,0.3);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--accent-hover) 0%, #4338CA 100%);
        box-shadow: 0 4px 14px rgba(99,102,241,0.35);
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0);
    }
    .stButton > button:not([kind="primary"]) {
        border-radius: var(--radius-md);
        border: 1px solid var(--border);
        color: var(--text-secondary) !important;
        font-weight: 500;
        font-size: 0.875rem;
        padding: 0.55rem 1.4rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        background: var(--bg-card);
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: var(--accent);
        color: var(--accent) !important;
        background: var(--accent-light);
    }

    /* Download button */
    .stDownloadButton > button {
        border-radius: var(--radius-md);
        border: 1px solid var(--border);
        color: var(--text-secondary) !important;
        font-weight: 500;
        font-size: 0.82rem;
        transition: all 0.2s ease;
        background: var(--bg-card);
    }
    .stDownloadButton > button:hover {
        border-color: var(--accent);
        color: var(--accent) !important;
        background: var(--accent-light);
    }

    /* ══════════════════════════════════════════
       Cards
       ══════════════════════════════════════════ */
    .dl-card {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border);
        padding: 0;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        overflow: hidden;
        animation: fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .dl-card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0.85rem 1.3rem;
        border-bottom: 1px solid var(--border-light);
        background: linear-gradient(135deg, #FAFBFF 0%, #F8FAFC 100%);
    }
    .dl-card-header .icon { font-size: 1.05rem; }
    .dl-card-header .title {
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.01em;
    }
    .dl-card-header .badge {
        margin-left: auto;
        background: var(--accent-light);
        color: var(--accent);
        padding: 2px 10px;
        border-radius: var(--radius-xl);
        font-size: 0.72rem;
        font-weight: 600;
    }
    .dl-card-body { padding: 1.2rem 1.3rem; }

    /* ══════════════════════════════════════════
       Step Indicator
       ══════════════════════════════════════════ */
    .step-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.9rem 2rem;
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
        margin-bottom: 1.2rem;
        gap: 0;
    }
    .step-item { display: flex; align-items: center; gap: 7px; }
    .step-circle {
        width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem; font-weight: 700; flex-shrink: 0;
        transition: all 0.3s ease;
    }
    .step-circle.done { background-color: var(--success-light); color: var(--success); }
    .step-circle.active {
        background: linear-gradient(135deg, var(--accent), var(--accent-hover));
        color: white;
        animation: pulse-indigo 2s ease-in-out infinite;
    }
    .step-circle.pending { background-color: var(--border-light); color: var(--text-muted); }
    .step-label { font-size: 0.78rem; font-weight: 600; letter-spacing: -0.01em; }
    .step-label.done { color: var(--success); }
    .step-label.active { color: var(--accent); }
    .step-label.pending { color: var(--text-muted); }
    .step-connector {
        width: 46px; height: 2px; margin: 0 10px;
        flex-shrink: 0; border-radius: 1px;
    }
    .step-connector.done { background-color: var(--success); }
    .step-connector.active { background: linear-gradient(90deg, var(--success), var(--accent)); }
    .step-connector.pending { background-color: var(--border); }

    /* ══════════════════════════════════════════
       Animations
       ══════════════════════════════════════════ */
    @keyframes pulse-indigo {
        0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }
        50% { box-shadow: 0 0 0 8px rgba(99,102,241,0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ══════════════════════════════════════════
       Done Screen
       ══════════════════════════════════════════ */
    .done-header {
        text-align: center; padding: 1.5rem 0 1rem;
        animation: fadeInUp 0.5s ease-out;
    }
    .done-header .checkmark {
        width: 48px; height: 48px; border-radius: 50%;
        background: var(--success-light); color: var(--success);
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 1.5rem; margin-bottom: 0.6rem;
    }
    .done-header h2 {
        font-size: 1.2rem; font-weight: 700;
        color: var(--text-primary) !important; margin-bottom: 0.2rem;
    }
    .done-header p { color: var(--text-muted) !important; font-size: 0.85rem; }

    /* ══════════════════════════════════════════
       Connection Badge
       ══════════════════════════════════════════ */
    .connection-badge {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 3px 10px; border-radius: var(--radius-xl);
        font-size: 0.72rem; font-weight: 600; margin-top: 4px;
    }
    .connection-badge.success { background: rgba(16,185,129,0.12); color: #34D399; }
    .connection-badge.error { background: rgba(239,68,68,0.12); color: #F87171; }

    /* ══════════════════════════════════════════
       App Header
       ══════════════════════════════════════════ */
    .app-header { text-align: center; padding: 0.2rem 0 1rem; }
    .app-header h1 {
        font-size: 1.3rem !important; font-weight: 800;
        color: var(--text-primary) !important;
        margin-bottom: 0.1rem; letter-spacing: -0.025em;
    }
    .app-header .subtitle {
        font-size: 0.78rem; color: var(--text-muted) !important; font-weight: 400;
    }

    /* ══════════════════════════════════════════
       Sidebar Logo
       ══════════════════════════════════════════ */
    .sidebar-logo {
        text-align: center; padding: 0.2rem 0 0.8rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 0.8rem;
    }
    .sidebar-logo .name {
        font-size: 1.15rem; font-weight: 800;
        color: #FFFFFF !important; letter-spacing: -0.02em;
    }
    .sidebar-logo .dot { color: #818CF8 !important; }
    .sidebar-logo .version {
        font-size: 0.65rem; color: var(--text-sidebar-muted) !important; font-weight: 500;
    }

    /* ══════════════════════════════════════════
       Saved URL Display
       ══════════════════════════════════════════ */
    .saved-url {
        display: flex; align-items: center; gap: 8px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: var(--radius-md);
        padding: 7px 11px; margin-bottom: 0.4rem;
    }
    .saved-url .url-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: #34D399; flex-shrink: 0;
    }
    .saved-url .url-text {
        font-size: 0.78rem; color: var(--text-sidebar) !important;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;
    }

    /* ══════════════════════════════════════════
       Log Terminal
       ══════════════════════════════════════════ */
    .log-terminal {
        background: #0C1222;
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: var(--radius-md);
        padding: 0.8rem 1rem;
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.72rem; line-height: 1.7;
        max-height: 200px; overflow-y: auto; color: #94A3B8;
    }
    .log-terminal .log-line { padding: 0; }
    .log-terminal .log-success { color: #34D399; }
    .log-terminal .log-warn { color: #FBBF24; }
    .log-terminal .log-error { color: #F87171; }
    .log-terminal .log-info { color: #818CF8; }

    /* ══════════════════════════════════════════
       Metric Grid
       ══════════════════════════════════════════ */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 10px; margin: 0.8rem 0;
    }
    .metric-item {
        background: var(--bg-main); border: 1px solid var(--border-light);
        border-radius: var(--radius-md); padding: 0.8rem; text-align: center;
    }
    .metric-item .metric-value {
        font-size: 1.3rem; font-weight: 700;
        color: var(--text-primary); letter-spacing: -0.02em;
    }
    .metric-item .metric-label {
        font-size: 0.68rem; font-weight: 500; color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 0.04em; margin-top: 2px;
    }
    .metric-item.accent .metric-value { color: var(--accent); }
    .metric-item.success .metric-value { color: var(--success); }
    .metric-item.warning .metric-value { color: var(--warning); }
    .metric-item.error .metric-value { color: var(--error); }

    /* ══════════════════════════════════════════
       Misc Overrides
       ══════════════════════════════════════════ */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--accent), #818CF8);
        border-radius: 4px;
    }
    hr { border: none; border-top: 1px solid var(--border-light); margin: 1rem 0; }
    .stDataFrame {
        border-radius: var(--radius-md); overflow: hidden;
        border: 1px solid var(--border);
    }
    .stSpinner > div > div { border-top-color: var(--accent) !important; }
    .streamlit-expanderHeader {
        font-size: 0.82rem; font-weight: 600;
        color: var(--text-secondary) !important;
    }
</style>
""",
        unsafe_allow_html=True,
    )


# ── Component Renderers ──────────────────────────────────────────────


def render_step_indicator(current_step: str):
    """3단계 프로그레스 인디케이터"""
    steps = [
        {"label": "한국어 검수", "key": "step1"},
        {"label": "번역 / 검수", "key": "step2"},
        {"label": "최종 승인", "key": "step3"},
    ]
    step_map = {
        "idle": ["pending", "pending", "pending"],
        "loading": ["active", "pending", "pending"],
        "ko_review": ["done", "pending", "pending"],
        "translating": ["done", "active", "pending"],
        "final_review": ["done", "done", "active"],
        "done": ["done", "done", "done"],
    }
    states = step_map.get(current_step, ["pending", "pending", "pending"])

    def circle(state, num):
        if state == "done":
            return '<div class="step-circle done">&#10003;</div>'
        if state == "active":
            return f'<div class="step-circle active">{num}</div>'
        return f'<div class="step-circle pending">{num}</div>'

    def connector(prev_state, curr_state):
        if prev_state == "done" and curr_state == "done":
            cls = "done"
        elif prev_state == "done" and curr_state == "active":
            cls = "active"
        else:
            cls = "pending"
        return f'<div class="step-connector {cls}"></div>'

    parts = []
    for i, (step, state) in enumerate(zip(steps, states)):
        if i > 0:
            parts.append(connector(states[i - 1], state))
        parts.append(
            f'<div class="step-item">'
            f"  {circle(state, i + 1)}"
            f'  <span class="step-label {state}">{step["label"]}</span>'
            f"</div>"
        )
    st.markdown(
        f'<div class="step-indicator">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def render_card_start(icon: str, title: str, badge: str = ""):
    """카드 시작"""
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    st.markdown(
        f'<div class="dl-card">'
        f'  <div class="dl-card-header">'
        f'    <span class="icon">{icon}</span>'
        f'    <span class="title">{title}</span>'
        f"    {badge_html}"
        f"  </div>"
        f'  <div class="dl-card-body">',
        unsafe_allow_html=True,
    )


def render_card_end():
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_sidebar_logo():
    st.markdown(
        '<div class="sidebar-logo">'
        '  <div class="name">Dev<span class="dot">.</span>Local</div>'
        '  <div class="version">v1.0</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_connection_badge(connected: bool, sheet_count: int = 0):
    if connected:
        st.markdown(
            f'<span class="connection-badge success">'
            f"&#9679; 연결됨 &middot; {sheet_count}개 시트</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="connection-badge error">&#9679; 미연결</span>',
            unsafe_allow_html=True,
        )


def render_app_header():
    st.markdown(
        '<div class="app-header">'
        "  <h1>게임 로컬라이징 자동화</h1>"
        '  <span class="subtitle">'
        "AI 기반 다국어 번역 &middot; 검수 &middot; 자동화</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_done_header():
    st.markdown(
        '<div class="done-header">'
        '  <div class="checkmark">&#10003;</div>'
        "  <h2>작업 완료</h2>"
        "  <p>번역 및 검수가 성공적으로 완료되었습니다</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_saved_url(url: str):
    """고정된 시트 URL 표시 (다크 사이드바용)"""
    display = url
    if len(url) > 50:
        display = url[:18] + "..." + url[-24:]
    safe_url = html_module.escape(url)
    safe_display = html_module.escape(display)
    st.markdown(
        f'<div class="saved-url">'
        f'  <div class="url-dot"></div>'
        f'  <span class="url-text" title="{safe_url}">{safe_display}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_log_terminal(logs: list):
    """터미널 스타일 실행 로그"""
    if not logs:
        return
    lines = []
    for log in logs:
        escaped = html_module.escape(str(log))
        css_class = "log-line"
        if any(kw in log for kw in ["완료", "성공"]):
            css_class += " log-success"
        elif any(kw in log for kw in ["경고", "Warning"]):
            css_class += " log-warn"
        elif any(kw in log for kw in ["오류", "실패", "Error"]):
            css_class += " log-error"
        elif any(kw in log for kw in ["디버그", "Node"]):
            css_class += " log-info"
        lines.append(f'<div class="{css_class}">{escaped}</div>')
    st.markdown(
        f'<div class="log-terminal">{"".join(lines)}</div>',
        unsafe_allow_html=True,
    )


def render_metric_grid(metrics: list):
    """메트릭 그리드

    metrics: [{"label": str, "value": str, "type": "accent"|"success"|"warning"|"error"|""}, ...]
    """
    items = []
    for m in metrics:
        cls = f"metric-item {m.get('type', '')}".strip()
        items.append(
            f'<div class="{cls}">'
            f'  <div class="metric-value">{html_module.escape(str(m["value"]))}</div>'
            f'  <div class="metric-label">{html_module.escape(str(m["label"]))}</div>'
            f"</div>"
        )
    st.markdown(
        f'<div class="metric-grid">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )
