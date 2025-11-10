# LLM Provider Cost Tracking Specification

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2025-01-10  
**Related Specs**: llm-provider-parameters-v2-spec.md

## Executive Summary

This specification defines a comprehensive cost tracking framework for all LLM providers in the Resume Optimizer system. It addresses token counting accuracy, pricing data management, usage metadata extraction, cost attribution, and real-time budget monitoring.

### Key Objectives
- **Accurate cost calculation** with provider-specific pricing and token counting
- **Real-time usage tracking** with per-request and cumulative cost monitoring
- **Budget controls** with alerts and automatic throttling
- **Cost attribution** by agent, user, session, and project
- **Audit trail** for compliance and billing reconciliation

## Current Implementation Analysis

### Existing Cost Tracking Patterns

All provider clients implement:
```python
class ProviderClient:
    last_request_cost: float
    total_cost: float
    
    def get_last_cost(self) -> float
    def get_total_cost(self) -> float
    def reset_total_cost(self) -> None
```

### Current Limitations

1. **Token Estimation vs Actual Usage** - Most providers use 4-char-per-token estimation (10-30% inaccurate)
2. **Hardcoded Pricing** - No versioning or update mechanism
3. **Limited Attribution** - No per-agent, user, or session tracking
4. **No Budget Controls** - No spending limits or alerts
5. **Missing Audit Trail** - No persistent cost records

## Provider-Specific Cost Tracking

### OpenRouter
- **Pricing**: Pass-through + 5.5% platform fee
- **Usage Metadata**: Available in response (actual tokens)
- **Billing**: Credit-based, failed requests not billed

### Zenmux
- **Pricing**: Per-token premium pricing
- **Usage Metadata**: Not provided (estimation required)
- **Billing**: Credit card, logprobs/JSON schema included

### Google Gemini
- **Pricing**: Token-based with modality-specific rates
- **Usage Metadata**: Comprehensive (actual tokens + multimodal)
- **Billing**: Free tier, batch API 50% discount, grounding extras

### Cerebras
- **Pricing**: Pay-per-token high-performance premium
- **Usage Metadata**: Not provided (estimation required)
- **Billing**: $10 minimum, tiered plans, 1M free tokens/day

### Meituan LongCat
- **Pricing**: Fixed per-token for MoE models
- **Usage Metadata**: Not provided (estimation required)
- **Billing**: OpenAI/Anthropic compatible, thinking tokens as output

## Unified Cost Tracking Architecture

### Data Model

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class CostSource(str, Enum):
    ACTUAL = "actual"
    ESTIMATED = "estimated"
    CACHED = "cached"

@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    thinking_tokens: Optional[int] = None
    source: CostSource = CostSource.ESTIMATED

@dataclass
class CostBreakdown:
    input_cost: float
    output_cost: float
    total_cost: float
    platform_fee: float = 0.0
    input_price_per_1m: float = 0.0
    output_price_per_1m: float = 0.0
    pricing_version: str = "unknown"

@dataclass
class RequestCostRecord:
    request_id: str
    session_id: Optional[str]
    user_id: Optional[str]
    agent_name: Optional[str]
    provider: str
    model: str
    timestamp: datetime
    latency_ms: float
    usage: TokenUsage
    cost: CostBreakdown
    success: bool
    tags: Dict[str, str]
```

### Cost Tracker Implementation

```python
class CostTracker:
    def __init__(self, db_path: str, pricing_config_path: str):
        self.db_path = Path(db_path)
        self.pricing_config = self._load_pricing_config(pricing_config_path)
        self._init_database()
    
    def record_request_cost(self, record: RequestCostRecord):
        """Record cost for a single request."""
        # Insert into SQLite database
    
    def get_session_cost(self, session_id: str) -> float:
        """Get total cost for a session."""
    
    def get_user_cost(self, user_id: str, days: int = 30) -> float:
        """Get total cost for a user over specified days."""
    
    def get_agent_cost_breakdown(self, days: int = 7) -> Dict[str, float]:
        """Get cost breakdown by agent."""
    
    def calculate_cost(
        self, provider: str, model: str, 
        input_tokens: int, output_tokens: int
    ) -> CostBreakdown:
        """Calculate cost for a request."""
```

### Pricing Configuration

```json
{
  "version": "2025-01-10",
  "providers": {
    "openrouter": {
      "platform_fee_percent": 5.5,
      "models": {
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "openai/gpt-4o": {"input": 5.0, "output": 15.0}
      }
    },
    "gemini": {
      "models": {
        "gemini-2.5-flash": {"input": 0.30, "output": 2.50}
      },
      "grounding": {
        "google_search_free_daily": 1500,
        "google_search_per_1000": 35.0
      }
    }
  }
}
```

## Budget Management

```python
@dataclass
class BudgetConfig:
    daily_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    per_session_limit: Optional[float] = None
    warning_threshold: float = 0.75
    auto_throttle_on_limit: bool = True

class BudgetManager:
    def check_budget(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Check budget status with alerts."""
```

## Implementation Recommendations

1. **Migrate to actual token counts** where available (OpenRouter, Gemini)
2. **Implement pricing updater** to fetch latest rates weekly
3. **Add cost tracking to all agent calls** with session/user attribution
4. **Set up budget alerts** via email/webhook
5. **Create cost dashboard** for monitoring and analysis
6. **Export cost records** for invoice reconciliation

## Migration Checklist

- [ ] Add `CostTracker` to backend initialization
- [ ] Update all provider clients with enhanced interface
- [ ] Create pricing configuration JSON
- [ ] Implement budget manager with alerts
- [ ] Add cost tracking to agent pipeline
- [ ] Create cost monitoring dashboard
- [ ] Set up automated pricing updates
- [ ] Add cost export for accounting
