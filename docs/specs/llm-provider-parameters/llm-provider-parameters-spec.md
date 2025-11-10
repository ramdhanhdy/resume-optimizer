# LLM Provider Parameters Specification

## Executive Summary

This document provides a comprehensive technical specification for parameter handling across all supported LLM providers in the Resume Optimizer system. It analyzes parameter variations, naming conventions, supported features, and configuration differences to enable flexible integration while maintaining a consistent developer experience.

### Supported Providers
- **OpenRouter** - Multi-provider marketplace with 400+ models
- **Zenmux** - OpenAI-compatible API with premium models
- **Google Gemini** - Native Google AI models with multimodal support
- **Cerebras** - High-performance inference for large models
- **Meituan LongCat** - Advanced MoE models with thinking capabilities

## Provider Comparison Matrix

| Parameter | OpenRouter | Zenmux | Gemini | Cerebras | LongCat |
|-----------|------------|--------|---------|----------|---------|
| **Base URL** | `https://openrouter.ai/api/v1` | `https://zenmux.ai/api/v1` | Native SDK | `https://api.cerebras.ai/v1` | `https://api.longcat.chat/openai` |
| **API Format** | OpenAI-compatible | OpenAI-compatible | Google GenAI SDK | OpenAI-compatible | OpenAI-compatible |
| **Temperature Range** | 0.0-2.0 | 0.0-2.0 | 0.0-2.0 | 0.0-1.5 | 0.0-1.0 |
| **Max Tokens** | `max_tokens` | `max_tokens` | `max_output_tokens` | `max_tokens` | `max_tokens` |
| **Default Max Tokens** | 4000 | 6000 | 4000 | 4000 | 10000 |
| **Streaming Support** | ✅ SSE | ✅ SSE | ✅ Native | ✅ SSE | ✅ SSE |
| **File Upload** | ✅ Images/PDFs | ✅ Images/PDFs | ✅ Multimodal | ❌ Text-only | ❌ Text-only |
| **Thinking Budget** | ❌ | ❌ | ✅ `thinking_config` | ❌ | ✅ `thinking_budget` |
| **System Prompt** | `messages[0]` | `messages[0]` | `system_instruction` | `messages[0]` | `messages[0]` |
| **Response Format** | ✅ JSON mode | ✅ JSON mode | ✅ `response_mime_type` | ✅ JSON mode | ❌ |
| **Top P Support** | ✅ `top_p` | ✅ `top_p` | ✅ `topP` | ✅ `top_p` | ✅ `top_p` |
| **Stop Sequences** | ✅ `stop` | ✅ `stop` | ✅ `stopSequences` | ❌ | ❌ |
| **Seed Parameter** | ✅ `seed` | ✅ `seed` | ✅ `seed` | ✅ `seed` | ❌ |
| **Usage Tracking** | ✅ Response headers | ❌ Estimation | ✅ Usage metadata | ❌ Estimation | ❌ Estimation |

## Detailed Parameter Analysis

### 1. OpenRouter Parameters

```typescript
interface OpenRouterParams {
  model: string;
  messages: ChatMessage[];
  temperature?: number; // 0.0-2.0, default 1.0
  max_tokens?: number; // default varies by model
  top_p?: number; // default 1.0
  top_k?: number; // default 0
  frequency_penalty?: number; // -2.0 to 2.0
  presence_penalty?: number; // -2.0 to 2.0
  repetition_penalty?: number; // default 1.0
  seed?: integer; // for deterministic outputs
  stop?: string | string[]; // stop sequences
  stream?: boolean; // default false
  response_format?: object; // JSON mode
  tools?: array; // function calling
  tool_choice?: string | object; // tool selection
  parallel_tool_calls?: boolean; // default true
  // OpenRouter-specific
  models?: string[]; // fallback models
  route?: string; // routing strategy
  provider?: object; // provider preferences
}
```

**Unique Features:**
- Multi-provider routing with fallbacks
- Per-model pricing and limits
- Provider-specific preferences
- Comprehensive function calling support

