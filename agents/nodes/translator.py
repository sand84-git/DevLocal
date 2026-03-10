"""Node 3: 번역 (LLM) — 청크 단위 번역, Shared Comments 컨텍스트 주입"""

import json
import litellm
from langchain_core.runnables import RunnableConfig
from backend.config import get_xai_api_key
from agents.state import LocalizationState
from agents.prompts import build_translator_prompt
from config.constants import (
    CHUNK_SIZE,
    LLM_MODEL,
    REQUIRED_COLUMNS,
    Status,
    SUPPORTED_LANGUAGES,
)
from utils.drip_feed import drip_feed_emit
from config.glossary import format_glossary_text


def _build_translation_prompt(rows: list[dict], lang: str) -> str:
    """번역 대상 행들을 프롬프트 메시지로 변환"""
    items = []
    for row in rows:
        key = row.get(REQUIRED_COLUMNS["key"], "")
        ko_text = row.get(REQUIRED_COLUMNS["korean"], "")
        shared_comments = row.get(REQUIRED_COLUMNS["shared_comments"], "")

        item = f"Key: {key}\nKorean: {ko_text}"
        if shared_comments:
            item += f"\nShared Comments (참고): {shared_comments}"
        items.append(item)

    return "\n\n---\n\n".join(items)


def _build_retry_prompt(items: list[dict], lang: str) -> str:
    """재번역 프롬프트 — 이전 번역 실패 피드백 포함"""
    parts = []
    for item in items:
        part = f"Key: {item['key']}\nKorean: {item['source_ko']}"
        if item.get("shared_comments"):
            part += f"\nShared Comments (참고): {item['shared_comments']}"
        part += f"\n이전 번역 (오류 있음): {item['translated']}"
        part += f"\n오류: {'; '.join(item['feedback'])}"
        part += (
            "\n위 오류를 수정하여 다시 번역하세요. "
            "특히 원문의 포맷팅 태그({변수}, <color>, \\n 등)를 "
            "번역 결과에 동일하게 보존해야 합니다."
        )
        parts.append(part)
    return "\n\n---\n\n".join(parts)


def _translate_retry(state: LocalizationState, needs_retry: list[dict]) -> dict:
    """재시도 모드: 실패한 항목만 재번역"""
    retry_count = dict(state.get("retry_count", {}))
    logs = list(state.get("logs", []))
    total_input_tokens = state.get("total_input_tokens", 0)
    total_output_tokens = state.get("total_output_tokens", 0)
    total_reasoning_tokens = state.get("total_reasoning_tokens", 0)
    total_cached_tokens = state.get("total_cached_tokens", 0)
    custom_prompt = state.get("custom_prompt", "")
    game_synopsis = state.get("game_synopsis", "")
    tone_and_manner = state.get("tone_and_manner", "")

    api_key = get_xai_api_key()

    # 언어별 그룹핑
    retry_by_lang: dict[str, list[dict]] = {}
    for item in needs_retry:
        retry_by_lang.setdefault(item["lang"], []).append(item)

    all_results = []

    for lang, items in retry_by_lang.items():
        glossary_text = format_glossary_text(lang)
        system_prompt = build_translator_prompt(lang, glossary_text, synopsis=game_synopsis, tone=tone_and_manner, custom_prompt=custom_prompt)
        total_chunks = (len(items) + CHUNK_SIZE - 1) // CHUNK_SIZE

        logs.append(
            f"[Node 3] {lang.upper()} 재번역 대상: {len(items)}건"
        )

        for chunk_idx in range(total_chunks):
            start = chunk_idx * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, len(items))
            chunk = items[start:end]

            user_prompt = _build_retry_prompt(chunk, lang)
            logs.append(
                f"[Node 3] {lang.upper()} 재번역 청크 "
                f"{chunk_idx + 1}/{total_chunks} ({len(chunk)}건) 처리 중..."
            )

            try:
                response = litellm.completion(
                    model=LLM_MODEL,
                    api_key=api_key,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=120,
                )

                total_input_tokens += getattr(
                    response.usage, "prompt_tokens", 0
                )
                total_output_tokens += getattr(
                    response.usage, "completion_tokens", 0
                )
                if hasattr(response.usage, "completion_tokens_details") and response.usage.completion_tokens_details:
                    total_reasoning_tokens += getattr(response.usage.completion_tokens_details, "reasoning_tokens", 0) or 0
                if hasattr(response.usage, "prompt_tokens_details") and response.usage.prompt_tokens_details:
                    total_cached_tokens += getattr(response.usage.prompt_tokens_details, "cached_tokens", 0) or 0

                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

                translated_items = json.loads(content)

                # 재시도 청크의 key→row_index 매핑
                retry_key_to_ri: dict[str, list] = {}
                for src in chunk:
                    retry_key_to_ri.setdefault(src["key"], []).append(src.get("row_index"))
                retry_key_counter: dict[str, int] = {}

                for ti in translated_items:
                    translated_text = ti.get("translated", "")
                    translated_text = translated_text.replace('\n', '\\n')
                    translated_text = translated_text.replace('\t', '\\t')
                    tkey = ti["key"]
                    cidx = retry_key_counter.get(tkey, 0)
                    retry_key_counter[tkey] = cidx + 1
                    ri_list = retry_key_to_ri.get(tkey, [])
                    ri = ri_list[cidx] if cidx < len(ri_list) else None
                    all_results.append({
                        "key": tkey,
                        "lang": lang,
                        "translated": translated_text,
                        "row_index": ri,
                    })

            except Exception as e:
                logs.append(
                    f"[Node 3] 재번역 오류 (청크 {chunk_idx + 1}): {e}"
                )
                for item in chunk:
                    all_results.append({
                        "key": item["key"],
                        "lang": lang,
                        "translated": "",
                        "error": str(e),
                        "row_index": item.get("row_index"),
                    })

    return {
        "translation_results": all_results,
        "_needs_retry": [],
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_reasoning_tokens": total_reasoning_tokens,
        "total_cached_tokens": total_cached_tokens,
        "retry_count": retry_count,
        "logs": logs,
    }


