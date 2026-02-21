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

    # 검수실패 Key 집합 먼저 수집 (Tool_Status 충돌 방지)
    failed_keys = set()
    for fail in failed_rows:
        failed_keys.add(fail["key"])

    # 업데이트 목록 생성
    updates = []
    completed_keys = set()  # Tool_Status 중복 방지

    # 성공한 번역 결과 반영 — 실제 변경된 셀만
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

        # 원본 값과 비교 — 실제로 변경된 경우만 업데이트 & 컬러링
        original_value = original_data[row_idx].get(lang_col, "")
        if translated != original_value:
            updates.append({
                "row_index": row_idx,
                "column_name": lang_col,
                "value": translated,
                "change_type": "translation",
            })

        # Tool_Status: 실패 Key가 아닌 경우만 최종완료 (실패는 아래에서 처리)
        if key not in completed_keys and key not in failed_keys:
            completed_keys.add(key)
            updates.append({
                "row_index": row_idx,
                "column_name": TOOL_STATUS_COLUMN,
                "value": Status.COMPLETED,
                "change_type": "completed",
            })

    # 검수실패 행 마킹
    for fail in failed_rows:
        key = fail["key"]
        row_idx = key_to_index.get(key)
        if row_idx is not None:
            updates.append({
                "row_index": row_idx,
                "column_name": TOOL_STATUS_COLUMN,
                "value": Status.REVIEW_FAILED,
                "change_type": "review_failed",
            })

    changed_count = sum(1 for u in updates if u.get("change_type") == "translation")
    unchanged_count = len(review_results) - changed_count
    fail_count = len(failed_keys)
    logs.append(
        f"[Node 5] 업데이트 준비: 변경 {changed_count}건, 변경없음 {unchanged_count}건, 실패 {fail_count}건"
    )

    return {
        "_updates": updates,
        "logs": logs,
    }
