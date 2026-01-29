# VAP SDK for Python

**Execution control layer for AI agents calling paid APIs.**

[![PyPI version](https://badge.fury.io/py/vap-sdk.svg)](https://badge.fury.io/py/vap-sdk)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

VAP enforces cost control, retry limits, and execution ownership when your agents call external media APIs. Pre-commit pricing with Reserve → Burn → Refund model. No surprise bills.

## 🚀 Quick Start

```bash
pip install vap-sdk
```

```python
from vap import VapClient

client = VapClient(api_key="your-api-key")
result = client.execute("streaming_campaign", text="Welcome to the future of AI media!")

print(result.video_url)  # Your video is ready!
```

## 📋 Features

- **Simple API**: One method to generate complete media packages
- **Preset System**: Pre-configured media generation pipelines
- **Deposit-Reserve-Burn**: Transparent prepaid financial model
- **Sync & Async**: Both synchronous and asynchronous clients
- **Type Safe**: Full Pydantic models with IDE autocomplete
- **Framework Ready**: Built for LangChain, CrewAI, and MCP integration

## 💰 Preset Pricing

| Preset | Output | Price |
|--------|--------|-------|
| `streaming_campaign` | Video + Music + Narration | $5.90 |
| `full_production` | Full Production Package | $7.90 |
| `video.basic` | Basic Video | $1.96 |
| `music.basic` | AI Music Track | $0.68 |
| `image.basic` | AI Generated Image | $0.18 |

## 📖 Usage Examples

### Basic Video Generation

```python
from vap import VapClient

with VapClient(api_key="your-key") as client:
    result = client.execute(
        "streaming_campaign",
        text="Introducing our revolutionary AI product",
        style="corporate",
        voice="professional_male"
    )
    
    print(f"Video: {result.video_url}")
    print(f"Cost: ${result.cost}")
```

### Async Usage

```python
import asyncio
from vap import AsyncVapClient

async def generate_video():
    async with AsyncVapClient(api_key="your-key") as client:
        result = await client.execute(
            "video.basic",
            text="Hello async world!",
            image_prompt="futuristic city skyline"
        )
        return result.video_url

url = asyncio.run(generate_video())
```

### Check Account Balance

```python
from vap import VapClient

client = VapClient(api_key="your-key")
account = client.get_account()

print(f"Balance: ${account.balance}")
print(f"Tier: {account.tier}")
```

### List Available Presets

```python
from vap import VapClient

client = VapClient(api_key="your-key")
presets = client.list_presets()

for preset in presets:
    print(f"{preset.name}: ${preset.price} - {preset.description}")
```

### Error Handling

```python
from vap import VapClient, VapInsufficientFundsError, VapAuthError

client = VapClient(api_key="your-key")

try:
    result = client.execute("streaming_campaign", text="My video")
except VapAuthError:
    print("Invalid API key")
except VapInsufficientFundsError as e:
    print(f"Need ${e.required}, have ${e.available}")
```

## 🔗 Framework Integrations

### LangChain Tool

```python
from langchain.tools import Tool
from vap import VapClient

client = VapClient(api_key="your-key")

vap_tool = Tool(
    name="generate_video",
    description="Generate a video from text description",
    func=lambda text: client.execute("video.basic", text=text).video_url
)
```

### CrewAI Integration

```python
from crewai import Agent, Tool
from vap import VapClient

client = VapClient(api_key="your-key")

video_tool = Tool(
    name="Video Generator",
    description="Creates videos from text prompts",
    func=lambda prompt: client.execute("streaming_campaign", text=prompt).video_url
)

creative_agent = Agent(
    role="Video Producer",
    tools=[video_tool]
)
```

## 🏗️ API Reference

### VapClient

```python
VapClient(
    api_key: str,           # Your VAP API key
    base_url: str = "...",  # API base URL (optional)
    timeout: float = 300.0  # Request timeout in seconds
)
```

### Methods

| Method | Description |
|--------|-------------|
| `execute(preset, **params)` | Execute a media generation preset |
| `get_execution(id)` | Get execution status and result |
| `get_account()` | Get account balance and info |
| `list_presets()` | List available presets |
| `estimate_cost(preset)` | Estimate cost before execution |

### VapResult

```python
result.execution_id   # Unique execution ID
result.status         # pending, processing, completed, failed
result.cost           # Actual cost charged
result.video_url      # First video output URL
result.audio_url      # First audio output URL
result.image_url      # First image output URL
result.outputs        # List of all outputs
result.is_completed   # Check if completed
```

## 🔑 Getting an API Key

1. Visit [vapagent.com](https://vapagent.com)
2. Create an account
3. Add funds to your balance
4. Generate an API key

## 📚 Documentation

Full documentation available at [api.vapagent.com/docs](https://api.vapagent.com/docs)

## 🤝 Support

- GitHub Issues: [github.com/elestirelbilinc-sketch/vap-showcase](https://github.com/elestirelbilinc-sketch/vap-showcase)
- Email: support@vapagent.com

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**VAP** - *VAP is where nondeterminism stops.* 🎯