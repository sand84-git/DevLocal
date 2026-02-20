"""Node 3: 번역 (LLM) — 청크 단위 번역, Shared Comments 컨텍스트 주입"""

import json
import litellm
import streamlit as st

from agents.state import LocalizationState
from agents.prompts import build_translator_prompt
from config.constants import (
    CHUNK_SIZE,
    LLM_MODEL,
    REQUIRED_COLUMNS,
    Status,
    SUPPORTED_LANGUAGES,
)
from config.glossary import GLOSSARY


def _format_glossary_text(lang: str) -> str:
    """Glossary를 프롬프트용 텍스트로 변환"""
    if lang not in GLOSSARY or not GLOSSARY[lang]:
        return "이 언어에 대한 고정 Glossary 없음. 일관성을 유지하여 자유 번역하세요."

    lines = []
    for ko, target in GLOSSARY[lang].items():
        lines.append(f"- {ko} → {target}")
    return "\n".join(lines)


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


def translator_node(state: LocalizationState) -> dict:
    """
    청크 단위 번역 수행.
    모드 A: 전체 행 번역
    모드 B: 타겟 언어 빈칸인 행만 번역
    """
    original_data = state.get("original_data", [])
    mode = state.get("mode", "A")
    target_languages = state.get("target_languages", [])
    ko_approval_result = state.get("ko_approval_result", "approved")
    ko_review_results = state.get("ko_review_results", [])
    retry_count = dict(state.get("retry_count", {}))
    logs = list(state.get("logs", []))
    total_input_tokens = state.get("total_input_tokens", 0)
    total_output_tokens = state.get("total_output_tokens", 0)

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
    all_results = list(state.get("translation_results", []))

    api_key = st.secrets.get("XAI_API_KEY", "")

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
                if existing:
                    continue

            target_rows.append(row)

        logs.append(f"[Node 3] {lang.upper()} 번역 대상: {len(target_rows)}행")

        # 청크 단위 처리
        glossary_text = _format_glossary_text(lang)
        system_prompt = build_translator_prompt(lang, glossary_text)
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

                content = response.choices[0].message.content.strip()
                # JSON 파싱 — 코드블록 제거
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

                translated_items = json.loads(content)

                for item in translated_items:
                    translated_text = item.get("translated", "")
                    # Fix: LLM이 JSON에서 \n을 실제 개행으로 출력하는 문제 보정
                    # json.loads()가 \n → 실제 줄바꿈으로 변환하므로,
                    # 게임 텍스트의 literal \n 태그를 복원
                    translated_text = translated_text.replace('\n', '\\n')
                    translated_text = translated_text.replace('\t', '\\t')
                    all_results.append({
                        "key": item["key"],
                        "lang": lang,
                        "translated": translated_text,
                    })

            except Exception as e:
                logs.append(f"[Node 3] 번역 오류 (청크 {chunk_idx + 1}): {e}")
                for row in chunk:
                    key = row.get(REQUIRED_COLUMNS["key"], "")
                    all_results.append({
                        "key": key,
                        "lang": lang,
                        "translated": "",
                        "error": str(e),
                    })

    return {
        "translation_results": all_results,
        "current_chunk_index": total_chunks if target_languages else 0,
        "total_chunks": total_chunks if target_languages else 0,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "retry_count": retry_count,
        "logs": logs,
    }
