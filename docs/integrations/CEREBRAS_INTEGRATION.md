# Cerebras Inference API Integration

This document describes the Cerebras Inference API integration added to the AI Resume Optimizer project.

## Overview

Cerebras provides high-performance LLM inference through an OpenAI-compatible API. The integration supports three powerful models optimized for different use cases.

## Supported Models

### 1. Qwen 3 235B Instruct (`qwen-3-235b-a22b-instruct-2507`)

**Capabilities:**
- Powerful multilingual support
- Strong instruction following
- Excellent logical reasoning and mathematics
- Advanced coding capabilities
- Tool usage support

**Context & Performance:**
- Context window: 131k tokens (paid tier), 65k tokens (free tier)
- Maximum output: 40k tokens (paid tier), 32k tokens (free tier)
- Speed: ~1,400 tokens/second

**Pricing:**
- Input: $0.60 per million tokens
- Output: $1.20 per million tokens

**Use Cases:**
- Complex reasoning tasks
- Multi-step problem solving
- Code generation and analysis
- Document processing with large context requirements

### 2. GPT OSS 120B (`gpt-oss-120b`)

**Capabilities:**
- Efficient reasoning across science, math, and coding
- Real-time coding assistance
- Document processing
- Research workflows
- Reasoning mode support

**Context & Performance:**
- Context window: 131k tokens (paid tier), 65k tokens (free tier)
- Maximum output: 40k tokens (paid tier), 32k tokens (free tier)
- Speed: ~3,000 tokens/second

**Pricing:**
- Input: $0.35 per million tokens
- Output: $0.75 per million tokens

**Use Cases:**
- Fast document processing
- Real-time applications requiring high throughput
- Cost-effective inference for large-scale tasks

### 3. Qwen 3 Coder 480B (`qwen-3-coder-480b`)

**Capabilities:**
- Ultra-efficient agentic code generation
- State-of-the-art programming performance
- Multi-language support
- Long context understanding
- Tool calling (including multi-turn)
- Structured outputs

**Context & Performance:**
- Context window: 131k tokens (paid tier), 65k tokens (free tier)
- Maximum output: 40k tokens (paid tier), 40k tokens (free tier)
- Speed: ~2,000 tokens/second

**Pricing:**
- Input: $2.00 per million tokens
- Output: $2.00 per million tokens

**Use Cases:**
- Advanced code generation and refactoring
- Agentic programming workflows
- Multi-turn coding conversations
- Large codebase analysis
- Complex software architecture design

**Important Notes:**
- ⚠️ **Deprecation Notice:** This model will be discontinued on **November 5, 2025**
- Migration to `zai-glm-4.6` is recommended for long-term projects
- Recommended settings: temperature=0.7, top_p=0.8
- Non-thinking mode only (no `<think>` tags)

## Configuration

### 1. Get API Key

