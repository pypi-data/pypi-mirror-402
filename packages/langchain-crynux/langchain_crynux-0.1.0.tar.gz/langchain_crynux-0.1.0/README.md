# langchain-crynux
Drop-in replacement for `langchain-openai` ChatOpenAI that lets existing OpenAI-compatible LLM code run on the Crynux network without changes.

## Installation
```bash
pip install langchain-crynux
```

Dependencies:
- langchain-openai>=1.0.1

## Usage

```python
import os
from langchain_crynux import ChatCrynux

# Option 1: environment variable (same as langchain-openai)
os.environ["OPENAI_API_KEY"] = "your-api-key"

chat = ChatCrynux(
    base_url="https://bridge.crynux-as.xyz/v1/llm",
    model="Qwen/Qwen-2.5-7B-Instruct",
    vram_limit=24,
    # Option 2: pass api_key directly
    # api_key="your-api-key",
)

response = chat.invoke("Hello from Crynux.")
print(response.content)
```

 * `base_url` defaults to `https://bridge.crynux-as.xyz/v1/llm`.

 * `vram_limit` is the minimum GPU VRAM (in GB) required for the inference run. Default is 24.
