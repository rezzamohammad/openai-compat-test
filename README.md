# OpenAI Compatible API Tester

A comprehensive testing tool for OpenAI-compatible APIs with universal multi-format response parsing. Test all available models with automatic response validation, retry mechanisms, and support for streaming (SSE) and non-streaming responses.

## Features

- **Universal Response Parser** - Auto-detects and handles SSE streams, standard JSON, Anthropic, Google, Azure formats
- **Multi-Provider Support** - Works with OpenAI, Anthropic, Google, Azure, and custom proxy gateways
- **Smart Request Routing** - Automatically handles streaming vs non-streaming endpoints
- **Multi-Model Testing** - Test single or multiple models simultaneously with configurable delays
- **Automatic Retry** - Built-in exponential backoff for transient errors
- **Detailed Results** - Comprehensive output with latency, tokens, status codes, and error details
- **Flexible Configuration** - Environment variables, interactive prompts, or CLI arguments
- **Automatic Model Discovery** - Fetches available models from your API

## Recent Improvements (v0.2.0)

### Fixed Issues
1. **Response Format Mismatch** - Now handles SSE streams, JSON, and various provider formats
2. **Content Already Consumed** - Smart caching prevents double-read errors
3. **URL Construction** - Auto-fixes double `/v1/v1/` paths
4. **Provider-Specific Errors** - Better error extraction and reporting

### Architecture Enhancements
- New `ResponseParser` class with format auto-detection
- Smart endpoint routing (chat vs non-chat)
- Cached response text for debugging
- Improved error messages with provider context

## Installation

```bash
cd openai-compat-test

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Alternatively, install as a package

```bash
pip install -e .
```

## To build the package

```bash
python -m build
```

## Usage

All commands use the same options:

```bash
python main.py \
  --base-url <url> \
  --api-key <key> \
  --models <model...>] \
  --endpoint <path>] \
  --max-tokens <n>] \
  --timeout <seconds>] \
  --request-delay-ms <ms>] \
  --verbose] \
  --no-json]
```

### Common Examples

```bash
# Test all models
python main.py \
  --base-url http://localhost:8000/v1 \
  --api-key sk-your-api-key

# Test specific models with verbose output
python main.py \
  --base-url http://localhost:8000/v1 \
  --api-key sk-your-api-key \
  --models model1 model2 model3 \
  --verbose --no-json

# Custom endpoint and request settings
python main.py \
  --base-url http://localhost:8000 \
  --endpoint /chat/completions \
  --api-key sk-your-api-key \
  --models cx/gpt-5.5-xhigh \
  --max-tokens 50 \
  --timeout 30 \
  --request-delay-ms 800
```

### Ollama

```bash
python main.py \
  --base-url http://localhost:11434/v1 \
  --api-key ollama \
  --models deepseek-v4-flash:cloud \
  --verbose
```

For Ollama, `--api-key` is ignored; any value such as `ollama`, `test`, or an empty string works.

### Gateways / Proxies

The same interface works with OpenRouter, local routers such as OmniRoute, 9router, and CliProxyApi, and other OpenAI-compatible gateways.

```bash
python main.py \
  --base-url http://localhost:8000/v1 \
  --api-key sk-your-api-key \
  --models high-tiers family-kimi family-deepseek \
  --max-tokens 50 \
  --timeout 60 \
  --request-delay-ms 2000 \
  --verbose
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--base-url` | API base URL (can include or exclude `/v1`) | Required |
| `--api-key` | API authentication key | Required |
| `--models` | Space-separated list of models to test | All available |
| `--max-tokens` | Maximum tokens for responses | 25 |
| `--endpoint` | Completions endpoint path | `/chat/completions` |
| `--timeout` | Request timeout in seconds | 30 |
| `--request-delay-ms` | Delay between requests (milliseconds) | 500 |
| `--verbose` | Show detailed output including requests | false |
| `--no-json` | Disable JSON formatting in output | false |

## Environment Variables

Set these for persistent configuration:

```bash
export OAI_TEST_BASE_URL="http://localhost:8000/v1"
export OAI_TEST_API_KEY="sk-your-api-key"
export OAI_TEST_TIMEOUT="30"
export OAI_TEST_MAX_TOKENS="50"
export OAI_TEST_REQUEST_DELAY_MS="800"
export OAI_TEST_VERBOSE="1"
```

## Output Format

### Standard Output

```
========== MODELS ==========
count=3
01. high-tiers
02. family-kimi
03. family-deepseek
============================

