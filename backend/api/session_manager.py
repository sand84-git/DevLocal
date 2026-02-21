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
        # Event loop reference (set when SSE stream starts)
        self._loop: Optional[asyncio.AbstractEventLoop] = None


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
