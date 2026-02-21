"""API 라우트 — REST + SSE endpoints"""

import asyncio
import io
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.types import Command
from sse_starlette.sse import EventSourceResponse

from backend.api.schemas import (
    ApprovalRequest,
    ConnectRequest,
    ConnectResponse,
    SessionStateResponse,
    StartRequest,
    StartResponse,
)
from backend.api.session_manager import session_manager
from config.constants import (
    LLM_PRICING,
    REQUIRED_COLUMNS,
    SUPPORTED_LANGUAGES,
    Status,
    TOOL_STATUS_COLUMN,
)
from utils.diff_report import generate_ko_diff_report, generate_translation_diff_report
from utils.sheets import (
    batch_format_cells,
    batch_update_sheet,
    connect_to_sheet,
    create_backup_csv,
    ensure_tool_status_column,
    get_bot_email,
    get_worksheet_names,
    load_sheet_data,
    save_backup_to_folder,
)

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)

# ── 로컬 설정 파일 ──────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / ".app_config.json"


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_config(data: dict):
    try:
        existing = _load_config()
        existing.update(data)
        _CONFIG_PATH.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


# ── Sheet Connection ─────────────────────────────────────────────────

@router.post("/connect", response_model=ConnectResponse)
def api_connect(req: ConnectRequest):
    """시트 연결 + 시트 목록 반환"""
    try:
        spreadsheet = connect_to_sheet(req.sheet_url)
        sheet_names = get_worksheet_names(spreadsheet)
        bot_email = get_bot_email()
        _save_config({"saved_url": req.sheet_url})
        return ConnectResponse(sheet_names=sheet_names, bot_email=bot_email)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Start Pipeline ───────────────────────────────────────────────────

@router.post("/start", response_model=StartResponse)
def api_start(req: StartRequest):
    """번역 파이프라인 시작 — 세션 생성 + 데이터 준비"""
    session = session_manager.create()
    try:
        session.spreadsheet = connect_to_sheet(req.sheet_url)
        ws = session.spreadsheet.worksheet(req.sheet_name)
        df = load_sheet_data(ws)
        df = ensure_tool_status_column(ws, df)

        if req.row_limit > 0:
            df = df.head(req.row_limit)

        session.worksheet = ws
        session.df = df

        # Tool_Status 초기화
        status_updates = []
        for idx in range(len(df)):
            current_status = df.iloc[idx].get(TOOL_STATUS_COLUMN, "")
            if not current_status:
                df.at[idx, TOOL_STATUS_COLUMN] = Status.WAITING
                status_updates.append({
                    "row_index": idx,
                    "column_name": TOOL_STATUS_COLUMN,
                    "value": Status.WAITING,
                })
        if status_updates:
            batch_update_sheet(ws, status_updates, df)

        # 백업
        filename, csv_bytes = create_backup_csv(df, req.sheet_name)
        session.backup_filename = filename
        session.backup_csv = csv_bytes
        save_backup_to_folder(df, req.sheet_name)

        # 초기 state 저장
        session.initial_state = {
            "sheet_name": req.sheet_name,
            "mode": req.mode,
            "target_languages": req.target_languages,
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
            "_needs_retry": [],
        }
        session.current_step = "loading"
        return StartResponse(session_id=session.id)
    except Exception as e:
        session_manager.delete(session.id)
        raise HTTPException(status_code=400, detail=str(e))


# ── SSE Stream ───────────────────────────────────────────────────────

def _run_initial_phase(session):
    """초기 phase 실행 (data_backup → context_glossary → ko_review → ko_approval interrupt)"""
    try:
        for event in session.graph.stream(
            session.initial_state, config=session.config, stream_mode="updates"
        ):
            if "__interrupt__" in event:
                asyncio.run_coroutine_threadsafe(
                    session.event_queue.put(("interrupt", {})),
                    session._loop,
                )
                break

            node_name = list(event.keys())[0]
            node_output = event[node_name]
            node_logs = node_output.get("logs", [])

            asyncio.run_coroutine_threadsafe(
                session.event_queue.put(("node_update", {
                    "node": node_name,
                    "step": "loading",
                    "logs": node_logs,
                })),
                session._loop,
            )

        # ko_review 결과 수집
        state_snapshot = session.graph.get_state(session.config)
        result = state_snapshot.values
        session.graph_result = result
        session.logs = result.get("logs", [])
        session.current_step = "ko_review"

        # KR diff 리포트 생성
        ko_results = result.get("ko_review_results", [])
        ko_report_data = None
        if ko_results and session.df is not None:
            original_rows = [
                {"Key": r.get(REQUIRED_COLUMNS["key"], ""),
                 "Korean(ko)": r.get(REQUIRED_COLUMNS["korean"], "")}
                for _, r in session.df.iterrows()
            ]
            revised_rows = [
                {"Key": r["key"],
                 "Korean(ko)": r.get("revised", r.get("original", ""))}
                for r in ko_results
            ]
            report_df, report_csv = generate_ko_diff_report(original_rows, revised_rows)
            session.ko_report_df = report_df
            session.ko_report_csv = report_csv
            ko_report_data = report_df.to_dict("records")

        asyncio.run_coroutine_threadsafe(
            session.event_queue.put(("ko_review_ready", {
                "results": ko_results,
                "count": len(ko_results),
                "report": ko_report_data,
            })),
            session._loop,
        )
    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            session.event_queue.put(("error", {"message": str(e)})),
            session._loop,
        )


