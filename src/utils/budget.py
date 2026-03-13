import logging
import math

class BudgetManager:
    def __init__(self, limit_usd: float = 2.00):
        self.limit_usd = limit_usd
        self.cumulative_spend = 0.0
        self.price_per_token = 0.10 / 1_000_000
        
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens using chars/4."""
        if not text:
            return 0
        return math.ceil(len(text) / 4)

    def update_cumulative_spend(self, token_count: int) -> float:
        """Update cumulative spend using $0.10 per 1M tokens."""
        if token_count < 0:
            raise ValueError("token_count cannot be negative")

        cost = token_count * self.price_per_token
        self.cumulative_spend += cost
        logging.info(f"Budget Update: Spent ${cost:.5f} | Total: ${self.cumulative_spend:.4f}")
        return self.cumulative_spend

    def update_spend(self, text_in: str, text_out: str) -> float:
        """Convenience helper that estimates tokens from input/output text."""
        tokens = self.estimate_tokens(text_in) + self.estimate_tokens(text_out)
        return self.update_cumulative_spend(tokens)

    def is_over_budget(self) -> bool:
        return self.cumulative_spend >= self.limit_usd