# a2a-llm-tracker

Track LLM usage and costs across providers (OpenAI, Gemini, Anthropic, etc.) from a single place.

## Installation

```bash
pip install a2a-llm-tracker
```

## Quick Start (Recommended Pattern)

For applications making multiple LLM calls, use a singleton pattern to initialize once and reuse everywhere.

### Step 1: Create a tracking module

Create `tracking.py` in your project:

```python
# tracking.py
from dotenv import load_dotenv
import os
import asyncio
import concurrent.futures

load_dotenv()

_meter = None

def get_meter():
    """Get or initialize the global meter singleton."""
    global _meter
    if _meter is None:
        try:
            from a2a_llm_tracker import init

            client_id = os.getenv("CLIENT_ID", "")
            client_secret = os.getenv("CLIENT_SECRET", "")
            client_server = os.getenv("CLIENT_SERVER", "https://a2aorchestra.com")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    init(client_id, client_secret, "my-app", client_server)
                )
                _meter = future.result(timeout=5)

        except Exception as e:
            print(f"LLM tracking initialization failed: {e}")
            return None
    return _meter
```

### Step 2: Use it anywhere

```python
import os
from openai import OpenAI
from tracking import get_meter

def call_openai(prompt: str):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    # Track usage
    try:
        from a2a_llm_tracker import analyze_response, ResponseType

        meter = get_meter()
        agent_id = os.getenv("AGENT_ID")  # Add AGENT_ID to your .env file

        if meter:
            analyze_response(response, ResponseType.OPENAI, meter, agent_id=int(agent_id))
    except Exception as e:
        print("LLM tracking skipped")

    return response
```

### Environment Variables

Set your credentials in `.env` file or export them:

```bash
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
CLIENT_SERVER=https://a2aorchestra.com  # optional, this is the default
AGENT_ID=my-agent  # optional, for tracking which agent made the call
OPENAI_API_KEY=sk-xxxxx
```

## Query Total Usage & Costs

Retrieve your accumulated costs and token usage from CCS:

```python
import os
import asyncio
from a2a_llm_tracker import init
from a2a_llm_tracker.sources import CCSSource

async def get_total_usage():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    await init(
        client_id=client_id,
        client_secret=client_secret,
        application_name="my-app",
    )

    source = CCSSource(int(client_id))
    total_cost = await source.count_cost()
    total_tokens = await source.count_total_tokens()

    print(f"Total cost: ${total_cost:.4f}")
    print(f"Total tokens: {total_tokens}")

asyncio.run(get_total_usage())
```

## Request Tracking (Multiple LLM Calls per Request)

Track multiple LLM calls as a single request using `set_request_id` and `set_session_id`. These work with any framework - no Starlette required.

### Basic Usage (Any Framework)

```python
from a2a_llm_tracker import set_request_id, set_session_id, generate_id

def handle_request():
    # Set at the start of each request - all LLM calls get these IDs automatically
    set_request_id(generate_id())
    set_session_id("user-session-123")

    # All LLM calls anywhere in this request share the same IDs
    step_one()
    step_two()
    step_three()
```

### Flask

```python
from flask import Flask, request
from a2a_llm_tracker import set_request_id, set_session_id, generate_id

app = Flask(__name__)

@app.before_request
def before_request():
    set_request_id(request.headers.get("X-Request-ID") or generate_id())
    set_session_id(request.headers.get("X-Session-ID") or generate_id())
```

### Django

```python
# middleware.py
from a2a_llm_tracker import set_request_id, set_session_id, generate_id

class LLMTrackerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_request_id(request.headers.get("X-Request-ID") or generate_id())
        set_session_id(request.headers.get("X-Session-ID") or generate_id())
        return self.get_response(request)
```

### FastAPI/Starlette (Optional)

If you have Starlette installed, you can use the built-in middleware:

```python
from fastapi import FastAPI
from a2a_llm_tracker import TrackerMiddleware

app = FastAPI()
app.add_middleware(TrackerMiddleware)
```

## Google ADK Integration

Track LLM usage in [Google Agent Development Kit (ADK)](https://github.com/google/adk-python) agents using the built-in callback:

```python
from google.adk.agents import LlmAgent
from a2a_llm_tracker import create_adk_callback
from tracking import get_meter

meter = get_meter()

agent = LlmAgent(
    name="my_agent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    after_model_callback=create_adk_callback(
        meter=meter,
        agent_id=123,  # Your agent concept ID (integer)
    ),
)
```

The callback automatically extracts token usage from ADK's `LlmResponse.usage_metadata` and records it to CCS.

## Supported Providers

| Provider | ResponseType |
|----------|-------------|
| OpenAI | `ResponseType.OPENAI` |
| Google Gemini | `ResponseType.GEMINI` |
| Anthropic | `ResponseType.ANTHROPIC` |
| Cohere | `ResponseType.COHERE` |
| Mistral | `ResponseType.MISTRAL` |
| Groq | `ResponseType.GROQ` |
| Together AI | `ResponseType.TOGETHER` |
| AWS Bedrock | `ResponseType.BEDROCK` |
| Google Vertex AI | `ResponseType.VERTEX` |
| Google ADK | `ResponseType.ADK` |

## Documentation

Full documentation available on GitHub:

- [LiteLLM Wrapper](https://github.com/Mentor-Friends/LLM-TRACKER-DOCS/blob/main/docs/litellm-wrapper.md) - Auto-tracking via LiteLLM
- [CCS Integration](https://github.com/Mentor-Friends/LLM-TRACKER-DOCS/blob/main/docs/ccs-integration.md) - Centralized tracking setup
- [Response Analysis](https://github.com/Mentor-Friends/LLM-TRACKER-DOCS/blob/main/docs/response-analysis.md) - Direct SDK tracking
- [Pricing](https://github.com/Mentor-Friends/LLM-TRACKER-DOCS/blob/main/docs/pricing.md) - Custom pricing configuration
- [Building](https://github.com/Mentor-Friends/LLM-TRACKER-DOCS/blob/main/docs/building.md) - Development and publishing

## What This Package Does NOT Do

- Guess exact billing from raw text
- Replace provider SDKs
- Upload data anywhere automatically
- Require a backend or SaaS
