# CLAUDE.md — 게임 로컬라이징 자동화 툴

## 프로젝트 개요
구글 스프레드시트 기반 게임 텍스트(한국어)를 AI(Grok 4.1 Fast Reasoning)로 다국어(EN, JA) 자동 번역/검수하는 Streamlit 웹앱.

## 기술 스택
- **Frontend**: Streamlit (Warm & Minimalist 테마)
- **Agent Orchestration**: LangGraph (5 Node + HITL 2곳 interrupt)
- **Google Sheets**: gspread (Batch Read/Write)
- **LLM**: LiteLLM → xai/grok-4-1-fast-reasoning
- **Data**: Pandas

## 프로젝트 구조
```
app.py                    # Streamlit 메인 앱
agents/
  graph.py                # LangGraph StateGraph (5 Node + HITL)
  state.py                # LocalizationState TypedDict
  prompts.py              # 시스템 프롬프트 (번역/검수/한국어교정)
  nodes/
    data_backup.py        # Node 1: 데이터 로드 & 백업
    context_glossary.py   # Node 2: 컨텍스트 & 글로서리 셋업
    translator.py         # Node 3: 청크 단위 번역 (LLM)
    reviewer.py           # Node 4: 정규식+Glossary+AI 검수 (LLM)
    writer.py             # Node 5: Batch Update 준비
config/
  constants.py            # 상수 (금지시트, 상태값, 태그패턴, LLM설정)
  glossary.py             # 언어별 Glossary 딕셔너리
utils/
  sheets.py               # gspread 래퍼 (인증, 로드, 백업, Batch Write)
  validation.py           # 정규식 태그 검증 + Glossary 후처리
  diff_report.py          # Diff 리포트 CSV 생성
  cost_tracker.py         # 토큰/비용 추적
```

## 핵심 규칙
- 포맷팅 태그({변수}, <color>, \n 등) 보존은 정규식 하드코딩으로 검증 (LLM 의존 X)
- JA 등급명은 Glossary 강제 치환 (의역 절대 금지)
- Google Sheets: 개별 cell.update() 금지 → 반드시 Batch Update
- Google Sheets: 1회 전체 로드 후 DataFrame 내에서 작업
- HITL 2단계: 한국어 검수 승인 → 최종 번역 승인 (interrupt 2곳)
- Reviewer 3회 재시도 실패 시 '검수실패' 마킹 후 다음 행 진행

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
