"""게임 로컬라이징 자동화 툴 — Streamlit 메인 앱"""

import uuid
import pandas as pd
import streamlit as st
from langgraph.types import Command

from agents.graph import build_graph
from config.constants import (
    LLM_PRICING,
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
    get_worksheet_names,
    load_sheet_data,
    save_backup_to_folder,
)
from utils.diff_report import (
    generate_ko_diff_report,
    generate_translation_diff_report,
)
from utils.ui_components import (
    inject_custom_css,
    render_step_indicator,
    render_card_start,
    render_card_end,
    render_sidebar_logo,
    render_connection_badge,
    render_app_header,
    render_done_header,
    render_saved_url,
    render_log_terminal,
    render_metric_grid,
)

# ── 페이지 설정 ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="게임 로컬라이징 자동화 툴",
    page_icon="🌐",
    layout="wide",
)

# ── 커스텀 CSS 주입 ──────────────────────────────────────────────────

inject_custom_css()

# ── Session State 초기화 ─────────────────────────────────────────────

_defaults = {
    "thread_id": str(uuid.uuid4()),
    "current_step": "idle",
    "spreadsheet": None,
    "worksheet": None,
    "df": None,
    "backup_csv": None,
    "backup_filename": None,
    "ko_report_df": None,
    "ko_report_csv": None,
    "translation_report_df": None,
    "translation_report_csv": None,
    "logs": [],
    "cost_summary": None,
    "graph_result": None,
    "translations_applied": False,
    # URL 고정 관련
    "saved_url": "",
    "url_editing": False,
    # 백업 폴더
    "backup_folder": "./backups",
}
for key, default in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

if "graph" not in st.session_state:
    graph, checkpointer = build_graph()
    st.session_state.graph = graph


# ── 헬퍼: 번역 phase 스트리밍 실행 ───────────────────────────────────

_NODE_LABELS = {
    "ko_approval": "한국어 검수 승인",
    "translator": "AI 번역",
    "reviewer": "품질 검수",
    "final_approval": "결과 준비",
}
_PROGRESS_NODES = ["translator", "reviewer", "final_approval"]


def _run_translation_streaming(resume_value: str, config: dict):
    """
    번역 phase를 graph.stream()으로 실행하며 실시간 진행 UI 표시.
    translator → reviewer → final_approval(interrupt) 순서로 진행.
    """
    app_logs = list(st.session_state.logs)
    graph_logs = []

    progress_bar = st.progress(0, text="번역 준비 중...")
    log_container = st.empty()

    completed = 0
    total = len(_PROGRESS_NODES)

    try:
        for event in st.session_state.graph.stream(
            Command(resume=resume_value), config, stream_mode="updates"
        ):
            if "__interrupt__" in event:
                break

            node_name = list(event.keys())[0]
            node_output = event[node_name]

            # 로그 업데이트 (각 노드는 누적 로그 전체를 반환)
            node_logs = node_output.get("logs", [])
            if node_logs:
                graph_logs = node_logs

            # 프로그레스 업데이트
            label = _NODE_LABELS.get(node_name, node_name)
            if node_name in _PROGRESS_NODES:
                completed += 1
                pct = min(completed / total, 1.0)
                progress_bar.progress(pct, text=f"{label} 완료")

            # 로그 터미널 실시간 갱신
            with log_container.container():
                render_log_terminal(app_logs + graph_logs)

        progress_bar.progress(1.0, text="번역 및 검수 완료")

    except Exception as e:
        progress_bar.progress(1.0, text="오류 발생")
        st.session_state.logs = app_logs + graph_logs
        raise

    # 최종 state 수집
    state_snapshot = st.session_state.graph.get_state(config)
    result = state_snapshot.values

    # 세션 로그 업데이트
    st.session_state.logs = app_logs + graph_logs

    return result


def _process_translation_result(result: dict):
    """번역 결과를 세션 상태에 저장 (리포트, 비용 등)"""
    st.session_state.graph_result = result

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
        report_df, report_csv = generate_translation_diff_report(
            old_trans, new_trans
        )
        st.session_state.translation_report_df = report_df
        st.session_state.translation_report_csv = report_csv

    st.session_state.cost_summary = {
        "input_tokens": result.get("total_input_tokens", 0),
        "output_tokens": result.get("total_output_tokens", 0),
    }


# ── 사이드바 ─────────────────────────────────────────────────────────

