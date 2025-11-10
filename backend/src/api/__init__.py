"""API module exposing external service clients."""

from .openrouter import OpenRouterClient
from .longcat import LongCatClient
from .zenmux import ZenmuxClient
from .gemini import GeminiClient
from .cerebras import CerebrasClient
from .multiprovider import MultiProviderClient
from .exa_client import (
    fetch_job_posting_text,
    fetch_public_page_text,
    ExaContentError,
)
from .pricing import get_pricing_manager, TokenUsage, CostBreakdown, PricingManager

__all__ = [
    "OpenRouterClient",
    "LongCatClient",
    "ZenmuxClient",
    "GeminiClient",
    "CerebrasClient",
    "MultiProviderClient",
    "fetch_job_posting_text",
    "fetch_public_page_text",
    "ExaContentError",
    "get_pricing_manager",
    "TokenUsage",
    "CostBreakdown",
    "PricingManager",
]
