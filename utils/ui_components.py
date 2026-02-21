"""UI 컴포넌트 헬퍼 — DevLocal Sky Blue 디자인 시스템"""

import html as html_module
import streamlit as st
import streamlit.components.v1 as components


def inject_custom_css():
    """전체 커스텀 CSS 주입 — Sky Blue 디자인 시스템"""
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    /* ══════════════════════════════════════════
       Design Tokens — Sky Blue
       ══════════════════════════════════════════ */
    :root {
        --primary: #0ea5e9;
        --primary-dark: #0284c7;
        --primary-light: #e0f2fe;
        --primary-glow: rgba(14,165,233,0.18);

        --bg-page: #f8fafc;
        --bg-surface: #ffffff;

        --border-subtle: #e2e8f0;
        --border-light: #f1f5f9;
        --border-strong: #cbd5e1;

        --text-main: #1e293b;
        --text-secondary: #475569;
        --text-muted: #64748b;

        --success: #10b981;
        --success-light: #d1fae5;
        --warning: #f59e0b;
        --warning-light: #fef3c7;
        --error: #ef4444;
        --error-light: #fee2e2;

        --diff-added: #dcfce7;
        --diff-removed: #fee2e2;

        --shadow-card: 0 4px 20px -2px rgba(0,0,0,0.05);
        --shadow-sm: 0 1px 3px 0 rgba(0,0,0,0.04);

        --radius-sm: 6px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 9999px;
    }

    /* ══════════════════════════════════════════
       Global
       ══════════════════════════════════════════ */
    .stApp {
        background-color: var(--bg-page);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-main) !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Hide sidebar completely */
    [data-testid="stSidebar"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }

    /* ══════════════════════════════════════════
       Header Bar
       ══════════════════════════════════════════ */
    .dl-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.8rem 1.5rem;
        background: var(--bg-surface);
        border-bottom: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-card);
        margin-bottom: 1.5rem;
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .dl-header-logo {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-main);
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.3px;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .dl-header-logo .logo-icon {
        font-size: 1.2rem;
    }
    .dl-header-steps {
        display: flex;
        align-items: center;
        gap: 0;
        flex: 1;
        justify-content: center;
    }

    /* ══════════════════════════════════════════
       5-Step Indicator (Stitch style)
       ══════════════════════════════════════════ */
    .step-indicator {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        padding: 0;
        background: transparent;
        border: none;
        margin-bottom: 0;
        gap: 0;
    }
    .step-row {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
    }
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
    }
    .step-circle {
        width: 32px; height: 32px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem; flex-shrink: 0;
        transition: all 0.3s ease;
    }
    .step-circle .material-symbols-rounded {
        font-size: 18px;
        font-variation-settings: 'FILL' 0, 'wght' 500, 'GRAD' 0, 'opsz' 20;
    }
    .step-circle.done {
        background-color: var(--success-light);
        color: var(--success);
    }
    .step-circle.done .material-symbols-rounded {
        font-variation-settings: 'FILL' 1, 'wght' 600, 'GRAD' 0, 'opsz' 20;
    }
    .step-circle.active {
        background: var(--primary);
        color: white;
        animation: pulse-primary 2s ease-in-out infinite;
    }
    .step-circle.pending {
        background-color: var(--border-light);
        color: var(--text-muted);
    }
    .step-label {
        font-size: 0.68rem; font-weight: 600;
        letter-spacing: -0.1px; font-family: 'Inter', sans-serif;
        white-space: nowrap;
    }
    .step-label.done { color: var(--success); }
    .step-label.active { color: var(--primary); font-weight: 700; }
    .step-label.pending { color: var(--text-muted); }
    .step-connector {
        width: 40px; height: 2px; margin: 0 6px;
        flex-shrink: 0; border-radius: 1px;
        margin-bottom: 20px;  /* align with circle center */
    }
    .step-connector.done { background-color: var(--success); }
    .step-connector.active { background: linear-gradient(90deg, var(--success), var(--primary)); }
    .step-connector.pending { background-color: var(--border-subtle); }

    /* ══════════════════════════════════════════
       Step Progress — spinner
       ══════════════════════════════════════════ */
    .step-progress {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        width: 100%;
        padding: 0.8rem 0 0.4rem;
    }
    .step-progress-spinner {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sparkle {
        display: inline-block;
        font-size: 0.9rem;
        color: var(--primary);
        animation: sparkle-spin 3s linear infinite;
    }
    .progress-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary);
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.2px;
    }
    .progress-label::after {
        content: '';
        animation: label-dots 1.8s steps(3, end) infinite;
    }
    .step-progress-track {
        width: 100%;
        max-width: 360px;
        height: 3px;
        background: var(--border-subtle);
        border-radius: 2px;
        overflow: hidden;
    }
    .step-progress-bar {
        height: 100%;
        background: var(--primary);
        border-radius: 2px;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .step-progress-bar.indeterminate {
        width: 40%;
        animation: progress-slide 1.8s ease-in-out infinite;
    }

    /* ══════════════════════════════════════════
       Buttons — Main Area (Primary)
       ══════════════════════════════════════════ */
    button[data-testid="stBaseButton-primary"],
    .stButton > button[kind="primary"] {
        background: var(--primary) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.6rem 1.4rem !important;
        letter-spacing: 0.3px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-sm);
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
        background: var(--primary-dark) !important;
        transform: translateY(-1px);
        box-shadow: var(--shadow-card);
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
        color: var(--text-main) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.6rem 1.4rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        background: var(--bg-surface) !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover,
    .stButton > button:not([kind="primary"]):hover {
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        background: var(--primary-light) !important;
    }

    /* Download button */
    .stDownloadButton > button,
    button[data-testid="stBaseButton-secondary"].st-emotion-cache-download {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-strong) !important;
        color: var(--text-main) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease;
        background: var(--bg-surface) !important;
    }
    .stDownloadButton > button:hover {
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        background: var(--primary-light) !important;
    }

    /* ══════════════════════════════════════════
       Cards
       ══════════════════════════════════════════ */
    .dl-card {
        background: var(--bg-surface);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-subtle);
        padding: 0;
        margin: 1rem 0;
        overflow: hidden;
        box-shadow: var(--shadow-card);
        animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .dl-card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 1rem 1.3rem;
        border-bottom: 1px solid var(--border-subtle);
    }
    .dl-card-header .icon { font-size: 1.05rem; }
    .dl-card-header .title {
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--text-main);
        letter-spacing: -0.3px;
        font-family: 'Inter', sans-serif;
    }
    .dl-card-header .badge {
        margin-left: auto;
        background: var(--primary-light);
        color: var(--primary);
        padding: 2px 10px;
        border-radius: var(--radius-xl);
        font-size: 0.72rem;
        font-weight: 700;
    }
    .dl-card-body { padding: 18px 20px; }

    /* ══════════════════════════════════════════
       Placeholder Card (idle state)
       ══════════════════════════════════════════ */
    .dl-placeholder-card {
        background: var(--bg-surface);
        border-radius: var(--radius-lg);
        border: 2px dashed var(--border-subtle);
        padding: 3rem 2rem;
        text-align: center;
        margin: 1rem 0;
        animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .dl-placeholder-card .placeholder-icon {
        font-size: 2.5rem;
        margin-bottom: 0.8rem;
        color: var(--text-muted);
    }
    .dl-placeholder-card .placeholder-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-main);
        margin-bottom: 0.4rem;
        font-family: 'Inter', sans-serif;
    }
    .dl-placeholder-card .placeholder-desc {
        font-size: 0.85rem;
        color: var(--text-muted);
        font-family: 'Inter', sans-serif;
    }

    /* ══════════════════════════════════════════
       Footer
       ══════════════════════════════════════════ */
    .dl-footer {
        position: sticky;
        bottom: 0;
        background: var(--bg-surface);
        border-top: 1px solid var(--border-subtle);
        padding: 12px 24px;
        margin-top: 2rem;
        z-index: 100;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.03);
    }

    /* ══════════════════════════════════════════
       Animations
       ══════════════════════════════════════════ */
    @keyframes sparkle-spin {
        0%   { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes label-dots {
        0%   { content: ''; }
        33%  { content: '.'; }
        66%  { content: '..'; }
        100% { content: '...'; }
    }
    @keyframes progress-slide {
        0%   { margin-left: 0; }
        50%  { margin-left: 60%; }
        100% { margin-left: 0; }
    }
    @keyframes pulse-primary {
        0%, 100% { box-shadow: 0 0 0 0 rgba(14,165,233,0.35); }
        50% { box-shadow: 0 0 0 8px rgba(14,165,233,0); }
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
        background: var(--primary-light); color: var(--primary);
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 1.5rem; margin-bottom: 0.6rem;
    }
    .done-header h2 {
        font-size: 1.2rem; font-weight: 700;
        color: var(--text-main) !important; margin-bottom: 0.2rem;
    }
    .done-header p { color: var(--text-muted) !important; font-size: 0.85rem; }

    /* ══════════════════════════════════════════
       Connection Badge
       ══════════════════════════════════════════ */
    .connection-badge {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 3px 10px; border-radius: var(--radius-xl);
        font-size: 0.72rem; font-weight: 700; margin-top: 4px;
        font-family: 'Inter', sans-serif;
    }
    .connection-badge.success { background: var(--primary-light); color: var(--primary); }
    .connection-badge.error { background: var(--error-light); color: var(--error); }

    /* ══════════════════════════════════════════
       Log Terminal
       ══════════════════════════════════════════ */
    .log-terminal {
        background: var(--bg-page);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 0.8rem 1rem;
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.72rem; line-height: 1.7;
        max-height: 160px; overflow-y: auto; color: var(--text-secondary);
    }
    .log-terminal .log-line { padding: 1px 0; }
    .log-terminal .log-success { color: var(--success); }
    .log-terminal .log-warn { color: var(--warning); }
    .log-terminal .log-error { color: var(--error); }
    .log-terminal .log-info { color: var(--primary); }
    .log-terminal .log-divider {
        border-top: 1px solid var(--border-subtle);
        margin: 6px 0 4px;
        padding-top: 4px;
        font-weight: 700;
        color: var(--text-main);
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
        background: var(--bg-surface); border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg); padding: 1rem; text-align: center;
        box-shadow: var(--shadow-sm);
    }
    .metric-item .metric-value {
        font-size: 1.6rem; font-weight: 700;
        color: var(--text-main); letter-spacing: -0.5px;
        font-family: 'Inter', sans-serif;
    }
    .metric-item .metric-label {
        font-size: 0.65rem; font-weight: 500; color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 1.2px; margin-top: 4px;
        font-family: 'Inter', sans-serif;
    }
    .metric-item.accent .metric-value { color: var(--primary); }
    .metric-item.success .metric-value { color: var(--success); }
    .metric-item.warning .metric-value { color: var(--warning); }
    .metric-item.error .metric-value { color: var(--error); }

    /* ══════════════════════════════════════════
       Misc Overrides
       ══════════════════════════════════════════ */
    .stProgress > div > div {
        background: var(--primary);
        border-radius: 4px;
    }
    hr { border: none; border-top: 1px solid var(--border-subtle); margin: 1rem 0; }
    .stDataFrame {
        border-radius: var(--radius-md); overflow: hidden;
        border: 1px solid var(--border-subtle);
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both;
    }

    /* Streamlit alert/expander animation */
    .stAlert, .stExpander, .stSuccess, .stInfo, .stWarning {
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    .stSpinner > div > div { border-top-color: var(--primary) !important; }
    .streamlit-expanderHeader {
        font-size: 0.82rem; font-weight: 700;
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif;
    }

    /* Disabled state for locked sections */
    .dl-disabled {
        opacity: 0.4;
        pointer-events: none;
    }

    /* ══════════════════════════════════════════
       Data Source Configuration Card
       ══════════════════════════════════════════ */
    .dl-card-body .stTextInput > div > div > input {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-subtle) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 0.8rem !important;
        transition: border-color 0.2s ease !important;
    }
    .dl-card-body .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px var(--primary-glow) !important;
    }
    .dl-card-body .stSelectbox > div > div {
        border-radius: var(--radius-md) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.88rem !important;
    }
    .dl-card-body .stMultiSelect > div > div {
        border-radius: var(--radius-md) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.88rem !important;
    }
    .dl-card-body .stRadio > div {
        font-family: 'Inter', sans-serif !important;
    }
    .dl-card-body .stRadio > div > label {
        font-size: 0.88rem !important;
        font-weight: 500 !important;
    }
    .dl-card-body .stNumberInput > div > div > input {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-subtle) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.88rem !important;
    }
    .dl-card-body label {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        letter-spacing: -0.1px !important;
    }
    .dl-card-body .stExpander {
        border: 1px solid var(--border-light) !important;
        border-radius: var(--radius-md) !important;
        margin-top: 0.5rem !important;
    }

    /* Saved URL inline display for Data Source card */
    .ds-saved-url {
        display: flex;
        align-items: center;
        gap: 8px;
        background: var(--bg-page);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 0.55rem 0.8rem;
        min-height: 38px;
    }
    .ds-saved-url .url-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: var(--primary); flex-shrink: 0;
    }
    .ds-saved-url .url-text {
        font-size: 0.85rem; color: var(--text-secondary);
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;
        font-family: 'Inter', sans-serif;
    }

    /* ══════════════════════════════════════════
       KR Review Table
       ══════════════════════════════════════════ */
    .review-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
        font-family: 'Inter', sans-serif;
    }
    .review-table th {
        background: var(--bg-page);
        font-weight: 600;
        text-align: left;
        padding: 10px 14px;
        border-bottom: 2px solid var(--border-subtle);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted);
    }
    .review-table td {
        padding: 10px 14px;
        border-bottom: 1px solid var(--border-subtle);
        vertical-align: top;
        color: var(--text-main);
    }
    .review-table tr:hover {
        background: var(--bg-page);
    }
    .review-table .col-num {
        width: 40px;
        text-align: center;
        color: var(--text-muted);
        font-weight: 500;
    }
    .review-table .col-key {
        font-weight: 600;
        font-size: 0.82rem;
        color: var(--text-secondary);
        white-space: nowrap;
    }
    .review-table .col-original {
        background: var(--diff-removed);
        border-radius: var(--radius-sm);
        color: var(--text-main);
    }
    .review-table .col-suggested {
        background: var(--diff-added);
        border-radius: var(--radius-sm);
        color: var(--text-main);
    }
    .review-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .review-badge.fix {
        background: var(--warning-light);
        color: var(--warning);
    }
    .review-badge.success {
        background: var(--success-light);
        color: var(--success);
    }
    .review-badge.fail {
        background: var(--error-light);
        color: var(--error);
    }

    /* ══════════════════════════════════════════
       Overall Progress Bar (Final Review)
       ══════════════════════════════════════════ */
    .overall-progress {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
    }
    .overall-progress-track {
        flex: 1;
        height: 8px;
        background: var(--border-subtle);
        border-radius: 4px;
        overflow: hidden;
        display: flex;
    }
    .overall-progress-success {
        height: 100%;
        background: var(--success);
        transition: width 0.4s ease;
    }
    .overall-progress-fail {
        height: 100%;
        background: var(--error);
        transition: width 0.4s ease;
    }
    .overall-progress-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-secondary);
        font-family: 'Inter', sans-serif;
        white-space: nowrap;
    }