with st.sidebar:
    render_sidebar_logo()

    # ── 시트 연결 ──
    st.markdown(
        '<p class="sidebar-section-title">시트 연결</p>',
        unsafe_allow_html=True,
    )

    # URL 고정 로직
    if st.session_state.saved_url and not st.session_state.url_editing:
        render_saved_url(st.session_state.saved_url)
        if st.button("변경", use_container_width=True):
            st.session_state.url_editing = True
            st.rerun()
        sheet_url = st.session_state.saved_url
    else:
        sheet_url = st.text_input(
            "구글 시트 URL",
            value=st.session_state.saved_url,
            placeholder="https://docs.google.com/spreadsheets/d/...",
            label_visibility="collapsed",
        )
        if sheet_url and sheet_url != st.session_state.saved_url:
            st.session_state.saved_url = sheet_url
            st.session_state.url_editing = False
            st.session_state.spreadsheet = None
            st.rerun()
        elif sheet_url and st.session_state.url_editing:
            st.session_state.url_editing = False

    sheet_names = []
    if sheet_url:
        try:
            if (
                st.session_state.spreadsheet is None
                or st.session_state.get("_last_url") != sheet_url
            ):
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
    st.markdown(
        '<p class="sidebar-section-title">번역 설정</p>',
        unsafe_allow_html=True,
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
        format_func=lambda x: (
            "모드 A (전체 번역/검수)" if x == "A" else "모드 B (빈칸 번역)"
        ),
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

    # ── 백업 폴더 설정 ──
    st.markdown(
        '<p class="sidebar-section-title">백업 설정</p>',
        unsafe_allow_html=True,
    )
    backup_folder = st.text_input(
        "백업 폴더",
        value=st.session_state.backup_folder,
        label_visibility="collapsed",
        placeholder="./backups",
    )
    if backup_folder:
        st.session_state.backup_folder = backup_folder

    st.divider()

    start_button = st.button(
        "작업 시작",
        type="primary",
        disabled=(not sheet_url or not selected_sheet or not target_langs),
        use_container_width=True,
    )

# ── 메인 영역 ────────────────────────────────────────────────────────

render_app_header()

# 스텝 인디케이터
render_step_indicator(st.session_state.current_step)

# ── 작업 시작 처리 ────────────────────────────────────────────────────

if start_button:
    # 이전 작업 상태 초기화 (재실행 허용)
    if st.session_state.current_step != "idle":
        for key in [
            "worksheet", "df", "backup_csv", "backup_filename",
            "ko_report_df", "ko_report_csv",
            "translation_report_df", "translation_report_csv",
            "graph_result", "cost_summary", "translations_applied",
        ]:
            if key in st.session_state:
                del st.session_state[key]
        graph, checkpointer = build_graph()
        st.session_state.graph = graph

    st.session_state.current_step = "loading"
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.logs = []

    with st.spinner("데이터 로드 및 백업 중..."):
        try:
            ws = st.session_state.spreadsheet.worksheet(selected_sheet)
            df = load_sheet_data(ws)
            df = ensure_tool_status_column(ws, df)

            if row_limit > 0:
                df = df.head(row_limit)

            st.session_state.worksheet = ws
            st.session_state.df = df

            # Tool_Status 초기값 '대기' 설정 + 시트에 반영
            status_updates = []
            for idx, row in df.iterrows():
                current_status = row.get(TOOL_STATUS_COLUMN, "")
                if not current_status:
                    df.at[idx, TOOL_STATUS_COLUMN] = Status.WAITING
                    status_updates.append({
                        "row_index": idx,
                        "column_name": TOOL_STATUS_COLUMN,
                        "value": Status.WAITING,
                    })
            if status_updates:
                batch_update_sheet(ws, status_updates, df)

            st.session_state._last_sheet = selected_sheet

            # 백업: 메모리(다운로드용) + 로컬 폴더 자동 저장
            filename, csv_bytes = create_backup_csv(df, selected_sheet)
            st.session_state.backup_filename = filename
            st.session_state.backup_csv = csv_bytes

            local_path = save_backup_to_folder(
                df, selected_sheet, st.session_state.backup_folder
            )

            st.session_state.logs.append(f"데이터 로드 완료: {len(df)}행")
            st.session_state.logs.append(f"원본 백업 저장: {local_path}")

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
                "_updates": [],
            }

            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            result = st.session_state.graph.invoke(initial_state, config=config)
            st.session_state.graph_result = result
            st.session_state.logs.extend(result.get("logs", []))

            ko_results = result.get("ko_review_results", [])
            if ko_results:
                original_rows = [
                    {
                        "Key": r.get(REQUIRED_COLUMNS["key"], ""),
                        "Korean(ko)": r.get(REQUIRED_COLUMNS["korean"], ""),
                    }
                    for r in df.to_dict("records")
                ]
                revised_rows = [
                    {
                        "Key": r["key"],
                        "Korean(ko)": r.get("revised", r.get("original", "")),
                    }
                    for r in ko_results
                ]
                report_df, report_csv = generate_ko_diff_report(
                    original_rows, revised_rows
                )
                st.session_state.ko_report_df = report_df
                st.session_state.ko_report_csv = report_csv

            st.session_state.current_step = "ko_review"

        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.session_state.logs.append(f"오류: {e}")
            st.session_state.current_step = "idle"

    st.rerun()

