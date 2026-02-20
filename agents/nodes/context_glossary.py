"""Node 2: 컨텍스트 & 글로서리 셋업 (LLM 미사용 유틸리티)"""

from agents.state import LocalizationState
from config.glossary import GLOSSARY
from agents.prompts import GAME_SYNOPSIS, TONE_AND_MANNER


def context_glossary_node(state: LocalizationState) -> dict:
    """
    시놉시스, 톤앤매너, Glossary를 셋업하여 번역 가이드라인 구성.
    LLM 호출 없이 Python으로 처리.
    """
    target_languages = state.get("target_languages", [])
    logs = list(state.get("logs", []))

    logs.append(f"[Node 2] 컨텍스트 셋업 — 타겟 언어: {target_languages}")
    logs.append(f"[Node 2] 게임 시놉시스 로드 완료")
    logs.append(f"[Node 2] 톤앤매너: {TONE_AND_MANNER}")

    for lang in target_languages:
        if lang in GLOSSARY:
            count = len(GLOSSARY[lang])
            logs.append(f"[Node 2] {lang.upper()} Glossary 로드: {count}개 항목")
        else:
            logs.append(f"[Node 2] {lang.upper()} Glossary 없음 (AI 자유 번역)")

    return {"logs": logs}
