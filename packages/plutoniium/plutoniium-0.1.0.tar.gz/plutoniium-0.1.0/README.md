# Plutoniium Python SDK

The **official Python client** for the Plutoniium AI Platform.

Plutoniium provides fast, modern, developer-friendly AI models that you can use for chatbots, assistants, automation, and AI-powered applications.  
This SDK allows seamless integration of Plutoniium models into Python projects with an OpenAI-style API.

👉 Website: https://plutoniium.com  
👉 Dashboard & API Keys: https://plutoniium.com  
👉 Documentation: https://plutoniium.com/developer-docs

---

## Installation

Install the SDK using pip:

```sh
pip install plutoniium
```

Requires **Python 3.8+**.

---

## Getting an API Key

1. Visit **https://plutoniium.com**
2. Sign in or create an account
3. Navigate to **API Keys**
4. Create a new key
5. Set it in your environment:

```sh
export PLUTONIIUM_API_KEY="your_api_key_here"
```

---

## Quick Start — Chat Completion Example

```python
from plutoniium import Plutoniium
import os

client = Plutoniium(
    api_key=os.getenv("PLUTONIIUM_API_KEY")
)

response = client.chat(
    model="plutoniium-1",
    messages=[
        {"role": "user", "content": "Explain artificial intelligence in simple words."}
    ]
)

print(response["choices"][0]["message"]["content"])
```

---

## Chat API

Send messages to a Plutoniium model:

```python
response = client.chat(
    model="plutoniium-1",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is machine learning?"}
    ]
)

print(response["choices"][0]["message"]["content"])
```

### Parameters

| Name       | Type         | Required | Description                       |
| ---------- | ------------ | -------- | --------------------------------- |
| `model`    | `string`     | ✔        | Model ID to use                   |
| `messages` | `list[dict]` | ✔        | Chat messages (`role`, `content`) |

### Message Format

```json
{
  "role": "user",
  "content": "Hello!"
}
```

---

## List Available Models

```python
models = client.list_models()
print(models["data"])
```

Example response:

```json
{
  "data": [{ "id": "plutoniium-1" }, { "id": "plutoniium-chat" }]
}
```

---

## SDK Features

- ✔ Official Plutoniium Python Client
- ✔ OpenAI-style API
- ✔ Simple & powerful chat interface
- ✔ Secure API key authentication
- ✔ Compatible with backend Python apps
- ✔ Works with FastAPI, Flask, Django, LangChain, etc.

---

## Security Guidelines

- Never expose API keys in frontend code
- Store keys in environment variables
- Rotate keys regularly via your dashboard
- Always route client requests through your backend

---

## Project Structure

```
plutoniium/
 ├─ __init__.py
 └─ client.py
```

---

## Requirements

- Python **3.8+**
- `requests` library

---

## Roadmap

- Streaming responses (`yield` / async)
- Async client (`aiohttp`)
- Token usage & cost reporting
- More model families
- Tools / function calling support

Follow updates at: https://plutoniium.com

---

## License

MIT License © Plutoniium  
https://plutoniium.com
