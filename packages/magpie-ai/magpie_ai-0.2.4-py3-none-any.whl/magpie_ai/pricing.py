"""
Model pricing configuration and cost calculation.

Supports major LLM providers with per-token pricing.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing for a specific model."""

    input_price_per_1m_tokens: float  # Price per 1 million input tokens
    output_price_per_1m_tokens: float  # Price per 1 million output tokens
    context_window: int  # Maximum tokens in context window


# Pricing data (as of January 2026)
# Update these based on current provider pricing
MODEL_PRICING: Dict[str, ModelPricing] = {
    # OpenAI - GPT-4 models
    "gpt-4": ModelPricing(
        input_price_per_1m_tokens=30.0, output_price_per_1m_tokens=60.0, context_window=8192
    ),
    "gpt-4-turbo": ModelPricing(
        input_price_per_1m_tokens=10.0, output_price_per_1m_tokens=30.0, context_window=128000
    ),
    "gpt-4-32k": ModelPricing(
        input_price_per_1m_tokens=60.0, output_price_per_1m_tokens=120.0, context_window=32768
    ),
    # OpenAI - GPT-3.5 models
    "gpt-3.5-turbo": ModelPricing(
        input_price_per_1m_tokens=0.5, output_price_per_1m_tokens=1.5, context_window=4096
    ),
    # Anthropic - Claude models
    "claude-3-sonnet": ModelPricing(
        input_price_per_1m_tokens=3.0, output_price_per_1m_tokens=15.0, context_window=200000
    ),
    "claude-3-opus": ModelPricing(
        input_price_per_1m_tokens=15.0, output_price_per_1m_tokens=75.0, context_window=200000
    ),
    "claude-3-haiku": ModelPricing(
        input_price_per_1m_tokens=0.25, output_price_per_1m_tokens=1.25, context_window=200000
    ),
    # Anthropic - Claude 2 (legacy)
    "claude-2": ModelPricing(
        input_price_per_1m_tokens=8.0, output_price_per_1m_tokens=24.0, context_window=100000
    ),
    # Google - Gemini models
    "gemini-pro": ModelPricing(
        input_price_per_1m_tokens=0.5, output_price_per_1m_tokens=1.0, context_window=32768
    ),
    "gemini-pro-vision": ModelPricing(
        input_price_per_1m_tokens=0.5, output_price_per_1m_tokens=1.0, context_window=32768
    ),
    # Meta - Llama (via providers)
    "llama-2-7b": ModelPricing(
        input_price_per_1m_tokens=0.1, output_price_per_1m_tokens=0.1, context_window=4096
    ),
    "llama-2-13b": ModelPricing(
        input_price_per_1m_tokens=0.2, output_price_per_1m_tokens=0.2, context_window=4096
    ),
}


def get_model_pricing(model: str) -> Optional[ModelPricing]:
    """
    Get pricing for a specific model.

    Args:
        model: Model name (e.g., "gpt-4", "claude-3-sonnet")

    Returns:
        ModelPricing object, or None if model not found
    """
    return MODEL_PRICING.get(model.lower())


def calculate_costs(
    input_tokens: int,
    output_tokens: int,
    model: Optional[str] = None,
    input_price_per_1m: Optional[float] = None,
    output_price_per_1m: Optional[float] = None,
) -> Tuple[float, float, float]:
    """
    Calculate input, output, and total costs.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name (takes precedence over explicit prices)
        input_price_per_1m: Explicit input price per 1M tokens
        output_price_per_1m: Explicit output price per 1M tokens

    Returns:
        Tuple of (input_cost, output_cost, total_cost) in USD

    Raises:
        ValueError: If model not found and prices not provided, or both specified
    """
    # Validation: can't have both model and explicit prices
    if model and (input_price_per_1m is not None or output_price_per_1m is not None):
        raise ValueError(
            "Cannot specify both 'model' and explicit prices. " "Use one or the other."
        )

    # Get pricing from model if provided
    if model:
        pricing = get_model_pricing(model)
        if not pricing:
            raise ValueError(
                f"Model '{model}' not found in pricing database. "
                f"Provide explicit prices via input_price_per_1m and output_price_per_1m."
            )
        input_price = pricing.input_price_per_1m_tokens
        output_price = pricing.output_price_per_1m_tokens
    elif input_price_per_1m is not None and output_price_per_1m is not None:
        input_price = input_price_per_1m
        output_price = output_price_per_1m
    else:
        raise ValueError(
            "Either 'model' or both 'input_price_per_1m' and 'output_price_per_1m' "
            "must be provided."
        )

    # Calculate costs (prices are per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    total_cost = input_cost + output_cost

    return input_cost, output_cost, total_cost


def get_context_utilization(
    input_tokens: int,
    output_tokens: int,
    model: Optional[str] = None,
    context_window: Optional[int] = None,
) -> float:
    """
    Calculate context utilization percentage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name (to look up context window)
        context_window: Explicit context window size

    Returns:
        Context utilization as percentage (0.0 to 100.0)
    """
    if model and not context_window:
        pricing = get_model_pricing(model)
        if pricing:
            context_window = pricing.context_window

    if not context_window:
        return 0.0  # Unknown context window

    total_tokens = input_tokens + output_tokens
    utilization = (total_tokens / context_window) * 100.0

    return min(utilization, 100.0)  # Cap at 100%


def list_available_models() -> list[str]:
    """Get list of all available models in pricing database."""
    return sorted(MODEL_PRICING.keys())
