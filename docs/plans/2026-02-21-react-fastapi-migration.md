# React + FastAPI Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Streamlit 앱을 React(Vite+Tailwind) 프론트엔드 + FastAPI 백엔드로 완전 마이그레이션하여, Stitch 디자인을 100% 재현한다.

**Architecture:** FastAPI가 SSE(Server-Sent Events)로 LangGraph `graph.stream()` 이벤트를 실시간 전달하고, HITL 인터럽트는 REST POST로 처리한다. 기존 8-node 그래프, 검증, 글로서리, 프롬프트 로직은 변경 없이 재사용한다. 프론트엔드는 Zustand로 상태 관리하며, React Query로 API 통신한다.

**Tech Stack:** FastAPI, uvicorn, python-dotenv, sse-starlette | React 18, Vite, TypeScript, Tailwind CSS, Zustand, React Query, EventSource

---

## Prerequisites

- **Node.js 18+** 설치 필요 (프론트엔드 빌드용)
- **Python 3.9+** (기존 환경 유지)
- 기존 `.streamlit/secrets.toml`의 값을 `.env` 파일로 이전

---

## 프로젝트 구조 (최종)

```
DevLocal/
├── backend/
│   ├── main.py                 # FastAPI app (CORS, lifespan)
│   ├── config.py               # Settings (from .env)
│   ├── api/
│   │   ├── routes.py           # REST + SSE endpoints
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── session_manager.py  # Graph instance + state management
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   └── client.ts       # Fetch + SSE helpers
│       ├── store/
│       │   └── useAppStore.ts  # Zustand state
│       ├── hooks/
│       │   └── useSSE.ts       # SSE hook
│       ├── types/
│       │   └── index.ts        # TypeScript interfaces
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Header.tsx          # Logo + Step Indicator
│       │   │   └── Footer.tsx          # Navigation buttons
│       │   ├── DataSourceCard.tsx      # Sheet connection form
│       │   ├── KoReviewScreen.tsx      # HITL 1: KR review table
│       │   ├── TranslationProgress.tsx # Streaming logs + cancel
│       │   ├── FinalReviewScreen.tsx   # HITL 2: Translation review
│       │   ├── DoneScreen.tsx          # Metrics + downloads
│       │   └── shared/
│       │       ├── ReviewTable.tsx     # Reusable table with pagination
│       │       ├── ProgressBar.tsx     # Overall progress
│       │       ├── Badge.tsx           # Category/status badges
│       │       └── LogTerminal.tsx     # Monospace log viewer
│       └── styles/
│           └── index.css       # Tailwind directives + custom
├── agents/                     # 변경 없음 (st.secrets 제거만)
├── config/                     # 변경 없음
├── utils/                      # sheets.py만 st.secrets 제거
├── .env                        # secrets (gitignore)
└── start.sh                    # 개발 서버 동시 시작 스크립트
```

---

## API Design

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/connect` | Sheet URL로 연결, 시트 목록 반환 |
| `POST` | `/api/start` | 번역 파이프라인 시작 → 세션 ID 반환 |
| `GET` | `/api/stream/{session_id}` | SSE 스트림 (노드 업데이트, 인터럽트, 완료) |
| `GET` | `/api/state/{session_id}` | 현재 세션 상태 조회 |
| `POST` | `/api/approve-ko/{session_id}` | HITL 1 승인/거부 |
| `POST` | `/api/approve-final/{session_id}` | HITL 2 승인/거부 |
| `POST` | `/api/cancel/{session_id}` | 번역 취소 → KR review로 복귀 |
| `GET` | `/api/download/{session_id}/{type}` | CSV 다운로드 (backup, ko_report, translation_report, failed, logs) |

### SSE Event Types

```
event: node_update
data: {"node": "translator", "step": "translating", "logs": [...], "progress": {"value": 0.5, "label": "..."}}

event: ko_review_ready
data: {"results": [...], "count": 12}

event: final_review_ready
data: {"review_results": [...], "failed_rows": [...], "cost": {...}}

event: done
data: {"updates_count": 150, "success": true}

