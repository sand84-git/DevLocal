# CLAUDE.md — 게임 로컬라이징 자동화 툴

## 프로젝트 개요
구글 스프레드시트 기반 게임 텍스트(한국어)를 AI(Grok 4.1 Fast Reasoning)로 다국어(EN, JA) 자동 번역/검수하는 웹앱.

## 기술 스택
- **Frontend**: React 19 + Vite + TypeScript + Tailwind CSS v4 + Zustand (SPA)
- **Backend**: FastAPI + SSE (sse-starlette) + uvicorn
- **Agent Orchestration**: LangGraph 0.6 (8 Node + HITL 2곳 interrupt)
- **Google Sheets**: gspread (Batch Read/Write + Exponential Backoff)
- **LLM**: LiteLLM → xai/grok-4-1-fast-reasoning (timeout=120s)
- **Data**: Pandas
- **Legacy Frontend**: Streamlit (app.py — 기존 버전, 별도 실행 가능)

## 그래프 워크플로우
```
data_backup → context_glossary → ko_review → ko_approval(HITL 1)
  → translator → reviewer → [should_retry → translator 재순환 가능]
  → final_approval(HITL 2) → [approved → writer → END / rejected → END]
```
- `ko_review`: AI 한국어 맞춤법 분석만 수행 (interrupt 없음, 결과 state에 저장)
- `ko_approval`: interrupt()로 사용자 승인 대기 (HITL 1)
- `final_approval`: interrupt()로 최종 승인 대기 (HITL 2)
- **중요**: AI 분석과 interrupt를 반드시 별도 노드로 분리할 것 (invoke 시 결과 유실 방지)

## 프로젝트 구조
```
run_dev.sh                # FastAPI(8000) + Vite(5173) 동시 실행 스크립트
.env                      # XAI_API_KEY + GCP_SERVICE_ACCOUNT_JSON_PATH (gitignore)
.gcp_service_account.json # GCP 서비스 계정 JSON (gitignore)
.app_config.json          # 시트 URL/백업폴더 영속 저장 (gitignore)

backend/
  config.py               # 환경변수 기반 설정 (st.secrets 대체)
  main.py                 # FastAPI 앱 (CORS, /api 라우터)
  api/
    routes.py             # 10개 REST+SSE 엔드포인트
    schemas.py            # Pydantic 요청/응답 모델
    session_manager.py    # 서버사이드 세션 (LRU, max 10, 그래프 인스턴스 보유)

frontend/
  src/
    index.css             # Tailwind v4 @theme 디자인 토큰
    App.tsx               # currentStep 기반 화면 라우팅
    types/index.ts        # TypeScript 인터페이스
    store/useAppStore.ts  # Zustand 전역 상태
    api/client.ts         # 9개 API 래퍼 함수
    hooks/useSSE.ts       # EventSource SSE 훅
    components/           # Header, Footer, StepIndicator, ProgressSection
    screens/              # DataSource, Loading, KoReview, Translating, FinalReview, Done

agents/
  graph.py                # LangGraph StateGraph (8 Node + HITL 2곳)
  state.py                # LocalizationState TypedDict
  prompts.py              # 시스템 프롬프트 (번역/검수/한국어교정)
  nodes/                  # data_backup, context_glossary, translator, reviewer, writer

config/
  constants.py            # 상수 (CHUNK_SIZE=15, LLM_MODEL, 태그패턴 등)
  glossary.py             # 언어별 Glossary 딕셔너리

utils/
  sheets.py               # gspread 래퍼 (인증, 로드, 백업, Batch Write, Backoff, 셀 포맷팅)
  validation.py           # 정규식 태그 검증 + Glossary 후처리
  diff_report.py          # Diff 리포트 CSV 생성
  cost_tracker.py         # 토큰/비용 추적 (CostTracker 클래스)

app.py                    # (Legacy) Streamlit 메인 앱
utils/ui_components.py    # (Legacy) Streamlit UI 컴포넌트
```

