"""Test script for model-centric pricing architecture (v2)."""

import sys
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import only pricing module (avoid full API imports)
import importlib.util
pricing_path = Path(__file__).parent / "src/api/pricing.py"
spec = importlib.util.spec_from_file_location("pricing", str(pricing_path))
pricing_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pricing_module)

PricingManager = pricing_module.PricingManager
TokenUsage = pricing_module.TokenUsage
CostBreakdown = pricing_module.CostBreakdown

def test_basic_loading():
    """Test that v2 config loads correctly."""
    print("=" * 60)
    print("TEST 1: Basic V2 Config Loading")
    print("=" * 60)
    
    pm = PricingManager(use_v2=True)
    print(f"✓ Pricing manager loaded")
    print(f"  Version: {pm._config.get('version')}")
    print(f"  Schema: {pm._config.get('schema')}")
    print(f"  Base models count: {len(pm._config.get('base_models', {}))}")
    print()

def test_base_model_lookup():
    """Test base model information retrieval."""
    print("=" * 60)
    print("TEST 2: Base Model Information Lookup")
    print("=" * 60)
    
    pm = PricingManager(use_v2=True)
    
    # Test direct lookup
    model = "anthropic/claude-sonnet-4.5"
    info = pm.get_base_model_info(model)
    print(f"Model: {model}")
    print(f"  Display name: {info['display_name']}")
    print(f"  Vendor: {info['vendor']}")
    print(f"  Base pricing: ${info['base_pricing']['input']}/1M input, ${info['base_pricing']['output']}/1M output")
    print(f"  Context window: {info['context_window']:,} tokens")
    print(f"  Supports thinking: {info['supports_thinking']}")
    print()
    
    # Test alias lookup
    alias = "claude-sonnet"
    info = pm.get_base_model_info(alias)
    print(f"Alias: {alias}")
    print(f"  Resolves to: {info['display_name']}")
    print()

def test_pricing_without_markup():
    """Test direct pricing (no markup)."""
    print("=" * 60)
    print("TEST 3: Direct Pricing (Gemini - No Markup)")
    print("=" * 60)
    
    pm = PricingManager(use_v2=True)
    
    model = "gemini-2.5-flash"
    pricing = pm.get_model_pricing("gemini", model, include_markup_details=True)
    
    print(f"Model: {model} via Gemini")
    print(f"  Input: ${pricing['input']}/1M tokens")
    print(f"  Output: ${pricing['output']}/1M tokens")
    print(f"  Base input: ${pricing['base_input']}/1M tokens")
    print(f"  Base output: ${pricing['base_output']}/1M tokens")
    print(f"  Markup: {pricing['markup_applied']}")
    print()

def test_pricing_with_platform_fee():
    """Test platform fee markup (OpenRouter)."""
    print("=" * 60)
    print("TEST 4: Platform Fee Markup (OpenRouter)")
    print("=" * 60)
    
    pm = PricingManager(use_v2=True)
    
    model = "anthropic/claude-sonnet-4.5"
    pricing = pm.get_model_pricing("openrouter", model, include_markup_details=True)
    
    print(f"Model: {model} via OpenRouter")
    print(f"  Base input: ${pricing['base_input']}/1M tokens")
    print(f"  Base output: ${pricing['base_output']}/1M tokens")
    print(f"  Final input: ${pricing['input']}/1M tokens (same as base)")
    print(f"  Final output: ${pricing['output']}/1M tokens (same as base)")
    print(f"  Markup: {pricing['markup_applied']}")
    print()

def test_pricing_with_multiplier():
    """Test multiplier markup (Zenmux)."""
    print("=" * 60)
    print("TEST 5: Multiplier Markup (Zenmux)")
    print("=" * 60)
    
    pm = PricingManager(use_v2=True)
    
    model = "anthropic/claude-sonnet-4.5"
    pricing = pm.get_model_pricing("zenmux", model, include_markup_details=True)
    
    print(f"Model: {model} via Zenmux")
    print(f"  Base input: ${pricing['base_input']}/1M tokens")
    print(f"  Base output: ${pricing['base_output']}/1M tokens")
    print(f"  Final input: ${pricing['input']}/1M tokens")
    print(f"  Final output: ${pricing['output']}/1M tokens")
    print(f"  Markup: {pricing['markup_applied']}")
    print(f"  Input multiplier: {pricing['input'] / pricing['base_input']:.2f}x")
    print(f"  Output multiplier: {pricing['output'] / pricing['base_output']:.2f}x")
    print()

def test_cost_calculation_openrouter():
    """Test cost calculation with OpenRouter platform fee."""
    print("=" * 60)
    print("TEST 6: Cost Calculation - OpenRouter Platform Fee")
    print("=" * 60)
    
    pm = PricingManager(use_v2=True)
    
    model = "anthropic/claude-sonnet-4.5"
    usage = TokenUsage(input_tokens=1000, output_tokens=2000)
    cost = pm.calculate_cost("openrouter", model, usage)
    
    print(f"Model: {model} via OpenRouter")
    print(f"Usage: {usage.input_tokens:,} input + {usage.output_tokens:,} output tokens")
    print()
    print("Cost Breakdown:")
    print(f"  Base input cost:  ${cost.input_cost:.6f}")
    print(f"  Base output cost: ${cost.output_cost:.6f}")
    print(f"  Subtotal:         ${cost.input_cost + cost.output_cost:.6f}")
    print(f"  Platform fee:     ${cost.platform_fee:.6f} ({cost.markup_value})")
    print(f"  Provider markup:  ${cost.provider_markup:.6f}")
    print(f"  TOTAL COST:       ${cost.total_cost:.6f}")
    print()
    print("Rates:")
    print(f"  Base input:  ${cost.base_input_price_per_1m:.2f}/1M tokens")
    print(f"  Base output: ${cost.base_output_price_per_1m:.2f}/1M tokens")
    print(f"  Final input:  ${cost.input_price_per_1m:.2f}/1M tokens")
    print(f"  Final output: ${cost.output_price_per_1m:.2f}/1M tokens")
    print()