### 2. Zenmux Parameters

```typescript
interface ZenmuxParams {
  model: string;
  messages: ChatMessage[];
  temperature?: number; // 0.0-2.0, default 1.0
  max_completion_tokens?: integer; // includes reasoning
  max_tokens?: integer; // legacy support
  top_p?: number; // default 1.0
  frequency_penalty?: number; // -2.0 to 2.0
  presence_penalty?: number; // -2.0 to 2.0
  seed?: integer;
  logit_bias?: map; // token biasing
  logprobs?: boolean; // default false
  top_logprobs?: integer; // 0-20
  response_format?: object; // structured output
  stop?: string | string[];
  tools?: array;
  tool_choice?: string | object;
  stream?: boolean; // default false
}
```

**Unique Features:**
- `max_completion_tokens` for models with reasoning
- Advanced logprobs support
- Structured output with schema enforcement
- JSON schema validation

### 3. Google Gemini Parameters

```typescript
interface GeminiParams {
  model: string;
  contents: Content[];
  systemInstruction?: Content;
  generationConfig: {
    temperature?: number; // 0.0-2.0, default 1.0
    topP?: number; // default 0.95
    topK?: number; // default 40
    candidateCount?: integer; // default 1
    maxOutputTokens?: integer;
    presencePenalty?: float; // 0.0-1.0
    frequencyPenalty?: float; // 0.0-1.0
    stopSequences?: string[];
    responseMimeType?: string; // "application/json"
    responseSchema?: Schema; // structured output
    seed?: integer;
    responseLogprobs?: boolean;
    logprobs?: integer;
    audioTimestamp?: boolean;
    thinkingConfig?: {
      thinkingBudget?: integer;
    };
  };
  tools?: Tool[];
  toolConfig?: ToolConfig;
  safetySettings?: SafetySetting[];
}
```

**Unique Features:**
- Native multimodal support (text, images, audio, video)
- `thinkingConfig` for reasoning models
- Structured output with JSON schema
- Advanced safety settings
- Content-based conversation structure

### 4. Cerebras Parameters

```typescript
interface CerebrasParams {
  model: string;
  messages: ChatMessage[];
  temperature?: number; // 0.0-1.5, default 0.7
  max_tokens?: integer; // default varies by model
  top_p?: number; // default 1.0
  seed?: number;
  stream?: boolean; // default false
  response_format?: {
    type: "json_object" | "json_schema";
    json_schema?: {
      name: string;
      strict: boolean;
      schema: object;
    };
  };
  // Cerebras-specific
  logprobs?: boolean; // default false
  top_logprobs?: integer; // 0-20
}
```

**Unique Features:**
- High-performance inference optimizations
- JSON schema enforcement (beta)
- Extended context support (up to 200K tokens)
- Specialized for large models (Qwen 235B, GPT-OSS 120B)

### 5. Meituan LongCat Parameters

```typescript
interface LongCatParams {
  model: string; // "LongCat-Flash-Chat" | "LongCat-Flash-Thinking"
  messages: ChatMessage[];
  temperature?: number; // 0.0-1.0, default 0.7
  max_tokens?: integer; // default 1024
  top_p?: number;
  stream?: boolean; // default false
  // LongCat-specific
  enable_thinking?: boolean; // default false
  thinking_budget?: integer; // min 1024, default 1024
}
```

**Unique Features:**
- MoE architecture with dynamic computation
- Thinking mode with budget control
- Long context support (128K tokens)
- Specialized for agentic tasks

## Unified Parameter Interface Design

### Core Parameter Schema