event: error
data: {"message": "..."}
```

---

## Task 1: Backend — De-Streamlit 핵심 파일 (st.secrets → os.environ)

**Files:**
- Modify: `agents/graph.py:1-10,33,71,197`
- Modify: `agents/nodes/translator.py:1-6,71,197`
- Modify: `agents/nodes/reviewer.py:1-6,74`
- Modify: `utils/sheets.py:1-10,39-41,49`
- Create: `backend/config.py`
- Create: `.env`

**Context:** 현재 4개 파일이 `import streamlit as st` + `st.secrets`에 의존합니다. 이를 `os.environ` / `python-dotenv`로 교체합니다.

**Step 1: `.env` 파일 생성**

```bash
# .env (gitignore에 추가)
XAI_API_KEY=your_xai_api_key_here
GCP_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"local-488014",...}
```

기존 `.streamlit/secrets.toml`에서 값을 복사합니다.

**Step 2: `backend/config.py` 생성**

```python
"""애플리케이션 설정 — 환경변수 기반"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# .env 로드 (프로젝트 루트 기준)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def get_xai_api_key() -> str:
    return os.environ.get("XAI_API_KEY", "")


def get_gcp_credentials() -> dict:
    raw = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "{}")
    return json.loads(raw)
```

**Step 3: `utils/sheets.py` 수정**

`import streamlit as st` 제거, `st.secrets` → `backend.config` 호출로 교체:

```python
# 변경 전
import streamlit as st
# ...
creds_info = st.secrets["gcp_service_account"]

# 변경 후
from backend.config import get_gcp_credentials
# ...
creds_info = get_gcp_credentials()
```

**Step 4: `agents/graph.py` 수정**

`import streamlit as st` 제거, `st.secrets` → `backend.config`:

```python
# 변경 전
import streamlit as st
# ko_review_node 내부:
api_key = st.secrets.get("XAI_API_KEY", "")

# 변경 후
from backend.config import get_xai_api_key
# ko_review_node 내부:
api_key = get_xai_api_key()
```

**Step 5: `agents/nodes/translator.py` 수정**

동일 패턴: `st.secrets.get("XAI_API_KEY", "")` → `get_xai_api_key()`

**Step 6: `agents/nodes/reviewer.py` 수정**

동일 패턴.

**Step 7: 검증**

```bash
python3 -c "from agents.graph import build_graph; print('OK')"
python3 -c "from utils.sheets import connect_to_sheet; print('OK')"
```

**Step 8: Commit**

```bash
git add .env.example backend/config.py agents/graph.py agents/nodes/translator.py agents/nodes/reviewer.py utils/sheets.py
git commit -m "refactor: remove streamlit dependency from backend modules"
```

---

## Task 2: Backend — FastAPI 앱 스켈레톤 + 세션 매니저

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/api/__init__.py`
- Create: `backend/api/schemas.py`
- Create: `backend/api/session_manager.py`
- Create: `backend/main.py`
- Create: `backend/requirements.txt`

**Step 1: `backend/requirements.txt` 생성**

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sse-starlette>=1.8.0
python-dotenv>=1.0.0
pydantic>=2.0.0
# 기존 dependencies (이미 설치됨)
langgraph>=0.6.0
litellm>=1.0.0
gspread>=5.0.0
google-auth>=2.0.0
pandas>=1.3.0
```

**Step 2: `backend/api/schemas.py` 생성**

```python
"""Pydantic 요청/응답 스키마"""

from typing import Optional
from pydantic import BaseModel


class ConnectRequest(BaseModel):
    sheet_url: str


class ConnectResponse(BaseModel):
    sheet_names: list
    bot_email: str


class StartRequest(BaseModel):
    sheet_url: str
    sheet_name: str
    mode: str = "A"
    target_languages: list = ["en", "ja"]
    row_limit: int = 0


class StartResponse(BaseModel):
    session_id: str


class ApprovalRequest(BaseModel):
    decision: str  # "approved" or "rejected"


class SessionStateResponse(BaseModel):
    session_id: str
    current_step: str
    ko_review_count: int = 0
    review_count: int = 0
    fail_count: int = 0
    cost_summary: Optional[dict] = None
    logs: list = []
```

**Step 3: `backend/api/session_manager.py` 생성**

```python
"""서버 사이드 세션 관리 — Graph 인스턴스 + 상태"""

import uuid
import asyncio
import threading
from typing import Optional
from collections import OrderedDict

from agents.graph import build_graph


class Session:
    """단일 번역 세션"""

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.graph, self.checkpointer = build_graph()
        self.thread_id = str(uuid.uuid4())
        self.config = {"configurable": {"thread_id": self.thread_id}}
        self.current_step = "idle"
        self.spreadsheet = None
        self.worksheet = None
        self.df = None
        self.graph_result = None
        self.logs: list = []
        self.initial_state: Optional[dict] = None
        self.ko_resume_value: str = "approved"
        # SSE event queue
        self.event_queue: asyncio.Queue = asyncio.Queue()
        # Lock for thread-safe operations
        self.lock = threading.Lock()


class SessionManager:
    """세션 풀 관리 (최대 10개, LRU 방식)"""

    MAX_SESSIONS = 10

    def __init__(self):
        self._sessions: OrderedDict[str, Session] = OrderedDict()

    def create(self) -> Session:
        session = Session()
        if len(self._sessions) >= self.MAX_SESSIONS:
            self._sessions.popitem(last=False)
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session:
            self._sessions.move_to_end(session_id)
        return session

    def delete(self, session_id: str):
        self._sessions.pop(session_id, None)


# Singleton
session_manager = SessionManager()
```

**Step 4: `backend/main.py` 생성**

```python
"""FastAPI 메인 앱"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (agents, config, utils 임포트용)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router

