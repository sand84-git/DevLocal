"""SSE 드립피드 유틸 — 150ms 간격 항목별 전송으로 부드러운 테이블 채워짐 효과"""

import time


def drip_feed_emit(
    emitter,
    event_name: str,
    items: list,
    progress_base: int,
    total: int,
    lang: str = "",
    delay: float = 0.15,
) -> None:
    """
    items를 한 건씩 delay 간격으로 SSE emit.

    Args:
        emitter: SSE emit callback (event_name, data_dict)
        event_name: SSE 이벤트명 ("ko_review_chunk", "translation_chunk", "review_chunk")
        items: 전송할 결과 리스트
        progress_base: 이 배치 시작 시점의 누적 완료 수
        total: 전체 예상 항목 수
        lang: 언어 코드 (translation_chunk용, 선택)
        delay: 항목 간 지연 시간 (초, 기본 0.15)
    """
    for i, item in enumerate(items):
        done = progress_base + i + 1

        data = {
            "chunk_results": [item],
            "progress": {
                "done": done,
                "total": total,
            },
        }

        if lang:
            data["lang"] = lang

        emitter(event_name, data)

        # 마지막 항목에는 딜레이 불필요
        if i < len(items) - 1:
            time.sleep(delay)
