# 개발 계획: 게임 로컬라이징 자동화 툴

> PRD v2 기반 구현 계획서
> **상태: 전 Phase 구현 완료 (2026-02-21) + React+FastAPI 마이그레이션 완료 (2026-02-22)**

---

## 프로젝트 구조 (최종)

```
DevLocal/
├── .streamlit/
│   ├── config.toml          # Streamlit 테마 설정 (Indigo + Dark Sidebar)
│   └── secrets.toml          # API 키 + GCP 서비스 계정 (gitignore)
├── .app_config.json          # 시트 URL/백업폴더 영속 저장 (gitignore)
├── app.py                    # Streamlit 메인 앱 (stream_mode="updates" 실시간 UI)
├── agents/
│   ├── graph.py              # LangGraph StateGraph (8 Node + HITL 2곳)
│   ├── state.py              # LocalizationState TypedDict
│   ├── prompts.py            # 시스템 프롬프트 (번역/검수/한국어교정)
│   └── nodes/
│       ├── data_backup.py    # Node 1: 데이터 확인 & 로그 (유틸리티)
│       ├── context_glossary.py  # Node 2: 컨텍스트 & 글로서리 셋업 (유틸리티)
│       ├── translator.py     # Node 3: 청크 단위 번역 (LLM)
│       ├── reviewer.py       # Node 4: 정규식+Glossary+AI 검수 (LLM)
│       └── writer.py         # Node 5: Batch Update 목록 생성 (유틸리티)
├── config/
│   ├── constants.py          # 상수 (CHUNK_SIZE, LLM_MODEL, 태그패턴 등)
│   └── glossary.py           # 언어별 Glossary 딕셔너리
├── utils/
│   ├── sheets.py             # gspread 래퍼 (인증, 로드, 백업, Batch Write, Backoff, 셀 포맷팅)
│   ├── validation.py         # 정규식 태그 검증 + Glossary 후처리
│   ├── diff_report.py        # Diff 리포트 CSV 생성
│   ├── ui_components.py      # SaaS UI 컴포넌트 (CSS, 카드, 스텝 인디케이터+프로그레스)
│   └── cost_tracker.py       # 토큰/비용 추적
├── requirements.txt
├── PRD_v2.md
├── DEVELOPMENT_PLAN.md
└── CLAUDE.md
```

---

## 구현 단계 (총 8단계) — 전체 완료

### Phase 1: 프로젝트 기초 세팅 — 완료
- `requirements.txt`, `.streamlit/config.toml`, `config/constants.py`, `config/glossary.py`
- 상수: CHUNK_SIZE=15, MAX_RETRY_COUNT=3, TAG_PATTERNS 10개, LLM_MODEL, 금지 시트 목록

### Phase 2: Google Sheets 연동 모듈 — 완료
- `utils/sheets.py`: connect, load, ensure_tool_status, batch_update, batch_format, backup
- Exponential Backoff (5회, 1~16초)
- **추가 구현**: `batch_format_cells()` — 변경된 셀 배경색 하이라이트 (노랑/빨강/파랑)

### Phase 3: 검증 유틸리티 모듈 — 완료
- `utils/validation.py`: validate_tags, apply_glossary_postprocess, check_glossary_compliance
- `utils/diff_report.py`: generate_ko_diff_report, generate_translation_diff_report
- `utils/cost_tracker.py`: CostTracker 클래스 (track, summary, total_cost)

### Phase 4: LangGraph State 및 에이전트 프롬프트 — 완료
- `agents/state.py`: LocalizationState TypedDict (45줄, 내부 전달용 `_updates`/`_needs_retry` 포함)
- `agents/prompts.py`: Translator, Reviewer, Ko Proofreader 프롬프트 (`\n` 보존 규칙 포함)

### Phase 5: LangGraph 워크플로우 — 완료
- **PRD 대비 변경**: 5 Node → 8 Node (ko_review + ko_approval 분리, final_approval 분리)
- `graph.py`: ko_review_node (AI 분석만), ko_approval_node (interrupt), final_approval_node (interrupt)
- `translator.py`: 청크 배치 번역 + 재시도 모드 (`_translate_retry`) + `\n`/`\t` 리터럴 복원
- `reviewer.py`: 3단계 검증 (Glossary 후처리 → 태그 정규식 → AI 품질) + CHUNK_SIZE 배치
- `writer.py`: 원본 비교 → 변경 셀만 업데이트, Tool_Status 충돌 방지 (failed_keys 우선)
- 조건부 엣지: should_retry (reviewer → translator 재순환), should_write (approved → writer / rejected → END)

### Phase 6: Streamlit UI 구현 — 완료
- **PRD 대비 변경**: Warm & Minimalist → Indigo + Dark Sidebar SaaS 테마
- `utils/ui_components.py`: 커스텀 CSS (~700줄), 스텝 인디케이터 (progress 통합), 카드, 로그 터미널
- `app.py`: stream_mode="updates" 실시간 프로그레스, 번역 취소 기능, 시트 URL 영속 저장
- **추가 구현**: 한국어 검수 0건 자동 승인, 스트리밍 영역 + 취소 버튼 레이아웃

