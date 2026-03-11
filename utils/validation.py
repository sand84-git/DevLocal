"""정규식 태그 검증 + Glossary 후처리"""

import re

from config.constants import TAG_PATTERNS
from config.glossary import get_glossary


def validate_tags(source_ko: str, translated: str) -> dict:
    """
    원문과 번역문의 포맷팅 태그 일치 여부를 정규식으로 검증.

    Returns: {"valid": bool, "errors": [str]}
    """
    errors = []

    # 리터럴 \\n, \\t 를 통일 (실제 개행/탭이 섞인 경우 보정)
    source_norm = source_ko.replace("\n", "\\n").replace("\t", "\\t")
    trans_norm = translated.replace("\n", "\\n").replace("\t", "\\t")

    for pattern in TAG_PATTERNS:
        source_tags = sorted(re.findall(pattern, source_norm))
        trans_tags = sorted(re.findall(pattern, trans_norm))

        if source_tags != trans_tags:
            errors.append(
                f"태그 불일치 [{pattern}]: "
                f"원문 {source_tags} ≠ 번역 {trans_tags}"
            )

    return {"valid": len(errors) == 0, "errors": errors}


def apply_glossary_postprocess(text: str, lang: str) -> str:
    """
    Glossary 강제 치환 — 번역 결과에서 오역된 Glossary 용어를 교정.
    JA 등급명 등 의역 금지 항목에 대해 str.replace() 적용.
    """
    glossary = get_glossary()
    lang_glossary = glossary.get(lang, {})

    if not lang_glossary:
        return text

    # 역방향 매핑: target → source_ko (잘못된 번역 감지용은 아님)
    # 정방향: source_ko → target (원문에 한국어가 남아있으면 치환)
    for ko_term, target_term in lang_glossary.items():
        if ko_term in text:
            text = text.replace(ko_term, target_term)

    return text


def check_glossary_compliance(
    text: str, lang: str, source_ko: str
) -> dict:
    """
    번역문에 Glossary 용어가 올바르게 반영되었는지 검증.

    원문(source_ko)에 Glossary의 한국어 키가 있으면,
    번역문에 대응하는 타겟 용어가 있어야 함.

    Returns: {"compliant": bool, "violations": [str]}
    """
    glossary = get_glossary()
    lang_glossary = glossary.get(lang, {})
    violations = []

    if not lang_glossary:
        return {"compliant": True, "violations": []}

    for ko_term, target_term in lang_glossary.items():
        if ko_term in source_ko and target_term not in text:
            violations.append(
                f"'{ko_term}' → '{target_term}' 미반영"
            )

    return {"compliant": len(violations) == 0, "violations": violations}