app = FastAPI(title="DevLocal API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
```

**Step 5: 검증**

```bash
pip3 install fastapi uvicorn sse-starlette python-dotenv
python3 -c "from backend.main import app; print('FastAPI app created')"
```

**Step 6: Commit**

```bash
git add backend/
git commit -m "feat: add FastAPI skeleton with session manager and schemas"
```

---

## Task 3: Backend — API 라우트 구현 (REST + SSE)

**Files:**
- Create: `backend/api/routes.py`

**Context:** 이 파일이 핵심입니다. `app.py`의 모든 로직(시트 연결, 파이프라인 시작, HITL 처리, 스트리밍, 다운로드)을 REST/SSE 엔드포인트로 변환합니다.

**Step 1: `backend/api/routes.py` 생성**

```python
"""API 라우트 — REST + SSE endpoints"""

import asyncio
import io
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

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
from backend.api.session_manager import Session, session_manager
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
        from utils.sheets import get_bot_email
        bot_email = get_bot_email()
        # 캐시용 세션에 spreadsheet 저장
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

def _run_initial_phase(session: Session):
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
                for r in session.df.to_dict("records")
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

def _run_translation_phase(session: Session, resume_value: str):
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
```

**Step 2: 검증**

```bash
python3 -c "from backend.api.routes import router; print(f'{len(router.routes)} routes')"
```

**Step 3: 서버 시작 테스트**

```bash
cd /Users/annmini/Desktop/claude/DevLocal
python3 -m uvicorn backend.main:app --reload --port 8000
# 다른 터미널에서:
curl http://localhost:8000/api/config
```

**Step 4: Commit**

```bash
git add backend/api/routes.py
git commit -m "feat: implement all API routes (REST + SSE) for FastAPI backend"
```

---

## Task 4: Frontend — React + Vite + Tailwind 초기 설정

**Files:**
- Create: `frontend/` 디렉토리 전체 (scaffold)

**Step 1: Vite + React + TypeScript 프로젝트 생성**

```bash
cd /Users/annmini/Desktop/claude/DevLocal
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

**Step 2: Tailwind CSS 설치 및 설정**

```bash
npm install -D tailwindcss @tailwindcss/vite
```

`frontend/src/styles/index.css`:
```css
@import "tailwindcss";
```

`frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

**Step 3: 추가 패키지 설치**

```bash
npm install zustand @tanstack/react-query
```

**Step 4: TypeScript 타입 정의**

`frontend/src/types/index.ts`:
```typescript
export type Step = 'idle' | 'loading' | 'ko_review' | 'translating' | 'final_review' | 'done'

export interface KoReviewItem {
  key: string
  original: string
  revised: string
  changes: string
}

export interface TranslationReviewItem {
  Key: string
  언어: string
  '기존 번역': string
  '새 번역': string
  '변경 사유/내역': string
}

export interface FailedRow {
  key: string
  lang: string
  reason: string
}

export interface CostSummary {
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
}

export interface SSEEvent {
  event: string
  data: any
}

export interface SessionState {
  sessionId: string | null
  currentStep: Step
  sheetUrl: string
  sheetNames: string[]
  selectedSheet: string
  mode: 'A' | 'B'
  targetLanguages: string[]
  rowLimit: number
  connected: boolean
  koReviewResults: KoReviewItem[]
  koReportData: any[]
  translationReportData: TranslationReviewItem[]
  failedRows: FailedRow[]
  costSummary: CostSummary | null
  logs: string[]
  translationsApplied: boolean
}
```

**Step 5: Zustand Store**

`frontend/src/store/useAppStore.ts`:
```typescript
import { create } from 'zustand'
import type { Step, KoReviewItem, TranslationReviewItem, FailedRow, CostSummary } from '../types'

interface AppState {
  // Session
  sessionId: string | null
  currentStep: Step
  // Connection
  sheetUrl: string
  sheetNames: string[]
  selectedSheet: string
  mode: 'A' | 'B'
  targetLanguages: string[]
  rowLimit: number
  connected: boolean
  botEmail: string
  // Data
  koReviewResults: KoReviewItem[]
  koReportData: any[]
  translationReportData: TranslationReviewItem[]
  failedRows: FailedRow[]
  costSummary: CostSummary | null
  logs: string[]
  translationsApplied: boolean
  // Actions
  setSessionId: (id: string | null) => void
  setCurrentStep: (step: Step) => void
  setSheetUrl: (url: string) => void
  setSheetNames: (names: string[]) => void
  setSelectedSheet: (name: string) => void
  setMode: (mode: 'A' | 'B') => void
  setTargetLanguages: (langs: string[]) => void
  setRowLimit: (limit: number) => void
  setConnected: (val: boolean) => void
  setBotEmail: (email: string) => void
  setKoReviewResults: (results: KoReviewItem[]) => void
  setKoReportData: (data: any[]) => void
  setTranslationReportData: (data: TranslationReviewItem[]) => void
  setFailedRows: (rows: FailedRow[]) => void
  setCostSummary: (summary: CostSummary | null) => void
  appendLog: (log: string) => void
  setLogs: (logs: string[]) => void
  setTranslationsApplied: (val: boolean) => void
  reset: () => void
}

const initialState = {
  sessionId: null,
  currentStep: 'idle' as Step,
  sheetUrl: '',
  sheetNames: [],
  selectedSheet: '',
  mode: 'A' as const,
  targetLanguages: ['en', 'ja'],
  rowLimit: 0,
  connected: false,
  botEmail: '',
  koReviewResults: [],
  koReportData: [],
  translationReportData: [],
  failedRows: [],
  costSummary: null,
  logs: [],
  translationsApplied: false,
}

export const useAppStore = create<AppState>((set) => ({
  ...initialState,
  setSessionId: (id) => set({ sessionId: id }),
  setCurrentStep: (step) => set({ currentStep: step }),
  setSheetUrl: (url) => set({ sheetUrl: url }),
  setSheetNames: (names) => set({ sheetNames: names }),
  setSelectedSheet: (name) => set({ selectedSheet: name }),
  setMode: (mode) => set({ mode }),
  setTargetLanguages: (langs) => set({ targetLanguages: langs }),
  setRowLimit: (limit) => set({ rowLimit: limit }),
  setConnected: (val) => set({ connected: val }),
  setBotEmail: (email) => set({ botEmail: email }),
  setKoReviewResults: (results) => set({ koReviewResults: results }),
  setKoReportData: (data) => set({ koReportData: data }),
  setTranslationReportData: (data) => set({ translationReportData: data }),
  setFailedRows: (rows) => set({ failedRows: rows }),
  setCostSummary: (summary) => set({ costSummary: summary }),
  appendLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
  setLogs: (logs) => set({ logs }),
  setTranslationsApplied: (val) => set({ translationsApplied: val }),
  reset: () => set(initialState),
}))
```

**Step 6: API Client**

`frontend/src/api/client.ts`:
```typescript
const BASE_URL = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  connect: (sheetUrl: string) =>
    request<{ sheet_names: string[]; bot_email: string }>('/connect', {
      method: 'POST',
      body: JSON.stringify({ sheet_url: sheetUrl }),
    }),

  start: (params: {
    sheet_url: string; sheet_name: string; mode: string;
    target_languages: string[]; row_limit: number
  }) =>
    request<{ session_id: string }>('/start', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  approveKo: (sessionId: string, decision: string) =>
    request<{ status: string }>(`/approve-ko/${sessionId}`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),

  approveFinal: (sessionId: string, decision: string) =>
    request<any>(`/approve-final/${sessionId}`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),

  cancel: (sessionId: string) =>
    request<{ status: string }>(`/cancel/${sessionId}`, {
      method: 'POST',
    }),

  getState: (sessionId: string) =>
    request<any>(`/state/${sessionId}`),

  getConfig: () => request<any>('/config'),

  saveConfig: (data: Record<string, string>) =>
    request<any>('/config', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  getDownloadUrl: (sessionId: string, fileType: string) =>
    `${BASE_URL}/download/${sessionId}/${fileType}`,

  getStreamUrl: (sessionId: string) =>
    `${BASE_URL}/stream/${sessionId}`,
}
```

**Step 7: SSE Hook**

`frontend/src/hooks/useSSE.ts`:
```typescript
import { useEffect, useRef, useCallback } from 'react'
import { useAppStore } from '../store/useAppStore'
import { api } from '../api/client'

export function useSSE(sessionId: string | null) {
  const sourceRef = useRef<EventSource | null>(null)
  const store = useAppStore()

  const close = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close()
      sourceRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!sessionId) return

    const es = new EventSource(api.getStreamUrl(sessionId))
    sourceRef.current = es

    es.addEventListener('node_update', (e) => {
      const data = JSON.parse(e.data)
      if (data.logs) store.setLogs(data.logs)
    })

    es.addEventListener('ko_review_ready', (e) => {
      const data = JSON.parse(e.data)
      store.setKoReviewResults(data.results || [])
      store.setKoReportData(data.report || [])
      store.setCurrentStep('ko_review')
    })

    es.addEventListener('final_review_ready', (e) => {
      const data = JSON.parse(e.data)
      store.setTranslationReportData(data.report || [])
      store.setFailedRows(data.failed_rows || [])
      if (data.cost) store.setCostSummary(data.cost)
      store.setCurrentStep('final_review')
    })

    es.addEventListener('done', () => {
      store.setCurrentStep('done')
      close()
    })

    es.addEventListener('error', (e) => {
      console.error('SSE error', e)
      close()
    })

    return close
  }, [sessionId, close])

  return { close }
}
```

**Step 8: 검증**

```bash
cd /Users/annmini/Desktop/claude/DevLocal/frontend
npm run dev
# http://localhost:5173 접속 확인
```

**Step 9: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React + Vite + Tailwind frontend with Zustand store"
```