```python
from typing import Optional, Dict, Any, List, Union
from enum import Enum

class ProviderType(Enum):
    OPENROUTER = "openrouter"
    ZENMUX = "zenmux"
    GEMINI = "gemini"
    CEREBRAS = "cerebras"
    LONGCAT = "longcat"

class UnifiedGenerationConfig(TypedDict, total=False):
    """Unified generation configuration across all providers."""
    temperature: float  # 0.0-2.0 (normalized)
    max_tokens: int  # Unified token limit
    top_p: float  # 0.0-1.0
    top_k: Optional[int]  # Provider-specific
    frequency_penalty: float  # -2.0 to 2.0
    presence_penalty: float  # -2.0 to 2.0
    seed: Optional[int]  # Deterministic outputs
    stop: Union[str, List[str]]  # Stop sequences
    stream: bool  # Streaming enabled
    # Advanced features
    thinking_budget: Optional[int]  # For reasoning models
    response_format: Optional[Dict[str, Any]]  # Structured output
    tools: Optional[List[Dict[str, Any]]]  # Function calling
    tool_choice: Optional[Union[str, Dict[str, Any]]]  # Tool selection
    # Provider-specific options
    provider_options: Dict[str, Any]  # Provider-specific parameters

class UnifiedCompletionRequest(TypedDict, total=False):
    """Unified request format for all providers."""
    model: str
    provider: ProviderType
    system_prompt: str
    user_text: Optional[str]
    messages: Optional[List[Dict[str, Any]]]  # Alternative to prompt+text
    files: Optional[List[Dict[str, Any]]]  # File attachments
    generation: UnifiedGenerationConfig
    metadata: Optional[Dict[str, Any]]  # Request metadata
```

### Parameter Mapping Functions

```python
class ParameterMapper:
    """Maps unified parameters to provider-specific formats."""
    
    @staticmethod
    def to_openrouter(config: UnifiedGenerationConfig) -> Dict[str, Any]:
        """Convert unified config to OpenRouter format."""
        return {
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 4000),
            "top_p": config.get("top_p"),
            "top_k": config.get("top_k"),
            "frequency_penalty": config.get("frequency_penalty"),
            "presence_penalty": config.get("presence_penalty"),
            "repetition_penalty": config.get("presence_penalty"),  # Map to repetition
            "seed": config.get("seed"),
            "stop": config.get("stop"),
            "stream": config.get("stream", False),
            "response_format": config.get("response_format"),
            "tools": config.get("tools"),
            "tool_choice": config.get("tool_choice"),
            "parallel_tool_calls": True,
            # OpenRouter-specific
            "models": config.get("provider_options", {}).get("fallback_models"),
            "route": config.get("provider_options", {}).get("route"),
            "provider": config.get("provider_options", {}).get("provider_preferences"),
        }
    
    @staticmethod
    def to_zenmux(config: UnifiedGenerationConfig) -> Dict[str, Any]:
        """Convert unified config to Zenmux format."""
        return {
            "temperature": config.get("temperature", 0.7),
            "max_completion_tokens": config.get("max_tokens", 6000),
            "max_tokens": config.get("max_tokens"),  # Legacy support
            "top_p": config.get("top_p"),
            "frequency_penalty": config.get("frequency_penalty"),
            "presence_penalty": config.get("presence_penalty"),
            "seed": config.get("seed"),
            "logit_bias": config.get("provider_options", {}).get("logit_bias"),
            "logprobs": config.get("provider_options", {}).get("logprobs", False),
            "top_logprobs": config.get("provider_options", {}).get("top_logprobs"),
            "response_format": config.get("response_format"),
            "stop": config.get("stop"),
            "tools": config.get("tools"),
            "tool_choice": config.get("tool_choice"),
            "stream": config.get("stream", False),
        }
    
    @staticmethod
    def to_gemini(config: UnifiedGenerationConfig) -> Dict[str, Any]:
        """Convert unified config to Gemini format."""
        generation_config = {
            "temperature": config.get("temperature", 0.7),
            "topP": config.get("top_p"),
            "topK": config.get("top_k"),
            "maxOutputTokens": config.get("max_tokens", 4000),
            "presencePenalty": max(0.0, min(1.0, config.get("presence_penalty", 0))),
            "frequencyPenalty": max(0.0, min(1.0, config.get("frequency_penalty", 0))),
            "stopSequences": config.get("stop") if isinstance(config.get("stop"), list) else [config.get("stop")] if config.get("stop") else None,
            "seed": config.get("seed"),
        }
        
        # Add thinking config for reasoning models
        if config.get("thinking_budget"):
            generation_config["thinkingConfig"] = {
                "thinkingBudget": config.get("thinking_budget")
            }
        
        # Add response format
        if config.get("response_format"):
            if config.get("response_format", {}).get("type") == "json_object":
                generation_config["responseMimeType"] = "application/json"
            elif config.get("response_format", {}).get("type") == "json_schema":
                generation_config["responseMimeType"] = "application/json"
                generation_config["responseSchema"] = config.get("response_format", {}).get("json_schema", {}).get("schema")
        
        return generation_config
    
    @staticmethod
    def to_cerebras(config: UnifiedGenerationConfig) -> Dict[str, Any]:
        """Convert unified config to Cerebras format."""
        return {
            "temperature": max(0.0, min(1.5, config.get("temperature", 0.7))),
            "max_tokens": config.get("max_tokens", 4000),
            "top_p": config.get("top_p"),
            "seed": config.get("seed"),
            "stream": config.get("stream", False),
            "response_format": config.get("response_format"),
            "logprobs": config.get("provider_options", {}).get("logprobs", False),
            "top_logprobs": config.get("provider_options", {}).get("top_logprobs"),
        }
    
    @staticmethod
    def to_longcat(config: UnifiedGenerationConfig) -> Dict[str, Any]:
        """Convert unified config to LongCat format."""
        params = {
            "temperature": max(0.0, min(1.0, config.get("temperature", 0.7))),
            "max_tokens": config.get("max_tokens", 10000),
            "top_p": config.get("top_p"),
            "stream": config.get("stream", False),
        }
        
        # Add thinking parameters for thinking models
        if config.get("thinking_budget") or config.get("provider_options", {}).get("enable_thinking"):
            params["enable_thinking"] = True
            params["thinking_budget"] = config.get("thinking_budget", 1024)
        
        return params
```