@router.get("/stream/{session_id}")
async def api_stream(session_id: str):
    """SSE 스트림 — 파이프라인 실시간 이벤트"""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    loop = asyncio.get_event_loop()
    session._loop = loop
    session.event_queue = asyncio.Queue()

    # 백그라운드에서 초기 phase 실행
    executor.submit(_run_initial_phase, session)

    async def event_generator():
        while True:
            try:
                event_type, data = await asyncio.wait_for(
                    session.event_queue.get(), timeout=300
                )
                yield {"event": event_type, "data": json.dumps(data, ensure_ascii=False)}
                if event_type in ("done", "error"):
                    break
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": "{}"}

    return EventSourceResponse(event_generator())


# ── HITL 1: KR Approval ─────────────────────────────────────────────

def _run_translation_phase(session, resume_value: str):
    """번역 phase 실행 (translator → reviewer → final_approval interrupt)"""
    try:
        for event in session.graph.stream(
            Command(resume=resume_value), session.config, stream_mode="updates"
        ):
            if "__interrupt__" in event:
                break

            node_name = list(event.keys())[0]
            node_output = event[node_name]
            node_logs = node_output.get("logs", [])

            asyncio.run_coroutine_threadsafe(
                session.event_queue.put(("node_update", {
                    "node": node_name,
                    "step": "translating",
                    "logs": node_logs,
                })),
                session._loop,
            )

        # 결과 수집
        state_snapshot = session.graph.get_state(session.config)
        result = state_snapshot.values
        session.graph_result = result
        session.logs = result.get("logs", [])
        session.current_step = "final_review"

        # Translation diff report
        review_results = result.get("review_results", [])
        report_data = None
        if review_results:
            old_trans = [{"Key": r["key"], "lang": r["lang"],
                         "old": r.get("old_translation", "")} for r in review_results]
            new_trans = [{"Key": r["key"], "lang": r["lang"],
                         "new": r["translated"], "reason": r.get("reason", "")}
                        for r in review_results]
            report_df, report_csv = generate_translation_diff_report(old_trans, new_trans)
            session.translation_report_df = report_df
            session.translation_report_csv = report_csv
            report_data = report_df.to_dict("records")

        cost_summary = {
            "input_tokens": result.get("total_input_tokens", 0),
            "output_tokens": result.get("total_output_tokens", 0),
        }

        asyncio.run_coroutine_threadsafe(
            session.event_queue.put(("final_review_ready", {
                "review_results": review_results,
                "failed_rows": result.get("failed_rows", []),
                "report": report_data,
                "cost": cost_summary,
            })),
            session._loop,
        )
    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            session.event_queue.put(("error", {"message": str(e)})),
            session._loop,
        )


@router.post("/approve-ko/{session_id}")
async def api_approve_ko(session_id: str, req: ApprovalRequest):
    """HITL 1: 한국어 검수 승인/거부 → 번역 phase 시작"""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ko_resume_value = req.decision
    session.current_step = "translating"

    # 시트 상태 업데이트
    if session.worksheet and session.df is not None:
        df = session.df
        ws = session.worksheet
        if req.decision == "approved":
            upd = [{"row_index": i, "column_name": TOOL_STATUS_COLUMN,
                     "value": Status.KO_REVIEW_DONE} for i in range(len(df))]
            batch_update_sheet(ws, upd, df)
        upd2 = [{"row_index": i, "column_name": TOOL_STATUS_COLUMN,
                  "value": Status.TRANSLATING} for i in range(len(df))]
        batch_update_sheet(ws, upd2, df)

    # 백그라운드에서 번역 실행
    loop = asyncio.get_event_loop()
    session._loop = loop
    executor.submit(_run_translation_phase, session, req.decision)

    return {"status": "translating"}


# ── HITL 2: Final Approval ───────────────────────────────────────────

