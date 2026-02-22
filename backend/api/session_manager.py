"""서버 사이드 세션 관리 — Graph 인스턴스 + 상태"""

import logging
import uuid
import asyncio
import threading
from typing import Optional
from collections import OrderedDict

from agents.graph import build_graph

logger = logging.getLogger("devlocal.session")


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
        # Cancel 복구용 ko_review 캐시 (초기 phase 완료 후 저장)
        self.cached_ko_review_results: list = []
        self.cached_ko_tokens: tuple = (0, 0)
        # SSE event queue (lazy init — async 컨텍스트에서 생성)
        self.event_queue: Optional[asyncio.Queue] = None
        # Lock for thread-safe operations
        self.lock = threading.Lock()
        # Event loop reference (set when SSE stream starts)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        # SSE generation counter — 이전 SSE 연결 무효화용
        self._sse_generation: int = 0


class SessionManager:
    """세션 풀 관리 (최대 10개, LRU 방식)"""

    MAX_SESSIONS = 10

    def __init__(self):
        self._sessions: OrderedDict[str, Session] = OrderedDict()

    def create(self) -> Session:
        session = Session()
        if len(self._sessions) >= self.MAX_SESSIONS:
            evicted_id, _ = self._sessions.popitem(last=False)
            logger.info("Session evicted (LRU): %s", evicted_id)
        self._sessions[session.id] = session
        logger.info("Session created: %s (total: %d)", session.id, len(self._sessions))
        return session

    def get(self, session_id: str) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session:
            self._sessions.move_to_end(session_id)
        return session

    def delete(self, session_id: str):
        removed = self._sessions.pop(session_id, None)
        if removed:
            logger.info("Session deleted: %s", session_id)


# Singleton
session_manager = SessionManager()
