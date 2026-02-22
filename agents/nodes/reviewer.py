"""Node 4: 검수 (LLM + Regex) — 태그 검증, Glossary 후처리, AI 품질 검증 (청크 배치)"""

import json
import litellm
from langchain_core.runnables import RunnableConfig
from backend.config import get_xai_api_key
from agents.state import LocalizationState
from agents.prompts import build_reviewer_prompt
from config.constants import (
    CHUNK_SIZE,
    LLM_MODEL,
    MAX_RETRY_COUNT,
    REQUIRED_COLUMNS,
    SUPPORTED_LANGUAGES,
)
from utils.drip_feed import drip_feed_emit
from config.glossary import GLOSSARY
from utils.validation import (
    apply_glossary_postprocess,
    check_glossary_compliance,
    validate_tags,
)


def _format_glossary_text(lang: str) -> str:
    if lang not in GLOSSARY or not GLOSSARY[lang]:
        return "고정 Glossary 없음."
    lines = [f"- {ko} → {target}" for ko, target in GLOSSARY[lang].items()]
    return "\n".join(lines)


def _build_review_prompt_batch(items_for_review: list[dict]) -> str:
    """여러 번역 항목을 하나의 프롬프트로 결합"""
    parts = []
    for item in items_for_review:
        part = (
            f"Key: {item['key']}\n"
            f"Korean (원문): {item['source_ko']}\n"
            f"Translation ({item['lang']}): {item['translated']}\n"
            f"기존 번역: {item['old_translation']}"
        )
        parts.append(part)
    return "\n\n---\n\n".join(parts)


