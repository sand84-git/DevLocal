"""Node 5: 시트 업데이트 (유틸리티) — HITL 2 승인 후 Batch Update 실행"""

from agents.state import LocalizationState
from config.constants import REQUIRED_COLUMNS, SUPPORTED_LANGUAGES, Status, TOOL_STATUS_COLUMN


def writer_node(state: LocalizationState) -> dict:
    """
    최종 승인된 번역 데이터를 시트에 일괄 업데이트할 업데이트 목록 생성.
    실제 시트 쓰기는 app.py에서 batch_update_sheet()를 호출하여 수행.
    """
    review_results = state.get("review_results", [])
    failed_rows = state.get("failed_rows", [])
    original_data = state.get("original_data", [])
    logs = list(state.get("logs", []))

    # 원본 데이터의 Key → row_index 매핑
    key_to_index = {}
    for idx, row in enumerate(original_data):
        key = row.get(REQUIRED_COLUMNS["key"], "")
        key_to_index[key] = idx

    # 업데이트 목록 생성
    updates = []

    # 성공한 번역 결과 반영
    for result in review_results:
        key = result["key"]
        lang = result["lang"]
        translated = result["translated"]
        row_idx = key_to_index.get(key)

        if row_idx is None:
            continue

        lang_col = SUPPORTED_LANGUAGES.get(lang, "")
        if not lang_col:
            continue

        updates.append({
            "row_index": row_idx,
            "column_name": lang_col,
            "value": translated,
            "change_type": "translation",
        })

        # Tool_Status를 최종완료로 업데이트
        updates.append({
            "row_index": row_idx,
            "column_name": TOOL_STATUS_COLUMN,
            "value": Status.COMPLETED,
            "change_type": "completed",
        })

    # 검수실패 행 마킹
    failed_keys = set()
    for fail in failed_rows:
        key = fail["key"]
        failed_keys.add(key)
        row_idx = key_to_index.get(key)
        if row_idx is not None:
            updates.append({
                "row_index": row_idx,
                "column_name": TOOL_STATUS_COLUMN,
                "value": Status.REVIEW_FAILED,
                "change_type": "review_failed",
            })

    success_count = len(review_results)
    fail_count = len(failed_keys)
    logs.append(
        f"[Node 5] 업데이트 준비 완료: 성공 {success_count}건, 실패 {fail_count}건"
    )

    return {
        "_updates": updates,
        "logs": logs,
    }
