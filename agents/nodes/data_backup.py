"""Node 1: 데이터 로드 & 백업 (LLM 미사용 유틸리티)"""

from agents.state import LocalizationState


def data_backup_node(state: LocalizationState) -> dict:
    """
    시트 데이터 로드 + 백업 생성.
    실제 시트 로드/백업은 app.py에서 사전 수행되어 state에 주입됨.
    이 노드는 state의 데이터를 확인하고 로그를 남김.
    """
    original_data = state.get("original_data", [])
    backup_data = state.get("backup_data", [])
    logs = list(state.get("logs", []))

    logs.append(f"[Node 1] 데이터 로드 완료: {len(original_data)}행")
    logs.append(f"[Node 1] 백업 생성 완료: {len(backup_data)}행")

    return {
        "original_data": original_data,
        "backup_data": backup_data,
        "logs": logs,
    }
