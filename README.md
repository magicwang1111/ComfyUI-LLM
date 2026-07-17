# ComfyUI-LLM

ComfyUI custom nodes for text generation through [VapeurAI](https://vapeur.ai/).

## Nodes

- `ComfyUI-LLM GPT`
- `ComfyUI-LLM Claude`
- `ComfyUI-LLM Gemini`
- `ComfyUI-LLM DeepSeek`
- `ComfyUI-LLM Agent Node`

GPT, Claude, and Gemini accept one optional ComfyUI `IMAGE` for image
understanding. DeepSeek is text-only. All nodes return:

- `text`: final model text, excluding thinking blocks
- `response_json`: formatted provider response for diagnostics

The default system prompt rewrites Chinese scripts for concise short-video
voice-over delivery. It remains editable in every node.

### Agent node

`ComfyUI-LLM Agent Node` discovers the workflows under `skills/`, selects one
from the prompt and input images, and executes it with the OpenAI Agents SDK
through Vapeur's `/v1/responses` route. Its controlled tools can:

- generate and edit images with Vapeur's OpenAI-compatible image endpoints;
- inspect generated images and build contact sheets;
- run Python scripts shipped inside the selected skill's `scripts/` directory;
- save full-resolution local artifacts and optionally publish temporary copies
  to Alibaba Cloud OSS.

The node exposes only an `IMAGE` preview batch and text summary. Full-resolution
originals, `artifacts.json`, and `state.json` are saved together in the task's
job folder. With Account Manager enabled, the layout is
`output/YYYY-MM-DD/<username>/ComfyUI-LLM-Agent/<job_id>/`; otherwise it falls
back to `output/ComfyUI-LLM-Agent/<job_id>/`. Persisted artifact data excludes
OSS signed URLs.
`skill_override=auto` is the normal mode; select a skill explicitly only to
correct or debug routing.

The node UI streams Skill routing, model status, reasoning summaries returned by
the Responses API, exact image prompts, tool start/completion, image review, and
errors. The same sanitized progress is printed to the ComfyUI terminal. It does
not expose private chain-of-thought. Missing required material fails the run
immediately; there is no `resume_state` input.

Skills may complete with text only when their own contract or the user's prompt
requires it. In that case `text` contains the deliverable, the saved
`artifacts.json` is an empty list, `state.json.delivery_mode` is `text`, and
`IMAGE` is only an empty preview placeholder for ComfyUI type compatibility.

## Installation

```powershell
cd D:\ComfyUI\custom_nodes\ComfyUI-LLM
python -m pip install -r requirements.txt
.\install_agent_runtime.ps1
```

On Linux, use:

```bash
cd /mnt/ComfyUI/custom_nodes/ComfyUI-LLM
python -m pip install -r requirements.txt
bash ./install_agent_runtime.sh
```

The platform-specific installer installs OpenAI Agents SDK in the isolated
`.agent_env` runtime. This avoids changing Pydantic and PyJWT versions used by
other ComfyUI custom nodes. If `requirements-agent.txt` is already installed in
the Python environment running ComfyUI, the Agent node uses that interpreter
when `.agent_env` is absent. Set `agent_python` in `config.local.json` only when
an explicit interpreter override is needed. Restart ComfyUI after installation.

## Configuration

Copy `config.example.json` to `config.local.json` and set the key:

```json
{
  "VAPEUR_API_KEY": "sk-...",
  "request_timeout": 600,
  "request_retries": 1,
  "retry_delay": 2,
  "allowed_input_roots": [],
  "allowed_output_roots": [],
  "oss_enabled": false,
  "oss_endpoint": "https://oss-cn-hangzhou.aliyuncs.com",
  "oss_region": "cn-hangzhou",
  "oss_bucket": "",
  "oss_prefix": "GouMEE-Comfyui-tmp",
  "oss_signed_url_expires": 86400
}
```

`VAPEUR_API_KEY` can also be supplied as an environment variable. A legacy
generic `api_key` is accepted only when `api_provider` is explicitly
`vapeur`. The LLM nodes always call `https://api.vapeur.ai`; legacy Azure or
relay `base_url` values are ignored.

Relative `input_path` and `output_dir` values resolve inside ComfyUI's input
and output roots. The Agent node follows any account prefix applied through
ComfyUI's standard save-path helper. Absolute paths must be included in
`allowed_input_roots` or `allowed_output_roots`.

To enable OSS publishing, set `oss_enabled`, bucket settings, and credentials in
the ignored `config.local.json`:

```json
{
  "oss_enabled": true,
  "oss_access_key_id": "your-key-id",
  "oss_access_key_secret": "your-key-secret",
  "oss_session_token": ""
}
```

Environment variables take precedence when present, which is useful for RAM or
STS credentials:

```powershell
$env:OSS_ACCESS_KEY_ID = "new-least-privilege-key-id"
$env:OSS_ACCESS_KEY_SECRET = "new-least-privilege-key-secret"
# Optional for STS credentials:
$env:OSS_SESSION_TOKEN = "temporary-session-token"
```

Never put OSS credentials in a workflow, prompt, committed config, or node
output, and never commit `config.local.json`. Configure a one-day lifecycle rule for the configured prefix separately
in OSS; signed URL expiry does not delete objects. The local artifact remains
the source of truth if OSS upload fails.

## Protocols

| Node | Route | Authentication |
| --- | --- | --- |
| GPT | `/v1/chat/completions` | Bearer |
| DeepSeek | `/v1/chat/completions` | Bearer |
| Claude | `/claude/v1/messages` | `x-api-key` |
| Gemini | `/gemini/v1beta/models/{model}:generateContent` | `x-goog-api-key` |
| Agent Node | `/v1/responses` | Bearer |
| Agent images | `/v1/images/generations`, `/v1/images/edits` | Bearer |

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
