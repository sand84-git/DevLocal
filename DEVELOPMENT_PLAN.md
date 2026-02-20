# 개발 계획: 게임 로컬라이징 자동화 툴

> PRD v2 기반 구현 계획서

---

## 프로젝트 구조

```
game-localization-tool/
├── .streamlit/
│   └── config.toml          # Streamlit 테마 설정 (Warm & Minimalist)
├── app.py                    # Streamlit 메인 앱 (UI + 이벤트 핸들링)
├── agents/
│   ├── __init__.py
│   ├── graph.py              # LangGraph 워크플로우 정의 (5 Node + HITL)
│   ├── state.py              # LocalizationState TypedDict
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── data_backup.py    # Node 1: 데이터 로드 & 백업 (유틸리티)
│   │   ├── context_glossary.py  # Node 2: 컨텍스트 & 글로서리 셋업 (유틸리티)
│   │   ├── translator.py     # Node 3: 번역 (LLM)
│   │   ├── reviewer.py       # Node 4: 검수 (LLM + Regex)
│   │   └── writer.py         # Node 5: 시트 업데이트 (유틸리티)
│   └── prompts.py            # 시스템 프롬프트 (세계관, 톤앤매너, 가이드라인)
├── utils/
│   ├── __init__.py
│   ├── sheets.py             # gspread 래퍼 (Batch Read/Write, 인증)
│   ├── validation.py         # 정규식 태그 검증 + Glossary 후처리
│   ├── diff_report.py        # Diff 리포트 생성 (CSV)
│   └── cost_tracker.py       # 토큰/비용 추적
├── config/
│   ├── glossary.py           # 언어별 Glossary 딕셔너리
│   └── constants.py          # 상수 (금지 시트, 상태값, 태그 패턴 등)
├── requirements.txt
├── PRD_v2.md
└── DEVELOPMENT_PLAN.md
```

---

## 구현 단계 (총 7단계)

### Phase 1: 프로젝트 기초 세팅
**목표**: 프로젝트 스켈레톤, 의존성, Streamlit 테마 구성

**작업 내용**:
1. `requirements.txt` 작성
   - `streamlit`, `langgraph`, `langchain-core`, `gspread`, `google-auth`, `litellm`, `pandas`, `nest_asyncio`
2. `.streamlit/config.toml` 작성
   - 컬러 팔레트: 메인 배경 `#F6F5F0`, 포인트 `#C85A32`, 텍스트 `#2C2C2C`
3. `config/constants.py` 작성
   - 금지 시트 목록, 상태값 enum, 태그 패턴 리스트
4. `config/glossary.py` 작성
   - 언어별 Glossary 딕셔너리 구조

**산출물**: 실행 가능한 빈 Streamlit 앱 + 테마 적용 확인

---

### Phase 2: Google Sheets 연동 모듈
**목표**: gspread 인증, 데이터 로드/쓰기, Tool_Status 컬럼 관리

**작업 내용**:
1. `utils/sheets.py` 구현
   - `connect_to_sheet(url)`: st.secrets 기반 인증 + 시트 연결
   - `get_worksheet_names(spreadsheet)`: 금지 시트 필터링된 시트 목록 반환
   - `load_sheet_data(worksheet)`: 1회 전체 로드 → DataFrame 변환 (헤더 이름 기반)
   - `ensure_tool_status_column(worksheet)`: Tool_Status 컬럼 존재 확인/생성
   - `batch_update_sheet(worksheet, updates)`: Batch Write 래퍼
   - `create_backup_csv(df, sheet_name)`: 백업 CSV 생성 + 파일 경로 반환
2. exponential backoff 재시도 로직 포함

**검증**: 실제 구글 시트에 연결하여 데이터 로드/쓰기 테스트

---

### Phase 3: 검증 유틸리티 모듈
**목표**: 정규식 태그 검증, Glossary 후처리, Diff 리포트 생성

**작업 내용**:
1. `utils/validation.py` 구현
   - `validate_tags(source_ko, translated)`: 정규식으로 태그 개수/문자열 동일성 검증
   - `apply_glossary_postprocess(text, lang)`: JA 등급명 강제 치환
   - `check_glossary_compliance(text, lang)`: Glossary 준수 여부 검증
2. `utils/diff_report.py` 구현
   - `generate_ko_diff_report(original, revised)`: 한국어 변경 리포트 CSV
   - `generate_translation_diff_report(old_translations, new_translations)`: 번역 변경 리포트 CSV
3. `utils/cost_tracker.py` 구현
   - LiteLLM 응답에서 토큰 사용량 추적

**검증**: 단위 테스트로 태그 검증 로직 확인 (정상 케이스 + 에러 케이스)

---

### Phase 4: LangGraph State 및 에이전트 프롬프트
**목표**: 상태 객체 정의, 에이전트 시스템 프롬프트 작성

**작업 내용**:
1. `agents/state.py` 구현
   - `LocalizationState` TypedDict (PRD 7.1 참조)
2. `agents/prompts.py` 구현
   - `SYSTEM_PROMPT_TRANSLATOR`: 세계관 + 톤앤매너 + Glossary 가이드 + Shared Comments 활용 지시
   - `SYSTEM_PROMPT_REVIEWER`: 크로스체크 가이드 + 변경 사유 생성 지시
   - `SYSTEM_PROMPT_KO_PROOFREADER`: 한국어 맞춤법/띄어쓰기 검수 지시

**검증**: 프롬프트를 직접 LLM에 테스트하여 번역 품질 확인

---

### Phase 5: LangGraph 워크플로우 (5 Node + HITL)
**목표**: 핵심 파이프라인 구현