## Validation Rules per Provider

### OpenRouter Validation
```python
def validate_openrouter_params(params: Dict[str, Any]) -> List[str]:
    """Validate OpenRouter parameters."""
    errors = []
    
    if "temperature" in params and not (0.0 <= params["temperature"] <= 2.0):
        errors.append("OpenRouter temperature must be between 0.0 and 2.0")
    
    if "max_tokens" in params and params["max_tokens"] < 1:
        errors.append("OpenRouter max_tokens must be at least 1")
    
    if "top_p" in params and not (0.0 <= params["top_p"] <= 1.0):
        errors.append("OpenRouter top_p must be between 0.0 and 1.0")
    
    if "frequency_penalty" in params and not (-2.0 <= params["frequency_penalty"] <= 2.0):
        errors.append("OpenRouter frequency_penalty must be between -2.0 and 2.0")
    
    if "presence_penalty" in params and not (-2.0 <= params["presence_penalty"] <= 2.0):
        errors.append("OpenRouter presence_penalty must be between -2.0 and 2.0")
    
    return errors
```

### Zenmux Validation
```python
def validate_zenmux_params(params: Dict[str, Any]) -> List[str]:
    """Validate Zenmux parameters."""
    errors = []
    
    if "temperature" in params and not (0.0 <= params["temperature"] <= 2.0):
        errors.append("Zenmux temperature must be between 0.0 and 2.0")
    
    if "max_completion_tokens" in params and params["max_completion_tokens"] < 1:
        errors.append("Zenmux max_completion_tokens must be at least 1")
    
    if "top_logprobs" in params and not (0 <= params["top_logprobs"] <= 20):
        errors.append("Zenmux top_logprobs must be between 0 and 20")
    
    return errors
```