--------------------------------------------------------------------------------
[START]   01/3 high-tiers
[REQUEST] 01/3 high-tiers  POST  http://localhost:8000/v1/chat/completions
[END]     01/3 high-tiers  PASS  latency=13836ms
  status_code=200 response_json={"id":"chatcmpl-...","choices":[...]}
--------------------------------------------------------------------------------

======== COMPLETED =========
total=3 passed=3 failed=0
total_time_ms=37585 avg_latency_ms=11027
============================
```

### JSON Output (default)

Results are formatted as JSON with detailed information:

```json
{
  "results": [
    {
      "model": "high-tiers",
      "status": "PASS",
      "latency_ms": 13836,
      "status_code": 200,
      "response_json": {
        "id": "chatcmpl-1784908754913",
        "choices": [...],
        "usage": {
          "prompt_tokens": 4391,
          "completion_tokens": 46,
          "total_tokens": 4437
        }
      }
    }
  ]
}
```

## Response Format Support

The universal parser automatically detects and handles:

| Format | Provider Examples | Detection Method |
|--------|------------------|------------------|
| **SSE Stream** | OpenAI, custom proxies | `Content-Type: text/event-stream` |
| **Standard JSON** | OpenAI, compatible APIs | OpenAI format with `choices[].message` |
| **Anthropic** | Claude API | `content[].text` structure |
| **Google** | Gemini API | `candidates[].content` |
| **Azure OpenAI** | Azure | Azure-specific fields |
| **NDJSON** | Some streaming APIs | Newline-delimited JSON |

## Architecture

```
src/
├── client.py           - HTTP client with endpoint-aware routing
├── config.py           - Configuration management with smart URL handling
├── models.py           - Data models and exceptions
├── output.py           - Results formatting
├── response_parser.py  - Universal multi-format response parser
├── retry.py            - Exponential backoff retry mechanism
├── runner.py           - Test execution with retry logic
├── ui.py               - User interface utilities
└── validation.py       - Response validation
```

## How It Works

### Request Flow

```
1. Fetch Models
   └─> GET /v1/models → Parse JSON list

2. For Each Model
   ├─> Build Request Payload
   ├─> POST /v1/chat/completions
   │   └─> Auto-detect response format
   │       ├─> SSE Stream? → Parse event stream
   │       ├─> JSON? → Parse standard format
   │       └─> Other? → Try provider-specific parsers
   ├─> Normalize to OpenAI Format
   ├─> Validate Response
   └─> Record Results
```

### Response Parser Logic

```python
# Automatic format detection
if 'text/event-stream' in content_type:
    return parse_sse_stream()
elif 'choices' in data and 'message' in data['choices'][0]:
    return parse_standard()
elif 'content' in data and isinstance(data['content'], list):
    return parse_anthropic()
elif 'candidates' in data:
    return parse_google()
# ... etc
```

## Troubleshooting

### Double `/v1/v1/` in URL

**Fixed automatically.** The tool now detects and removes duplicate `/v1` segments.

```bash
# Both work correctly now:
--base-url http://localhost:8000/v1
--base-url http://localhost:8000
```

### "Content Already Consumed" Error

**Fixed automatically.** Response text is now cached during parsing.

### "No Text in Response" with 200 OK

**Fixed automatically.** The universal parser now handles SSE streams and empty responses.

### Timeouts with Large Model Pools

Increase timeout and delay:

```bash
--timeout 60 --request-delay-ms 2000
```

### Rate Limiting (429 errors)

Increase delay between requests:

```bash
--request-delay-ms 3000
```

## License

MIT

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

---

## Project Context

**Note:** This project is part of an AI workflow testing and benchmarking initiative.

This repository serves as a **test case** and **benchmark** for evaluating:
- AI-assisted development workflows
- Autonomous coding agents and harnesses
- Agent skill systems and orchestration
- Code quality and delivery automation

The goal is to validate that AI workflows, custom skills, and harness configurations can successfully:
- ✅ Deliver production-ready code
- ✅ Follow best practices automatically
- ✅ Generate comprehensive documentation
- ✅ Implement proper testing and security
- ✅ Create maintainable, clean codebases

**This is not a primary serious production project** — it's a proof-of-concept demonstrating what automated AI development workflows can achieve when properly prepared, configured with the right tools, context, skills, and guardrails.

If the code quality, documentation, and structure meet professional standards, it validates the effectiveness of the underlying AI workflow system being tested.
