"""FastAPI 메인 앱"""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("devlocal")

# 프로젝트 루트를 sys.path에 추가 (agents, config, utils 임포트용)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router

app = FastAPI(title="DevLocal API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
def validate_environment():
    from backend.config import get_xai_api_key, get_gcp_credentials

    issues = []
    if not get_xai_api_key():
        issues.append("XAI_API_KEY is not set in .env")
    creds = get_gcp_credentials()
    if not creds or not creds.get("client_email"):
        issues.append("GCP service account credentials not found or invalid")

    if issues:
        for issue in issues:
            logger.error("ENV VALIDATION FAILED: %s", issue)
        logger.warning("Server started with missing credentials. Some features will fail.")
    else:
        logger.info("Environment validation passed")
