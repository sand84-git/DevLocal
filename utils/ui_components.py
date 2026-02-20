"""UI 컴포넌트 헬퍼 — Fixoria 디자인 시스템 (Warm Neutral + Green Accent)"""

import html as html_module
import streamlit as st
import streamlit.components.v1 as components


def inject_custom_css():
    """전체 커스텀 CSS 주입 — Fixoria 워밍 뉴트럴 스타일"""
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

    /* ══════════════════════════════════════════
       Design Tokens — Fixoria Warm Neutral
       ══════════════════════════════════════════ */
    :root {
        --bg-main: #F4F2EE;
        --bg-card: #FFFFFF;
        --bg-sidebar: #FAFAF8;
        --bg-sidebar-hover: #F0EDE7;
        --bg-sidebar-active: #F0EDE7;

        --accent: #4A7C59;
        --accent-hover: #3D6B4C;
        --accent-light: #E4F0E4;
        --accent-glow: rgba(74,124,89,0.18);

        --success: #4A7C59;
        --success-light: #E4F0E4;
        --warning: #C4A67D;
        --warning-light: #FFF6E9;
        --error: #C75050;
        --error-light: #FFEBEE;

        --text-primary: #1A1A1A;
        --text-secondary: #5A5A5A;
        --text-muted: #A0A0A0;
        --text-sidebar: #1A1A1A;
        --text-sidebar-muted: #8A8A8A;

        --border: #EEEDEA;
        --border-light: #F5F4F1;
        --border-strong: #DEDBD5;

        --shadow-sm: none;
        --shadow-md: none;

        --radius-sm: 6px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 20px;
    }

    /* ══════════════════════════════════════════
       Global
       ══════════════════════════════════════════ */
    .stApp {
        background-color: var(--bg-main);
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary) !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* ══════════════════════════════════════════
       Light Sidebar
       ══════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: var(--bg-sidebar);
        border-right: 1px solid var(--border);
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
        font-weight: 500;
        color: var(--text-sidebar-muted) !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.5rem;
        padding-bottom: 0;
        border-bottom: none;
    }

    /* Sidebar text input */
    [data-testid="stSidebar"] .stTextInput input {
        background-color: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        color: var(--text-primary) !important;
        font-size: 0.85rem;
        font-family: 'DM Sans', sans-serif;
    }
    [data-testid="stSidebar"] .stTextInput input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-glow);
    }
    [data-testid="stSidebar"] .stTextInput input::placeholder {
        color: var(--text-muted) !important;
    }

    /* Sidebar selectbox */
    [data-testid="stSidebar"] [data-baseweb="select"] {
        border-radius: var(--radius-md);
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #FFFFFF;
        border-color: var(--border);
        color: var(--text-primary) !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div:hover {
        border-color: var(--border-strong);
    }

    /* Sidebar multiselect */
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div {
        background-color: #FFFFFF;
        border-color: var(--border);
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background-color: var(--accent) !important;
        color: white !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] span,
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] div,
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] * {
        color: white !important;
        font-weight: 600 !important;
    }

    /* Sidebar radio */
    [data-testid="stSidebar"] .stRadio label {
        color: var(--text-sidebar) !important;
    }

    /* Sidebar number input */
    [data-testid="stSidebar"] .stNumberInput input {
        background-color: #FFFFFF;
        border-color: var(--border);
        color: var(--text-primary) !important;
        border-radius: var(--radius-md);
        font-family: 'DM Sans', sans-serif;
    }

    /* Sidebar divider */
    [data-testid="stSidebar"] hr {
        border-color: var(--border);
        margin: 0.8rem 0;
    }

    /* Sidebar buttons — primary */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        border: none !important;
        color: white !important;
        width: 100%;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        font-family: 'DM Sans', sans-serif !important;
        padding: 0.6rem 1rem !important;
        letter-spacing: 0.3px;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] p,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] span,
    [data-testid="stSidebar"] .stButton > button[kind="primary"] p,
    [data-testid="stSidebar"] .stButton > button[kind="primary"] span {
        color: white !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: var(--accent-hover) !important;
    }
    /* Sidebar buttons — secondary */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
        background: #FFFFFF !important;
        border-color: var(--border) !important;
        color: var(--text-secondary) !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {
        background: var(--bg-sidebar-hover) !important;
        border-color: var(--border-strong) !important;
        color: var(--text-primary) !important;
    }

    /* Sidebar expander */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        color: var(--text-secondary) !important;
        font-size: 0.8rem;
    }

    /* ══════════════════════════════════════════
       Buttons — Main Area (Primary)
       ══════════════════════════════════════════ */
    button[data-testid="stBaseButton-primary"],
    .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        font-family: 'DM Sans', sans-serif !important;
        padding: 0.6rem 1.4rem !important;
        letter-spacing: 0.3px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    button[data-testid="stBaseButton-primary"] p,
    button[data-testid="stBaseButton-primary"] span,
    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span {
        color: white !important;
        font-weight: 700 !important;
    }
    button[data-testid="stBaseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        background: var(--accent-hover) !important;
        transform: translateY(-1px);
    }
    button[data-testid="stBaseButton-primary"]:active,
    .stButton > button[kind="primary"]:active {
        transform: translateY(0);
    }

    /* Buttons — Main Area (Secondary) */
    button[data-testid="stBaseButton-secondary"],
    .stButton > button:not([kind="primary"]) {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-strong) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        font-family: 'DM Sans', sans-serif !important;
        padding: 0.6rem 1.4rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        background: var(--bg-card) !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover,
    .stButton > button:not([kind="primary"]):hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--accent-light) !important;
    }

    /* Download button */
    .stDownloadButton > button,
    button[data-testid="stBaseButton-secondary"].st-emotion-cache-download {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-strong) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: all 0.2s ease;
        background: var(--bg-card) !important;
    }
    .stDownloadButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--accent-light) !important;
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
        overflow: hidden;
        animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .dl-card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 1rem 1.3rem;
        border-bottom: 1px solid var(--border);
    }
    .dl-card-header .icon { font-size: 1.05rem; }
    .dl-card-header .title {
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.3px;
        font-family: 'DM Sans', sans-serif;
    }
    .dl-card-header .badge {
        margin-left: auto;
        background: var(--accent-light);
        color: var(--accent);
        padding: 2px 10px;
        border-radius: var(--radius-xl);
        font-size: 0.72rem;
        font-weight: 700;
    }
    .dl-card-body { padding: 18px 20px; }

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
        margin-bottom: 1.2rem;
        gap: 0;
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .step-item { display: flex; align-items: center; gap: 7px; }
    .step-circle {
        width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem; font-weight: 700; flex-shrink: 0;
        transition: all 0.3s ease;
        font-family: 'DM Sans', sans-serif;
    }
    .step-circle.done { background-color: var(--success-light); color: var(--success); }
    .step-circle.active {
        background: var(--accent);
        color: white;
        animation: pulse-green 2s ease-in-out infinite;
    }
    .step-circle.pending { background-color: var(--border-light); color: var(--text-muted); }
    .step-label {
        font-size: 0.78rem; font-weight: 700;
        letter-spacing: -0.2px; font-family: 'DM Sans', sans-serif;
    }
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
    @keyframes pulse-green {
        0%, 100% { box-shadow: 0 0 0 0 rgba(74,124,89,0.35); }
        50% { box-shadow: 0 0 0 8px rgba(74,124,89,0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-12px); }
        to   { opacity: 1; transform: translateX(0); }
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
        font-size: 0.72rem; font-weight: 700; margin-top: 4px;
        font-family: 'DM Sans', sans-serif;
    }
    .connection-badge.success { background: var(--accent-light); color: var(--accent); }
    .connection-badge.error { background: var(--error-light); color: var(--error); }

    /* ══════════════════════════════════════════
       App Header
       ══════════════════════════════════════════ */
    .app-header { text-align: center; padding: 0.2rem 0 1rem; }
    .app-header h1 {
        font-size: 1.3rem !important; font-weight: 700;
        color: var(--text-primary) !important;
        margin-bottom: 0.1rem; letter-spacing: -0.5px;
        font-family: 'DM Sans', sans-serif !important;
    }
    .app-header .subtitle {
        font-size: 0.78rem; color: var(--text-muted) !important;
        font-weight: 400; font-family: 'DM Sans', sans-serif;
    }

    /* ══════════════════════════════════════════
       Sidebar Logo
       ══════════════════════════════════════════ */
    .sidebar-logo {
        text-align: center; padding: 0.2rem 0 0.8rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 0.8rem;
    }
    .sidebar-logo .name {
        font-size: 1.15rem; font-weight: 700;
        color: var(--text-primary) !important; letter-spacing: -0.3px;
        font-family: 'DM Sans', sans-serif;
    }
    .sidebar-logo .dot { color: var(--accent) !important; }
    .sidebar-logo .version {
        font-size: 0.65rem; color: var(--text-muted) !important; font-weight: 500;
    }

    /* ══════════════════════════════════════════
       Saved URL Display
       ══════════════════════════════════════════ */
    .saved-url {
        display: flex; align-items: center; gap: 8px;
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 7px 11px; margin-bottom: 0.4rem;
    }
    .saved-url .url-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--accent); flex-shrink: 0;
    }
    .saved-url .url-text {
        font-size: 0.78rem; color: var(--text-secondary) !important;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;
    }

    /* ══════════════════════════════════════════
       Log Terminal
       ══════════════════════════════════════════ */
    .log-terminal {
        background: #FAFAF8;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 0.8rem 1rem;
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.72rem; line-height: 1.7;
        max-height: 200px; overflow-y: auto; color: var(--text-secondary);
    }
    .log-terminal .log-line { padding: 1px 0; }
    .log-terminal .log-success { color: var(--success); }
    .log-terminal .log-warn { color: var(--warning); }
    .log-terminal .log-error { color: var(--error); }
    .log-terminal .log-info { color: var(--accent); }
    .log-terminal .log-divider {
        border-top: 1px solid var(--border);
        margin: 6px 0 4px;
        padding-top: 4px;
        font-weight: 700;
        color: var(--text-primary);
        font-size: 0.74rem;
    }
    .log-terminal .log-icon {
        display: inline-block;
        width: 16px;
        text-align: center;
        margin-right: 4px;
    }

    /* ══════════════════════════════════════════
       Metric Grid
       ══════════════════════════════════════════ */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 10px; margin: 0.8rem 0;
    }
    .metric-item {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--radius-lg); padding: 1rem; text-align: center;
    }
    .metric-item .metric-value {
        font-size: 1.6rem; font-weight: 700;
        color: var(--text-primary); letter-spacing: -0.5px;
        font-family: 'DM Sans', sans-serif;
    }
    .metric-item .metric-label {
        font-size: 0.65rem; font-weight: 500; color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 1.2px; margin-top: 4px;
        font-family: 'DM Sans', sans-serif;
    }
    .metric-item.accent .metric-value { color: var(--accent); }
    .metric-item.success .metric-value { color: var(--success); }
    .metric-item.warning .metric-value { color: var(--warning); }
    .metric-item.error .metric-value { color: var(--error); }

    /* ══════════════════════════════════════════
       Misc Overrides
       ══════════════════════════════════════════ */
    .stProgress > div > div {
        background: var(--accent);
        border-radius: 4px;
    }
    hr { border: none; border-top: 1px solid var(--border); margin: 1rem 0; }
    .stDataFrame {
        border-radius: var(--radius-md); overflow: hidden;
        border: 1px solid var(--border);
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both;
    }

    /* Streamlit alert/expander 등장 애니메이션 */
    .stAlert, .stExpander, .stSuccess, .stInfo, .stWarning {
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    .stSpinner > div > div { border-top-color: var(--accent) !important; }
    .streamlit-expanderHeader {
        font-size: 0.82rem; font-weight: 700;
        color: var(--text-secondary) !important;
        font-family: 'DM Sans', sans-serif;
    }

    /* Disabled state for locked sections */
    .dl-disabled {
        opacity: 0.4;
        pointer-events: none;
    }

    /* ══════════════════════════════════════════
       Pipeline Visualization
       ══════════════════════════════════════════ */
    .pipeline {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
        animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .pipeline-node {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 6px 0;
        animation: slideInLeft 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    .pipeline-node:nth-child(1)  { animation-delay: 0s; }
    .pipeline-node:nth-child(3)  { animation-delay: 0.05s; }
    .pipeline-node:nth-child(5)  { animation-delay: 0.1s; }
    .pipeline-node:nth-child(7)  { animation-delay: 0.15s; }
    .pipeline-node:nth-child(9)  { animation-delay: 0.2s; }
    .pipeline-node:nth-child(11) { animation-delay: 0.25s; }
    .pipeline-node:nth-child(13) { animation-delay: 0.3s; }
    .pipeline-node:nth-child(15) { animation-delay: 0.35s; }
    .pipeline-dot {
        width: 22px; height: 22px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.65rem; font-weight: 700;
        flex-shrink: 0;
        transition: all 0.3s ease;
    }
    .pipeline-dot.pending {
        background: transparent;
        border: 2px solid var(--border-strong);
        color: var(--text-muted);
    }
    .pipeline-dot.active {
        background: var(--accent);
        border: 2px solid var(--accent);
        color: white;
        animation: pulse-green 2s ease-in-out infinite;
    }
    .pipeline-dot.done {
        background: var(--accent);
        border: 2px solid var(--accent);
        color: white;
    }
    .pipeline-dot.error {
        background: var(--error);
        border: 2px solid var(--error);
        color: white;
    }
    .pipeline-label {
        font-size: 0.82rem;
        font-weight: 500;
        font-family: 'DM Sans', sans-serif;
        flex: 1;
    }
    .pipeline-label.pending { color: var(--text-muted); }
    .pipeline-label.active { color: var(--text-primary); font-weight: 700; }
    .pipeline-label.done { color: var(--text-secondary); }
    .pipeline-label.error { color: var(--error); }
    .pipeline-status {
        font-size: 0.72rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        white-space: nowrap;
    }
    .pipeline-status.pending { color: var(--text-muted); }
    .pipeline-status.active { color: var(--accent); }
    .pipeline-status.done { color: var(--success); }
    .pipeline-status.error { color: var(--error); }
    .pipeline-connector {
        width: 2px; height: 10px;
        margin-left: 10px;
        flex-shrink: 0;
    }
    .pipeline-connector.done { background: var(--accent); }
    .pipeline-connector.active { background: linear-gradient(180deg, var(--accent), var(--border-strong)); }
    .pipeline-connector.pending { background: var(--border); }
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
        "ko_review": ["active", "pending", "pending"],
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
    """고정된 시트 URL 표시 (라이트 사이드바용)"""
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
    """터미널 스타일 실행 로그 — 아이콘 + 노드별 구분"""
    if not logs:
        return
    lines = []
    for log in logs:
        log_str = str(log)
        escaped = html_module.escape(log_str)

        # 노드 구분선 감지: [Node X] 패턴
        if "[Node " in log_str and "]" in log_str:
            lines.append(f'<div class="log-line log-divider">{escaped}</div>')
            continue

        # 레벨 감지 + 아이콘
        css_class = "log-line"
        icon = ""
        if any(kw in log_str for kw in ["완료", "성공"]):
            css_class += " log-success"
            icon = '<span class="log-icon">✓</span>'
        elif any(kw in log_str for kw in ["경고", "Warning"]):
            css_class += " log-warn"
            icon = '<span class="log-icon">⚠</span>'
        elif any(kw in log_str for kw in ["오류", "실패", "Error"]):
            css_class += " log-error"
            icon = '<span class="log-icon">✕</span>'
        elif any(kw in log_str for kw in ["디버그"]):
            css_class += " log-info"
            icon = '<span class="log-icon">ℹ</span>'

        lines.append(f'<div class="{css_class}">{icon}{escaped}</div>')
    st.markdown(
        f'<div class="log-terminal">{"".join(lines)}</div>',
        unsafe_allow_html=True,
    )
    # 자동 스크롤: 새 로그 추가 시 터미널 하단으로 이동
    components.html(
        """<script>
        const terminals = window.parent.document.querySelectorAll('.log-terminal');
        terminals.forEach(el => { el.scrollTop = el.scrollHeight; });
        </script>""",
        height=0,
        scrolling=False,
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


# ── Pipeline 노드 정의 ──────────────────────────────────────────────

PIPELINE_NODES = [
    {"key": "data_backup", "label": "데이터 확인"},
    {"key": "context_glossary", "label": "컨텍스트 로드"},
    {"key": "ko_review", "label": "한국어 검수"},
    {"key": "ko_approval", "label": "한국어 승인"},
    {"key": "translator", "label": "AI 번역"},
    {"key": "reviewer", "label": "품질 검수"},
    {"key": "final_approval", "label": "최종 승인"},
    {"key": "writer", "label": "시트 업데이트"},
]

_STATUS_ICONS = {
    "pending": "○",
    "active": "◉",
    "done": "✓",
    "error": "✕",
}

_STATUS_TEXTS = {
    "pending": "대기",
    "active": "진행중",
    "done": "완료",
    "error": "오류",
}


def render_pipeline(pipeline_status: dict):
    """8노드 버티컬 파이프라인 시각화.

    pipeline_status: {"data_backup": "done", "translator": "active", ...}
    키가 없으면 "pending"으로 처리.
    """
    parts = []
    for i, node in enumerate(PIPELINE_NODES):
        state = pipeline_status.get(node["key"], "pending")
        icon = _STATUS_ICONS.get(state, "○")
        status_text = pipeline_status.get(f"{node['key']}_text", _STATUS_TEXTS.get(state, ""))

        # 커넥터 (첫 노드 제외)
        if i > 0:
            prev_state = pipeline_status.get(PIPELINE_NODES[i - 1]["key"], "pending")
            if prev_state in ("done",) and state in ("done", "active"):
                conn_cls = "done"
            elif prev_state in ("done",) and state == "pending":
                conn_cls = "active"
            else:
                conn_cls = "pending"
            parts.append(
                f'<div class="pipeline-connector {conn_cls}"></div>'
            )

        parts.append(
            f'<div class="pipeline-node">'
            f'  <div class="pipeline-dot {state}">{icon}</div>'
            f'  <span class="pipeline-label {state}">{node["label"]}</span>'
            f'  <span class="pipeline-status {state}">{html_module.escape(status_text)}</span>'
            f'</div>'
        )

    st.markdown(
        f'<div class="pipeline">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )
