# LLM Provider Parameters Specification v2.0

**Version**: 2.0.0  
**Status**: Production Ready  
**Last Updated**: 2025-01-09  
**Supersedes**: llm-provider-parameters-spec.md v1.0

## Executive Summary

This specification defines a production-ready framework for managing LLM provider parameters with:
- Unified parameter interface with type-safe validation
- Dynamic configuration with environment interpolation
- Experiment tracking integration (W&B, MLflow)
- LangChain/LangSmith compatibility
- Security, error handling, and performance optimization

### Supported Providers
- **OpenRouter** - Multi-provider marketplace (400+ models)
- **Zenmux** - OpenAI-compatible premium models
- **Google Gemini** - Native multimodal with thinking
- **Cerebras** - High-performance large model inference
- **Meituan LongCat** - Advanced MoE with agentic optimization

## Provider Comparison Matrix

| Parameter | OpenRouter | Zenmux | Gemini | Cerebras | LongCat |
|-----------|------------|--------|---------|----------|---------|
| **Temperature** | 0.0-2.0 | 0.0-2.0 | 0.0-2.0 | 0.0-1.5 | 0.0-1.0 |
| **Max Tokens** | `max_tokens` | `max_completion_tokens` | `maxOutputTokens` | `max_tokens` | `max_tokens` |
| **Streaming** | ✅ SSE | ✅ SSE | ✅ Native | ✅ SSE | ✅ SSE |
| **File Upload** | ✅ Images/PDFs | ✅ Images/PDFs | ✅ Multimodal | ❌ | ❌ |
| **Thinking Mode** | ❌ | ❌ | ✅ `thinkingConfig` | ❌ | ✅ `thinking_budget` |
| **Structured Output** | ✅ JSON | ✅ Schema | ✅ Schema | ✅ Schema | ❌ |
| **Function Calling** | ✅ Parallel | ✅ Sequential | ✅ Parallel | ❌ | ❌ |
| **Usage Tracking** | ✅ Headers | ❌ Estimate | ✅ Metadata | ❌ Estimate | ❌ Estimate |

## Unified Parameter Interface

### Core Schema

```python
from typing import Optional, Dict, Any, List, Union, Literal
from typing_extensions import TypedDict
from enum import Enum

class ProviderType(str, Enum):
    OPENROUTER = "openrouter"
    ZENMUX = "zenmux"
    GEMINI = "gemini"
    CEREBRAS = "cerebras"
    LONGCAT = "longcat"

class UnifiedGenerationConfig(TypedDict, total=False):
    """Unified generation configuration across all providers."""
    temperature: float  # 0.0-2.0, default 0.7
    max_tokens: int  # Minimum 1, default 4000
    top_p: float  # 0.0-1.0
    top_k: Optional[int]  # Provider-specific
    frequency_penalty: float  # -2.0 to 2.0
    presence_penalty: float  # -2.0 to 2.0
    seed: Optional[int]  # Reproducible outputs
    stop: Union[str, List[str]]  # Stop sequences
    stream: bool  # Enable streaming
    thinking_budget: Optional[int]  # For reasoning models
    response_format: Optional[Dict[str, Any]]  # Structured output
    tools: Optional[List[Dict[str, Any]]]  # Function calling
    tool_choice: Optional[Union[str, Dict[str, Any]]]
    logprobs: bool
    top_logprobs: Optional[int]
    provider_options: Dict[str, Any]  # Provider-specific

class UnifiedCompletionRequest(TypedDict, total=False):
    provider: ProviderType
    model: str
    system_prompt: str
    user_text: Optional[str]
    messages: Optional[List[Dict[str, Any]]]
    files: Optional[List[Dict[str, Any]]]
    generation: UnifiedGenerationConfig
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    run_id: Optional[str]
    parent_run_id: Optional[str]
```

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UnifiedGenerationConfig",
  "type": "object",
  "properties": {
    "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0, "default": 0.7},
    "max_tokens": {"type": "integer", "minimum": 1, "default": 4000},
    "top_p": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "seed": {"type": ["integer", "null"]},
    "stream": {"type": "boolean", "default": true},
    "thinking_budget": {"type": "integer", "minimum": 1024},
    "provider_options": {"type": "object", "default": {}}
  },
  "dependencies": {
    "top_logprobs": ["logprobs"]
  }
}
```

## Configuration Management

### Precedence Order
```
CLI Arguments > Environment Variables > Config File (YAML) > Defaults
```

### Configuration File Example

```yaml
# config/llm.yaml
version: "2.0"

defaults:
  temperature: 0.7
  max_tokens: 4000
  stream: true
  seed: ${LLM_SEED:42}