### Gemini Validation
```python
def validate_gemini_params(params: Dict[str, Any]) -> List[str]:
    """Validate Gemini parameters."""
    errors = []
    
    if "temperature" in params and not (0.0 <= params["temperature"] <= 2.0):
        errors.append("Gemini temperature must be between 0.0 and 2.0")
    
    if "topP" in params and not (0.0 <= params["topP"] <= 1.0):
        errors.append("Gemini topP must be between 0.0 and 1.0")
    
    if "topK" in params and params["topK"] < 1:
        errors.append("Gemini topK must be at least 1")
    
    if "presencePenalty" in params and not (0.0 <= params["presencePenalty"] <= 1.0):
        errors.append("Gemini presencePenalty must be between 0.0 and 1.0")
    
    if "thinkingBudget" in params and params["thinkingBudget"] < 1024:
        errors.append("Gemini thinkingBudget must be at least 1024")
    
    return errors
```

### Cerebras Validation
```python
def validate_cerebras_params(params: Dict[str, Any]) -> List[str]:
    """Validate Cerebras parameters."""
    errors = []
    
    if "temperature" in params and not (0.0 <= params["temperature"] <= 1.5):
        errors.append("Cerebras temperature must be between 0.0 and 1.5")
    
    if "max_tokens" in params and params["max_tokens"] < 1:
        errors.append("Cerebras max_tokens must be at least 1")
    
    if "top_logprobs" in params and not (0 <= params["top_logprobs"] <= 20):
        errors.append("Cerebras top_logprobs must be between 0 and 20")
    
    return errors
```

### LongCat Validation
```python
def validate_longcat_params(params: Dict[str, Any]) -> List[str]:
    """Validate LongCat parameters."""
    errors = []
    
    if "temperature" in params and not (0.0 <= params["temperature"] <= 1.0):
        errors.append("LongCat temperature must be between 0.0 and 1.0")
    
    if "max_tokens" in params and params["max_tokens"] < 1:
        errors.append("LongCat max_tokens must be at least 1")
    
    if "thinking_budget" in params and params["thinking_budget"] < 1024:
        errors.append("LongCat thinking_budget must be at least 1024")
    
    # Check thinking model compatibility
    if params.get("enable_thinking") and not params.get("model", "").startswith("LongCat-Flash-Thinking"):
        errors.append("LongCat enable_thinking requires LongCat-Flash-Thinking model")
    
    return errors
```

## Migration Pathways for Parameter Changes

### 1. Legacy Parameter Deprecation

```python
# Migration map for deprecated parameters
DEPRECATED_PARAMS = {
    "openrouter": {
        "max_completion_tokens": "max_tokens",  # v1 -> v2
        "model_list": "models",  # v1 -> v2
    },
    "zenmux": {
        "max_tokens": "max_completion_tokens",  # Legacy -> current
    },
    "gemini": {
        "max_tokens": "maxOutputTokens",  # v1 -> v2
        "top_p": "topP",  # v1 -> v2
        "stop": "stopSequences",  # v1 -> v2
    },
}

def migrate_deprecated_params(provider: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate deprecated parameters to current format."""
    migrated = params.copy()
    
    if provider in DEPRECATED_PARAMS:
        for old_param, new_param in DEPRECATED_PARAMS[provider].items():
            if old_param in migrated:
                migrated[new_param] = migrated.pop(old_param)
    
    return migrated
```

### 2. Parameter Normalization

```python
def normalize_parameter_ranges(provider: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize parameter ranges across providers."""
    normalized = params.copy()
    
    # Temperature normalization
    if "temperature" in normalized:
        temp = normalized["temperature"]
        if provider == "cerebras":
            normalized["temperature"] = max(0.0, min(1.5, temp))
        elif provider == "longcat":
            normalized["temperature"] = max(0.0, min(1.0, temp))
        else:
            normalized["temperature"] = max(0.0, min(2.0, temp))
    
    # Penalty normalization for Gemini
    if provider == "gemini":
        if "frequency_penalty" in normalized:
            normalized["frequency_penalty"] = max(0.0, min(1.0, normalized["frequency_penalty"]))
        if "presence_penalty" in normalized:
            normalized["presence_penalty"] = max(0.0, min(1.0, normalized["presence_penalty"]))
    
    return normalized
```

