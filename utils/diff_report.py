"""Diff 리포트 CSV 생성 — 한국어 교정 / 번역 변경 리포트"""

import io

import pandas as pd


def generate_ko_diff_report(
    original_rows: list[dict],
    revised_rows: list[dict],
) -> tuple[pd.DataFrame, bytes]:
    """
    한국어 교정 Diff 리포트 생성.

    original_rows: [{"Key": str, "Korean(ko)": str}, ...]
    revised_rows:  [{"Key": str, "Korean(ko)": str}, ...]

    변경된 행만 포함. 반환: (DataFrame, csv_bytes)
    """
    original_map = {r["Key"]: r.get("Korean(ko)", "") for r in original_rows}

    diff_records = []
    for row in revised_rows:
        key = row.get("Key", "")
        revised = row.get("Korean(ko)", "")
        original = original_map.get(key, "")

        if original != revised:
            diff_records.append({
                "Key": key,
                "기존 한국어": original,
                "교정 한국어": revised,
            })

    df = pd.DataFrame(diff_records)
    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    return df, buf.getvalue()


def generate_translation_diff_report(
    old_trans: list[dict],
    new_trans: list[dict],
) -> tuple[pd.DataFrame, bytes]:
    """
    번역 변경 Diff 리포트 생성.

    old_trans: [{"Key": str, "lang": str, "old": str}, ...]
    new_trans: [{"Key": str, "lang": str, "new": str, "reason": str}, ...]

    반환: (DataFrame, csv_bytes)
    """
    # old_trans와 new_trans를 Key+lang으로 매칭
    old_map = {(r["Key"], r["lang"]): r.get("old", "") for r in old_trans}

    diff_records = []
    for row in new_trans:
        key = row.get("Key", "")
        lang = row.get("lang", "")
        new_val = row.get("new", "")
        reason = row.get("reason", "")
        old_val = old_map.get((key, lang), "")

        diff_records.append({
            "Key": key,
            "언어": lang,
            "기존 번역": old_val,
            "새 번역": new_val,
            "변경 사유/내역": reason,
        })

    df = pd.DataFrame(diff_records)
    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    return df, buf.getvalue()
