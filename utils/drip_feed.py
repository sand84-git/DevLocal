"""SSE drip-feed 유틸리티 — LLM 배치 응답을 1행씩 ~150ms 간격으로 프론트엔드에 전송."""

import time


def drip_feed_emit(emitter, event_name, items, progress_base, total, lang="", delay=0.15):
    """items를 1건씩 SSE emitter로 전송하며 각 호출 사이 delay초 대기.

    노드는 ThreadPoolExecutor 안에서 실행되므로 time.sleep()은
    asyncio 이벤트 루프를 블로킹하지 않음.

    Args:
        emitter: SSE emit 콜백 (event_name, data_dict)
        event_name: SSE 이벤트 이름 (e.g. "translation_chunk")
        items: 전송할 결과 리스트
        progress_base: 이 배치 시작 시점의 누적 완료 수
        total: 전체 예상 항목 수
        lang: 언어 코드 (옵션, translation_chunk에서 사용)
        delay: 항목 간 대기 시간(초), 기본 0.15
    """
    for i, item in enumerate(items):
        progress = {
            "done": progress_base + i + 1,
            "total": total,
        }
        if lang:
            progress["lang"] = lang
        emitter(event_name, {
            "chunk_results": [item],
            "progress": progress,
        })
        if i < len(items) - 1:
            time.sleep(delay)