### 3. Feature Compatibility Matrix

```python
FEATURE_COMPATIBILITY = {
    "streaming": {
        "openrouter": {"supported": True, "format": "SSE"},
        "zenmux": {"supported": True, "format": "SSE"},
        "gemini": {"supported": True, "format": "Native"},
        "cerebras": {"supported": True, "format": "SSE"},
        "longcat": {"supported": True, "format": "SSE"},
    },
    "file_upload": {
        "openrouter": {"supported": True, "types": ["image", "pdf", "document"]},
        "zenmux": {"supported": True, "types": ["image", "pdf", "document"]},
        "gemini": {"supported": True, "types": ["image", "audio", "video", "pdf", "document"]},
        "cerebras": {"supported": False, "types": []},
        "longcat": {"supported": False, "types": []},
    },
    "thinking_mode": {
        "openrouter": {"supported": False},
        "zenmux": {"supported": False},
        "gemini": {"supported": True, "models": ["gemini-2.5-flash"]},
        "cerebras": {"supported": False},
        "longcat": {"supported": True, "models": ["LongCat-Flash-Thinking"]},
    },
    "structured_output": {
        "openrouter": {"supported": True, "format": "json_mode"},
        "zenmux": {"supported": True, "format": "json_schema"},
        "gemini": {"supported": True, "format": "response_schema"},
        "cerebras": {"supported": True, "format": "json_schema"},
        "longcat": {"supported": False},
    },
    "function_calling": {
        "openrouter": {"supported": True, "parallel": True},
        "zenmux": {"supported": True, "parallel": False},
        "gemini": {"supported": True, "parallel": True},
        "cerebras": {"supported": False},
        "longcat": {"supported": False},
    },
}
```

## Code Examples for Each Parameter Set

### OpenRouter Example
```python
from src.api.openrouter import OpenRouterClient

client = OpenRouterClient()

# Advanced configuration with provider-specific features
response = client.stream_completion(
    prompt="You are a resume optimization expert.",
    model="anthropic/claude-3.5-sonnet",
    text_content="Optimize this resume for a software engineering role.",
    temperature=0.7,
    max_tokens=4000,
    top_p=0.9,
    frequency_penalty=0.1,
    presence_penalty=0.1,
    seed=42,
    stop=["\n\n", "END"],
    response_format={"type": "json_object"},
    tools=[{
        "type": "function",
        "function": {
            "name": "analyze_resume",
            "description": "Analyze resume for job matching",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_text": {"type": "string"},
                    "job_description": {"type": "string"}
                }
            }
        }
    }],
    tool_choice="auto"
)
```

### Zenmux Example
```python
from src.api.zenmux import ZenmuxClient

client = ZenmuxClient()

# Structured output with schema validation
response = client.stream_completion(
    prompt="Generate a professional resume summary.",
    model="openai/gpt-5",
    text_content="Senior Software Engineer with 5 years experience",
    temperature=0.5,
    max_completion_tokens=6000,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "resume_summary",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "key_skills": {"type": "array", "items": {"type": "string"}},
                    "years_experience": {"type": "integer"}
                },
                "required": ["summary", "key_skills", "years_experience"]
            }
        }
    },
    logprobs=True,
    top_logprobs=5
)
```

### Gemini Example
```python
from src.api.gemini import GeminiClient

client = GeminiClient()

# Multimodal with thinking mode
response = client.stream_completion(
    prompt="Analyze this resume and provide optimization suggestions.",
    model="gemini-2.5-flash",
    text_content="Resume content here",
    file_path="resume.pdf",
    file_type="application/pdf",
    temperature=0.8,
    max_output_tokens=4000,
    thinking_budget=2048,
    response_mime_type="application/json",
    stop=["---END---"],
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}
    ]
)
```

