# Gemini API Integration Specification

## Overview

This document specifies the integration of Google Gemini API as an LLM provider in the Resume Optimizer application, enabling multimodal AI capabilities with competitive pricing and high-quality models.

## Requirements

### Functional Requirements

1. **Multi-Provider Support**: Gemini should work alongside existing providers (OpenRouter, Zenmux, LongCat)
2. **Model Variety**: Support for multiple Gemini models with different capabilities and pricing
3. **Feature Parity**: Full compatibility with existing agent system and streaming infrastructure
4. **Cost Tracking**: Accurate token-based cost calculation using real API response data
5. **Error Handling**: Robust error handling and fallback mechanisms

### Technical Requirements

1. **Native SDK Integration**: Use official `google-genai` Python SDK, not OpenAI-compatible endpoints
2. **Streaming Support**: Full streaming response capability for real-time user experience
3. **Multimodal Input**: Support for text, images, and PDFs via base64 encoding
4. **System Instructions**: Proper handling of system prompts via GenerateContentConfig
5. **Thinking Budget**: Support for thinking tokens in 2.5 models

## Architecture

### Client Implementation (`backend/src/api/gemini.py`)

```python
class GeminiClient:
    """Google Gemini API client using official SDK"""
    
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model
    
    async def generate_stream(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_instruction: str = None,
        thinking_budget: int = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response with full parameter support"""
```

### Model Registry Integration

```python
# In backend/src/api/model_registry.py
ProviderName = Literal["openrouter", "zenmux", "longcat", "gemini"]

GEMINI_MODELS = {
    "gemini::gemini-2.5-flash": ModelInfo(
        provider="gemini",
        model_name="gemini-2.5-flash",
        context_length=1000000,
        input_cost_per_million=0.30,
        output_cost_per_million=2.50,
        supports_files=True,
        supports_images=True,
        supports_thinking_budget=True
    ),
    # ... other models
}
```

### Client Factory Integration

```python
# In backend/src/api/client_factory.py
def get_client(provider: str, model: str, api_key: str) -> ClientType:
    if provider == "gemini":
        return GeminiClient(api_key, model)
    # ... other providers
```

## Supported Models

| Model ID | Context | Input Cost | Output Cost | Features | Use Case |
|----------|---------|------------|-------------|----------|----------|
| `gemini::gemini-2.5-flash` | 1M tokens | $0.30/1M | $2.50/1M | Files, Images, Thinking | Default choice |
| `gemini::gemini-2.5-pro` | 1M tokens | $1.25/1M | $10.00/1M | Files, Images, Thinking | Complex tasks |
| `gemini::gemini-2.5-flash-lite` | 1M tokens | $0.10/1M | $0.40/1M | Files, Images | High volume |
| `gemini::gemini-2.0-flash` | 1M tokens | $0.10/1M | $0.40/1M | Files, Images | Production stable |

**Note**: Output costs include thinking tokens for 2.5 models. Free tier available with rate limits.

## API Integration Details

### Authentication

```python
# Environment variable
GEMINI_API_KEY=AIza... # Starts with "AI"

# Client initialization
client = genai.Client(api_key=api_key)
```

### Request Format

```python
response = client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents=[{"parts": [{"text": user_message}]}],
    config=types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temperature,
        max_output_tokens=max_tokens,
        thinking_budget=thinking_budget  # 2.5 models only
    )
)
```

### Response Handling

```python
async for chunk in response:
    if chunk.text:
        yield chunk.text
    if chunk.usage_metadata:
        # Track real token usage
        input_tokens = chunk.usage_metadata.prompt_token_count
        output_tokens = chunk.usage_metadata.candidates_token_count
        thinking_tokens = chunk.usage_metadata.total_token_count - input_tokens - output_tokens
```

## Configuration Requirements

### Environment Variables

```bash
# backend/.env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Dependencies

```toml
# backend/pyproject.toml
[tool.poetry.dependencies]
google-genai = ">=1.0.0"
```

### Model Selection UI

Users can select Gemini models in the application interface:
1. Navigate to Model Configuration section
2. Choose any Gemini model from the dropdown:
   - `gemini::gemini-2.5-flash` (recommended)
   - `gemini::gemini-2.5-pro`
   - `gemini::gemini-2.5-flash-lite`
   - `gemini::gemini-2.0-flash`

## Feature Support Matrix

| Feature | 2.5 Flash | 2.5 Pro | 2.5 Flash Lite | 2.0 Flash |
|---------|-----------|---------|----------------|-----------|
| Text Generation | ✅ | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ | ✅ |
| System Instructions | ✅ | ✅ | ✅ | ✅ |
| Temperature Control | ✅ | ✅ | ✅ | ✅ |
| Max Tokens | ✅ | ✅ | ✅ | ✅ |
| Image Input | ✅ | ✅ | ✅ | ✅ |
| PDF Input | ✅ | ✅ | ✅ | ✅ |
| Thinking Budget | ✅ | ✅ | ✅ | ❌ |
| 1M+ Context | ✅ | ✅ | ✅ | ✅ |

## Cost Tracking Implementation

### Real-Time Token Usage

```python
class CostTracker:
    def track_gemini_usage(self, usage_metadata):
        input_cost = (usage_metadata.prompt_token_count / 1_000_000) * self.input_cost_per_million
        output_cost = (usage_metadata.candidates_token_count / 1_000_000) * self.output_cost_per_million
        thinking_cost = (usage_metadata.thinking_token_count / 1_000_000) * self.output_cost_per_million
        return input_cost + output_cost + thinking_cost