---

## Task 5: Frontend — Header + Step Indicator (Stitch 디자인)

**Files:**
- Create: `frontend/src/components/layout/Header.tsx`
- Create: `frontend/src/components/layout/Footer.tsx`

**Context:** Stitch 스크린샷의 5단계 번호 인디케이터를 React로 구현합니다. 기존 Material Icons 대신 번호(1-5)를 사용하고, 체크마크 아이콘은 완료 단계에서만 표시합니다.

**Step 1: `Header.tsx` 구현**

```tsx
import { useAppStore } from '../../store/useAppStore'
import type { Step } from '../../types'

const STEPS = [
  { num: 1, label: 'Data Load' },
  { num: 2, label: 'KR Review' },
  { num: 3, label: 'Translation' },
  { num: 4, label: 'Multi-Review' },
  { num: 5, label: 'Complete' },
]

const STEP_MAP: Record<Step, number[]> = {
  idle:         [0, 0, 0, 0, 0],
  loading:      [1, 0, 0, 0, 0],
  ko_review:    [2, 1, 0, 0, 0],
  translating:  [2, 2, 1, 0, 0],
  final_review: [2, 2, 2, 1, 0],
  done:         [2, 2, 2, 2, 2],
}

// 0=pending, 1=active, 2=done

export default function Header() {
  const currentStep = useAppStore((s) => s.currentStep)
  const states = STEP_MAP[currentStep] || [0, 0, 0, 0, 0]

  return (
    <header className="bg-white border-b border-slate-200 shadow-sm rounded-xl mb-6 px-6 py-3 flex items-center justify-between animate-fade-in">
      <div className="flex items-center gap-2 font-bold text-slate-800 text-base whitespace-nowrap">
        <span className="text-xl">🌐</span>
        Game Localization Tool
      </div>
      <div className="flex items-center gap-0 flex-1 justify-center">
        {STEPS.map((step, i) => {
          const state = states[i]
          return (
            <div key={step.num} className="flex items-center">
              {i > 0 && (
                <div className={`w-10 h-0.5 mx-1.5 rounded-full transition-colors ${
                  states[i - 1] === 2 && state === 2 ? 'bg-emerald-500' :
                  states[i - 1] === 2 && state === 1 ? 'bg-gradient-to-r from-emerald-500 to-sky-500' :
                  'bg-slate-200'
                }`} />
              )}
              <div className="flex flex-col items-center gap-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                  state === 2 ? 'bg-emerald-100 text-emerald-600' :
                  state === 1 ? 'bg-sky-500 text-white animate-pulse-slow' :
                  'bg-slate-100 text-slate-400'
                }`}>
                  {state === 2 ? '✓' : step.num}
                </div>
                <span className={`text-xs font-semibold ${
                  state === 2 ? 'text-emerald-600' :
                  state === 1 ? 'text-sky-500 font-bold' :
                  'text-slate-400'
                }`}>
                  {step.label}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </header>
  )
}
```

**Step 2: `Footer.tsx` 구현**

```tsx
interface FooterProps {
  onBack?: () => void
  onNext?: () => void
  backLabel?: string
  nextLabel?: string
  backDisabled?: boolean
  nextDisabled?: boolean
  nextPrimary?: boolean
  children?: React.ReactNode
}

