"""Centralized pricing utilities for accurate cost tracking across providers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token usage breakdown."""
    input_tokens: int
    output_tokens: int
    thinking_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens + self.thinking_tokens


@dataclass
class CostBreakdown:
    """Detailed cost breakdown."""
    input_cost: float
    output_cost: float
    thinking_cost: float = 0.0
    
    # Fees and markups
    provider_markup: float = 0.0  # Provider markup amount
    platform_fee: float = 0.0
    total_cost: float = 0.0
    
    # Pricing rates (final after markup)
    input_price_per_1m: float = 0.0
    output_price_per_1m: float = 0.0
    thinking_price_per_1m: float = 0.0
    
    # Base rates (before markup)
    base_input_price_per_1m: float = 0.0
    base_output_price_per_1m: float = 0.0
    base_thinking_price_per_1m: float = 0.0
    
    # Markup info
    markup_type: str = ""  # "direct", "multiplier", "platform_fee"
    markup_value: str = ""  # "4.0x", "5.5% fee", "none"
    
    # Metadata
    pricing_version: str = "unknown"
    provider: str = ""
    model: str = ""
    base_model: str = ""  # Canonical model name
    
    def __post_init__(self):
        if self.total_cost == 0.0:
            self.total_cost = (
                self.input_cost + 
                self.output_cost + 
                self.thinking_cost + 
                self.provider_markup +
                self.platform_fee
            )