providers:
  openrouter:
    base_url: ${OPENROUTER_API_BASE:https://openrouter.ai/api/v1}
    api_key: ${OPENROUTER_API_KEY}
    default_model: anthropic/claude-3.5-sonnet
    generation:
      temperature: 0.7
      max_tokens: 4000
      top_p: 0.95
  
  gemini:
    api_key: ${GEMINI_API_KEY}
    default_model: gemini-2.5-flash
    generation:
      temperature: 0.8
      max_tokens: 4096
      thinking_budget: ${GEMINI_THINKING_BUDGET:2048}

agents:
  polish:
    provider: ${POLISH_PROVIDER:zenmux}
    model: ${POLISH_MODEL:anthropic/claude-sonnet-4.5}
    generation:
      temperature: ${POLISH_TEMP:0.6}
      max_tokens: 32000

tracking:
  enabled: ${TRACKING_ENABLED:true}
  backend: ${TRACKING_BACKEND:wandb}
  wandb:
    project: ${WANDB_PROJECT:resume-optimizer}
    entity: ${WANDB_ENTITY}
  mlflow:
    tracking_uri: ${MLFLOW_TRACKING_URI:http://localhost:5000}

security:
  pii_redaction:
    enabled: ${PII_REDACTION:true}
    level: ${PII_REDACTION_LEVEL:basic}

performance:
  request_timeout: ${REQUEST_TIMEOUT:60}
  max_retries: ${MAX_RETRIES:3}
  retry_delay: 1.0
```

### Configuration Loader

```python
import os, re, yaml
from pathlib import Path
from typing import Any, Dict, Optional

ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)(?::([^}]*))?\}")

class ConfigLoader:
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None
    
    def load(self, cli_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raw_yaml = self.config_path.read_text(encoding="utf-8")
        expanded = self._expand_env_vars(raw_yaml)
        config = yaml.safe_load(expanded) or {}
        
        if cli_overrides:
            config = self._apply_overrides(config, cli_overrides)
        
        self._config = config
        return config
    
    def _expand_env_vars(self, text: str) -> str:
        def replace(m):
            var, default = m.group(1), m.group(2) or ""
            return os.getenv(var, default)
        return ENV_PATTERN.sub(replace, text)
    
    def _apply_overrides(self, config: Dict, overrides: Dict) -> Dict:
        result = config.copy()
        for key, value in overrides.items():
            parts = key.split(".")
            node = result
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = value
        return result
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        agent_cfg = self._config.get("agents", {}).get(agent_name, {})
        provider = agent_cfg.get("provider", "openrouter")
        provider_cfg = self._config.get("providers", {}).get(provider, {})
        
        return {
            "provider": provider,
            "model": agent_cfg.get("model") or provider_cfg.get("default_model"),
            "generation": {
                **self._config.get("defaults", {}),
                **provider_cfg.get("generation", {}),
                **agent_cfg.get("generation", {}),
            }
        }
```

## Parameter Validation

```python
from typing import List

class ParameterValidator:
    @staticmethod
    def validate_openrouter(config: Dict) -> List[str]:
        errors = []
        if "temperature" in config and not (0.0 <= config["temperature"] <= 2.0):
            errors.append("OpenRouter temperature must be 0.0-2.0")
        if "max_tokens" in config and config["max_tokens"] < 1:
            errors.append("OpenRouter max_tokens must be >= 1")
        return errors
    
    @staticmethod
    def validate_gemini(config: Dict) -> List[str]:
        errors = []
        if "thinking_budget" in config and config["thinking_budget"] < 1024:
            errors.append("Gemini thinkingBudget must be >= 1024")
        # Gemini penalties are 0.0-1.0 (not -2.0 to 2.0)
        if "presence_penalty" in config and not (0.0 <= config["presence_penalty"] <= 1.0):
            errors.append("Gemini presencePenalty must be 0.0-1.0")
        return errors
```

## Experiment Tracking Integration

### W&B Integration

```python
import wandb, json, hashlib
from pathlib import Path

def log_run_to_wandb(request, result, usage, artifacts_dir: Path):
    config_hash = hashlib.sha256(
        json.dumps(request.get("generation", {}), sort_keys=True).encode()
    ).hexdigest()[:12]
    
    with wandb.init(
        project=os.getenv("WANDB_PROJECT", "resume-optimizer"),
        tags=[request["provider"].value, request["model"], "spec:v2.0"],
        config={
            "provider": request["provider"].value,
            "model": request["model"],
            "spec_version": "2.0.0",
            "config_hash": config_hash,
            "generation": request.get("generation", {})
        }
    ) as run:
        wandb.log({
            "latency_ms": usage.get("latency_ms", 0),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cost_usd": usage.get("cost", 0.0),
        })
        
        for name in ["system_prompt.txt", "response.txt", "resume.docx"]:
            p = artifacts_dir / name
            if p.exists():
                wandb.save(str(p))
```

### MLflow Integration

```python
import mlflow

def log_run_to_mlflow(request, result, usage, artifacts_dir: str):
    mlflow.set_experiment("resume-optimizer")
    
    flat_params = {
        f"provider": request["provider"].value,
        f"model": request["model"],
        **{f"gen.{k}": v for k, v in request.get("generation", {}).items()}
    }
    
    with mlflow.start_run(run_name=f'{request["provider"].value}:{request["model"]}'):
        mlflow.log_params(flat_params)
        mlflow.set_tags({"spec_version": "2.0.0"})
        mlflow.log_metrics({
            "latency_ms": usage.get("latency_ms", 0),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cost_usd": usage.get("cost", 0.0),
        })
        mlflow.log_artifacts(artifacts_dir, artifact_path="artifacts")
```

## LangChain/LangSmith Compatibility

### LangChain Adapter

```python
from typing import Iterator, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import AIMessage, BaseMessage

class UnifiedChatModel(BaseChatModel):
    def __init__(self, client, provider, model: str, generation: dict):
        super().__init__()
        self.client = client
        self.provider = provider
        self.model = model
        self.generation = generation
    
    @property
    def _llm_type(self) -> str:
        return f"{self.provider.value}:{self.model}"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ):
        system = "\n".join(m.content for m in messages if m.type == "system")
        user = "\n".join(m.content for m in messages if m.type == "human")
        
        final = ""
        for token in self.client.stream_completion({
            "provider": self.provider,
            "model": self.model,
            "system_prompt": system,
            "user_text": user,
            "generation": {**self.generation, "stop": stop or self.generation.get("stop")}
        }):
            final += token
            if run_manager:
                run_manager.on_llm_new_token(token)
        
        return AIMessage(content=final)
