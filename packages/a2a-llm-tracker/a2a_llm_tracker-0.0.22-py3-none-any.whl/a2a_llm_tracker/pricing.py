from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re

@dataclass(frozen=True)
class ModelPrice:
    input_per_million: float
    output_per_million: float


@dataclass(frozen=True)
class ImageGenerationPrice:
    """Pricing for image generation models (per-image pricing)."""
    # Price per image by size and quality
    # Key format: "size" or "size:quality" (e.g., "1024x1024", "1024x1024:hd")
    prices: dict[str, float]

    def get_price(self, size: str = "1024x1024", quality: str = "standard") -> Optional[float]:
        """Get price for a specific size and quality combination."""
        # Try size:quality first
        key = f"{size}:{quality}"
        if key in self.prices:
            return self.prices[key]
        # Fall back to just size
        if size in self.prices:
            return self.prices[size]
        # Fall back to default
        if "default" in self.prices:
            return self.prices["default"]
        return None


@dataclass(frozen=True)
class ModelKey:
    provider: str
    model: str

_DATE_SUFFIX = re.compile(r"-\d{4}-\d{2}-\d{2}$")

def canonicalize(provider: str, model: str) -> ModelKey:
    p = provider.strip().lower()

    m = model.strip()

    # Handle models that already have provider prefix(es)
    # e.g., "gemini/gemini-2.5-flash" or even "gemini/gemini/gemini-2.5-flash"
    # Strip all leading provider prefixes to get the base model name
    while "/" in m:
        prefix, rest = m.split("/", 1)
        # If the prefix looks like a provider name, strip it
        if prefix.lower() in ("gemini", "openai", "anthropic", "cohere", "mistral",
                               "groq", "together", "bedrock", "vertex", "google"):
            m = rest
        else:
            # The slash is part of the model name (e.g., "meta-llama/Llama-2-7b")
            break

    # Now add the canonical provider prefix
    m = f"{p}/{m}"

    # strip dated suffix: openai/gpt-4.1-2025-04-14 -> openai/gpt-4.1
    m = _DATE_SUFFIX.sub("", m)

    return ModelKey(provider=p, model=m)


class PricingRegistry:
    def __init__(self):
        self._prices: dict[ModelKey, ModelPrice] = {}
        self._image_gen_prices: dict[ModelKey, ImageGenerationPrice] = {}

    def set_price(self, provider: str, model: str, *, input_per_million: float, output_per_million: float) -> None:
        key = canonicalize(provider, model)
        self._prices[key] = ModelPrice(
            input_per_million=float(input_per_million),
            output_per_million=float(output_per_million),
        )

    def get_price(self, provider: str, model: str) -> Optional[ModelPrice]:
        """
        Get pricing for a model. Returns None if not configured.

        This allows tracking to continue without cost calculation for models
        that don't have pricing configured (e.g., native Gemini via ADK).
        """
        key = canonicalize(provider, model)
        return self._prices.get(key)

    def set_image_generation_price(
        self,
        provider: str,
        model: str,
        *,
        prices: dict[str, float],
    ) -> None:
        """
        Set per-image pricing for an image generation model.

        Args:
            provider: Provider name (e.g., "openai")
            model: Model name (e.g., "dall-e-3")
            prices: Dict mapping size/quality to price per image.
                    Keys can be:
                    - "1024x1024" (size only)
                    - "1024x1024:standard" (size:quality)
                    - "1024x1024:hd" (size:quality)
                    - "default" (fallback price)

        Example:
            pricing.set_image_generation_price(
                provider="openai",
                model="dall-e-3",
                prices={
                    "1024x1024:standard": 0.040,
                    "1024x1024:hd": 0.080,
                    "1792x1024:standard": 0.080,
                    "1792x1024:hd": 0.120,
                    "default": 0.040,
                }
            )
        """
        key = canonicalize(provider, model)
        self._image_gen_prices[key] = ImageGenerationPrice(prices=prices)

    def get_image_generation_price(self, provider: str, model: str) -> Optional[ImageGenerationPrice]:
        """Get image generation pricing for a model, or None if not configured."""
        key = canonicalize(provider, model)
        return self._image_gen_prices.get(key)