# API 레퍼런스 (FastAPI, /api prefix)

## 엔드포인트
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

## SSE 이벤트 타입 (/api/stream/{id})
| 이벤트 | 데이터 | 발생 시점 |
|--------|--------|-----------|
| node_update | `{node, step, logs}` | 각 그래프 노드 완료 시 |
| original_data | `{rows}` | data_backup 완료 후 원본 데이터 전송 |
| ko_review_chunk | `{chunk_results, progress}` | ko_review 드립피드 (1항목씩) |
| ko_review_ready | `{results, count, report}` | ko_review 완료 → HITL 1 대기 |
| translation_chunk | `{chunk_results, progress}` | translator 드립피드 (1항목씩) |
| review_chunk | `{chunk_results, progress}` | reviewer 드립피드 (1항목씩) |
| final_review_ready | `{review_results, failed_rows, report, cost}` | 번역+검수 완료 → HITL 2 대기 |
| done | `{}` | 모든 작업 완료 |
| error | `{message}` | 에러 발생 |
| ping | `{}` | 5분 타임아웃 방지 keepalive |

## Pydantic 스키마
- 요청/응답 모델: `backend/api/schemas.py`
- 세션 상태: `backend/api/session_manager.py`
- 그래프 상태: `agents/state.py` (LocalizationState TypedDict)
