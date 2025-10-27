# Gemini API Setup Guide

This guide will help you set up Google Gemini API support for the Resume Optimizer application.

## Overview

Google Gemini API has been integrated as an additional LLM provider alongside OpenRouter, Zenmux, and Meituan LongCat. Gemini offers:

- **Competitive pricing**: Starting at $0.30/1M input tokens for gemini-2.5-flash
- **Free tier**: Generous free tier for development and testing
- **High quality**: State-of-the-art language models with thinking capabilities
- **Multimodal support**: Text, images, PDFs, audio, and video
- **Streaming responses**: Fast, token-by-token response streaming

## Getting Your API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Get API key"**
4. Create a new API key or use an existing one
5. Copy your API key (starts with `AI...`)

**Note**: The free tier is available in most regions. Check [available regions](https://ai.google.dev/gemini-api/docs/available-regions) for details.

## Configuration

### 1. Add API Key to Environment

Add your Gemini API key to the `.env` file in the `backend/` directory:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Available Models

The following Gemini models are now available in the Resume Optimizer:

| Model ID | Description | Input Cost | Output Cost | Best For |
|----------|-------------|------------|-------------|----------|
| `gemini::gemini-2.5-flash` | Fast, balanced model | $0.30/1M | $2.50/1M | Most tasks, recommended default |
| `gemini::gemini-2.5-pro` | Most capable model | $1.25/1M | $10.00/1M | Complex reasoning, coding |
| `gemini::gemini-2.5-flash-lite` | Ultra-fast, cost-effective | $0.10/1M | $0.40/1M | High-volume, simple tasks |
| `gemini::gemini-2.0-flash` | Stable 2.0 model | $0.10/1M | $0.40/1M | Production stability |

**Pricing Note**: Output costs include thinking tokens for 2.5 models. Free tier available with rate limits.

### 3. Using Gemini in the Application

Select Gemini models in the Streamlit sidebar:

1. Go to **Model Configuration** section
2. For any agent (Job Analyzer, Resume Optimizer, etc.), select a Gemini model:
   - `gemini::gemini-2.5-flash` (recommended)
   - `gemini::gemini-2.5-pro`
   - `gemini::gemini-2.5-flash-lite`
   - `gemini::gemini-2.0-flash`

## Testing Your Setup

Run the test script to verify your Gemini integration:

```bash
cd backend
.venv/Scripts/python test_gemini.py  # Windows
# OR
.venv/bin/python test_gemini.py     # Linux/Mac
```

Expected output:
- ✓ Model registry configured correctly
- ✓ Client factory returns correct client type
- ✓ Response received from Gemini API

## Features

### Supported Capabilities

- ✅ **Streaming responses**: Token-by-token streaming for real-time output
- ✅ **Multimodal input**: Images, PDFs (via base64 encoding)
- ✅ **System instructions**: Custom system prompts
- ✅ **Temperature control**: Adjustable randomness (0.0-2.0)
- ✅ **Token limits**: Configurable max_tokens
- ✅ **Thinking budget**: For 2.5 models (set to 0 to disable thinking)
- ✅ **Cost tracking**: Accurate token-based cost estimation

### Model Capabilities

All Gemini models support:
- Text generation
- Image understanding (via file upload)
- 1M+ token context windows (2.5 models)
- JSON mode for structured output

## Pricing & Limits

### Free Tier
- Access to all listed models
- Rate limited (500 RPD for some features)
- Great for development and testing

### Paid Tier
- Higher rate limits
- Context caching support
- Batch API (50% cost reduction)
- Production-ready SLAs

See [official pricing](https://ai.google.dev/gemini-api/docs/pricing) for latest details.

## Troubleshooting

### "Gemini API key not provided"
- Ensure `GEMINI_API_KEY` is set in your `.env` file
- Restart the application after adding the key
- Verify the key is correct (should start with `AI`)

### API Rate Limits
- Free tier has lower rate limits
- Consider upgrading to paid tier for production use
- Use Flash-Lite model for high-volume tasks

### Model Not Available
- Some models may not be available in all regions
- Check [available regions](https://ai.google.dev/gemini-api/docs/available-regions)
- Fall back to other providers if needed

## API Documentation

For more details on the Gemini API:
- [Quickstart Guide](https://ai.google.dev/gemini-api/docs/quickstart)
- [API Reference](https://ai.google.dev/api)
- [Python SDK Docs](https://googleapis.github.io/python-genai/)
- [Model Details](https://ai.google.dev/gemini-api/docs/models)

## Technical Details

### Implementation Notes

The Gemini integration:
1. Uses the official `google-genai` Python SDK
2. Follows the same interface as other providers (OpenRouter, Zenmux, LongCat)
3. Supports the same agent parameters (temperature, max_tokens, etc.)
4. Provides accurate cost tracking based on actual token usage
5. Handles streaming responses with proper error handling

### Code Location

- Client: `backend/src/api/gemini.py`
- Registry: `backend/src/api/model_registry.py`
- Factory: `backend/src/api/client_factory.py`

## Support

For issues specific to Gemini API:
- [Google AI Forum](https://discuss.ai.google.dev/c/gemini-api/)
- [GitHub Issues](https://github.com/googleapis/python-genai/issues)

For Resume Optimizer integration issues:
- Check test script output
- Review backend logs
- Verify environment configuration
