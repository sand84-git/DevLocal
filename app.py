"""게임 로컬라이징 자동화 툴 — Streamlit 메인 앱"""

import uuid
import pandas as pd
import streamlit as st
from langgraph.types import Command

from agents.graph import build_graph
from config.constants import (
    REQUIRED_COLUMNS,
    SUPPORTED_LANGUAGES,
    Status,
    TOOL_STATUS_COLUMN,
)
from utils.sheets import (
    batch_update_sheet,
    connect_to_sheet,
    create_backup_csv,
    ensure_tool_status_column,
    get_bot_email,
    get_worksheet_names,
    load_sheet_data,
)
from utils.diff_report import (
    generate_ko_diff_report,
    generate_translation_diff_report,
)

# ── 페이지 설정 ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="게임 로컬라이징 자동화 툴",
    page_icon="🌐",
    layout="wide",
)

# ── 커스텀 CSS (Warm & Minimalist) ────────────────────────────────────

st.markdown("""
<style>
    /* 메인 배경 */
    .stApp {
        background-color: #F6F5F0;
    }

    /* 카드 스타일 */
    .card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* 포인트 컬러 버튼 */
    .stButton > button[kind="primary"] {
        background-color: #C85A32;
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #B04E2A;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
    }

    /* 텍스트 */
    h1, h2, h3, p, span, label {
        color: #2C2C2C !important;
    }

    /* 다운로드 버튼 스타일 */
    .stDownloadButton > button {
        border-radius: 12px;
        border: 1px solid #C85A32;
        color: #C85A32;
    }

    /* Progress bar */
    .stProgress > div > div {
        background-color: #C85A32;
    }

    /* 구분선 */
    hr {
        border: none;
        border-top: 1px solid #E8E6E1;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Session State 초기화 ─────────────────────────────────────────────

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "current_step" not in st.session_state:
    st.session_state.current_step = "idle"  # idle → ko_review → translating → final_review → done
if "spreadsheet" not in st.session_state:
    st.session_state.spreadsheet = None
if "worksheet" not in st.session_state:
    st.session_state.worksheet = None
if "df" not in st.session_state:
    st.session_state.df = None
if "backup_csv" not in st.session_state:
    st.session_state.backup_csv = None
if "backup_filename" not in st.session_state:
    st.session_state.backup_filename = None
if "ko_report_df" not in st.session_state:
    st.session_state.ko_report_df = None
if "ko_report_csv" not in st.session_state:
    st.session_state.ko_report_csv = None
if "translation_report_df" not in st.session_state:
    st.session_state.translation_report_df = None
if "translation_report_csv" not in st.session_state:
    st.session_state.translation_report_csv = None
if "graph" not in st.session_state:
    graph, checkpointer = build_graph()
    st.session_state.graph = graph
if "logs" not in st.session_state:
    st.session_state.logs = []
if "cost_summary" not in st.session_state:
    st.session_state.cost_summary = None
if "graph_result" not in st.session_state:
    st.session_state.graph_result = None

# ── 사이드바 ─────────────────────────────────────────────────────────

with st.sidebar:
    st.header("설정")

    sheet_url = st.text_input(
        "구글 시트 URL",
        placeholder="https://docs.google.com/spreadsheets/d/...",
    )

    # 시트 연결
    sheet_names = []
    if sheet_url:
        try:
            if st.session_state.spreadsheet is None or st.session_state.get("_last_url") != sheet_url:
                with st.spinner("시트 연결 중..."):
                    st.session_state.spreadsheet = connect_to_sheet(sheet_url)
                    st.session_state._last_url = sheet_url
            sheet_names = get_worksheet_names(st.session_state.spreadsheet)
        except Exception as e:
            st.error(f"시트 연결 실패: {e}")

    selected_sheet = st.selectbox(
        "작업 대상 시트",
        options=sheet_names,
        disabled=not sheet_names,
    )

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
    )

    st.divider()

    start_button = st.button(
        "작업 시작",
        type="primary",
        disabled=(not sheet_url or not selected_sheet or not target_langs),
        use_container_width=True,
    )

# ── 메인 영역 ────────────────────────────────────────────────────────

st.title("게임 로컬라이징 자동화 툴")

# 봇 이메일 안내
try:
    bot_email = get_bot_email()
    if bot_email:
        st.info(
            f"💡 [공유] 버튼을 누르고 아래 봇 이메일을 **편집자**로 초대해 주세요: `{bot_email}`"
        )
except Exception:
    pass

# ── 작업 시작 처리 ────────────────────────────────────────────────────

if start_button and st.session_state.current_step == "idle":
    st.session_state.current_step = "loading"
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.logs = []

    with st.spinner("데이터 로드 및 백업 중..."):
        try:
            # 워크시트 로드
            ws = st.session_state.spreadsheet.worksheet(selected_sheet)
            df = load_sheet_data(ws)
            df = ensure_tool_status_column(ws, df)

            st.session_state.worksheet = ws
            st.session_state.df = df

            # 강제 백업
            filename, csv_bytes = create_backup_csv(df, selected_sheet)
            st.session_state.backup_filename = filename
            st.session_state.backup_csv = csv_bytes

            st.session_state.logs.append(
                f"데이터 로드 완료: {len(df)}행, 백업 생성: {filename}"
            )

            # LangGraph 초기 상태 구성
            initial_state = {
                "sheet_name": selected_sheet,
                "mode": mode,
                "target_languages": target_langs,
                "original_data": df.to_dict("records"),
                "backup_data": df.to_dict("records"),
                "ko_review_results": [],
                "translation_results": [],
                "review_results": [],
                "failed_rows": [],
                "diff_report_ko": None,
                "diff_report_translation": None,
                "wait_for_ko_approval": False,
                "ko_approval_result": None,
                "wait_for_final_approval": False,
                "final_approval_result": None,
                "current_chunk_index": 0,
                "total_chunks": 0,
                "retry_count": {},
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "logs": [],
            }

            config = {"configurable": {"thread_id": st.session_state.thread_id}}

            # 그래프 실행 → HITL 1(ko_review)에서 interrupt될 때까지
            result = st.session_state.graph.invoke(initial_state, config=config)
            st.session_state.graph_result = result
            st.session_state.logs.extend(result.get("logs", []))

            # 한국어 검수 결과 → 리포트 생성
            ko_results = result.get("ko_review_results", [])
            if ko_results:
                original_rows = [
                    {"Key": r.get(REQUIRED_COLUMNS["key"], ""), "Korean(ko)": r.get(REQUIRED_COLUMNS["korean"], "")}
                    for r in df.to_dict("records")
                ]
                revised_rows = [
                    {"Key": r["key"], "Korean(ko)": r.get("revised", r.get("original", ""))}
                    for r in ko_results
                ]
                report_df, report_csv = generate_ko_diff_report(original_rows, revised_rows)
                st.session_state.ko_report_df = report_df
                st.session_state.ko_report_csv = report_csv

            st.session_state.current_step = "ko_review"

        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.session_state.logs.append(f"오류: {e}")
            st.session_state.current_step = "idle"

    st.rerun()

# ── 백업 다운로드 ─────────────────────────────────────────────────────

if st.session_state.backup_csv:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("백업 파일")
    st.warning("⚠️ 백업 파일을 반드시 다운로드하세요!")
    st.download_button(
        label=f"📥 {st.session_state.backup_filename} 다운로드",
        data=st.session_state.backup_csv,
        file_name=st.session_state.backup_filename,
        mime="text/csv",
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ── HITL 1: 한국어 검수 승인 ──────────────────────────────────────────

if st.session_state.current_step == "ko_review":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Step 1: 한국어 사전 검수 결과")

    if st.session_state.ko_report_df is not None and not st.session_state.ko_report_df.empty:
        st.dataframe(st.session_state.ko_report_df, use_container_width=True)
        st.download_button(
            label="📥 한국어 변경 리포트 (CSV) 다운로드",
            data=st.session_state.ko_report_csv,
            file_name="ko_review_report.csv",
            mime="text/csv",
        )
    else:
        st.success("수정 제안 없음 — 원본 한국어가 양호합니다.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 변경 사항 승인 및 번역 시작", type="primary", use_container_width=True):
            st.session_state.current_step = "translating"
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            with st.spinner("번역 및 검수 진행 중... (시간이 소요될 수 있습니다)"):
                try:
                    result = st.session_state.graph.invoke(
                        Command(resume="approved"), config=config
                    )
                    st.session_state.graph_result = result
                    st.session_state.logs.extend(result.get("logs", []))

                    # 번역 변경 리포트 생성
                    review_results = result.get("review_results", [])
                    if review_results:
                        old_trans = []
                        new_trans = []
                        for r in review_results:
                            old_trans.append({
                                "Key": r["key"],
                                "lang": r["lang"],
                                "old": r.get("old_translation", ""),
                            })
                            new_trans.append({
                                "Key": r["key"],
                                "lang": r["lang"],
                                "new": r["translated"],
                                "reason": r.get("reason", ""),
                            })
                        report_df, report_csv = generate_translation_diff_report(old_trans, new_trans)
                        st.session_state.translation_report_df = report_df
                        st.session_state.translation_report_csv = report_csv

                    # 비용 요약
                    st.session_state.cost_summary = {
                        "input_tokens": result.get("total_input_tokens", 0),
                        "output_tokens": result.get("total_output_tokens", 0),
                    }

                    st.session_state.current_step = "final_review"
                except Exception as e:
                    st.error(f"번역 중 오류: {e}")
                    st.session_state.logs.append(f"번역 오류: {e}")
            st.rerun()

    with col2:
        if st.button("👎 제안 무시하고 원본 그대로 번역 시작", use_container_width=True):
            st.session_state.current_step = "translating"
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            with st.spinner("번역 및 검수 진행 중... (시간이 소요될 수 있습니다)"):
                try:
                    result = st.session_state.graph.invoke(
                        Command(resume="rejected"), config=config
                    )
                    st.session_state.graph_result = result
                    st.session_state.logs.extend(result.get("logs", []))

                    review_results = result.get("review_results", [])
                    if review_results:
                        old_trans = []
                        new_trans = []
                        for r in review_results:
                            old_trans.append({
                                "Key": r["key"],
                                "lang": r["lang"],
                                "old": r.get("old_translation", ""),
                            })
                            new_trans.append({
                                "Key": r["key"],
                                "lang": r["lang"],
                                "new": r["translated"],
                                "reason": r.get("reason", ""),
                            })
                        report_df, report_csv = generate_translation_diff_report(old_trans, new_trans)
                        st.session_state.translation_report_df = report_df
                        st.session_state.translation_report_csv = report_csv

                    st.session_state.cost_summary = {
                        "input_tokens": result.get("total_input_tokens", 0),
                        "output_tokens": result.get("total_output_tokens", 0),
                    }

                    st.session_state.current_step = "final_review"
                except Exception as e:
                    st.error(f"번역 중 오류: {e}")
                    st.session_state.logs.append(f"번역 오류: {e}")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── HITL 2: 최종 번역 승인 ────────────────────────────────────────────

if st.session_state.current_step == "final_review":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Step 3: 최종 번역 변경 사항 검토")

    if st.session_state.translation_report_df is not None and not st.session_state.translation_report_df.empty:
        st.dataframe(st.session_state.translation_report_df, use_container_width=True)
        st.download_button(
            label="📥 번역 변경 리포트 (CSV) 다운로드",
            data=st.session_state.translation_report_csv,
            file_name="translation_diff_report.csv",
            mime="text/csv",
        )
    else:
        st.info("변경 사항 없음")

    # 검수실패 행 표시
    if st.session_state.graph_result:
        failed_rows = st.session_state.graph_result.get("failed_rows", [])
        if failed_rows:
            st.warning(f"⚠️ 검수 실패: {len(failed_rows)}건")
            failed_df = pd.DataFrame(failed_rows)
            st.dataframe(failed_df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 시트에 최종 업데이트 적용", type="primary", use_container_width=True):
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            with st.spinner("시트 업데이트 중..."):
                try:
                    result = st.session_state.graph.invoke(
                        Command(resume="approved"), config=config
                    )
                    st.session_state.graph_result = result
                    st.session_state.logs.extend(result.get("logs", []))

                    # 실제 시트에 Batch Update 실행
                    updates = result.get("_updates", [])
                    if updates and st.session_state.worksheet and st.session_state.df is not None:
                        batch_update_sheet(
                            st.session_state.worksheet,
                            updates,
                            st.session_state.df,
                        )
                        st.session_state.logs.append(
                            f"시트 업데이트 완료: {len(updates)}건"
                        )

                    st.session_state.current_step = "done"
                except Exception as e:
                    st.error(f"시트 업데이트 오류: {e}")
                    st.session_state.logs.append(f"업데이트 오류: {e}")
            st.rerun()

    with col2:
        if st.button("❌ 반려 (시트 미변경)", use_container_width=True):
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            try:
                st.session_state.graph.invoke(
                    Command(resume="rejected"), config=config
                )
            except Exception:
                pass
            st.session_state.current_step = "done"
            st.session_state.logs.append("최종 승인 반려 — 시트 미변경")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── 완료 화면 ─────────────────────────────────────────────────────────

if st.session_state.current_step == "done":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("작업 완료")
    st.success("모든 작업이 완료되었습니다!")

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

    if st.button("새 작업 시작", use_container_width=True):
        for key in [
            "current_step", "spreadsheet", "worksheet", "df",
            "backup_csv", "backup_filename", "ko_report_df", "ko_report_csv",
            "translation_report_df", "translation_report_csv",
            "graph_result", "logs", "cost_summary",
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.current_step = "idle"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── 실시간 로그 ───────────────────────────────────────────────────────

if st.session_state.logs:
    with st.expander("📋 실행 로그", expanded=False):
        log_text = "\n".join(st.session_state.logs)
        st.text_area("로그", value=log_text, height=300, disabled=True)

# ── Progress Bar (번역 진행 중일 때) ──────────────────────────────────

if st.session_state.current_step == "translating":
    st.progress(0.5, text="번역 및 검수 진행 중...")