export default function Footer({
  onBack, onNext, backLabel = 'Back', nextLabel = 'Next Step →',
  backDisabled, nextDisabled, nextPrimary = true, children,
}: FooterProps) {
  return (
    <footer className="sticky bottom-0 bg-white border-t border-slate-200 px-6 py-3 mt-8 shadow-[0_-2px_10px_rgba(0,0,0,0.03)] z-50">
      <div className="flex justify-between items-center">
        <div>
          {onBack && (
            <button
              onClick={onBack}
              disabled={backDisabled}
              className="px-5 py-2.5 border border-slate-300 rounded-lg font-semibold text-sm text-slate-700 hover:border-sky-500 hover:text-sky-500 hover:bg-sky-50 transition disabled:opacity-40 disabled:cursor-not-allowed"
            >
              ← {backLabel}
            </button>
          )}
        </div>
        <div className="flex items-center gap-3">
          {children}
          {onNext && (
            <button
              onClick={onNext}
              disabled={nextDisabled}
              className={`px-5 py-2.5 rounded-lg font-bold text-sm transition shadow-sm hover:-translate-y-px disabled:opacity-40 disabled:cursor-not-allowed ${
                nextPrimary
                  ? 'bg-sky-500 text-white hover:bg-sky-600'
                  : 'border border-slate-300 text-slate-700 hover:border-sky-500'
              }`}
            >
              {nextLabel}
            </button>
          )}
        </div>
      </div>
    </footer>
  )
}
```

**Step 3: Tailwind 커스텀 애니메이션**

`frontend/src/styles/index.css`에 추가:
```css
@import "tailwindcss";