```

### LangSmith Tracing

```python
# Set environment variables
# export LANGSMITH_TRACING=true
# export LANGSMITH_API_KEY=...

from langsmith import traceable

@traceable(
    tags=["resume-optimizer", "polish"],
    metadata={"provider": "openrouter", "spec_version": "2.0.0"}
)
def run_polish_agent(chain, inputs):
    return chain.invoke(inputs)
```

## Security and Compliance

### PII Redaction

```python
import re

PII_PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "phone": re.compile(r"\+?\d[\d\s\-\(\)]{7,}\d"),
    "ssn": re.compile(r"\d{3}-\d{2}-\d{4}"),
}

def redact_pii(text: str, level: str = "basic") -> str:
    if level == "none":
        return text
    
    patterns = ["email", "phone"]
    if level == "strict":
        patterns.append("ssn")
    
    for pattern_name in patterns:
        text = PII_PATTERNS[pattern_name].sub("[REDACTED]", text)
    
    return text
```

## Error Handling and Retry Logic

### Error Taxonomy

```python
ERROR_MAP = {
    "authentication_error": "auth_error",
    "invalid_api_key": "auth_error",
    "rate_limit_exceeded": "rate_limited",
    "insufficient_quota": "quota_exceeded",
    "invalid_parameter": "invalid_request",
    "timeout": "timeout",
    "internal_error": "server_error",
}

RETRY_POLICY = {
    "rate_limited": {"max_retries": 5, "base_delay": 1.0, "jitter": True},
    "server_error": {"max_retries": 3, "base_delay": 2.0, "jitter": True},
    "timeout": {"max_retries": 2, "base_delay": 2.0, "jitter": True},
}
```

## Performance Optimization

### Recommended Settings

```python
PERFORMANCE_DEFAULTS = {
    "request_timeout": 60,  # seconds
    "max_retries": 3,
    "retry_delay": 1.0,
    "jitter": True,
    "connection_pool_size": 10,
    "stream_chunk_size": 1024,  # bytes
    "max_concurrent_requests": 5,
}
```

## Migration Guide

### From v1.0 to v2.0

1. **Update configuration format**:
   - Add `version: "2.0"` to YAML
   - Migrate to new `agents` section structure
   - Add `tracking`, `security`, `performance` sections

2. **Update code**:
   - Import `UnifiedGenerationConfig` from new types
   - Use `ConfigLoader` instead of manual env parsing
   - Add experiment tracking calls

3. **Environment variables**:
   - Rename `DEFAULT_MODEL` → use agent-specific vars
   - Add tracking vars: `WANDB_PROJECT`, `MLFLOW_TRACKING_URI`
   - Add security vars: `PII_REDACTION`, `PII_REDACTION_LEVEL`

## Implementation Checklist

- [ ] Update `backend/src/api/types.py` with v2 schemas
- [ ] Add `ConfigLoader` to `backend/src/config/`
- [ ] Add experiment tracking helpers to `backend/src/tracking/`
- [ ] Add LangChain adapter to `backend/src/adapters/`
- [ ] Update agent initialization to use `ConfigLoader`
- [ ] Add PII redaction to logging pipeline
- [ ] Implement error taxonomy mapping
- [ ] Add performance monitoring
- [ ] Update documentation and examples
- [ ] Add integration tests for all providers

## Conclusion

This v2.0 specification provides a production-ready framework for LLM provider parameter management with comprehensive support for experiment tracking, agent frameworks, security, and performance optimization. The unified interface enables seamless provider switching while maintaining type safety and observability.
