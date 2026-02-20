"""Google Sheets 연동 모듈 — gspread 래퍼 (Batch Read/Write, 인증)"""

import time
import datetime
import io
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

from config.constants import FORBIDDEN_SHEETS, TOOL_STATUS_COLUMN


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Exponential backoff 설정
MAX_RETRIES = 5
BASE_DELAY = 1  # 초


def _retry_with_backoff(func, *args, **kwargs):
    """Exponential backoff 재시도 래퍼"""
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429 and attempt < MAX_RETRIES - 1:
                delay = BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
            else:
                raise


def connect_to_sheet(url: str) -> gspread.Spreadsheet:
    """st.secrets 기반 인증 + 스프레드시트 연결"""
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(dict(creds_info), scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = _retry_with_backoff(client.open_by_url, url)
    return spreadsheet


def get_bot_email() -> str:
    """서비스 계정 봇 이메일 반환"""
    creds_info = st.secrets["gcp_service_account"]
    return creds_info.get("client_email", "")


def get_worksheet_names(spreadsheet: gspread.Spreadsheet) -> list[str]:
    """금지 시트 필터링된 시트 목록 반환"""
    all_sheets = [ws.title for ws in spreadsheet.worksheets()]
    return [name for name in all_sheets if name not in FORBIDDEN_SHEETS]


def load_sheet_data(worksheet: gspread.Worksheet) -> pd.DataFrame:
    """1회 전체 로드 → DataFrame 변환 (헤더 이름 기반)"""
    records = _retry_with_backoff(worksheet.get_all_records)
    df = pd.DataFrame(records)
    return df


def ensure_tool_status_column(worksheet: gspread.Worksheet, df: pd.DataFrame) -> pd.DataFrame:
    """Tool_Status 컬럼 존재 확인/생성"""
    headers = _retry_with_backoff(worksheet.row_values, 1)

    if TOOL_STATUS_COLUMN not in headers:
        col_index = len(headers) + 1
        _retry_with_backoff(worksheet.update_cell, 1, col_index, TOOL_STATUS_COLUMN)
        df[TOOL_STATUS_COLUMN] = ""
    elif TOOL_STATUS_COLUMN not in df.columns:
        df[TOOL_STATUS_COLUMN] = ""

    return df


def batch_update_sheet(
    worksheet: gspread.Worksheet,
    updates: list[dict],
    df: pd.DataFrame,
):
    """
    Batch Write 래퍼 — 개별 cell.update() 금지, 일괄 업데이트.

    updates: [{"row_index": int (0-based in df), "column_name": str, "value": str}, ...]
    df: 현재 DataFrame (헤더 이름 → 컬럼 위치 매핑용)
    """
    if not updates:
        return

    headers = list(df.columns)
    cells = []

    for upd in updates:
        row_idx = upd["row_index"]
        col_name = upd["column_name"]
        value = upd["value"]

        if col_name not in headers:
            continue

        col_idx = headers.index(col_name) + 1  # 1-based
        sheet_row = row_idx + 2  # +1 for 0-based, +1 for header row
        cells.append(gspread.Cell(row=sheet_row, col=col_idx, value=value))

    if cells:
        _retry_with_backoff(worksheet.update_cells, cells)


def create_backup_csv(df: pd.DataFrame, sheet_name: str) -> tuple[str, bytes]:
    """
    백업 CSV 생성 — 파일명과 바이트 데이터 반환.
    Streamlit Cloud에서는 로컬 파일이 초기화되므로 바이트로 반환하여
    st.download_button + st.session_state에 보관.
    """
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{sheet_name}_backup_{now}.csv"

    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    csv_bytes = buffer.getvalue()

    return filename, csv_bytes