@layer utilities {
  .animate-fade-in {
    animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .animate-pulse-slow {
    animation: pulse-primary 2s ease-in-out infinite;
  }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse-primary {
  0%, 100% { box-shadow: 0 0 0 0 rgba(14,165,233,0.35); }
  50% { box-shadow: 0 0 0 8px rgba(14,165,233,0); }
}
```

**Step 4: Commit**

```bash
git add frontend/src/components/layout/ frontend/src/styles/
git commit -m "feat: add Header with 5-step indicator and Footer navigation"
```

---

## Task 6: Frontend — Shared Components (Badge, Table, ProgressBar, LogTerminal)

**Files:**
- Create: `frontend/src/components/shared/Badge.tsx`
- Create: `frontend/src/components/shared/ReviewTable.tsx`
- Create: `frontend/src/components/shared/ProgressBar.tsx`
- Create: `frontend/src/components/shared/LogTerminal.tsx`

**Context:** Stitch 디자인의 핵심 재사용 컴포넌트. ReviewTable은 페이지네이션 + 행별 액션을 포함합니다.

**Step 1: `Badge.tsx`**

```tsx
type BadgeVariant = 'typo' | 'grammar' | 'spacing' | 'style' | 'success' | 'fail' | 'pending' | 'info'

const VARIANTS: Record<BadgeVariant, string> = {
  typo: 'bg-amber-100 text-amber-700',
  grammar: 'bg-purple-100 text-purple-700',
  spacing: 'bg-blue-100 text-blue-700',
  style: 'bg-teal-100 text-teal-700',
  success: 'bg-emerald-100 text-emerald-600',
  fail: 'bg-red-100 text-red-600',
  pending: 'bg-slate-100 text-slate-500',
  info: 'bg-sky-100 text-sky-600',
}

interface BadgeProps {
  variant: BadgeVariant
  children: React.ReactNode
}

export default function Badge({ variant, children }: BadgeProps) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold uppercase tracking-wide ${VARIANTS[variant]}`}>
      {children}
    </span>
  )
}
```

**Step 2: `ProgressBar.tsx`**

```tsx
interface ProgressBarProps {
  successCount: number
  failCount: number
  pendingCount?: number
  percentage?: number
}

export default function ProgressBar({ successCount, failCount, pendingCount = 0, percentage }: ProgressBarProps) {
  const total = successCount + failCount + pendingCount
  const pct = percentage ?? (total > 0 ? Math.round((successCount / total) * 100) : 0)
  const successPct = total > 0 ? (successCount / total) * 100 : 0
  const failPct = total > 0 ? (failCount / total) * 100 : 0

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm animate-fade-in">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-slate-700">Overall Progress</h3>
        <span className="text-2xl font-bold text-sky-500">{pct}%</span>
      </div>
      <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden flex mb-3">
        <div className="h-full bg-emerald-500 transition-all" style={{ width: `${successPct}%` }} />
        <div className="h-full bg-red-500 transition-all" style={{ width: `${failPct}%` }} />
      </div>
      <div className="flex gap-6 text-xs font-semibold">
        <span className="text-emerald-600">{successCount.toLocaleString()} DONE</span>
        {pendingCount > 0 && <span className="text-amber-500">{pendingCount.toLocaleString()} PENDING</span>}
        <span className="text-red-500">{failCount} ERRORS</span>
      </div>
    </div>
  )
}
```

**Step 3: `ReviewTable.tsx`**

```tsx
import { useState } from 'react'

interface Column<T> {
  key: string
  header: string
  render?: (row: T, index: number) => React.ReactNode
  className?: string
}

interface ReviewTableProps<T> {
  data: T[]
  columns: Column<T>[]
  pageSize?: number
  actions?: (row: T, index: number) => React.ReactNode
  onApproveAll?: (pageItems: T[]) => void
}

export default function ReviewTable<T extends Record<string, any>>({
  data, columns, pageSize = 10, actions, onApproveAll,
}: ReviewTableProps<T>) {
  const [page, setPage] = useState(0)
  const totalPages = Math.ceil(data.length / pageSize)
  const pageData = data.slice(page * pageSize, (page + 1) * pageSize)

  return (
    <div>
      {/* Pagination header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-500">
          Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, data.length)} of {data.length}
        </span>
        <div className="flex items-center gap-2">
          {onApproveAll && (
            <button
              onClick={() => onApproveAll(pageData)}
              className="px-3 py-1.5 bg-sky-500 text-white text-xs font-bold rounded-lg hover:bg-sky-600 transition"
            >
              APPROVE ALL ON PAGE
            </button>
          )}
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold disabled:opacity-40 hover:bg-slate-50 transition"
          >
            Previous
          </button>
          <span className="text-xs text-slate-500">Page {page + 1} of {totalPages}</span>
          <button
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold disabled:opacity-40 hover:bg-slate-50 transition"
          >
            Next
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-slate-200 rounded-xl">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50">
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">#</th>
              {columns.map((col) => (
                <th key={col.key} className={`px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide ${col.className || ''}`}>
                  {col.header}
                </th>
              ))}
              {actions && (
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wide">Action</th>
              )}
            </tr>
          </thead>
          <tbody>
            {pageData.map((row, idx) => {
              const globalIdx = page * pageSize + idx
              return (
                <tr key={globalIdx} className="border-t border-slate-100 hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 text-slate-400 font-medium text-center w-10">{globalIdx + 1}</td>
                  {columns.map((col) => (
                    <td key={col.key} className={`px-4 py-3 text-slate-700 ${col.className || ''}`}>
                      {col.render ? col.render(row, globalIdx) : row[col.key]}
                    </td>
                  ))}
                  {actions && (
                    <td className="px-4 py-3 text-center">
                      {actions(row, globalIdx)}
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

**Step 4: `LogTerminal.tsx`**

```tsx
import { useEffect, useRef } from 'react'

interface LogTerminalProps {
  logs: string[]
  maxHeight?: string
}

export default function LogTerminal({ logs, maxHeight = '180px' }: LogTerminalProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [logs])

  if (!logs.length) return null

  const getLogClass = (log: string) => {
    if (log.includes('완료') || log.includes('성공')) return 'text-emerald-600'
    if (log.includes('오류') || log.includes('실패')) return 'text-red-500'
    if (log.includes('경고')) return 'text-amber-500'
    if (log.startsWith('[Node ')) return 'text-slate-800 font-bold border-t border-slate-200 mt-1 pt-1'
    return 'text-slate-500'
  }

  return (
    <div
      ref={ref}
      className="bg-slate-50 border border-slate-200 rounded-lg p-3 font-mono text-xs leading-relaxed overflow-y-auto"
      style={{ maxHeight }}
    >
      {logs.map((log, i) => (
        <div key={i} className={`py-0.5 ${getLogClass(log)}`}>{log}</div>
      ))}
    </div>
  )
}
```

**Step 5: Commit**

```bash
git add frontend/src/components/shared/
git commit -m "feat: add shared UI components (Badge, ReviewTable, ProgressBar, LogTerminal)"
```

---

## Task 7: Frontend — DataSourceCard (Stitch 디자인 — idle 화면)

**Files:**
- Create: `frontend/src/components/DataSourceCard.tsx`

**Context:** Stitch 스크린샷의 "Data Source Configuration" 카드를 구현합니다. Connected 뱃지, Google Sheet URL, Sheet Tab 드롭다운, Row Range 입력, Start 버튼 포함.

**Step 1: `DataSourceCard.tsx` 구현**

Stitch 디자인의 카드 형태:
- Connected/Not Connected 뱃지 (상단 우측)
- Google Sheet URL 입력 (고정 URL 시 읽기 전용 표시)
- Sheet Tab 드롭다운 + Mode 라디오
- Target Languages 멀티셀렉트
- Advanced Settings (접기/펼치기)
- Start Translation 버튼 (하단)

전체 코드는 Stitch 디자인에 맞춰 Tailwind CSS 클래스로 구현합니다. 개별 입력 컴포넌트는 Tailwind의 `focus:ring-2 focus:ring-sky-300` 등으로 일관된 포커스 스타일을 적용합니다.

**Step 2: Commit**

```bash
git add frontend/src/components/DataSourceCard.tsx
git commit -m "feat: add DataSourceCard with Stitch design"
```

---

## Task 8: Frontend — KoReviewScreen (HITL 1 — Stitch 디자인)

**Files:**
- Create: `frontend/src/components/KoReviewScreen.tsx`

**Context:** Stitch 스크린샷의 "Source Language (Korean) Review" 화면. 핵심 기능:
- "AI has detected potential issues in N rows" 서브타이틀
- 카테고리 뱃지 (TYPO, GRAMMAR, SPACING, STYLE) — `changes` 필드에서 추출
- AI Comment 칼럼 (View Note 버튼 → 팝오버/모달)
- 행별 Accept(✓) / Reject(✕) 버튼
- 페이지네이션 (Showing 1-4 of 12)
- Footer: Back | Save Draft | Next Step →
- KR Diff 리포트 CSV 다운로드

**카테고리 추출 로직:** `changes` 문자열에서 키워드 매칭으로 분류:
- "맞춤법" → TYPO
- "문법" → GRAMMAR
- "띄어쓰기" → SPACING
- 나머지 → STYLE

**행별 Accept/Reject:**
- Accept: 해당 행의 수정 제안을 적용 (로컬 상태에서 관리)
- Reject: 해당 행의 수정 제안을 무시 (원본 유지)
- 최종적으로 "Next Step" 클릭 시 승인 결과를 서버에 전송

**Step 1: `KoReviewScreen.tsx` 구현**

ReviewTable 재사용, columns 정의:
- Key
- Original (Korean) — 배경 연한 빨강
- AI Suggested Fix — 배경 연한 초록 + 카테고리 뱃지
- AI Comment (View Note)
- Action (✓ / ✕)

**Step 2: Commit**

```bash
git add frontend/src/components/KoReviewScreen.tsx
git commit -m "feat: add KoReviewScreen with per-row actions and category badges"
```

---

## Task 9: Frontend — TranslationProgress (스트리밍 진행 화면)

**Files:**
- Create: `frontend/src/components/TranslationProgress.tsx`

**Context:** 번역 진행 중 화면. SSE 이벤트를 수신하며 실시간 로그와 프로그레스를 표시합니다.

**구성:**
- 스피너 + "AI 번역 진행중..." 라벨
- 프로그레스바 (indeterminate 또는 node 진행률)
- LogTerminal (실시간 업데이트)
- "번역 취소" 버튼 (ko_review로 복귀)

**Step 1: 구현** — useSSE 훅과 연동

**Step 2: Commit**

```bash
git add frontend/src/components/TranslationProgress.tsx
git commit -m "feat: add TranslationProgress with SSE streaming and cancel"
```

---

## Task 10: Frontend — FinalReviewScreen (HITL 2 — Stitch 디자인)

**Files:**
- Create: `frontend/src/components/FinalReviewScreen.tsx`

**Context:** Stitch 스크린샷의 "Translation Review" 화면. 핵심 기능:
- Overall Progress 카드 (ProgressBar 재사용)
- 언어 필터 드롭다운
- Review Drafts 카운트 뱃지
- 페이지네이션 + "APPROVE ALL ON PAGE"
- 테이블: KEY ID, SOURCE (KR), PREVIOUS TRANSLATION, NEW TRANSLATION (DRAFT), ACTION
- 단어 단위 diff 하이라이팅 (변경 단어에 초록 배경)
- 행별 인라인 편집 (텍스트 입력 + Save)
- 검수실패 행 별도 표시
- Footer: ← Back | Confirm & Next Step →
- CSV 다운로드

**단어 diff 구현:** 두 문자열을 단어 단위로 비교하여, 변경된 단어에 `<span class="bg-emerald-100 rounded px-0.5">` 적용. JavaScript `diff-words` 또는 간단한 커스텀 diff 함수 사용.

**인라인 편집:** 행을 클릭하면 NEW TRANSLATION 셀이 `<input>` 으로 전환. Save 버튼으로 로컬 상태 업데이트 (실제 서버 반영은 최종 승인 시).

**Step 1: 단어 diff 유틸리티 함수**

`frontend/src/utils/wordDiff.ts`:
```typescript
export function diffWords(oldStr: string, newStr: string): { text: string; added: boolean; removed: boolean }[] {
  // 간단한 단어 단위 diff
  const oldWords = oldStr.split(/(\s+)/)
  const newWords = newStr.split(/(\s+)/)
  // LCS 기반 또는 간단한 순차 비교로 구현
  // ...
}
```

**Step 2: FinalReviewScreen 구현**

**Step 3: Commit**

```bash
git add frontend/src/components/FinalReviewScreen.tsx frontend/src/utils/
git commit -m "feat: add FinalReviewScreen with word-level diff and inline editing"
```

---

## Task 11: Frontend — DoneScreen (완료 화면)

**Files:**
- Create: `frontend/src/components/DoneScreen.tsx`

**Context:** 완료 화면. 메트릭 그리드 + 다운로드 버튼 + "새 작업 시작" 버튼.

**Step 1: 구현**

```tsx
// 메트릭: 번역 건수, 실패, Input 토큰, Output 토큰, 예상 비용
// 다운로드: 원본 백업, 번역 리포트, 검수 실패, 전체 로그
// "새 작업 시작" → store.reset()
```

**Step 2: Commit**

---

## Task 12: Frontend — App.tsx 라우팅 + 통합

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

**Context:** 모든 컴포넌트를 연결하여 `currentStep`에 따른 화면 전환을 구현합니다.

**Step 1: `App.tsx` 구현**

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAppStore } from './store/useAppStore'
import { useSSE } from './hooks/useSSE'
import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import DataSourceCard from './components/DataSourceCard'
import KoReviewScreen from './components/KoReviewScreen'
import TranslationProgress from './components/TranslationProgress'
import FinalReviewScreen from './components/FinalReviewScreen'
import DoneScreen from './components/DoneScreen'
import LogTerminal from './components/shared/LogTerminal'

const queryClient = new QueryClient()

function AppContent() {
  const { currentStep, sessionId, logs } = useAppStore()
  useSSE(sessionId)

  return (
    <div className="min-h-screen bg-slate-50 font-[Inter]">
      <div className="max-w-6xl mx-auto px-4 py-6">
        <Header />
        {currentStep === 'idle' && <DataSourceCard />}
        {currentStep === 'loading' && <TranslationProgress />}
        {currentStep === 'ko_review' && <KoReviewScreen />}
        {currentStep === 'translating' && <TranslationProgress />}
        {currentStep === 'final_review' && <FinalReviewScreen />}
        {currentStep === 'done' && <DoneScreen />}
        {logs.length > 0 && !['idle', 'done', 'translating', 'loading'].includes(currentStep) && (
          <div className="mt-6">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Execution Log</h4>
            <LogTerminal logs={logs} />
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}
```

**Step 2: `main.tsx` 수정**

```tsx
import './styles/index.css'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

**Step 3: Commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat: integrate all screens in App.tsx with step-based routing"
```

---

## Task 13: 개발 서버 스크립트 + .gitignore 업데이트

**Files:**
- Create: `start.sh`
- Modify: `.gitignore`

**Step 1: `start.sh`**

```bash
#!/bin/bash
# DevLocal 개발 서버 (FastAPI + Vite 동시 실행)

# Backend
echo "Starting FastAPI backend..."
cd "$(dirname "$0")"
python3 -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Frontend
echo "Starting Vite dev server..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
```

**Step 2: `.gitignore` 업데이트**

```
# 기존 항목 유지 +
.env
frontend/node_modules/
frontend/dist/
```

**Step 3: Commit**

```bash
chmod +x start.sh
git add start.sh .gitignore
git commit -m "chore: add dev server script and update gitignore"
```

---

## Task 14: End-to-End 통합 테스트

**Step 1: 백엔드 서버 시작**

```bash
cd /Users/annmini/Desktop/claude/DevLocal
python3 -m uvicorn backend.main:app --reload --port 8000
```

**Step 2: 프론트엔드 서버 시작**

```bash
cd /Users/annmini/Desktop/claude/DevLocal/frontend
npm run dev
```

**Step 3: 테스트 시나리오**

1. `http://localhost:5173` 접속
2. idle 화면: Data Source Configuration 카드 → Sheet URL 입력 → Connect
3. Sheet Tab 선택 → Start Translation 클릭
4. loading → ko_review 전환: KR Review 테이블 표시, 카테고리 뱃지, 페이지네이션
5. 행별 Accept/Reject 테스트
6. Next Step → translating: 실시간 로그 스트리밍
7. final_review: Overall Progress, 언어 필터, 단어 diff, 인라인 편집
8. Confirm → done: 메트릭, 다운로드 버튼
9. "새 작업 시작" → idle 복귀

**Step 4: 확인 사항**

- [ ] SSE 스트림이 노드 업데이트를 실시간 전달하는가
- [ ] HITL 1 (ko_review) 승인/거부가 정상 작동하는가
- [ ] HITL 2 (final_review) 승인 시 시트에 실제 업데이트되는가
- [ ] HITL 2 거부 시 Tool_Status가 원복되는가
- [ ] 번역 취소 시 ko_review로 정상 복귀하는가
- [ ] CSV 다운로드 5종이 모두 작동하는가
- [ ] 프로그레스바, 뱃지, 페이지네이션이 Stitch 디자인과 일치하는가

---

## 기존 파일 처리

| 파일 | 처리 |
|------|------|
| `app.py` | 보존 (레거시 Streamlit 앱, 원하면 삭제) |
| `utils/ui_components.py` | 보존 (레거시, 원하면 삭제) |
| `agents/graph.py` | Task 1에서 `st.secrets` 제거 |
| `agents/nodes/translator.py` | Task 1에서 `st.secrets` 제거 |
| `agents/nodes/reviewer.py` | Task 1에서 `st.secrets` 제거 |
| `utils/sheets.py` | Task 1에서 `st.secrets` 제거 |
| `agents/state.py` | 변경 없음 |
| `agents/prompts.py` | 변경 없음 |
| `config/constants.py` | 변경 없음 |
| `config/glossary.py` | 변경 없음 |
| `utils/validation.py` | 변경 없음 |
| `utils/diff_report.py` | 변경 없음 |
| `utils/cost_tracker.py` | 변경 없음 |
