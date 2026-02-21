"""LangGraph 워크플로우 정의 — 6 Node + HITL 2곳 interrupt"""

import re
import json
import litellm
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from agents.state import LocalizationState
from agents.prompts import build_ko_proofreader_prompt
from agents.nodes.data_backup import data_backup_node
from agents.nodes.context_glossary import context_glossary_node
from agents.nodes.translator import translator_node
from utils.drip_feed import drip_feed_emit
from agents.nodes.reviewer import reviewer_node
from agents.nodes.writer import writer_node
from backend.config import get_xai_api_key
from config.constants import LLM_MODEL, REQUIRED_COLUMNS, CHUNK_SIZE, TAG_PATTERNS


# ── 한국어 검수 노드 (AI 분석만, interrupt 없음) ─────────────────────

def ko_review_node(state: LocalizationState, config: RunnableConfig) -> dict:
    """
    한국어 맞춤법/띄어쓰기 검수 — AI 분석만 수행.
    interrupt는 별도 ko_approval_node에서 처리.
    """
    original_data = state.get("original_data", [])
    logs = list(state.get("logs", []))
    total_input_tokens = state.get("total_input_tokens", 0)
    total_output_tokens = state.get("total_output_tokens", 0)

    # 청크별 이벤트 emitter (없으면 무시)
    emitter = config.get("configurable", {}).get("event_emitter") if config else None

    api_key = get_xai_api_key()

    # 한국어 원문 수집
    ko_rows = []
    for row in original_data:
        key = row.get(REQUIRED_COLUMNS["key"], "")
        ko_text = row.get(REQUIRED_COLUMNS["korean"], "")
        if ko_text:
            ko_rows.append({"key": key, REQUIRED_COLUMNS["korean"]: ko_text})

    logs.append(f"[한국어 검수] 대상: {len(ko_rows)}행")

    # 청크 단위로 AI 검수
    ko_review_results = []
    system_prompt = build_ko_proofreader_prompt()
    total_ko_rows = len(ko_rows)
    processed_count = 0

    for chunk_start in range(0, len(ko_rows), CHUNK_SIZE):
        chunk = ko_rows[chunk_start:chunk_start + CHUNK_SIZE]
        user_content = "\n\n".join(
            f"Key: {r['key']}\nKorean: {r[REQUIRED_COLUMNS['korean']]}"
            for r in chunk
        )

        try:
            response = litellm.completion(
                model=LLM_MODEL,
                api_key=api_key,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                timeout=120,
            )

            total_input_tokens += getattr(response.usage, "prompt_tokens", 0)
            total_output_tokens += getattr(
                response.usage, "completion_tokens", 0
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

            items = json.loads(content)
            # LLM 필드 변환: changes → comment, has_issue 추가
            for item in items:
                item["comment"] = item.pop("changes", "")
                item["has_issue"] = item.get("original", "") != item.get("revised", "")
            ko_review_results.extend(items)

            # 청크별 부분 결과를 1행씩 drip-feed 전송
            processed_count += len(chunk)
            if emitter:
                drip_feed_emit(
                    emitter,
                    "ko_review_chunk",
                    items,
                    progress_base=processed_count - len(items),
                    total=total_ko_rows,
                )

        except Exception as e:
            processed_count += len(chunk)
            logs.append(f"[한국어 검수] 오류: {e}")

    # 태그 보존 후처리: AI가 태그를 삭제/변경한 경우 원본에서 복원
    original_map = {r["key"]: r[REQUIRED_COLUMNS["korean"]] for r in ko_rows}
    validated_results = []
    restored_count = 0

    for item in ko_review_results:
        key = item.get("key", "")
        original = original_map.get(key, "")
        revised = item.get("revised", "")

        if not original or not revised:
            validated_results.append(item)
            continue

        # 각 태그 패턴에 대해 원본과 수정본의 태그 일치 검증
        tag_broken = False
        for pattern in TAG_PATTERNS:
            orig_tags = re.findall(pattern, original)
            rev_tags = re.findall(pattern, revised)
            if sorted(orig_tags) != sorted(rev_tags):
                tag_broken = True
                break

        if tag_broken:
            # 태그가 손상된 수정은 버림 (원본 유지)
            restored_count += 1
        else:
            validated_results.append(item)

    if restored_count:
        logs.append(
            f"[한국어 검수] 태그 손상 수정 {restored_count}건 제외 (원본 유지)"
        )

    ko_review_results = validated_results
    logs.append(f"[한국어 검수] 최종 수정 제안: {len(ko_review_results)}건")

    return {
        "ko_review_results": ko_review_results,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "logs": logs,
    }


# ── 한국어 검수 승인 노드 (HITL 1 interrupt) ────────────────────────

def ko_approval_node(state: LocalizationState) -> dict:
    """
    한국어 검수 결과를 사용자에게 보여주고 승인 대기 (HITL 1).
    """
    ko_review_results = state.get("ko_review_results", [])
    logs = list(state.get("logs", []))

    # HITL 1 — 사용자 승인 대기
    approval = interrupt({
        "type": "ko_review",
        "results": ko_review_results,
        "count": len(ko_review_results),
    })

    logs.append(f"[한국어 검수] 사용자 결정: {approval}")

    return {
        "ko_approval_result": approval,
        "logs": logs,
    }


# ── 최종 승인 노드 (HITL 2 interrupt 포함) ────────────────────────────

def final_approval_node(state: LocalizationState) -> dict:
    """
    번역 검수 완료 후, 시트에 쓰기 전 최종 승인을 기다림 (HITL 2).
    """
    review_results = state.get("review_results", [])
    failed_rows = state.get("failed_rows", [])
    logs = list(state.get("logs", []))

    logs.append(
        f"[최종 승인 대기] 번역 완료: {len(review_results)}건, "
        f"실패: {len(failed_rows)}건"
    )

    # HITL 2 — 최종 승인 대기
    approval = interrupt({
        "type": "final_approval",
        "review_results": review_results,
        "failed_rows": failed_rows,
    })

    return {
        "final_approval_result": approval,
        "logs": logs,
    }


# ── 조건부 분기 함수 ──────────────────────────────────────────────────

def should_retry(state: LocalizationState) -> str:
    """Node 4 → Node 3 재순환 또는 최종 승인으로 분기"""
    needs_retry = state.get("_needs_retry", [])
    if needs_retry:
        return "translator"
    return "final_approval"


def should_write(state: LocalizationState) -> str:
    """최종 승인 결과에 따라 쓰기 또는 종료"""
    approval = state.get("final_approval_result", "")
    if approval == "approved":
        return "writer"
    return END


# ── 그래프 빌드 ───────────────────────────────────────────────────────

def build_graph():
    """LangGraph StateGraph 구성 및 컴파일"""
    workflow = StateGraph(LocalizationState)

    # 노드 등록
    workflow.add_node("data_backup", data_backup_node)
    workflow.add_node("context_glossary", context_glossary_node)
    workflow.add_node("ko_review", ko_review_node)
    workflow.add_node("ko_approval", ko_approval_node)
    workflow.add_node("translator", translator_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("final_approval", final_approval_node)
    workflow.add_node("writer", writer_node)

    # 엣지 연결
    workflow.set_entry_point("data_backup")
    workflow.add_edge("data_backup", "context_glossary")
    workflow.add_edge("context_glossary", "ko_review")
    workflow.add_edge("ko_review", "ko_approval")
    # ko_approval → (HITL 1 interrupt 후 resume) → translator
    workflow.add_edge("ko_approval", "translator")
    workflow.add_edge("translator", "reviewer")
    # reviewer → 조건부: retry가 필요하면 translator, 아니면 final_approval
    workflow.add_conditional_edges("reviewer", should_retry)
    # final_approval → 조건부: approved면 writer, 아니면 END
    workflow.add_conditional_edges("final_approval", should_write)
    workflow.add_edge("writer", END)

    # 체크포인터 (MemorySaver — 세션 내 유지)
    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)

    return graph, checkpointer