### Cerebras Example
```python
from src.api.cerebras import CerebrasClient

client = CerebrasClient()

# High-performance large model inference
response = client.stream_completion(
    prompt="You are an expert career coach.",
    model="qwen-3-235b-a22b-instruct-2507",
    text_content="Help me improve my resume for a tech lead position.",
    temperature=0.6,
    max_tokens=8000,
    top_p=0.95,
    seed=123,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "career_advice",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "recommendations": {"type": "array"},
                    "priority_score": {"type": "number"}
                }
            }
        }
    }
)
```

### LongCat Example
```python
from src.api.longcat import LongCatClient

client = LongCatClient()

# Thinking mode with budget control
response = client.stream_completion(
    prompt="Provide detailed resume optimization analysis.",
    model="LongCat-Flash-Thinking",
    text_content="Resume for senior developer position",
    temperature=0.7,
    max_tokens=15000,
    enable_thinking=True,
    thinking_budget=4096,
    top_p=0.9
)
```

## Implementation Recommendations

### 1. Unified Client Interface

```python
class UnifiedLLMClient:
    """Unified interface for all LLM providers."""
    
    def __init__(self, provider: ProviderType, **kwargs):
        self.provider = provider
        self.client = self._create_client(provider, **kwargs)
        self.mapper = ParameterMapper()
    
    def _create_client(self, provider: ProviderType, **kwargs):
        """Create provider-specific client."""
        if provider == ProviderType.OPENROUTER:
            return OpenRouterClient(**kwargs)
        elif provider == ProviderType.ZENMUX:
            return ZenmuxClient(**kwargs)
        elif provider == ProviderType.GEMINI:
            return GeminiClient(**kwargs)
        elif provider == ProviderType.CEREBRAS:
            return CerebrasClient(**kwargs)
        elif provider == ProviderType.LONGCAT:
            return LongCatClient(**kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def stream_completion(
        self,
        request: UnifiedCompletionRequest
    ) -> Generator[str, None, Dict[str, Any]]:
        """Stream completion with unified interface."""
        # Validate parameters
        errors = self._validate_params(request)
        if errors:
            raise ValueError(f"Parameter validation failed: {errors}")
        
        # Map parameters to provider format
        provider_params = self._map_params(request)
        
        # Call provider-specific method
        return self.client.stream_completion(**provider_params)
    
    def _validate_params(self, request: UnifiedCompletionRequest) -> List[str]:
        """Validate parameters for the specific provider."""
        validators = {
            ProviderType.OPENROUTER: validate_openrouter_params,
            ProviderType.ZENMUX: validate_zenmux_params,
            ProviderType.GEMINI: validate_gemini_params,
            ProviderType.CEREBRAS: validate_cerebras_params,
            ProviderType.LONGCAT: validate_longcat_params,
        }
        
        validator = validators.get(self.provider)
        if validator:
            return validator(request.get("generation", {}))
        return []
    
    def _map_params(self, request: UnifiedCompletionRequest) -> Dict[str, Any]:
        """Map unified parameters to provider format."""
        mappers = {
            ProviderType.OPENROUTER: self.mapper.to_openrouter,
            ProviderType.ZENMUX: self.mapper.to_zenmux,
            ProviderType.GEMINI: self.mapper.to_gemini,
            ProviderType.CEREBRAS: self.mapper.to_cerebras,
            ProviderType.LONGCAT: self.mapper.to_longcat,
        }
        
        mapper = mappers.get(self.provider)
        if mapper:
            return mapper(request.get("generation", {}))
        return {}
```

### 2. Configuration Management

