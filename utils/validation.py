"""정규식 태그 검증 + Glossary 후처리"""

import re

from config.constants import TAG_PATTERNS
from config.glossary import GLOSSARY


def validate_tags(source_ko: str, translated: str) -> dict:
    """
    정규식으로 태그 개수/문자열 동일성 검증.
    원본(ko)에 존재하는 태그가 번역 결과에도 동일하게 존재하는지 확인.

    Returns:
        {"valid": bool, "errors": [str]}
    """
    errors = []

    for pattern in TAG_PATTERNS:
        source_tags = re.findall(pattern, source_ko)
        translated_tags = re.findall(pattern, translated)

        if sorted(source_tags) != sorted(translated_tags):
            errors.append(
                f"태그 불일치 [{pattern}]: "
                f"원본={source_tags}, 번역={translated_tags}"
            )

    return {"valid": len(errors) == 0, "errors": errors}


def apply_glossary_postprocess(text: str, lang: str) -> str:
    """
    Glossary 강제 치환 (후처리).
    JA 등급명 등 고정 매핑이 있는 경우 파이썬 replace()로 강제 적용.
    """
    if lang not in GLOSSARY:
        return text

    glossary = GLOSSARY[lang]
    for ko_term, target_term in glossary.items():
        # 한국어 원어가 번역문에 남아있는 경우 치환
        text = text.replace(ko_term, target_term)

    return text


def check_glossary_compliance(text: str, lang: str, source_ko: str) -> dict:
    """
    Glossary 준수 여부 검증.
    원문에 Glossary 키워드가 있는 경우, 번역문에 대응 번역이 존재하는지 확인.

    Returns:
        {"compliant": bool, "violations": [str]}
    """
    if lang not in GLOSSARY:
        return {"compliant": True, "violations": []}

    violations = []
    glossary = GLOSSARY[lang]

    for ko_term, target_term in glossary.items():
        if ko_term in source_ko and target_term not in text:
            violations.append(
                f"Glossary 위반: '{ko_term}' → '{target_term}' 미적용"
            )

    return {"compliant": len(violations) == 0, "violations": violations}