## UI 아키텍처 (React)
- **디자인 시스템**: Stitch 기반 — Sky Blue (#0ea5e9) + Inter 폰트 + Material Symbols Outlined
- **디자인 토큰 참조**: `memory/ui-design-rules.md` (색상/타이포/그림자/컴포넌트 상세)
- **화면 흐름**: idle → loading → ko_review → translating → final_review → done
- **스텝 인디케이터**: 5단계 (Load, KR Review, Translating, Multi-Review, Complete)
- **실시간 업데이트**: SSE (`/api/stream/{sessionId}`) → EventSource → Zustand 상태 갱신
- **HITL**: ko_review에서 Accept/Reject → POST `/api/approve-ko`, final_review → POST `/api/approve-final`
- **번역 취소**: POST `/api/cancel/{sessionId}` → 그래프 재생성 → ko_review 복귀

## API 엔드포인트 (FastAPI, /api prefix)
| Method | Path | 설명 |
|--------|------|------|
| POST | /connect | 시트 연결 → 시트 목록 + 봇 이메일 |
| POST | /start | 세션 생성 + 데이터 로드 + 백업 |
| GET | /stream/{id} | SSE 실시간 이벤트 스트림 |
| POST | /approve-ko/{id} | HITL 1 승인/거부 → 번역 시작 |
| POST | /approve-final/{id} | HITL 2 승인 → 시트 업데이트 / 거부 → 원복 |
| POST | /cancel/{id} | 번역 취소 → ko_review 복귀 |
| GET | /state/{id} | 세션 상태 조회 |
| GET | /download/{id}/{type} | CSV 다운로드 (backup, ko_report, translation_report, failed, logs) |
| GET | /config | 저장된 설정 조회 |
| PUT | /config | 설정 저장 |

## 구현 워크플로우 규칙
- 각 구현 단계(Phase)마다 바로 코드를 작성하지 않는다
- 먼저 해당 단계의 점검 체크리스트를 작성하고, 점검을 통과한 뒤 구현에 들어간다

## 핵심 규칙
- 포맷팅 태그({변수}, <color>, \n 등) 보존은 정규식 하드코딩으로 검증 (LLM 의존 X)
- JA 등급명은 Glossary 강제 치환 (의역 절대 금지)
- Google Sheets: 개별 cell.update() 금지 → 반드시 Batch Update
- Google Sheets: 1회 전체 로드 후 DataFrame 내에서 작업
- HITL 2단계: 한국어 검수 승인 → 최종 번역 승인 (interrupt 2곳)
- LLM 호출은 반드시 청크 배치(CHUNK_SIZE=15) + timeout=120s 적용
- Reviewer도 청크 배치 호출 (개별 호출 절대 금지 — rate limit 및 멈춤 원인)
- 번역 에러 시 그래프 재생성 후 idle로 복구 (translating 멈춤 상태 방지)
- Writer: 원본 값과 비교하여 실제 변경된 셀만 시트 업데이트 & 컬러링
- Writer: 같은 Key가 일부 언어 성공 + 일부 실패 시, Tool_Status는 "검수실패"로 단일 설정
- 한국어 검수 제안 0건 시 자동 승인 (빈 카드 표시 안 함)
- 시트 URL/백업폴더는 `.app_config.json`에 영속 저장 (gitignore 포함)
- Translator: LLM JSON 파싱 후 `\n`→`\\n`, `\t`→`\\t` 리터럴 복원 필수

## LLM 설정
- **모델**: `xai/grok-4-1-fast-reasoning`
- **CHUNK_SIZE**: 15행 (번역/검수 모두 동일)
- **timeout**: 120초 (모든 LLM 호출)
- **가격**: input $0.20/1M, output $0.50/1M, cached $0.05/1M

## Secrets 위치
**React+FastAPI (현재)**:
- `.env` — `XAI_API_KEY`, `GCP_SERVICE_ACCOUNT_JSON_PATH`
- `.gcp_service_account.json` — GCP 서비스 계정 JSON
- `backend/config.py`의 `get_xai_api_key()`, `get_gcp_credentials()`로 접근

**Legacy Streamlit**:
- `.streamlit/secrets.toml` — XAI_API_KEY + gcp_service_account

## 봇 이메일 (시트 편집자 초대 필요)
`local-agent@local-488014.iam.gserviceaccount.com`

## 금지 시트 (UI 드롭다운 노출 금지)
사용법, Texture, 수정금지_Common

## 개발서버 실행
```bash
# 동시 실행 (FastAPI:8000 + Vite:5173)
./run_dev.sh

# 또는 개별 실행
python3 -m uvicorn backend.main:app --reload --port 8000
cd frontend && npm run dev
```

## 참고 문서
- PRD_v2.md: 상세 요구사항
- DEVELOPMENT_PLAN.md: 구현 계획서
- docs/plans/2026-02-21-react-fastapi-migration.md: React 마이그레이션 계획
- memory/ui-design-rules.md: Stitch 기반 UI 디자인 토큰/컴포넌트 규칙