Sign up at [Cerebras Inference](https://cerebras.ai) to obtain your API key.

### 2. Set Environment Variable

Add the following to your `backend/.env` file:

```bash
CEREBRAS_API_KEY=your_cerebras_api_key_here
```

### 3. Use in Application

Use models with the `cerebras::` prefix:

```python
# In agent configuration or service code
model = "cerebras::qwen-3-235b-a22b-instruct-2507"
# or
model = "cerebras::gpt-oss-120b"
# or
model = "cerebras::qwen-3-coder-480b"
```

## Technical Details

### API Endpoint

Base URL: `https://api.cerebras.ai/v1`

### Capabilities

Both Cerebras models support:
- ✅ Streaming responses
- ✅ Structured outputs
- ✅ Tool calling
- ✅ Chat completions

Limitations:
- ❌ Image/file inputs (text-only)
- ❌ Thinking budget parameter (GPT OSS 120B supports reasoning mode through standard API)
- ❌ Streaming not supported for reasoning models with JSON mode or tool calling

### Cost Tracking

The `CerebrasClient` automatically tracks:
- Input token count (estimated)
- Output token count (estimated)
- Per-request cost
- Cumulative cost across requests

Access cost information:
```python
client = CerebrasClient()
# After streaming completion
last_cost = client.get_last_cost()
total_cost = client.get_total_cost()
```

## Architecture

### Client Implementation

**File:** `backend/src/api/cerebras.py`

The `CerebrasClient` class:
- Extends the OpenAI SDK with Cerebras base URL
- Implements streaming completion interface
- Provides cost tracking and token estimation
- Handles text-only content (Cerebras models don't support image inputs)

### Model Registry

**File:** `backend/src/api/model_registry.py`

Registered models:
- `cerebras::qwen-3-235b-a22b-instruct-2507`
- `cerebras::gpt-oss-120b`

Each entry includes:
- Provider: `"cerebras"`
- Capabilities: Text-only, no image/file support
- API model identifier

### Client Factory

**File:** `backend/src/api/client_factory.py`

The factory pattern:
1. Detects `cerebras::` prefix
2. Routes to `CerebrasClient`
3. Caches client instance for reuse

## Usage Examples

### Direct Client Usage

```python
from src.api.cerebras import CerebrasClient

client = CerebrasClient(api_key="your_key")

# Stream completion
stream = client.stream_completion(
    prompt="You are a helpful assistant.",
    model="qwen-3-235b-a22b-instruct-2507",
    text_content="Explain quantum computing",
    temperature=0.7,
    max_tokens=2000
)

for chunk in stream:
    print(chunk, end="", flush=True)

# Get metadata (returned after stream exhaustion)
try:
    while True:
        chunk = next(stream)
        print(chunk, end="")
except StopIteration as e:
    metadata = e.value
    print(f"\nCost: ${metadata['cost']:.4f}")
```

### Multi-Provider Client

```python
from src.api.multiprovider import MultiProviderClient

client = MultiProviderClient()

# Automatically routes to CerebrasClient based on model prefix
stream = client.stream_completion(
    prompt="You are a code reviewer.",
    model="cerebras::gpt-oss-120b",
    text_content="Review this Python function...",
    temperature=0.5,
    max_tokens=1500
)

for chunk in stream:
    print(chunk, end="")
```

### In Agent Configuration

Agents can use Cerebras models by specifying the model name:

```python
# In agent instantiation
from src.agents.base import BaseAgent

agent = BaseAgent(
    name="ResumeOptimizer",
    prompt_file="agent2_resume_optimizer.md",
    model="cerebras::qwen-3-235b-a22b-instruct-2507"
)
```

## Performance Characteristics

### Speed Comparison

| Model | Tokens/Second | Best For |
|-------|--------------|----------|
| Qwen 3 235B | ~1,400 | Complex reasoning, detailed analysis |
| GPT OSS 120B | ~3,000 | Fast document processing, real-time apps |
| Qwen 3 Coder 480B | ~2,000 | Code generation, agentic workflows |

### Cost Comparison (per 1M tokens)

| Model | Input | Output | Total (typical 50/50 mix) |
|-------|-------|--------|---------------------------|
| Qwen 3 235B | $0.60 | $1.20 | $0.90 |
| GPT OSS 120B | $0.35 | $0.75 | $0.55 |
| Qwen 3 Coder 480B | $2.00 | $2.00 | $2.00 |

## Best Practices

### When to Use Cerebras

✅ **Good Use Cases:**
- Large document processing (up to 131k context)
- High-throughput requirements (3k tokens/sec)
- Cost-sensitive projects (competitive pricing)
- Code generation and analysis
- Mathematical and logical reasoning

❌ **Not Suitable For:**
- Tasks requiring image/vision capabilities
- Multimodal applications
- Use cases requiring file upload analysis

### Model Selection

**Choose Qwen 3 235B when:**
- You need the highest quality output
- Complex reasoning is required
- Multilingual support is important
- Cost is less of a concern

**Choose GPT OSS 120B when:**
- Speed is the priority
- Cost optimization is important
- Processing high volumes
- Real-time responsiveness needed

**Choose Qwen 3 Coder 480B when:**
- Code generation is the primary task
- Working with agentic programming workflows
- Need state-of-the-art coding performance
- Multi-turn coding conversations
- Large codebase analysis required
- ⚠️ Note: Consider deprecation timeline (Nov 5, 2025)

## Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'openai'`

**Solution:** Install dependencies:
```bash
cd backend
uv sync
```

**Issue:** `ValueError: Cerebras API key not provided`

**Solution:** Set the environment variable:
```bash
export CEREBRAS_API_KEY=your_key_here
```

**Issue:** API returns 401 Unauthorized

**Solution:** Verify your API key is valid and active at [Cerebras Dashboard](https://cerebras.ai/dashboard)

**Issue:** Rate limiting errors

**Solution:** Check your tier limits:
- Free: 30 requests/min, 60k input tokens/min
- Developer: 1,000 requests/min, 1M input tokens/min

## Testing

Verify the integration:

```bash
cd backend
python -m py_compile src/api/cerebras.py
python -m py_compile src/api/model_registry.py
python -m py_compile src/api/client_factory.py
```

All syntax checks should pass.

## Additional Resources

- [Cerebras API Documentation](https://inference-docs.cerebras.ai/resources/openai)
- [Qwen 3 235B Model Docs](https://inference-docs.cerebras.ai/models/qwen-3-235b-2507)
- [GPT OSS 120B Model Docs](https://inference-docs.cerebras.ai/models/openai-oss)
- [Qwen 3 Coder 480B Model Docs](https://inference-docs.cerebras.ai/models/qwen-3-480b)
- [Cerebras Dashboard](https://cerebras.ai/dashboard)

## Changelog

### 2025-10-31 - Added Qwen 3 Coder 480B

- Added `cerebras::qwen-3-coder-480b` model support
- Updated pricing table with new model costs ($2.00/M tokens)
- Added model selection guidance for code generation use cases
- Updated performance comparison tables

### 2025-10-31 - Initial Integration

- Added `CerebrasClient` class with OpenAI-compatible interface
- Registered initial models in model registry:
  - `cerebras::qwen-3-235b-a22b-instruct-2507`
  - `cerebras::gpt-oss-120b`
- Updated client factory with Cerebras provider support
- Added environment variable configuration
- Updated documentation (CLAUDE.md, README.md)
- Added cost tracking and token estimation
