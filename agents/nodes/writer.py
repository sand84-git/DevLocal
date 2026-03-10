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

    # 원본 데이터의 Key → row_index 매핑 (fallback용)
    key_to_index = {}
    for idx, row in enumerate(original_data):
        key = row.get(REQUIRED_COLUMNS["key"], "")
        if key not in key_to_index:  # 첫 번째만 (중복 Key fallback)
            key_to_index[key] = idx

    # 검수실패 row_index 집합 먼저 수집 (Tool_Status 충돌 방지)
    failed_indices = set()
    for fail in failed_rows:
        ri = fail.get("row_index")
        if ri is not None:
            failed_indices.add(ri)
        else:
            failed_indices.add(fail["key"])  # fallback

    # 업데이트 목록 생성
    updates = []
    completed_indices = set()  # Tool_Status 중복 방지

    # 성공한 번역 결과 반영 — 실제 변경된 셀만
    for result in review_results:
        key = result["key"]
        lang = result["lang"]
        translated = result["translated"]
        # row_index 직접 사용, fallback으로 key lookup
        row_idx = result.get("row_index")
        if row_idx is None:
            row_idx = key_to_index.get(key)
        if row_idx is None:
            continue

        lang_col = SUPPORTED_LANGUAGES.get(lang, "")
        if not lang_col:
            continue

        # 원본 값과 비교 — 실제로 변경된 경우만 업데이트 & 컬러링
        original_value = original_data[row_idx].get(lang_col, "") if row_idx < len(original_data) else ""
        if translated != original_value:
            updates.append({
                "row_index": row_idx,
                "column_name": lang_col,
                "value": translated,
                "change_type": "translation",
            })

        # Tool_Status: 실패 row가 아닌 경우만 최종완료 (실패는 아래에서 처리)
        fail_id = row_idx if row_idx is not None else key
        if row_idx not in completed_indices and fail_id not in failed_indices:
            completed_indices.add(row_idx)
            updates.append({
                "row_index": row_idx,
                "column_name": TOOL_STATUS_COLUMN,
                "value": Status.COMPLETED,
                "change_type": "completed",
            })

    # 검수실패 행 마킹
    for fail in failed_rows:
        row_idx = fail.get("row_index")
        if row_idx is None:
            row_idx = key_to_index.get(fail["key"])
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
