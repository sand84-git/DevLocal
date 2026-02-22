"""Node 2: 컨텍스트 & 글로서리 셋업 (LLM 미사용 유틸리티)"""

from agents.state import LocalizationState
from config.glossary import get_glossary


def context_glossary_node(state: LocalizationState) -> dict:
    """
    시놉시스, 톤앤매너, Glossary를 셋업하여 번역 가이드라인 구성.
    LLM 호출 없이 Python으로 처리.
    """
    target_languages = state.get("target_languages", [])
    tone_and_manner = state.get("tone_and_manner", "")
    logs = list(state.get("logs", []))

    logs.append(f"[Node 2] 컨텍스트 셋업 — 타겟 언어: {target_languages}")
    logs.append(f"[Node 2] 게임 시놉시스 로드 완료")
    logs.append(f"[Node 2] 톤앤매너: {tone_and_manner}")

    glossary = get_glossary()
    for lang in target_languages:
        if lang in glossary:
            count = len(glossary[lang])
            logs.append(f"[Node 2] {lang.upper()} Glossary 로드: {count}개 항목")
        else:
            logs.append(f"[Node 2] {lang.upper()} Glossary 없음 (AI 자유 번역)")

    return {"logs": logs}