```python
# config/llm_providers.yaml
providers:
  openrouter:
    api_key_env: OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1
    default_model: anthropic/claude-3.5-sonnet
    max_tokens: 4000
    temperature_range: [0.0, 2.0]
    features:
      - streaming
      - file_upload
      - function_calling
      - structured_output
  
  zenmux:
    api_key_env: ZENMUX_API_KEY
    base_url: https://zenmux.ai/api/v1
    default_model: openai/gpt-5
    max_tokens: 6000
    temperature_range: [0.0, 2.0]
    features:
      - streaming
      - file_upload
      - structured_output
      - logprobs
  
  gemini:
    api_key_env: GEMINI_API_KEY
    default_model: gemini-2.5-flash
    max_tokens: 4000
    temperature_range: [0.0, 2.0]
    features:
      - streaming
      - multimodal
      - thinking_mode
      - structured_output
      - function_calling
  
  cerebras:
    api_key_env: CEREBRAS_API_KEY
    base_url: https://api.cerebras.ai/v1
    default_model: qwen-3-235b-a22b-instruct-2507
    max_tokens: 4000
    temperature_range: [0.0, 1.5]
    features:
      - streaming
      - structured_output
      - high_performance
  
  longcat:
    api_key_env: LONGCAT_API_KEY
    base_url: https://api.longcat.chat/openai
    default_model: LongCat-Flash-Chat
    max_tokens: 10000
    temperature_range: [0.0, 1.0]
    features:
      - streaming
      - thinking_mode
      - long_context
      - moe_architecture
```

### 3. Error Handling and Fallbacks

```python
class ProviderManager:
    """Manages multiple providers with fallback support."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = self._initialize_providers()
        self.fallback_chain = self._build_fallback_chain()
    
    def stream_with_fallback(
        self,
        request: UnifiedCompletionRequest
    ) -> Generator[str, None, Dict[str, Any]]:
        """Attempt streaming with fallback providers."""
        last_error = None
        
        for provider_name in self.fallback_chain:
            try:
                provider = self.providers[provider_name]
                yield from provider.stream_completion(request)
                return
            except Exception as e:
                last_error = e
                print(f"Provider {provider_name} failed: {e}")
                continue
        
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    def _build_fallback_chain(self) -> List[str]:
        """Build provider fallback chain based on capabilities."""
        # Prioritize providers that support required features
        required_features = self.config.get("required_features", [])
        
        available_providers = []
        for name, config in self.config["providers"].items():
            if all(feature in config["features"] for feature in required_features):
                available_providers.append(name)
        
        return available_providers or list(self.providers.keys())
```

## Future Considerations

### 1. Emerging Provider Support
- **Anthropic Claude API** - Direct integration for Claude models
- **OpenAI API** - Direct GPT model access
- **Cohere** - Enterprise-focused models
- **Mistral AI** - European model provider
- **Stability AI** - Image and text generation

### 2. Advanced Parameter Features
- **Dynamic Parameter Adjustment** - Runtime parameter optimization
- **Cost-aware Routing** - Automatic provider selection based on cost
- **Performance Monitoring** - Real-time provider performance tracking
- **Parameter Learning** - ML-based parameter optimization

### 3. Standardization Efforts
- **OpenAI API Compatibility** - Maintain OpenAI-like interface
- **REST API Standardization** - Common REST patterns
- **WebSocket Streaming** - Real-time bidirectional communication
- **gRPC Support** - High-performance RPC for enterprise use

### 4. Security and Compliance
- **Parameter Validation** - Input sanitization and validation
- **Rate Limiting** - Per-provider rate limit handling
- **Audit Logging** - Parameter usage tracking
- **Data Privacy** - GDPR/CCPA compliance for parameters

### 5. Monitoring and Analytics
- **Parameter Effectiveness** - Track parameter impact on quality
- **Cost Optimization** - Parameter-based cost recommendations
- **Performance Metrics** - Latency and throughput by parameter set
- **Error Analysis** - Parameter-related error patterns

## Conclusion

This specification provides a comprehensive framework for handling parameter differences across LLM providers while maintaining a consistent developer experience. The unified interface design enables flexible provider switching, proper validation, and future extensibility.

Key benefits:
- **Provider Agnostic** - Single interface for all providers
- **Type Safety** - Comprehensive parameter validation
- **Future Proof** - Extensible design for new providers
- **Performance Optimized** - Provider-specific optimizations
- **Cost Aware** - Built-in cost tracking and optimization

Implementation of this specification will enable the Resume Optimizer system to leverage the unique capabilities of each provider while maintaining code consistency and reliability.