def translator_node(state: LocalizationState, config: RunnableConfig) -> dict:
    """
    청크 단위 번역 수행.
    _needs_retry가 있으면 해당 항목만 재번역 (retry 모드).
    없으면 정상 번역:
      모드 A: 전체 행 번역
      모드 B: 타겟 언어 빈칸인 행만 번역
    """
    # 청크별 이벤트 emitter (없으면 무시)
    emitter = config.get("configurable", {}).get("event_emitter") if config else None

    # 재시도 모드 확인
    needs_retry = state.get("_needs_retry", [])
    if needs_retry:
        return _translate_retry(state, needs_retry)

    # ── 정상 번역 모드 ──
    original_data = state.get("original_data", [])
    mode = state.get("mode", "A")
    target_languages = state.get("target_languages", [])
    ko_approval_result = state.get("ko_approval_result", "approved")
    ko_review_results = state.get("ko_review_results", [])
    retry_count = dict(state.get("retry_count", {}))
    logs = list(state.get("logs", []))
    total_input_tokens = state.get("total_input_tokens", 0)
    total_output_tokens = state.get("total_output_tokens", 0)
    total_reasoning_tokens = state.get("total_reasoning_tokens", 0)
    total_cached_tokens = state.get("total_cached_tokens", 0)
    custom_prompt = state.get("custom_prompt", "")
    game_synopsis = state.get("game_synopsis", "")
    tone_and_manner = state.get("tone_and_manner", "")

    # 한국어 검수 승인 시, 수정된 텍스트 적용
    working_data = []
    ko_revised_map = {}
    if ko_approval_result == "approved" and ko_review_results:
        for r in ko_review_results:
            ko_revised_map[r["key"]] = r["revised"]

    for row in original_data:
        row_copy = dict(row)
        key = row_copy.get(REQUIRED_COLUMNS["key"], "")
        if key in ko_revised_map:
            row_copy[REQUIRED_COLUMNS["korean"]] = ko_revised_map[key]
        working_data.append(row_copy)

    # 번역 결과 저장
    all_results = []

    api_key = get_xai_api_key()

    for lang in target_languages:
        lang_col = SUPPORTED_LANGUAGES.get(lang, "")
        if not lang_col:
            logs.append(f"[Node 3] 지원하지 않는 언어: {lang}")
            continue

        # 모드에 따른 대상 행 필터링
        target_rows = []
        for row in working_data:
            key = row.get(REQUIRED_COLUMNS["key"], "")
            ko_text = row.get(REQUIRED_COLUMNS["korean"], "")

            if not ko_text:
                continue

            if mode == "B":
                existing = row.get(lang_col, "")
                if existing and existing.strip():
                    continue

            target_rows.append(row)

        logs.append(f"[Node 3] {lang.upper()} 번역 대상: {len(target_rows)}행")

        # 청크 단위 처리
        glossary_text = format_glossary_text(lang)
        system_prompt = build_translator_prompt(lang, glossary_text, synopsis=game_synopsis, tone=tone_and_manner, custom_prompt=custom_prompt)
        total_chunks = (len(target_rows) + CHUNK_SIZE - 1) // CHUNK_SIZE

        for chunk_idx in range(total_chunks):
            start = chunk_idx * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, len(target_rows))
            chunk = target_rows[start:end]

            user_prompt = _build_translation_prompt(chunk, lang)
            logs.append(
                f"[Node 3] {lang.upper()} 청크 {chunk_idx + 1}/{total_chunks} "
                f"({len(chunk)}행) 번역 중..."
            )

            try:
                response = litellm.completion(
                    model=LLM_MODEL,
                    api_key=api_key,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=120,
                )

                total_input_tokens += getattr(
                    response.usage, "prompt_tokens", 0
                )
                total_output_tokens += getattr(
                    response.usage, "completion_tokens", 0
                )
                if hasattr(response.usage, "completion_tokens_details") and response.usage.completion_tokens_details:
                    total_reasoning_tokens += getattr(response.usage.completion_tokens_details, "reasoning_tokens", 0) or 0
                if hasattr(response.usage, "prompt_tokens_details") and response.usage.prompt_tokens_details:
                    total_cached_tokens += getattr(response.usage.prompt_tokens_details, "cached_tokens", 0) or 0

                content = response.choices[0].message.content.strip()
                # JSON 파싱 — 코드블록 제거
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

                translated_items = json.loads(content)

                # 청크 소스 행의 key→row_index 매핑 (순서 기반, 중복 Key 대응)
                chunk_key_to_ri: dict[str, list[int]] = {}
                for src_row in chunk:
                    sk = src_row.get(REQUIRED_COLUMNS["key"], "")
                    chunk_key_to_ri.setdefault(sk, []).append(src_row.get("_row_index"))
                chunk_key_counter: dict[str, int] = {}

                chunk_results = []
                for item in translated_items:
                    translated_text = item.get("translated", "")
                    # Fix: LLM이 JSON에서 \n을 실제 개행으로 출력하는 문제 보정
                    translated_text = translated_text.replace('\n', '\\n')
                    translated_text = translated_text.replace('\t', '\\t')
                    ikey = item["key"]
                    cidx = chunk_key_counter.get(ikey, 0)
                    chunk_key_counter[ikey] = cidx + 1
                    ri_list = chunk_key_to_ri.get(ikey, [])
                    ri = ri_list[cidx] if cidx < len(ri_list) else None
                    result_item = {
                        "key": ikey,
                        "lang": lang,
                        "translated": translated_text,
                        "row_index": ri,
                    }
                    all_results.append(result_item)
                    chunk_results.append(result_item)

                # 청크별 부분 결과를 1행씩 drip-feed 전송
                if emitter and chunk_results:
                    drip_feed_emit(
                        emitter,
                        "translation_chunk",
                        chunk_results,
                        progress_base=len(all_results) - len(chunk_results),
                        total=len(target_rows) * len(target_languages),
                        lang=lang,
                    )

            except Exception as e:
                logs.append(f"[Node 3] 번역 오류 (청크 {chunk_idx + 1}): {e}")
                for row in chunk:
                    key = row.get(REQUIRED_COLUMNS["key"], "")
                    all_results.append({
                        "key": key,
                        "lang": lang,
                        "translated": "",
                        "error": str(e),
                        "row_index": row.get("_row_index"),
                    })

    return {
        "translation_results": all_results,
        "current_chunk_index": total_chunks if target_languages else 0,
        "total_chunks": total_chunks if target_languages else 0,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_reasoning_tokens": total_reasoning_tokens,
        "total_cached_tokens": total_cached_tokens,
        "retry_count": retry_count,
        "logs": logs,
    }
