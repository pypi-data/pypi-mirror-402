from __future__ import annotations

from typing import Iterable, Optional

from .context import get_context
from .events import UsageEvent
from .pricing import ModelPrice, PricingRegistry
from .sinks.base import Sink


class Meter:
    def __init__(
        self,
        *,
        pricing: Optional[PricingRegistry] = None,
        sinks: Optional[Iterable[Sink]] = None,
        project: Optional[str] = None,
    ) -> None:
        self.pricing = pricing or PricingRegistry()
        self.sinks = list(sinks or [])
        self.project = project

    def compute_cost(
        self,
        provider: str,
        model: str,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
    ) -> tuple[Optional[float], Optional[float], Optional[float], Optional[ModelPrice]]:
        if input_tokens is None or output_tokens is None:
            return None, None, None, None

        # Try internal pricing registry first
        price = self.pricing.get_price(provider, model)
        if price is not None:
            in_cost = (input_tokens / 1_000_000) * price.input_per_million
            out_cost = (output_tokens / 1_000_000) * price.output_per_million
            return in_cost, out_cost, (in_cost + out_cost), price

        # Fallback to LiteLLM's pricing database
        try:
            import litellm
            # LiteLLM expects model in format like "gemini/gemini-2.5-flash" or just "gemini-2.5-flash"
            litellm_model = model if "/" in model else f"{provider}/{model}"
            total_cost = litellm.completion_cost(
                model=litellm_model,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
            )
            # LiteLLM returns total cost, estimate split based on typical ratios
            # Most models have ~3:1 input:output cost ratio, but we'll use 50/50 as approximation
            # since we don't have exact per-token rates from litellm
            return None, None, total_cost, None
        except Exception:
            # LiteLLM not available or model not in its database
            pass

        return None, None, None, None

    def record(self, event: UsageEvent) -> None:
        # enrich with context if missing
        ctx = get_context()
        event.agent_id = event.agent_id or ctx.agent_id
        event.user_id = event.user_id or ctx.user_id
        event.session_id = event.session_id or ctx.session_id
        event.trace_id = event.trace_id or ctx.trace_id

        if self.project:
            event.metadata.setdefault("project", self.project)

        for sink in self.sinks:
            sink.write(event)