@router.post("/approve-final/{session_id}")
async def api_approve_final(session_id: str, req: ApprovalRequest):
    """HITL 2: 최종 승인 → 시트 업데이트 / 거부 → 원복"""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    config = session.config

    if req.decision == "approved":
        try:
            result = session.graph.invoke(Command(resume="approved"), config=config)
            session.graph_result = result
            session.logs = result.get("logs", [])

            updates = result.get("_updates", [])
            if updates and session.worksheet and session.df is not None:
                batch_update_sheet(session.worksheet, updates, session.df)
                try:
                    batch_format_cells(session.worksheet, updates, session.df)
                except Exception:
                    pass

            session.current_step = "done"
            return {
                "status": "done",
                "updates_count": len(updates),
                "translations_applied": True,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # 거부: Tool_Status 원복
        try:
            session.graph.invoke(Command(resume="rejected"), config=config)
        except Exception:
            pass

        if session.worksheet and session.df is not None:
            backup_data = (session.graph_result.get("backup_data", [])
                          if session.graph_result else [])
            revert_updates = []
            for i in range(len(session.df)):
                original_status = ""
                if i < len(backup_data):
                    original_status = backup_data[i].get(TOOL_STATUS_COLUMN, "")
                revert_updates.append({
                    "row_index": i,
                    "column_name": TOOL_STATUS_COLUMN,
                    "value": original_status,
                })
            if revert_updates:
                batch_update_sheet(session.worksheet, revert_updates, session.df)

        session.current_step = "done"
        return {"status": "done", "translations_applied": False}


# ── Cancel ───────────────────────────────────────────────────────────

@router.post("/cancel/{session_id}")
def api_cancel(session_id: str):
    """번역 취소 → ko_review로 복귀"""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from agents.graph import build_graph

    # 그래프 재생성
    session.graph, session.checkpointer = build_graph()
    session.thread_id = str(uuid.uuid4())
    session.config = {"configurable": {"thread_id": session.thread_id}}

    if session.initial_state:
        try:
            for ev in session.graph.stream(
                session.initial_state, config=session.config, stream_mode="updates"
            ):
                if "__interrupt__" in ev:
                    break
            session.current_step = "ko_review"
            return {"status": "ko_review"}
        except Exception as e:
            session.current_step = "idle"
            raise HTTPException(status_code=500, detail=str(e))

    session.current_step = "idle"
    return {"status": "idle"}


# ── State Query ──────────────────────────────────────────────────────

@router.get("/state/{session_id}", response_model=SessionStateResponse)
def api_state(session_id: str):
    """세션 상태 조회"""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    ko_count = 0
    review_count = 0
    fail_count = 0
    cost_summary = None

    if session.graph_result:
        ko_count = len(session.graph_result.get("ko_review_results", []))
        review_count = len(session.graph_result.get("review_results", []))
        fail_count = len(session.graph_result.get("failed_rows", []))
        input_t = session.graph_result.get("total_input_tokens", 0)
        output_t = session.graph_result.get("total_output_tokens", 0)
        cost = (input_t * LLM_PRICING["input"]) + (output_t * LLM_PRICING["output"])
        cost_summary = {
            "input_tokens": input_t,
            "output_tokens": output_t,
            "estimated_cost_usd": round(cost, 4),
        }

    return SessionStateResponse(
        session_id=session.id,
        current_step=session.current_step,
        ko_review_count=ko_count,
        review_count=review_count,
        fail_count=fail_count,
        cost_summary=cost_summary,
        logs=session.logs,
    )


# ── Downloads ────────────────────────────────────────────────────────

@router.get("/download/{session_id}/{file_type}")
def api_download(session_id: str, file_type: str):
    """CSV 다운로드"""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if file_type == "backup":
        data = getattr(session, "backup_csv", None)
        name = getattr(session, "backup_filename", "backup.csv")
    elif file_type == "ko_report":
        data = getattr(session, "ko_report_csv", None)
        name = "ko_review_report.csv"
    elif file_type == "translation_report":
        data = getattr(session, "translation_report_csv", None)
        name = "translation_diff_report.csv"
    elif file_type == "failed":
        if session.graph_result:
            failed = session.graph_result.get("failed_rows", [])
            if failed:
                data = pd.DataFrame(failed).to_csv(index=False).encode("utf-8")
            else:
                data = None
        else:
            data = None
        name = "review_failed_rows.csv"
    elif file_type == "logs":
        data = "\n".join(session.logs).encode("utf-8") if session.logs else None
        name = "execution_log.txt"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown file type: {file_type}")

    if not data:
        raise HTTPException(status_code=404, detail="No data available")

    media_type = "text/plain" if file_type == "logs" else "text/csv"
    return StreamingResponse(
        io.BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


# ── Config (saved URL) ──────────────────────────────────────────────

@router.get("/config")
def api_get_config():
    """저장된 설정 조회"""
    return _load_config()


@router.put("/config")
def api_save_config(data: dict):
    """설정 저장"""
    _save_config(data)
    return {"status": "saved"}
