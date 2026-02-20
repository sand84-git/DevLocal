# CLAUDE.md — 게임 로컬라이징 자동화 툴

## 프로젝트 개요
구글 스프레드시트 기반 게임 텍스트(한국어)를 AI(Grok 4.1 Fast Reasoning)로 다국어(EN, JA) 자동 번역/검수하는 Streamlit 웹앱.

## 기술 스택
- **Frontend**: Streamlit (Indigo + Dark Sidebar SaaS 테마)
- **Agent Orchestration**: LangGraph 0.6 (8 Node + HITL 2곳 interrupt)
- **Google Sheets**: gspread (Batch Read/Write + Exponential Backoff)
- **LLM**: LiteLLM → xai/grok-4-1-fast-reasoning (timeout=120s)
- **Data**: Pandas

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
app.py                    # Streamlit 메인 앱 (stream_mode="updates" 실시간 UI)
agents/
  graph.py                # LangGraph StateGraph (8 Node + HITL 2곳)
  state.py                # LocalizationState TypedDict
  prompts.py              # 시스템 프롬프트 (번역/검수/한국어교정)
  nodes/
    data_backup.py        # Node 1: 데이터 확인 & 로그
    context_glossary.py   # Node 2: 컨텍스트 & 글로서리 셋업
    translator.py         # Node 3: 청크 단위 번역 (LLM)
    reviewer.py           # Node 4: 정규식+Glossary+AI 검수 (청크 배치 LLM)
    writer.py             # Node 5: Batch Update 목록 생성
config/
  constants.py            # 상수 (CHUNK_SIZE=15, LLM_MODEL, 태그패턴 등)
  glossary.py             # 언어별 Glossary 딕셔너리
utils/
  sheets.py               # gspread 래퍼 (인증, 로드, 백업, Batch Write, Backoff)
  validation.py           # 정규식 태그 검증 + Glossary 후처리
  diff_report.py          # Diff 리포트 CSV 생성
  ui_components.py        # 모던 SaaS UI 컴포넌트 (CSS, 카드, 스텝 인디케이터)
  cost_tracker.py         # 토큰/비용 추적
```

## 핵심 규칙
- 포맷팅 태그({변수}, <color>, \n 등) 보존은 정규식 하드코딩으로 검증 (LLM 의존 X)
- JA 등급명은 Glossary 강제 치환 (의역 절대 금지)
- Google Sheets: 개별 cell.update() 금지 → 반드시 Batch Update
- Google Sheets: 1회 전체 로드 후 DataFrame 내에서 작업
- HITL 2단계: 한국어 검수 승인 → 최종 번역 승인 (interrupt 2곳)
- LLM 호출은 반드시 청크 배치(CHUNK_SIZE=15) + timeout=120s 적용
- Reviewer도 청크 배치 호출 (개별 호출 절대 금지 — rate limit 및 멈춤 원인)
- 번역 에러 시 그래프 재생성 후 idle로 복구 (translating 멈춤 상태 방지)

## LLM 설정
- **모델**: `xai/grok-4-1-fast-reasoning`
- **CHUNK_SIZE**: 15행 (번역/검수 모두 동일)
- **timeout**: 120초 (모든 LLM 호출)
- **가격**: input $0.20/1M, output $0.50/1M, cached $0.05/1M

## Secrets 위치
`.streamlit/secrets.toml` (gitignore 포함)
- `XAI_API_KEY`: Grok API 키
- `[gcp_service_account]`: Google Service Account JSON

## 봇 이메일 (시트 편집자 초대 필요)
`local-agent@local-488014.iam.gserviceaccount.com`

## 금지 시트 (UI 드롭다운 노출 금지)
사용법, Texture, 수정금지_Common

## 참고 문서
- PRD_v2.md: 상세 요구사항
- DEVELOPMENT_PLAN.md: 구현 계획서