</style>
""",
        unsafe_allow_html=True,
    )


# ── Component Renderers ──────────────────────────────────────────────

# Module-level constants for step indicator (used by render_header)
_STEPS = [
    {"label": "Load", "icon": "check"},
    {"label": "KR Review", "icon": "chat_bubble"},
    {"label": "Translating", "icon": "g_translate"},
    {"label": "Multi-Review", "icon": "checklist"},
    {"label": "Complete", "icon": "check_circle"},
]

_STEP_MAP = {
    "idle": [0, 0, 0, 0, 0],
    "loading": [1, 0, 0, 0, 0],
    "ko_review": [2, 1, 0, 0, 0],
    "translating": [2, 2, 1, 0, 0],
    "final_review": [2, 2, 2, 1, 0],
    "done": [2, 2, 2, 2, 2],
}

_STATE_NAMES = {0: "pending", 1: "active", 2: "done"}


def _build_steps_html(current_step: str) -> str:
    """Build the step circles + connectors HTML string."""
    state_codes = _STEP_MAP.get(current_step, [0, 0, 0, 0, 0])
    states = [_STATE_NAMES[c] for c in state_codes]

    def circle(state, icon_name):
        icon_html = f'<span class="material-symbols-rounded">{icon_name}</span>'
        return f'<div class="step-circle {state}">{icon_html}</div>'

    def connector(prev_state, curr_state):
        if prev_state == "done" and curr_state == "done":
            cls = "done"
        elif prev_state == "done" and curr_state == "active":
            cls = "active"
        else:
            cls = "pending"
        return f'<div class="step-connector {cls}"></div>'

    parts = []
    for i, (step, state) in enumerate(zip(_STEPS, states)):
        if i > 0:
            parts.append(connector(states[i - 1], state))
        parts.append(
            f'<div class="step-item">'
            f'  {circle(state, step["icon"])}'
            f'  <span class="step-label {state}">{step["label"]}</span>'
            f"</div>"
        )
    return "".join(parts)


def _build_progress_html(current_step: str, progress: dict) -> str:
    """Build the progress spinner + bar HTML string."""
    if not progress or not progress.get("label") or current_step in ("idle", "done"):
        return ""
    label = html_module.escape(progress["label"])
    value = progress.get("value", 0)
    bar_cls = "step-progress-bar indeterminate" if value <= 0 else "step-progress-bar"
    bar_style = f"width: {int(value * 100)}%;" if value > 0 else ""
    return (
        f'<div class="step-progress">'
        f'  <div class="step-progress-spinner">'
        f'    <span class="sparkle">&#10022;</span>'
        f'    <span class="progress-label">{label}</span>'
        f'  </div>'
        f'  <div class="step-progress-track">'
        f'    <div class="{bar_cls}" style="{bar_style}"></div>'
        f'  </div>'
        f'</div>'
    )


def render_header(current_step: str = "idle", progress: dict = None):
    """헤더 바: 로고 + 5단계 스텝 인디케이터 통합

    Args:
        current_step: 현재 단계
        progress: 프로그레스 데이터
    """
    steps_html = _build_steps_html(current_step)
    progress_html = _build_progress_html(current_step, progress)

    st.markdown(
        f'<div class="dl-header">'
        f'  <div class="dl-header-logo">'
        f'    <span class="logo-icon">&#127760;</span>'
        f'    Game Localization Tool'
        f'  </div>'
        f'  <div class="dl-header-steps">{steps_html}</div>'
        f'</div>'
        f'{progress_html}',
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


def render_done_header():
    st.markdown(
        '<div class="done-header">'
        '  <div class="checkmark">&#10003;</div>'
        "  <h2>작업 완료</h2>"
        "  <p>번역 및 검수가 성공적으로 완료되었습니다</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_footer():
    """하단 Footer — 시각적 구분선 역할. 실제 버튼은 Phase 2~4에서 배치."""
    st.markdown(
        '<div class="dl-footer">'
        '  <div style="display:flex;justify-content:space-between;align-items:center;">'
        '    <div class="footer-left"></div>'
        '    <div class="footer-right"></div>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_saved_url_inline(url: str):
    """Data Source 카드 내 고정된 시트 URL 표시"""
    display = url
    if len(url) > 60:
        display = url[:22] + "..." + url[-28:]
    safe_url = html_module.escape(url)
    safe_display = html_module.escape(display)
    st.markdown(
        f'<div class="ds-saved-url">'
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


def render_ko_review_table(ko_report_df):
    """한국어 검수 테이블 -- 커스텀 HTML 렌더링

    Args:
        ko_report_df: DataFrame with columns: Key, 기존 한국어, 수정 제안
    """
    if ko_report_df is None or ko_report_df.empty:
        return

    rows_html = []
    for row_num, (_, row) in enumerate(ko_report_df.iterrows(), start=1):
        key = html_module.escape(str(row.get("Key", "")))
        original = html_module.escape(str(row.get("기존 한국어", "")))
        suggested = html_module.escape(str(row.get("수정 제안", "")))

        rows_html.append(
            f"<tr>"
            f'  <td class="col-num">{row_num}</td>'
            f'  <td class="col-key">{key}</td>'
            f'  <td class="col-original">{original}</td>'
            f'  <td class="col-suggested">{suggested}</td>'
            f"</tr>"
        )

    table_html = (
        '<table class="review-table">'
        "<thead><tr>"
        "<th>#</th>"
        "<th>Key</th>"
        '<th>원본 (Korean)</th>'
        '<th>AI 수정 제안</th>'
        "</tr></thead>"
        f'<tbody>{"".join(rows_html)}</tbody>'
        "</table>"
    )

    st.markdown(table_html, unsafe_allow_html=True)


def render_translation_review_table(translation_report_df, failed_keys: set = None):
    """번역 검수 테이블 -- 커스텀 HTML 렌더링

    Args:
        translation_report_df: DataFrame with columns from generate_translation_diff_report()
            - Key, 언어, 기존 번역, 새 번역, 변경 사유/내역
        failed_keys: set of Key values that failed review (for status badge)
    """
    if translation_report_df is None or translation_report_df.empty:
        return

    if failed_keys is None:
        failed_keys = set()

    rows_html = []
    for row_num, (_, row) in enumerate(translation_report_df.iterrows(), start=1):
        key = html_module.escape(str(row.get("Key", "")))
        lang = html_module.escape(str(row.get("언어", "")))
        old_text = html_module.escape(str(row.get("기존 번역", "")))
        new_text = html_module.escape(str(row.get("새 번역", "")))

        # Status badge
        raw_key = str(row.get("Key", ""))
        if raw_key in failed_keys:
            badge = '<span class="review-badge fail">검수실패</span>'
        else:
            badge = '<span class="review-badge success">번역완료</span>'

        rows_html.append(
            f"<tr>"
            f'  <td class="col-num">{row_num}</td>'
            f'  <td class="col-key">{key}</td>'
            f"  <td>{lang}</td>"
            f"  <td>{old_text}</td>"
            f'  <td class="col-suggested">{new_text}</td>'
            f"  <td>{badge}</td>"
            f"</tr>"
        )

    table_html = (
        '<table class="review-table">'
        "<thead><tr>"
        "<th>#</th>"
        "<th>Key</th>"
        "<th>Lang</th>"
        '<th>기존 번역</th>'
        '<th>새 번역</th>'
        "<th>Status</th>"
        "</tr></thead>"
        f'<tbody>{"".join(rows_html)}</tbody>'
        "</table>"
    )

    st.markdown(table_html, unsafe_allow_html=True)


def render_overall_progress(success_count: int, fail_count: int):
    """Overall progress bar — success/fail ratio

    Args:
        success_count: number of successful translations
        fail_count: number of failed translations
    """
    total = success_count + fail_count
    if total == 0:
        return

    success_pct = (success_count / total) * 100
    fail_pct = (fail_count / total) * 100

    st.markdown(
        f'<div class="overall-progress">'
        f'  <span class="overall-progress-label">'
        f'    {success_count} passed'
        f'  </span>'
        f'  <div class="overall-progress-track">'
        f'    <div class="overall-progress-success" style="width: {success_pct:.1f}%;"></div>'
        f'    <div class="overall-progress-fail" style="width: {fail_pct:.1f}%;"></div>'
        f'  </div>'
        f'  <span class="overall-progress-label">'
        f'    {fail_count} failed'
        f'  </span>'
        f'</div>',
        unsafe_allow_html=True,
    )