**작업 내용**:
1. `agents/nodes/data_backup.py` (Node 1)
   - 시트 데이터 로드 + 백업 생성 (LLM 미사용)
2. `agents/nodes/context_glossary.py` (Node 2)
   - 시놉시스/톤앤매너/Glossary 가이드라인 조합 (LLM 미사용)
3. `agents/nodes/translator.py` (Node 3)
   - 청크 단위 번역 (LiteLLM → grok-4-1-fast-reasoning)
   - Shared Comments 컨텍스트 주입
   - 모드 A/B에 따른 대상 행 필터링
4. `agents/nodes/reviewer.py` (Node 4)
   - 정규식 태그 검증 (하드코딩)
   - Glossary 후처리 (JA 등급명 강제 치환)
   - AI 품질 검증 (LLM 호출)
   - 변경 사유 자동 생성 (LLM 호출)
   - 실패 시 Node 3 피드백 (최대 3회, 초과 시 `검수실패` 마킹)
5. `agents/nodes/writer.py` (Node 5)
   - HITL 2 승인 대기 후 Batch Update 실행
   - Tool_Status를 `최종완료`로 업데이트
6. `agents/graph.py`
   - LangGraph StateGraph 구성
   - Node 3 ↔ Node 4 조건부 순환 (retry_count 기반)
   - `interrupt()` 2곳: Step 1 한국어 검수 후 / Step 3 최종 승인 전
   - `MemorySaver` 체크포인터 연결
   - 동기 API (`graph.invoke()`) 사용

**검증**: 소규모 테스트 시트(5~10행)로 전체 파이프라인 E2E 테스트

---

### Phase 6: Streamlit UI 구현
**목표**: 사이드바 + 메인 대시보드 + HITL 인터랙션

**작업 내용**:
1. `app.py` 구현
   - **사이드바**:
     - 구글 시트 URL 입력 (`st.text_input`)
     - 시트 선택 드롭다운 (`st.selectbox`, 금지 시트 필터링)
     - 타겟 언어 선택 (`st.multiselect`, 기본값: EN, JA)
     - 모드 선택 (`st.radio`: 모드 A / 모드 B)
     - [작업 시작] 버튼 (`st.button`)
   - **메인 영역**:
     - 봇 이메일 초대 안내 문구 (상단)
     - Progress Bar (`st.progress`)
     - 실시간 로그 (`st.expander` + `st.text_area`)
     - HITL 1: 한국어 변경 리포트 DataFrame + 다운로드 버튼 + 승인/반려 버튼
     - HITL 2: 번역 변경 리포트 DataFrame + 다운로드 버튼 + 승인/반려 버튼
     - 백업 CSV 다운로드 버튼
     - 토큰/비용 요약
   - **커스텀 CSS**:
     - `st.markdown(unsafe_allow_html=True)`로 Warm & Minimalist 스타일 주입
     - 카드 컴포넌트, 둥근 모서리, 옅은 그림자
2. `st.session_state` 관리
   - `thread_id`: LangGraph 체크포인터용
   - `current_step`: UI 단계 제어 (idle → ko_review → translating → final_review → done)
   - `backup_df`: 백업 데이터
   - `ko_report_df`, `translation_report_df`: 리포트 데이터

**검증**: 로컬에서 `streamlit run app.py`로 전체 플로우 수동 테스트

---

### Phase 7: 통합 테스트 및 배포
**목표**: E2E 테스트 + Streamlit Cloud 배포

**작업 내용**:
1. 테스트 시나리오 실행
   - 모드 A: 기존 번역이 있는 시트에서 전체 재번역 → Diff 확인 → 승인
   - 모드 B: 빈칸만 있는 시트에서 신규 번역 → 승인
   - 3회 재시도 실패 케이스 → `검수실패` 마킹 확인
   - HITL 1 반려 → 원본 그대로 번역 진행 확인
   - HITL 2 반려 → 시트 미변경 확인
   - 태그 포함 텍스트 (`<color=#FF0000>{player_name}\n`) 번역 후 태그 보존 확인
   - JA 등급명 강제 치환 확인
2. Streamlit Cloud 배포
   - GitHub 리포지토리 연결
   - `st.secrets` 설정 (Google Service Account JSON + XAI_API_KEY)
   - 배포 후 동작 확인

---

## 구현 순서 및 의존 관계

```
Phase 1 (기초 세팅)
   ↓
Phase 2 (Google Sheets) ──┐
   ↓                      │
Phase 3 (검증 유틸리티) ───┤
   ↓                      │
Phase 4 (State/프롬프트) ──┘
   ↓
Phase 5 (LangGraph 파이프라인) ← Phase 2, 3, 4 모두 필요
   ↓
Phase 6 (Streamlit UI)
   ↓
Phase 7 (통합 테스트 & 배포)
```

Phase 2, 3, 4는 서로 독립적이므로 **병렬 작업 가능**.
Phase 5는 2, 3, 4가 모두 완료되어야 진행 가능.

---

## 핵심 리스크 및 완화 전략

| 리스크 | 완화 전략 |
|---|---|
| Streamlit 재실행 시 상태 소실 | MemorySaver + st.session_state.thread_id |
| asyncio 이벤트 루프 충돌 | graph.invoke() 동기 호출 우선, 필요 시 nest_asyncio |
| Google Sheets Rate Limit | 1회 전체 로드 + DataFrame 내 작업 + Batch Write |
| 태그 누락으로 클라이언트 크래시 | 정규식 하드코딩 검증 (LLM 의존 X) |
| 대량 데이터 처리 시 타임아웃 | 청크 단위 처리 + Progress Bar + 재개 기능 |
| 백업 파일 손실 (Streamlit Cloud) | 즉시 다운로드 버튼 제공 + session_state 보관 |
