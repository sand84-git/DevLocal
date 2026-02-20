"""토큰/비용 추적"""

from config.constants import LLM_PRICING


class CostTracker:
    """LiteLLM 응답에서 토큰 사용량 및 비용 추적"""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def track(self, response):
        """LiteLLM 응답 객체에서 사용량 추출 및 누적"""
        usage = getattr(response, "usage", None)
        if usage:
            self.total_input_tokens += getattr(usage, "prompt_tokens", 0)
            self.total_output_tokens += getattr(usage, "completion_tokens", 0)

    @property
    def total_cost(self) -> float:
        input_cost = self.total_input_tokens * LLM_PRICING["input"]
        output_cost = self.total_output_tokens * LLM_PRICING["output"]
        return input_cost + output_cost

    def summary(self) -> dict:
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": round(self.total_cost, 4),
        }