class PricingManager:
    """Manages pricing data and cost calculations."""
    
    def __init__(self, config_path: Optional[str] = None, use_v2: bool = True):
        """Initialize pricing manager.
        
        Args:
            config_path: Path to pricing config JSON. Defaults to pricing_config_v2.json
            use_v2: Use model-centric v2 config format (default: True)
        """
        if config_path is None:
            if use_v2:
                config_path = str(Path(__file__).parent / "pricing_config_v2.json")
            else:
                config_path = str(Path(__file__).parent / "pricing_config.json")
        
        self.config_path = Path(config_path)
        self._config: Dict = {}
        self._is_v2_schema = use_v2
        self._load_config()
    
    def _load_config(self):
        """Load pricing configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
                # Auto-detect schema version
                if "schema" in self._config and self._config["schema"] == "model-centric":
                    self._is_v2_schema = True
                elif "base_models" in self._config:
                    self._is_v2_schema = True
        except Exception as e:
            print(f"Warning: Could not load pricing config: {e}")
            self._config = {"version": "unknown", "providers": {}}
    
    def get_base_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get base model information (v2 schema only).
        
        Args:
            model: Model identifier
            
        Returns:
            Dict with model info including base_pricing, or None if not found
        """
        if not self._is_v2_schema:
            return None
        
        base_models = self._config.get("base_models", {})
        
        # Try direct lookup
        if model in base_models:
            return base_models[model]
        
        # Try aliases
        aliases = self._config.get("model_aliases", {})
        canonical = aliases.get(model)
        if canonical and canonical in base_models:
            return base_models[canonical]
        
        return None
    
    def get_model_pricing(
        self, 
        provider: str, 
        model: str,
        include_markup_details: bool = False
    ) -> Dict[str, float]:
        """Get pricing data for a specific model.
        
        Args:
            provider: Provider name (openrouter, gemini, etc.)
            model: Model identifier
            include_markup_details: Include base pricing and markup info (v2 only)
            
        Returns:
            Dict with 'input', 'output', and optionally 'thinking' prices per 1M tokens
            If include_markup_details=True: also includes base_input, base_output, markup_applied
        """
        if self._is_v2_schema:
            return self._get_model_pricing_v2(provider, model, include_markup_details)
        else:
            return self._get_model_pricing_v1(provider, model)
    
    def _get_model_pricing_v1(self, provider: str, model: str) -> Dict[str, float]:
        """Get pricing using legacy provider-centric schema."""
        provider_data = self._config.get("providers", {}).get(provider, {})
        models = provider_data.get("models", {})
        
        # Try exact match first
        if model in models:
            return models[model]
        
        # Fallback defaults by provider
        defaults = {
            "openrouter": {"input": 1.0, "output": 2.0},
            "zenmux": {"input": 5.0, "output": 10.0},
            "gemini": {"input": 0.30, "output": 2.50},
            "cerebras": {"input": 0.60, "output": 1.20},
            "longcat": {"input": 0.15, "output": 0.75},
        }
        
        return defaults.get(provider, {"input": 1.0, "output": 2.0})
    
    def _get_model_pricing_v2(
        self, 
        provider: str, 
        model: str,
        include_markup_details: bool = False
    ) -> Dict[str, float]:
        """Get pricing using model-centric v2 schema with markup calculation."""
        # Get base model pricing
        base_info = self.get_base_model_info(model)
        if not base_info:
            # Fallback to v1 style
            return self._get_model_pricing_v1(provider, model)
        
        base_pricing = base_info["base_pricing"].copy()
        
        # Get provider config
        provider_config = self._config.get("providers", {}).get(provider, {})
        
        # Check for model-specific overrides
        overrides = provider_config.get("model_overrides", {})
        if model in overrides:
            result = overrides[model].copy()
            if include_markup_details:
                result["base_input"] = base_pricing.get("input", 0)
                result["base_output"] = base_pricing.get("output", 0)
                result["markup_applied"] = "override"
            return result
        
        # Apply markup based on provider strategy
        markup_type = provider_config.get("markup_type", "direct")
        
        if markup_type == "direct":
            # No markup
            final_pricing = base_pricing.copy()
            if include_markup_details:
                final_pricing["base_input"] = base_pricing.get("input", 0)
                final_pricing["base_output"] = base_pricing.get("output", 0)
                final_pricing["markup_applied"] = "none"
            return final_pricing
        
        elif markup_type == "platform_fee":
            # Platform fee is applied separately, return base pricing
            final_pricing = base_pricing.copy()
            if include_markup_details:
                final_pricing["base_input"] = base_pricing.get("input", 0)
                final_pricing["base_output"] = base_pricing.get("output", 0)
                platform_fee_pct = provider_config.get("platform_fee_percent", 0)
                final_pricing["markup_applied"] = f"{platform_fee_pct}% platform fee"
            return final_pricing
        
        elif markup_type == "multiplier":
            # Apply multiplier markup
            model_specific = provider_config.get("model_specific_markup", {}).get(model, {})
            
            if model_specific:
                input_mult = model_specific.get("input_multiplier", 1.0)
                output_mult = model_specific.get("output_multiplier", 1.0)
            else:
                default_mult = provider_config.get("default_multiplier", {"input": 1.0, "output": 1.0})
                input_mult = default_mult.get("input", 1.0)
                output_mult = default_mult.get("output", 1.0)
            
            final_pricing = {}
            for token_type, base_cost in base_pricing.items():
                if token_type == "input":
                    final_pricing[token_type] = base_cost * input_mult
                elif token_type in ["output", "thinking"]:
                    final_pricing[token_type] = base_cost * output_mult
                else:
                    final_pricing[token_type] = base_cost
            
            if include_markup_details:
                final_pricing["base_input"] = base_pricing.get("input", 0)
                final_pricing["base_output"] = base_pricing.get("output", 0)
                final_pricing["markup_applied"] = f"{input_mult}x input, {output_mult}x output"
            
            return final_pricing
        
        # Unknown markup type, return base
        return base_pricing
    
    def calculate_cost(
        self,
        provider: str,
        model: str,
        usage: TokenUsage,
    ) -> CostBreakdown:
        """Calculate detailed cost breakdown.
        
        Args:
            provider: Provider name
            model: Model identifier
            usage: Token usage data
            
        Returns:
            CostBreakdown with detailed costs and markup information
        """
        # Get pricing with markup details if using v2 schema
        pricing = self.get_model_pricing(provider, model, include_markup_details=self._is_v2_schema)
        
        # Extract base and final pricing
        base_input_price = pricing.get("base_input", pricing.get("input", 0.0))
        base_output_price = pricing.get("base_output", pricing.get("output", 0.0))
        base_thinking_price = pricing.get("base_thinking", pricing.get("thinking", pricing.get("output", 0.0)))
        
        final_input_price = pricing.get("input", 0.0)
        final_output_price = pricing.get("output", 0.0)
        final_thinking_price = pricing.get("thinking", pricing.get("output", 0.0))
        
        # Calculate costs at base rates
        base_input_cost = (usage.input_tokens / 1_000_000) * base_input_price
        base_output_cost = (usage.output_tokens / 1_000_000) * base_output_price
        base_thinking_cost = (usage.thinking_tokens / 1_000_000) * base_thinking_price
        
        # Calculate costs at final rates
        input_cost = (usage.input_tokens / 1_000_000) * final_input_price
        output_cost = (usage.output_tokens / 1_000_000) * final_output_price
        thinking_cost = (usage.thinking_tokens / 1_000_000) * final_thinking_price
        
        # Calculate provider markup (difference between final and base)
        provider_markup = (input_cost - base_input_cost) + (output_cost - base_output_cost) + (thinking_cost - base_thinking_cost)
        
        # Calculate platform fee (OpenRouter only, applied on base cost)
        platform_fee = 0.0
        markup_type = ""
        markup_value = ""
        
        if self._is_v2_schema:
            provider_config = self._config.get("providers", {}).get(provider, {})
            markup_type = provider_config.get("markup_type", "direct")
            
            if markup_type == "platform_fee" and provider == "openrouter":
                fee_percent = provider_config.get("platform_fee_percent", 5.5)
                platform_fee = (base_input_cost + base_output_cost + base_thinking_cost) * (fee_percent / 100)
                markup_value = f"{fee_percent}% platform fee"
                # Reset provider_markup since we're using platform_fee instead
                provider_markup = 0.0
            elif markup_type == "multiplier":
                markup_value = pricing.get("markup_applied", "multiplier")
            elif markup_type == "direct":
                markup_value = "none"
            else:
                markup_value = markup_type
        else:
            # Legacy v1 schema - check for OpenRouter platform fee
            if provider == "openrouter":
                fee_percent = self._config.get("providers", {}).get("openrouter", {}).get("platform_fee_percent", 5.5)
                platform_fee = (input_cost + output_cost + thinking_cost) * (fee_percent / 100)
                markup_type = "platform_fee"
                markup_value = f"{fee_percent}% platform fee"
        
        # Get base model name if using v2
        base_model = model
        if self._is_v2_schema:
            base_info = self.get_base_model_info(model)
            if base_info:
                base_model = model  # Already canonical
        
        return CostBreakdown(
            input_cost=input_cost,
            output_cost=output_cost,
            thinking_cost=thinking_cost,
            provider_markup=provider_markup,
            platform_fee=platform_fee,
            input_price_per_1m=final_input_price,
            output_price_per_1m=final_output_price,
            thinking_price_per_1m=final_thinking_price,
            base_input_price_per_1m=base_input_price,
            base_output_price_per_1m=base_output_price,
            base_thinking_price_per_1m=base_thinking_price,
            markup_type=markup_type,
            markup_value=markup_value,
            pricing_version=self._config.get("version", "unknown"),
            provider=provider,
            model=model,
            base_model=base_model,
        )
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average).
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return len(text) // 4 if text else 0


# Global pricing manager instance
_pricing_manager: Optional[PricingManager] = None


def get_pricing_manager() -> PricingManager:
    """Get or create global pricing manager instance."""
    global _pricing_manager
    if _pricing_manager is None:
        _pricing_manager = PricingManager()
    return _pricing_manager


__all__ = [
    "TokenUsage",
    "CostBreakdown",
    "PricingManager",
    "get_pricing_manager",
]
