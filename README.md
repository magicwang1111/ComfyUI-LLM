# ComfyUI-LLM

ComfyUI custom nodes for text generation through [VapeurAI](https://vapeur.ai/).

## Nodes

- `ComfyUI-LLM GPT`
- `ComfyUI-LLM Claude`
- `ComfyUI-LLM Gemini`
- `ComfyUI-LLM DeepSeek`

GPT, Claude, and Gemini accept one optional ComfyUI `IMAGE` for image
understanding. DeepSeek is text-only. All nodes return:

- `text`: final model text, excluding thinking blocks
- `response_json`: formatted provider response for diagnostics

The default system prompt rewrites Chinese scripts for concise short-video
voice-over delivery. It remains editable in every node.

## Installation

```powershell
cd D:\ComfyUI\custom_nodes\ComfyUI-LLM
python -m pip install -r requirements.txt
```

Restart ComfyUI after installation.

## Configuration

Copy `config.example.json` to `config.local.json` and set the key:

```json
{
  "VAPEUR_API_KEY": "sk-...",
  "request_timeout": 600,
  "request_retries": 1,
  "retry_delay": 2
}
```

`VAPEUR_API_KEY` can also be supplied as an environment variable. A legacy
generic `api_key` is accepted only when `api_provider` is explicitly
`vapeur`. The LLM nodes always call `https://api.vapeur.ai`; legacy Azure or
relay `base_url` values are ignored.

## Protocols

| Node | Route | Authentication |
| --- | --- | --- |
| GPT | `/v1/chat/completions` | Bearer |
| DeepSeek | `/v1/chat/completions` | Bearer |
| Claude | `/claude/v1/messages` | `x-api-key` |
| Gemini | `/gemini/v1beta/models/{model}:generateContent` | `x-goog-api-key` |

`thinking_level` is normalized to `off`, `low`, `medium`, or `high`.
Providers that cannot fully disable thinking use their lowest supported level.
The output token limit is selected automatically from the chosen model.

Vapeur's Claude gateway currently rejects the native top-level `system`
field. The Claude node therefore places the editable system instructions in
a clearly delimited first user message while keeping the same behavior.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests use mocked HTTP transports and do not make billable model requests.
