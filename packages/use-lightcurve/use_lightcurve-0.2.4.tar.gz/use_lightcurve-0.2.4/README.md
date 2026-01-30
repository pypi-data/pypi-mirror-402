# use-lightcurve

The official Python SDK for Lightcurve, the observability and evaluation platform for LLM Agents.

## Installation

```bash
pip install use-lightcurve
```

## Quick Start

### Magic Mode (Auto-Instrumentation)

The easiest way to use Lightcurve is to enable auto-instrumentation for your AI libraries.

```python
import lightcurve

# Automatically monitors OpenAI, Anthropic, Gemini, and LangChain
lightcurve.monitor(
    api_key="lc_live_...",
    integrations=['openai', 'gemini'] # Optional: specify integrations
)

# Optional: Verify connection
if lightcurve.is_connected():
    print("✅ Lightcurve is active")
```

### Self-Hosted

If you are running the Lightcurve platform on your own infrastructure, specify your `base_url`:

```python
lightcurve.monitor(
    api_key="...",
    base_url="https://your-lightcurve-instance.com",
    integrations=['openai']
)
```

## Troubleshooting

### verify connection failure
If you don't see data in your dashboard:
1. Check your API key.
2. Ensure you are using the correct `base_url` if self-hosting.
3. Use `lightcurve.is_connected()` to check initialization status.

### 405 Method Not Allowed
- Ensure your `base_url` does NOT end with `/v1/ingest`. The SDK appends this automatically.
- Correct: `https://api.uselightcurve.com`
- Incorrect: `https://api.uselightcurve.com/v1/ingest`
