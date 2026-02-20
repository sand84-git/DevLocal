"""Node 4: 검수 (LLM + Regex) — 태그 검증, Glossary 후처리, AI 품질 검증"""

import json
import litellm
import streamlit as st

from agents.state import LocalizationState
from agents.prompts import build_reviewer_prompt
from config.constants import (
    LLM_MODEL,
    MAX_RETRY_COUNT,
    REQUIRED_COLUMNS,
    SUPPORTED_LANGUAGES,
)
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


def reviewer_node(state: LocalizationState) -> dict:
    """
    번역 결과물 검수:
    1. 정규식 태그 검증 (하드코딩)
    2. Glossary 후처리 (JA 등급명 강제 치환)
    3. AI 품질 검증 (LLM 호출)
    4. 변경 사유 자동 생성 (LLM 호출)
    5. 실패 시 피드백 (최대 3회, 초과 시 검수실패 마킹)
    """
    original_data = state.get("original_data", [])
    translation_results = list(state.get("translation_results", []))
    retry_count = dict(state.get("retry_count", {}))
    failed_rows = list(state.get("failed_rows", []))
    logs = list(state.get("logs", []))
    total_input_tokens = state.get("total_input_tokens", 0)
    total_output_tokens = state.get("total_output_tokens", 0)

    # 원본 데이터 맵 구축
    original_map = {}
    for row in original_data:
        key = row.get(REQUIRED_COLUMNS["key"], "")
        original_map[key] = row

    api_key = st.secrets.get("XAI_API_KEY", "")

    review_results = []
    needs_retry = []  # 재번역이 필요한 항목

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

        # --- Step 1: Glossary 후처리 (JA 등급명 강제 치환) ---
        translated = apply_glossary_postprocess(translated, lang)

        # --- Step 2: 정규식 태그 검증 (하드코딩) ---
        tag_result = validate_tags(source_ko, translated)

        # --- Step 3: Glossary 준수 여부 검증 ---
        glossary_result = check_glossary_compliance(translated, lang, source_ko)

        # 하드코딩 검증 실패 처리
        if not tag_result["valid"] or not glossary_result["compliant"]:
            current_retry = retry_count.get(f"{key}_{lang}", 0)

            if current_retry >= MAX_RETRY_COUNT:
                all_errors = tag_result["errors"] + glossary_result["violations"]
                failed_rows.append({
                    "key": key,
                    "lang": lang,
                    "reason": "; ".join(all_errors),
                })
                logs.append(
                    f"[Node 4] 검수실패 (3회 초과) — {key} ({lang}): "
                    f"{'; '.join(all_errors)}"
                )
            else:
                retry_count[f"{key}_{lang}"] = current_retry + 1
                needs_retry.append({
                    "key": key,
                    "lang": lang,
                    "feedback": tag_result["errors"] + glossary_result["violations"],
                })
                logs.append(
                    f"[Node 4] 재시도 요청 ({current_retry + 1}/{MAX_RETRY_COUNT}) "
                    f"— {key} ({lang})"
                )
            continue

        # --- Step 4: AI 품질 검증 + 변경 사유 생성 ---
        lang_col = SUPPORTED_LANGUAGES.get(lang, "")
        old_translation = original_row.get(lang_col, "")
        reason = ""

        try:
            glossary_text = _format_glossary_text(lang)
            system_prompt = build_reviewer_prompt(lang, glossary_text)
            user_prompt = (
                f"Key: {key}\n"
                f"Korean (원문): {source_ko}\n"
                f"Translation ({lang}): {translated}\n"
                f"기존 번역: {old_translation}\n\n"
                f"위 번역을 검수하고, 기존 번역 대비 변경 사유를 한 줄로 작성하세요."
            )

            response = litellm.completion(
                model=LLM_MODEL,
                api_key=api_key,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            total_input_tokens += getattr(response.usage, "prompt_tokens", 0)
            total_output_tokens += getattr(
                response.usage, "completion_tokens", 0
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

            review_items = json.loads(content)
            if review_items and isinstance(review_items, list):
                review_item = review_items[0]
                if review_item.get("status") == "fail":
                    current_retry = retry_count.get(f"{key}_{lang}", 0)
                    if current_retry >= MAX_RETRY_COUNT:
                        failed_rows.append({
                            "key": key,
                            "lang": lang,
                            "reason": "; ".join(review_item.get("issues", [])),
                        })
                    else:
                        retry_count[f"{key}_{lang}"] = current_retry + 1
                        needs_retry.append({
                            "key": key,
                            "lang": lang,
                            "feedback": review_item.get("issues", []),
                        })
                    continue

                reason = review_item.get("reason", "")

        except Exception as e:
            logs.append(f"[Node 4] AI 검수 오류 — {key} ({lang}): {e}")
            reason = "AI 검수 스킵 (오류)"

        review_results.append({
            "key": key,
            "lang": lang,
            "translated": translated,
            "old_translation": old_translation,
            "reason": reason,
        })

    # 재시도가 필요한 항목이 있으면 translation_results를 갱신하여
    # 그래프 조건부 순환으로 Node 3 재호출
    if needs_retry:
        logs.append(f"[Node 4] 재번역 필요: {len(needs_retry)}건 → Node 3 피드백")

    return {
        "review_results": review_results,
        "failed_rows": failed_rows,
        "retry_count": retry_count,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "logs": logs,
        # 그래프 조건 분기용 — needs_retry가 있으면 translator로 재순환
        "_needs_retry": needs_retry,
    }