### Phase 7: 통합 테스트 — 완료
- 전체 파일 구문/임포트 검증 (16개 파일)
- 그래프 빌드 + 8 노드 연결 검증
- 태그 검증 엣지케이스 16건 PASS
- Glossary 후처리 5건 + 컴플라이언스 4건 PASS
- Writer 원본 비교 로직 + Tool_Status 충돌 방지 PASS
- 시트 배치 인덱스 매핑 검증 PASS
- 상태 머신 전환 (6 step) + 에러 복구 (4곳) 검증
- Translator `\n`/`\t` 복원 PASS
- Reviewer 3회 재시도 + 검수실패 로직 PASS

### Phase 8: React+FastAPI 마이그레이션 — 완료 (2026-02-22)
**Backend (De-Streamlit)**:
- `backend/config.py`: `.env` 기반 환경변수 관리 (st.secrets 대체)
- `backend/main.py`: FastAPI 앱 (CORS, /api 라우터)
- `backend/api/routes.py`: 10개 REST+SSE 엔드포인트
- `backend/api/schemas.py`: Pydantic 요청/응답 모델
- `backend/api/session_manager.py`: LRU 세션 관리 (max 10, 그래프 인스턴스 보유)
- `utils/drip_feed.py`: SSE 드립피드 유틸리티 (150ms 간격 항목별 전송)

**Frontend (React SPA)**:
- React 19 + Vite 7 + TypeScript + Tailwind CSS v4 + Zustand
- 4 화면: DataSourceScreen, KoReviewWorkspace, TranslationWorkspace, DoneScreen
- 5 컴포넌트: Header, Footer, StepIndicator, ConfirmModal, SettingsModal
- 4 훅: useSSE (실시간 스트리밍), useSheetQueue (All Sheets), useNavigationGuard, useCountUp
- SSE 실시간 스트리밍 + 자동 재연결 (지수 백오프 5회)
- 세션 복원 (localStorage + getSessionState 동기화)
- 통합 워크스페이스: loading↔ko_review, translating↔final_review 그룹 내 부드러운 전환
- All Sheets 모드: 전체 시트 자동 순차 처리 (2초 딜레이)
- Settings 모달: Glossary/시놉시스/톤앤매너/커스텀 프롬프트 웹 편집
- Stitch 기반 디자인: Sky Blue + Inter 폰트 + Material Symbols Outlined
- LCS Diff 하이라이팅, 캐스케이드 애니메이션, 프로그레스 시머 효과

---

## 구현 순서 및 의존 관계

```
Phase 1 (기초 세팅) ✅
   ↓
Phase 2 (Google Sheets) ✅ ──┐
   ↓                         │
Phase 3 (검증 유틸리티) ✅ ───┤
   ↓                         │
Phase 4 (State/프롬프트) ✅ ──┘
   ↓
Phase 5 (LangGraph 파이프라인) ✅
   ↓
Phase 6 (Streamlit UI) ✅
   ↓
Phase 7 (통합 테스트) ✅
   ↓
Phase 8 (React+FastAPI 마이그레이션) ✅
```

---

## 핵심 리스크 및 완화 전략 (구현 결과)

| 리스크 | 완화 전략 | 구현 상태 |
|---|---|---|
| Streamlit 재실행 시 상태 소실 | MemorySaver + st.session_state.thread_id | 완료 |
| asyncio 이벤트 루프 충돌 | graph.invoke()/graph.stream() 동기 호출 | 완료 |
| Google Sheets Rate Limit | 1회 전체 로드 + DataFrame 내 작업 + Batch Write + Backoff | 완료 |
| 태그 누락으로 클라이언트 크래시 | 정규식 하드코딩 검증 (10개 패턴) + 3회 재시도 | 완료 |
| 대량 데이터 처리 시 타임아웃 | CHUNK_SIZE=15 + 120s timeout + 실시간 프로그레스 | 완료 |
| 백업 파일 손실 (Streamlit Cloud) | 로컬 저장 + 다운로드 버튼 + session_state 보관 | 완료 |
| LLM이 `\n` 태그를 실제 개행으로 변환 | JSON 파싱 후 `.replace('\n', '\\n')` 복원 | 완료 |
| 같은 Key 성공+실패 시 Tool_Status 충돌 | failed_keys 우선 수집 → 실패 Key는 completed 스킵 | 완료 |
| SSE 연결 끊김 시 상태 유실 | 자동 재연결 (지수 백오프 5회) + getSessionState() 동기화 | 완료 |
| 브라우저 새로고침 시 세션 유실 | localStorage sessionId + 세션 복원 로직 | 완료 |
| 대량 시트 순차 처리 | All Sheets 모드 + useSheetQueue 훅 (2초 딜레이) | 완료 |