```

### Model-Specific Pricing

- **Input tokens**: Billed at model-specific input rates
- **Output tokens**: Billed at model-specific output rates
- **Thinking tokens**: Included in output cost for 2.5 models
- **Free tier**: Rate-limited but no cost for development

## Error Handling

### API Errors

```python
try:
    response = await client.generate_content_stream(...)
except genai.types.APIError as e:
    if e.status_code == 429:
        # Rate limit exceeded
        await asyncio.sleep(retry_delay)
        # Retry with backoff
    elif e.status_code == 400:
        # Bad request - invalid parameters
        raise ValueError(f"Invalid request: {e.message}")
    else:
        # Other API errors
        raise RuntimeError(f"Gemini API error: {e.message}")
```

### Fallback Strategy

1. **Temporary Errors**: Retry with exponential backoff
2. **Rate Limits**: Switch to lower-tier model or provider
3. **Invalid Requests**: Validate parameters before retry
4. **Service Unavailable**: Fall back to alternative provider

## Testing Requirements

### Unit Tests

```python
# test_gemini_client.py
async def test_gemini_streaming():
    client = GeminiClient(api_key, "gemini-2.5-flash")
    chunks = []
    async for chunk in client.generate_stream([{"role": "user", "content": "Hello"}]):
        chunks.append(chunk)
    assert len(chunks) > 0

async def test_cost_tracking():
    client = GeminiClient(api_key, "gemini-2.5-flash")
    # Test cost calculation with mock usage data
```

### Integration Tests

```python
# test_integration.py
async def test_model_registry():
    models = get_available_models("gemini")
    assert "gemini::gemini-2.5-flash" in models

async def test_client_factory():
    client = get_client("gemini", "gemini-2.5-flash", api_key)
    assert isinstance(client, GeminiClient)
```

### Manual Testing Script

```python
# backend/test_gemini.py
async def main():
    # Test model registry
    # Test client factory
    # Test API calls (if key available)
    # Test cost tracking
    print("✅ Gemini integration verified")
```

## Security Considerations

### API Key Management

- Store API keys in environment variables only
- Never log or expose API keys
- Rotate keys regularly for production
- Use different keys for development/production

### Data Privacy

- Gemini API processes data in Google's infrastructure
- Review Google's data processing policies
- Consider data residency requirements
- Implement input sanitization for sensitive data

### Rate Limiting

- Implement client-side rate limiting
- Monitor API quota usage
- Handle rate limit errors gracefully
- Provide user feedback for limits

## Performance Optimization

### Connection Pooling

```python
class GeminiClient:
    _instances = {}  # Client caching
    
    @classmethod
    def get_instance(cls, api_key: str, model: str):
        key = (api_key[:10], model)  # Cache by partial key
        if key not in cls._instances:
            cls._instances[key] = cls(api_key, model)
        return cls._instances[key]
```

### Streaming Optimization

- Use streaming for all long responses
- Buffer chunks appropriately
- Handle connection drops gracefully
- Monitor streaming latency

### Cost Optimization

- Use Flash-Lite for high-volume tasks
- Implement request batching where possible
- Monitor token usage in real-time
- Provide cost estimates to users

## Deployment Requirements

### Production Configuration

```bash
# Production environment
GEMINI_API_KEY=${GEMINI_API_KEY}
# Optional: Model-specific settings
GEMINI_DEFAULT_MODEL=gemini-2.5-flash
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=30
```

### Monitoring

- Track API call success rates
- Monitor token usage and costs
- Alert on rate limit breaches
- Log performance metrics

### Scaling Considerations

- Implement request queuing for high load
- Use multiple API keys for higher throughput
- Consider regional deployment for latency
- Plan for cost scaling with usage

## Troubleshooting Guide

### Common Issues

1. **"API key not provided"**
   - Check GEMINI_API_KEY in environment
   - Restart application after adding key
   - Verify key format (starts with "AI")

2. **Rate limit exceeded**
   - Implement exponential backoff
   - Consider upgrading to paid tier
   - Use Flash-Lite model for cost efficiency

3. **Model not available**
   - Check regional availability
   - Fall back to alternative provider
   - Verify model ID format

4. **Streaming issues**
   - Check network connectivity
   - Verify async context management
   - Monitor for connection drops

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Context Caching**: Reduce costs for repeated contexts
2. **Batch API**: 50% cost reduction for batched requests
3. **Function Calling**: Enhanced structured output capabilities
4. **Tuning**: Custom model tuning for specific use cases
5. **Multimodal Expansion**: Audio and video input support

### Integration Opportunities

1. **Google Cloud**: Integration with other Google Cloud services
2. **Vertex AI**: Enterprise-grade model management
3. **TPU Acceleration**: Faster inference for specific models
4. **Edge Deployment**: On-device processing capabilities

## Dependencies

### Required Packages

```python
google-genai>=1.0.0
google-auth>=2.0.0
```

### Compatible Versions

- Python 3.8+
- AsyncIO support required
- Compatible with existing FastAPI infrastructure

## Compliance and Legal

### Data Processing

- Google Gemini API terms of service
- Data processing agreement compliance
- Regional data residency considerations
- GDPR compliance for EU users

### Usage Limits

- Free tier: 500 requests per day
- Paid tier: Higher limits available
- Content policy compliance required
- Acceptable use policy enforcement

---

**Specification Version**: 1.0  
**Last Updated**: 2025-01-31  
**Status**: Implemented and tested