# ── HITL 1: 한국어 검수 승인 ──────────────────────────────────────────

if st.session_state.current_step == "ko_review":
    ko_count = (
        len(st.session_state.ko_report_df)
        if st.session_state.ko_report_df is not None
        and not st.session_state.ko_report_df.empty
        else 0
    )
    render_card_start(
        "✏️",
        "한국어 사전 검수",
        f"수정 제안 {ko_count}건" if ko_count else "",
    )

    if ko_count > 0:
        st.dataframe(st.session_state.ko_report_df, use_container_width=True)
        st.download_button(
            label="한국어 변경 리포트 (CSV)",
            data=st.session_state.ko_report_csv,
            file_name="ko_review_report.csv",
            mime="text/csv",
        )
    else:
        st.success("수정 제안 없음 — 원본 한국어가 양호합니다.")

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        btn_approve = st.button(
            "변경 사항 승인 및 번역 시작",
            type="primary",
            use_container_width=True,
        )
    with col2:
        btn_reject = st.button(
            "제안 무시하고 원본 그대로 번역",
            use_container_width=True,
        )

    render_card_end()

    # 버튼 핸들러 — 카드 밖에서 실행 (진행 UI를 전체 폭으로 표시)
    if btn_approve or btn_reject:
        resume_value = "approved" if btn_approve else "rejected"

        # 시트 상태 업데이트
        if st.session_state.worksheet and st.session_state.df is not None:
            _df = st.session_state.df
            _ws = st.session_state.worksheet
            if btn_approve:
                _upd = [
                    {"row_index": i, "column_name": TOOL_STATUS_COLUMN,
                     "value": Status.KO_REVIEW_DONE}
                    for i in range(len(_df))
                ]
                batch_update_sheet(_ws, _upd, _df)
            _upd2 = [
                {"row_index": i, "column_name": TOOL_STATUS_COLUMN,
                 "value": Status.TRANSLATING}
                for i in range(len(_df))
            ]
            batch_update_sheet(_ws, _upd2, _df)

        st.session_state.current_step = "translating"
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        try:
            result = _run_translation_streaming(resume_value, config)
            _process_translation_result(result)
            st.session_state.current_step = "final_review"
        except Exception as e:
            st.session_state.logs.append(f"번역 오류: {e}")
            # 그래프 재생성 후 ko_review로 복구 (재시도 가능)
            graph, _ = build_graph()
            st.session_state.graph = graph
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.current_step = "idle"

        st.rerun()

# ── HITL 2: 최종 번역 승인 ────────────────────────────────────────────

if st.session_state.current_step == "final_review":
    review_count = (
        len(st.session_state.translation_report_df)
        if st.session_state.translation_report_df is not None
        and not st.session_state.translation_report_df.empty
        else 0
    )
    fail_count = (
        len(st.session_state.graph_result.get("failed_rows", []))
        if st.session_state.graph_result
        else 0
    )
    render_card_start(
        "🔍",
        "최종 번역 검토",
        f"변경 {review_count}건 · 실패 {fail_count}건",
    )

    if review_count > 0:
        st.dataframe(
            st.session_state.translation_report_df, use_container_width=True
        )
        st.download_button(
            label="번역 변경 리포트 (CSV)",
            data=st.session_state.translation_report_csv,
            file_name="translation_diff_report.csv",
            mime="text/csv",
        )
    else:
        st.info("변경 사항 없음")

    if fail_count > 0:
        st.warning(
            f"검수 실패: {fail_count}건 — 아래 행은 검증 통과 실패"
        )
        failed_df = pd.DataFrame(
            st.session_state.graph_result.get("failed_rows", [])
        )
        st.dataframe(failed_df, use_container_width=True)

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "시트에 최종 업데이트 적용",
            type="primary",
            use_container_width=True,
        ):
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            with st.spinner("시트 업데이트 중..."):
                try:
                    result = st.session_state.graph.invoke(
                        Command(resume="approved"), config=config
                    )
                    st.session_state.graph_result = result
                    st.session_state.logs.extend(result.get("logs", []))

                    updates = result.get("_updates", [])
                    if (
                        updates
                        and st.session_state.worksheet
                        and st.session_state.df is not None
                    ):
                        batch_update_sheet(
                            st.session_state.worksheet,
                            updates,
                            st.session_state.df,
                        )
                        st.session_state.logs.append(
                            f"시트 업데이트 완료: {len(updates)}건"
                        )

                    st.session_state.translations_applied = True
                    st.session_state.current_step = "done"
                except Exception as e:
                    st.error(f"시트 업데이트 오류: {e}")
                    st.session_state.logs.append(f"업데이트 오류: {e}")
            st.rerun()

    with col2:
        if st.button("적용 취소 (시트 원복)", use_container_width=True):
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            try:
                st.session_state.graph.invoke(
                    Command(resume="rejected"), config=config
                )
            except Exception:
                pass

            # Tool_Status 컬럼을 원래 상태로 복원
            if (
                st.session_state.worksheet is not None
                and st.session_state.df is not None
            ):
                _ws = st.session_state.worksheet
                _df = st.session_state.df
                backup_data = st.session_state.graph_result.get("backup_data", []) if st.session_state.graph_result else []
                revert_updates = []
                for i in range(len(_df)):
                    original_status = ""
                    if i < len(backup_data):
                        original_status = backup_data[i].get(TOOL_STATUS_COLUMN, "")
                    revert_updates.append({
                        "row_index": i,
                        "column_name": TOOL_STATUS_COLUMN,
                        "value": original_status,
                    })
                if revert_updates:
                    try:
                        batch_update_sheet(_ws, revert_updates, _df)
                        st.session_state.logs.append(
                            f"Tool_Status 원복 완료: {len(revert_updates)}건"
                        )
                    except Exception as e:
                        st.session_state.logs.append(f"Tool_Status 원복 오류: {e}")

            st.session_state.translations_applied = False
            st.session_state.current_step = "done"
            st.session_state.logs.append("적용 취소 — 시트가 원래 상태로 복원되었습니다")
            st.rerun()

    render_card_end()