def reviewer_node(state: LocalizationState, config: RunnableConfig) -> dict:
    """
    번역 결과물 검수:
    1. Glossary 후처리 (JA 등급명 강제 치환)
    2. 정규식 태그 검증 → 실패 시 재시도(최대 3회) 또는 검수실패 마킹
    3. Glossary 준수 여부 검증 (경고 기록)
    4. AI 품질 검증 + 변경 사유 생성 (청크 배치 LLM 호출)

    태그 검증 실패 항목은 _needs_retry로 translator에 재전달.
    3회 재시도 후에도 실패하면 failed_rows에 검수실패로 마킹.
    """
    # 청크별 이벤트 emitter (없으면 무시)
    emitter = config.get("configurable", {}).get("event_emitter") if config else None

    original_data = state.get("original_data", [])
    translation_results = list(state.get("translation_results", []))

    # 이전 라운드의 통과 결과를 보존 (재시도 시 누적)
    prev_review_results = list(state.get("review_results", []))

    failed_rows = list(state.get("failed_rows", []))
    retry_count = dict(state.get("retry_count", {}))
    logs = list(state.get("logs", []))
    total_input_tokens = state.get("total_input_tokens", 0)
    total_output_tokens = state.get("total_output_tokens", 0)

    # 원본 데이터 맵 구축
    original_map = {}
    for row in original_data:
        key = row.get(REQUIRED_COLUMNS["key"], "")
        original_map[key] = row

    api_key = get_xai_api_key()

    # ── Step 1~3: 정규식/Glossary 검증 + 재시도 분기 ──
    validated_items = []
    needs_retry_items = []

    for item in translation_results:
        key = item["key"]
        lang = item["lang"]
        translated = item.get("translated", "")

        if item.get("error"):
            failed_rows.append({
                "key": key,
                "lang": lang,
                "reason": f"번역 오류: {item['error']}",
            })
            continue

        if not translated:
            continue

        original_row = original_map.get(key, {})
        source_ko = original_row.get(REQUIRED_COLUMNS["korean"], "")

        # Glossary 후처리
        translated = apply_glossary_postprocess(translated, lang)

        # 정규식 태그 검증
        tag_result = validate_tags(source_ko, translated)

        if not tag_result["valid"]:
            count_key = f"{key}_{lang}"
            current = retry_count.get(count_key, 0)

            if current < MAX_RETRY_COUNT:
                retry_count[count_key] = current + 1
                shared_comments = original_row.get(
                    REQUIRED_COLUMNS["shared_comments"], ""
                )
                needs_retry_items.append({
                    "key": key,
                    "lang": lang,
                    "source_ko": source_ko,
                    "shared_comments": shared_comments,
                    "translated": translated,
                    "feedback": tag_result["errors"],
                })
                logs.append(
                    f"[Node 4] 태그 검증 실패 → 재번역 요청 "
                    f"({current + 1}/{MAX_RETRY_COUNT}) — {key} ({lang})"
                )
                continue
            else:
                failed_rows.append({
                    "key": key,
                    "lang": lang,
                    "reason": f"태그 검증 {MAX_RETRY_COUNT}회 실패: "
                              f"{'; '.join(tag_result['errors'])}",
                })
                logs.append(
                    f"[Node 4] 태그 검증 {MAX_RETRY_COUNT}회 초과 → "
                    f"검수실패 — {key} ({lang})"
                )
                continue

        # Glossary 준수 여부 검증 (경고만, 재시도 트리거 아님)
        warnings = []
        glossary_result = check_glossary_compliance(translated, lang, source_ko)
        if not glossary_result["compliant"]:
            warnings.extend(glossary_result["violations"])
            logs.append(
                f"[Node 4] 글로서리 경고 — {key} ({lang}): "
                f"{'; '.join(glossary_result['violations'])}"
            )

        lang_col = SUPPORTED_LANGUAGES.get(lang, "")
        old_translation = original_row.get(lang_col, "")

        validated_items.append({
            "key": key,
            "lang": lang,
            "translated": translated,
            "source_ko": source_ko,
            "old_translation": old_translation,
            "warnings": warnings,
        })

    logs.append(
        f"[Node 4] 정규식/Glossary 검증: 통과 {len(validated_items)}건, "
        f"재시도 {len(needs_retry_items)}건"
    )

    # ── Step 4+5: AI 품질 검증 + 결합 + 청크별 drip-feed emit ──
    lang_groups: dict[str, list[dict]] = {}
    for item in validated_items:
        lang_groups.setdefault(item["lang"], []).append(item)

    # 전체 진행률 기준 (초기 신호 + 청크별 emit 모두 동일 total 사용)
    progress_total = len(prev_review_results) + len(validated_items) + len(needs_retry_items)
    if progress_total == 0:
        progress_total = max(len(prev_review_results) + len(failed_rows), 1)

    # 초기 진행률 신호 — LLM 호출 전 즉시 발행하여 프론트엔드 agentPhase 전환
    if emitter:
        emitter("review_chunk", {
            "chunk_results": [],
            "progress": {
                "done": len(prev_review_results),
                "total": progress_total,
            },
        })

    new_review_results = []
    cumulative_done = len(prev_review_results)

    for lang, items in lang_groups.items():
        glossary_text = _format_glossary_text(lang)
        system_prompt = build_reviewer_prompt(lang, glossary_text)
        total_chunks = (len(items) + CHUNK_SIZE - 1) // CHUNK_SIZE

        for chunk_idx in range(total_chunks):
            start = chunk_idx * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, len(items))
            chunk = items[start:end]

            user_prompt = _build_review_prompt_batch(chunk)
            user_prompt += (
                "\n\n위 번역들을 각각 검수하고, "
                "기존 번역 대비 변경 사유를 포함하여 JSON 배열로 출력하세요."
            )

            logs.append(
                f"[Node 4] {lang.upper()} 검수 청크 {chunk_idx + 1}/{total_chunks} "
                f"({len(chunk)}건) 처리 중..."
            )

            # LLM 호출
            chunk_ai_map: dict[str, dict] = {}
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

                total_input_tokens += getattr(response.usage, "prompt_tokens", 0)
                total_output_tokens += getattr(
                    response.usage, "completion_tokens", 0
                )

                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

                review_items = json.loads(content)
                if isinstance(review_items, list):
                    for ri in review_items:
                        ri_key = ri.get("key", "")
                        chunk_ai_map[ri_key] = ri

            except Exception as e:
                logs.append(
                    f"[Node 4] AI 검수 오류 (청크 {chunk_idx + 1}): {e}"
                )

            # 이 청크의 결과 즉시 결합
            chunk_results = []
            for item in chunk:
                key = item["key"]
                warnings = list(item["warnings"])

                ai_result = chunk_ai_map.get(key, {})
                reason = ai_result.get("reason", "")

                if ai_result.get("status") == "fail":
                    ai_issues = ai_result.get("issues", [])
                    warnings.extend(ai_issues)
                    logs.append(
                        f"[Node 4] AI 검수 경고 — {key} ({lang}): {'; '.join(ai_issues)}"
                    )

                if warnings and not reason:
                    reason = "; ".join(warnings)
                elif warnings and reason:
                    reason = f"{reason} | 경고: {'; '.join(warnings)}"

                chunk_results.append({
                    "key": key,
                    "lang": lang,
                    "translated": item["translated"],
                    "old_translation": item["old_translation"],
                    "original_ko": item["source_ko"],
                    "reason": reason,
                })

            new_review_results.extend(chunk_results)

            # 청크별 drip-feed emit
            if emitter and chunk_results:
                drip_feed_emit(
                    emitter,
                    "review_chunk",
                    chunk_results,
                    progress_base=cumulative_done,
                    total=progress_total,
                )
                cumulative_done += len(chunk_results)

    all_review_results = prev_review_results + new_review_results

    # validated_items가 비어있을 때도 progress 이벤트 보장 (엣지 케이스)
    if emitter and not new_review_results:
        emitter("review_chunk", {
            "chunk_results": [],
            "progress": {
                "done": len(all_review_results),
                "total": progress_total,
            },
        })

    logs.append(
        f"[Node 4] 검수 완료: 누적 통과 {len(all_review_results)}건, "
        f"실패 {len(failed_rows)}건, 재시도 대기 {len(needs_retry_items)}건"
    )

    return {
        "review_results": all_review_results,
        "failed_rows": failed_rows,
        "_needs_retry": needs_retry_items,
        "retry_count": retry_count,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "logs": logs,
    }