def test_cost_calculation_zenmux():
    """Test cost calculation with Zenmux multiplier."""
    print("=" * 60)
    print("TEST 7: Cost Calculation - Zenmux Multiplier")
    print("=" * 60)
    
    pm = PricingManager(use_v2=True)
    
    model = "anthropic/claude-sonnet-4.5"
    usage = TokenUsage(input_tokens=1000, output_tokens=2000)
    cost = pm.calculate_cost("zenmux", model, usage)
    
    print(f"Model: {model} via Zenmux")
    print(f"Usage: {usage.input_tokens:,} input + {usage.output_tokens:,} output tokens")
    print()
    print("Cost Breakdown:")
    print(f"  Input cost:       ${cost.input_cost:.6f}")
    print(f"  Output cost:      ${cost.output_cost:.6f}")
    print(f"  Provider markup:  ${cost.provider_markup:.6f} ({cost.markup_value})")
    print(f"  Platform fee:     ${cost.platform_fee:.6f}")
    print(f"  TOTAL COST:       ${cost.total_cost:.6f}")
    print()
    print("Rates:")
    print(f"  Base input:  ${cost.base_input_price_per_1m:.2f}/1M tokens")
    print(f"  Base output: ${cost.base_output_price_per_1m:.2f}/1M tokens")
    print(f"  Final input:  ${cost.input_price_per_1m:.2f}/1M tokens ({cost.input_price_per_1m / cost.base_input_price_per_1m:.1f}x)")
    print(f"  Final output: ${cost.output_price_per_1m:.2f}/1M tokens ({cost.output_price_per_1m / cost.base_output_price_per_1m:.1f}x)")
    print()

def test_cost_comparison():
    """Compare costs across providers for the same model."""
    print("=" * 60)
    print("TEST 8: Cost Comparison Across Providers")
    print("=" * 60)
    
    pm = PricingManager(use_v2=True)
    
    model = "anthropic/claude-sonnet-4.5"
    usage = TokenUsage(input_tokens=1000, output_tokens=2000)
    
    print(f"Model: {model}")
    print(f"Usage: {usage.input_tokens:,} input + {usage.output_tokens:,} output tokens")
    print()
    
    providers = ["openrouter", "zenmux"]
    costs = []
    
    for provider in providers:
        cost = pm.calculate_cost(provider, model, usage)
        costs.append((provider, cost))
        print(f"{provider.upper()}:")
        print(f"  Base cost:   ${cost.input_cost + cost.output_cost - cost.provider_markup:.6f}")
        print(f"  Markup:      ${cost.provider_markup:.6f}")
        print(f"  Platform fee: ${cost.platform_fee:.6f}")
        print(f"  TOTAL:       ${cost.total_cost:.6f}")
        print()
    
    # Calculate price difference
    cheapest = min(costs, key=lambda x: x[1].total_cost)
    most_expensive = max(costs, key=lambda x: x[1].total_cost)
    
    price_diff = most_expensive[1].total_cost - cheapest[1].total_cost
    price_ratio = most_expensive[1].total_cost / cheapest[1].total_cost
    
    print(f"Cheapest: {cheapest[0]} at ${cheapest[1].total_cost:.6f}")
    print(f"Most expensive: {most_expensive[0]} at ${most_expensive[1].total_cost:.6f}")
    print(f"Price difference: ${price_diff:.6f} ({price_ratio:.2f}x)")
    print()

def test_thinking_tokens():
    """Test cost calculation with thinking tokens (Gemini 2.5)."""
    print("=" * 60)
    print("TEST 9: Thinking Tokens Cost (Gemini 2.5)")
    print("=" * 60)
    
    pm = PricingManager(use_v2=True)
    
    model = "gemini-2.5-flash"
    usage = TokenUsage(input_tokens=1000, output_tokens=2000, thinking_tokens=500)
    cost = pm.calculate_cost("gemini", model, usage)
    
    print(f"Model: {model} via Gemini")
    print(f"Usage: {usage.input_tokens:,} input + {usage.output_tokens:,} output + {usage.thinking_tokens:,} thinking tokens")
    print()
    print("Cost Breakdown:")
    print(f"  Input cost:    ${cost.input_cost:.6f}")
    print(f"  Output cost:   ${cost.output_cost:.6f}")
    print(f"  Thinking cost: ${cost.thinking_cost:.6f}")
    print(f"  TOTAL COST:    ${cost.total_cost:.6f}")
    print()
    print("Rates:")
    print(f"  Input:    ${cost.input_price_per_1m:.2f}/1M tokens")
    print(f"  Output:   ${cost.output_price_per_1m:.2f}/1M tokens")
    print(f"  Thinking: ${cost.thinking_price_per_1m:.2f}/1M tokens")
    print()

def main():
    """Run all tests."""
    try:
        test_basic_loading()
        test_base_model_lookup()
        test_pricing_without_markup()
        test_pricing_with_platform_fee()
        test_pricing_with_multiplier()
        test_cost_calculation_openrouter()
        test_cost_calculation_zenmux()
        test_cost_comparison()
        test_thinking_tokens()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Key Insights:")
        print("  • Model-centric pricing provides transparency")
        print("  • Provider markups are clearly visible")
        print("  • Easy to compare costs across providers")
        print("  • Thinking tokens tracked separately")
        print()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