# ── 완료 화면 ─────────────────────────────────────────────────────────

if st.session_state.current_step == "done":
    if st.session_state.get("translations_applied"):
        render_card_start("✅", "작업 완료", "번역이 시트에 적용되었습니다")
    else:
        render_card_start("↩️", "작업 완료", "적용 취소 — 시트가 원래 상태로 복원되었습니다")
    render_done_header()

    # 메트릭 그리드
    if st.session_state.cost_summary:
        summary = st.session_state.cost_summary
        input_t = summary.get("input_tokens", 0)
        output_t = summary.get("output_tokens", 0)
        cost = (input_t * LLM_PRICING["input"]) + (output_t * LLM_PRICING["output"])

        review_count = 0
        if (
            st.session_state.translation_report_df is not None
            and not st.session_state.translation_report_df.empty
        ):
            review_count = len(st.session_state.translation_report_df)

        fail_count = 0
        if st.session_state.graph_result:
            fail_count = len(st.session_state.graph_result.get("failed_rows", []))

        render_metric_grid([
            {"label": "번역 건수", "value": str(review_count), "type": "accent"},
            {"label": "실패", "value": str(fail_count),
             "type": "error" if fail_count else "success"},
            {"label": "Input 토큰", "value": f"{input_t:,}", "type": ""},
            {"label": "Output 토큰", "value": f"{output_t:,}", "type": ""},
            {"label": "예상 비용", "value": f"${cost:.4f}", "type": "warning"},
        ])

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # 다운로드 버튼 그리드
    dl_cols = st.columns(3)
    with dl_cols[0]:
        if st.session_state.backup_csv:
            st.download_button(
                label="원본 백업 (CSV)",
                data=st.session_state.backup_csv,
                file_name=st.session_state.backup_filename or "backup.csv",
                mime="text/csv",
                use_container_width=True,
            )
    with dl_cols[1]:
        if st.session_state.translation_report_csv:
            st.download_button(
                label="번역 리포트 (CSV)",
                data=st.session_state.translation_report_csv,
                file_name="translation_diff_report.csv",
                mime="text/csv",
                use_container_width=True,
            )
    with dl_cols[2]:
        if st.session_state.logs:
            log_text = "\n".join(st.session_state.logs)
            st.download_button(
                label="전체 로그 (TXT)",
                data=log_text.encode("utf-8"),
                file_name="execution_log.txt",
                mime="text/plain",
                use_container_width=True,
            )

    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    if st.button("새 작업 시작", use_container_width=True):
        for key in [
            "current_step", "worksheet", "df",
            "backup_csv", "backup_filename", "ko_report_df", "ko_report_csv",
            "translation_report_df", "translation_report_csv",
            "graph_result", "logs", "cost_summary", "translations_applied",
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.current_step = "idle"
        st.rerun()

    render_card_end()

# ── 실행 로그 (터미널 스타일) ─────────────────────────────────────────

if st.session_state.logs and st.session_state.current_step != "done":
    render_log_terminal(st.session_state.logs)
