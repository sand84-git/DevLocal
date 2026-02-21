"""애플리케이션 설정 — 환경변수 기반"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# .env 로드 (프로젝트 루트 기준)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def get_xai_api_key() -> str:
    return os.environ.get("XAI_API_KEY", "")


def get_gcp_credentials() -> dict:
    """GCP 서비스 계정 인증 정보 로드 (JSON 파일 또는 환경변수)"""
    json_path = os.environ.get("GCP_SERVICE_ACCOUNT_JSON_PATH", "")
    if json_path:
        full_path = _PROJECT_ROOT / json_path
        if full_path.exists():
            with open(full_path) as f:
                return json.load(f)
    raw = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "{}")
    return json.loads(raw)
