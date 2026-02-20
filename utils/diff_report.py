"""Diff 리포트 생성 (CSV) + 시각화 스타일링"""

import io
import pandas as pd


def generate_ko_diff_report(
    original_rows: list[dict],
    revised_rows: list[dict],
) -> tuple[pd.DataFrame, bytes]:
    """
    한국어 변경 리포트 생성.
    original_rows, revised_rows: [{"Key": str, "Korean(ko)": str}, ...]

    변경된 행만 추출하여 DataFrame + CSV 바이트 반환.
    """
    diffs = []
    original_map = {row["Key"]: row["Korean(ko)"] for row in original_rows}
    revised_map = {row["Key"]: row["Korean(ko)"] for row in revised_rows}

    for key, revised_text in revised_map.items():
        original_text = original_map.get(key, "")
        if original_text != revised_text:
            diffs.append({
                "Key": key,
                "기존 한국어": original_text,
                "수정 제안": revised_text,
            })

    df = pd.DataFrame(diffs)

    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    csv_bytes = buffer.getvalue()

    return df, csv_bytes


def style_ko_diff(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    """한국어 Diff DataFrame에 색상 코딩 적용."""
    if df.empty:
        return df.style

    def _highlight(col):
        if col.name == "기존 한국어":
            return ["background-color: #FFEBEE"] * len(col)
        if col.name == "수정 제안":
            return ["background-color: #E8F5E9"] * len(col)
        return [""] * len(col)

    return df.style.apply(_highlight)


def style_translation_diff(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    """번역 Diff DataFrame에 색상 코딩 적용."""
    if df.empty:
        return df.style

    def _highlight(col):
        if col.name == "기존 번역":
            return ["background-color: #FFEBEE"] * len(col)
        if col.name == "새 번역":
            return ["background-color: #E8F5E9"] * len(col)
        return [""] * len(col)

    return df.style.apply(_highlight)


def generate_translation_diff_report(
    old_translations: list[dict],
    new_translations: list[dict],
) -> tuple[pd.DataFrame, bytes]:
    """
    번역 변경 리포트 생성 (Step 3 HITL 2용).
    각 항목: {"Key": str, "lang": str, "old": str, "new": str, "reason": str}

    변경된 항목만 추출하여 DataFrame + CSV 바이트 반환.
    """
    diffs = []

    old_map = {}
    for row in old_translations:
        old_map[(row["Key"], row["lang"])] = row.get("old", "")

    for row in new_translations:
        key = row["Key"]
        lang = row["lang"]
        new_text = row.get("new", "")
        old_text = old_map.get((key, lang), "")
        reason = row.get("reason", "")

        if old_text != new_text:
            diffs.append({
                "Key": key,
                "언어": lang.upper(),
                "기존 번역": old_text,
                "새 번역": new_text,
                "변경 사유/내역": reason,
            })

    df = pd.DataFrame(diffs)

    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    csv_bytes = buffer.getvalue()

    return df, csv_bytes
