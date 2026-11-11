# ComfyUI-LLM

ComfyUI custom nodes for text generation through [VapeurAI](https://vapeur.ai/).

Requests use `api.vapeur.ai` first and fall back once to `apiv2.vapeur.ai` on
connection errors or connection timeouts, preserving the API path and payload.
HTTP errors and failures after connecting do not trigger endpoint switching.

## Nodes

- `ComfyUI-LLM GPT`
- `ComfyUI-LLM Claude`
- `ComfyUI-LLM Gemini`
- `ComfyUI-LLM DeepSeek`
- `ComfyUI-LLM Qwen`
- `ComfyUI-LLM Qwen 百炼` (direct Alibaba Cloud Model Studio, video input)
- `ComfyUI-LLM Agent Node`

GPT, Claude, Gemini, and Qwen accept one optional ComfyUI `IMAGE` for image
understanding. DeepSeek is text-only. The provider nodes return:

- `text`: final model text, excluding thinking blocks
- `response_json`: formatted provider response for diagnostics

After a GPT request completes, its estimated cost is shown in a read-only
summary at the bottom of the node. It is calculated from the response token
usage and Vapeur's per-model input, cached-input, output, and 272K
long-context rates.

The default system prompt rewrites Chinese scripts for concise short-video
voice-over delivery. It remains editable in every node.

### GPT model list

The dropdown includes all 30 GPT text models in Vapeur's
[model hub](https://vapeur.ai/model-square), checked **2026-11-04**. The default
remains `gpt-5.5`. Restart ComfyUI and refresh the browser after updating.

| Series | Models |
| --- | --- |
| 6.1 | `gpt-6.1-terra`, `gpt-6.1-sol` |
| 6 | `gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna` |
| 5.6 | `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` |
| Latest chat | `gpt-chat-latest` |
| 5.5 / 5.4 | `gpt-5.5`, `gpt-5.4`, `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-5.4-nano` |
| 5.3 / 5.2 | `gpt-5.3-codex`, `gpt-5.2`, `gpt-5.2-codex` |
| 5.1 | `gpt-5.1`, `gpt-5.1-codex`, `gpt-5.1-codex-mini`, `gpt-5.1-codex-max` |
| 5 | `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-5-pro`, `gpt-5-codex` |
| 4 | `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o` |

Codex and Pro models use `/v1/responses`; other models use Chat Completions.
GPT-4 and the latest-chat alias omit reasoning controls. Models that cannot
disable reasoning use their minimum supported level; GPT-5 Pro always uses
`high`. The original GPT-5 / mini / nano map `off` to `minimal`.

GPT-6.1 Sol uses the official [128,000-token output limit](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
correcting the hub's 1,280,000 entry. Prices for all listed models, including
the changed GPT-5.6 rates, come from the same Vapeur catalog snapshot. Cost
estimates cover input, cached input and output tokens; they exclude cache-write
charges, service-tier adjustments and account discounts. Image-generation
models use a different API and are not included in this text node.

Live text checks on 2026-11-04 succeeded for 29 of the 30 models, including
all five GPT-6/6.1 entries and all Codex/Pro entries. `gpt-5.6-sol` timed out
after 45 seconds in this check. These short text requests do not establish
image quality, long-context behavior or every reasoning setting. The Agent
node keeps its existing six-model tool-enabled list.

### Qwen (DashScope)

Qwen video frame-sampling helpers are retained in the source but disabled in
the node: there is no `video` or `video_frames` input, and node execution does
not decode or sample video. Gemini video input remains available.

Restart ComfyUI and add `ComfyUI-LLM Qwen`, select `qwen3.7-max`, and enter
`user_prompt`. The node reuses the existing Vapeur API key and calls
`/qwen/api/v1/services/aigc/multimodal-generation/generation` with DashScope's
native `input.messages` format and `parameters.result_format: message`.
With an optional `IMAGE` connected, it uses `/v1/chat/completions` and
`image_url` instead: the native route did not reliably forward inline images
in live tests. Model/channel image support still depends on Vapeur.
It supports both string and text-block response content. Thinking controls
are omitted because the supplied API specification does not define them;
sampling and output length use server defaults.

The dropdown includes all **16 Qwen chat models** listed in Vapeur's
[model hub](https://vapeur.ai/model-square) on **2026-11-03**:

| Series | Models |
| --- | --- |
| 3.8 | `qwen3.8-max`, `qwen3.8-flash`, `qwen3.8-max-glb` |
| 3.7 | `qwen3.7-max`, `qwen3.7-plus`, `qwen3.7-flash`, `qwen3.7-max-glb` |
| 3.6 | `qwen3.6-plus`, `qwen3.6-flash`, `qwen3.6-plus-glb`, `qwen3.6-flash-glb` |
| 3.5 | `qwen3.5-plus`, `qwen3.5-flash`, `qwen3.5-plus-glb`, `qwen3.5-flash-glb` |
| Plus | `qwen-plus-latest` (text only; leave `image` disconnected) |

Image-generation models are excluded. This is a checked-in model list, not an
automatic catalog refresh.

All 16 models returned `OK` in a live text smoke test on 2026-11-03 using
the native route. Image tests through the chat route correctly identified a
solid red image with `qwen3.8-flash` and `qwen3.7-flash`; `qwen3.7-max` and
`qwen3.7-max-glb` returned upstream HTTP 400 image-parameter errors. Use the
tested Flash models for images. Other chat-route vision models have not been
live-tested; text smoke tests do not establish long-context or answer quality.

### Qwen 百炼 (direct Model Studio, video input)

`ComfyUI-LLM Qwen 百炼` calls Alibaba Cloud Model Studio's OpenAI-compatible
`/compatible-mode/v1/chat/completions` directly, not through Vapeur. Set in
`config.local.json`:

```json
{
  "BAILIAN_API_KEY": "sk-...",
  "BAILIAN_BASE_URL": "https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com"
}
```

`BAILIAN_BASE_URL` defaults to `https://dashscope.aliyuncs.com`; a trailing
`/compatible-mode/v1` or `/api/v1` is accepted and stripped. The key can also
come from the `BAILIAN_API_KEY` or `DASHSCOPE_API_KEY` environment variable.
`request_timeout`, `request_retries` and `retry_delay` are shared with the
Vapeur nodes.

Inputs: `model`, `thinking_level`, `system_prompt`, `user_prompt`, optional
`image` and optional `video`. With video connected and the default system
prompt unchanged, it uses the same video voice-over instructions as Gemini.
Requests are always streamed (Qwen3.5-Omni rejects non-streaming calls) and
merged into one `chat.completion`-shaped `response_json`.

The video is serialized to MP4 with audio. Clips whose Base64 is under ~9.5 MB
are sent inline; larger ones (up to 1 GB) are uploaded to Model Studio's free
temporary storage (`oss://`, 48 h, bound to the selected model) and sent with
`X-DashScope-OssResourceResolve: enable`.

| Model | Hears video audio | `thinking_level` |
| --- | --- | --- |
| `qwen3.8-omni-flash` (default) | Yes | `reasoning_effort`; `off` → `low`, `high` → `xhigh` |
| `qwen3.5-omni-plus`, `qwen3.5-omni-flash` | Yes | ignored (no thinking) |
| `qwen3.8-max`, `qwen3.8-flash` | No, visuals only | `reasoning_effort`; `off` → `none` |
| `qwen3.7-max/plus/flash`, `qwen3.6-plus/flash` | No, visuals only | `enable_thinking`; low/medium budgets 4,096 / 16,384 |

Use an Omni model when the reference video's spoken voice-over matters. In
live tests on 2026-11-11 with a synthetic Chinese TTS clip, all three Omni
models transcribed the speech; `qwen3.8-max`, `qwen3.8-flash` and `qwen3.7-*`
reported "no voice". `qwen3.8-omni-flash` with `reasoning_effort: none` also
reported "no voice" in 2 of 2 tries, so this node never sends `none` to it.
A 25 MB, 13-second clip went through the temporary-upload path with
`qwen3.8-flash`. Omni models require the model to be enabled (and billable)
in the workspace; otherwise the API returns `403 AccessDenied.Unpurchased`.

### Gemini video to product voice-over

Import [the example workflow](examples/gemini_video_product_voiceover.json) into
ComfyUI, upload your reference video in **Load Video**, replace the example
product facts in `user_prompt`, and click Run. The final script appears in
**Preview as Text**. The example selects `gemini-3.8-flash` with `low` thinking
and uses only this plugin plus built-in ComfyUI nodes. It contains no video or
API key; the existing Vapeur configuration is used. Restart ComfyUI after
updating the plugin so the video input and current model list are available.

Connect ComfyUI's **Load Video** `VIDEO` output to the optional `video` input
of **ComfyUI-LLM Gemini**. Enter your product facts and writing requirements in
`user_prompt`, for example:

```text
产品名称：纯棉圆领T恤
卖点：100%棉，宽松版型，黑白两色
目标人群：日常通勤的年轻人
要求：参考视频的表达节奏，写一段约30秒的中文口播，只输出正文。
```

With video connected and the original default `system_prompt` unchanged, the
node uses video-specific instructions to understand the original speech,
subtitles and visuals, then write a new script grounded in your product facts.
A custom `system_prompt` takes precedence. Connect `text` to a text display or
downstream node for the final script; `response_json` remains diagnostic output.

The video is serialized as MP4 with its audio and active trim preserved, and
sent inline to Vapeur's Gemini `generateContent` endpoint. Connect an actual
`VIDEO`, not an `IMAGE` frame batch (which does not carry audio). Temporary
files are removed after encoding. The local serialized-video limit is 64 MiB;
Vapeur/model request limits may be lower, and Base64 adds roughly one third to
the upload size. Trim or compress large clips before connecting them. Video
requests incur the provider's normal usage charges. No video is generated.

Gemini availability was checked on **2026-09-22** against Vapeur's
[model hub](https://vapeur.ai/model-square): 9 chat models and 3 image-generation
models. All 9 chat models are listed; image-generation models are excluded.
The default remains `gemini-3.5-flash`. Output limits (65,536 tokens) come from
the hub; minimum thinking levels follow [Google's model-specific table](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/thinking).
For 3.8 Flash and 3.7 Flash, `off` maps to `low`; these models do not support
`minimal`. Gemini 2.5 Flash uses `thinkingBudget`: `off` disables thinking with
0 tokens; `low` / `medium` / `high` use 1,024 / 8,192 / 24,576 tokens, within
Google's documented 1–24,576 range for enabled thinking.

Each model received the same six-second MP4 with a changing color/word sequence,
spoken English, and separate product facts, through the actual Gemini node.
Initial tests used `medium` thinking and a reduced 512-token combined thinking
and output cap. Three `MAX_TOKENS` answers received one corrective test with
`low` thinking and a 4,096-token cap. The fixed 2.5 Flash node was tested with
`off` / 4,096; 3.7 Flash received one fresh `low` / 4,096 test after HTTP 502.
All calls used a 75-second HTTP timeout and no automatic retries.

| Model | HTTP | Video/audio and product-copy result |
| --- | --- | --- |
| `gemini-3.8-flash` | 200 | Correct visuals, speech transcription, and copy |
| `gemini-3.7-flash` | 502 → 200 | Fresh test: correct visuals, speech transcription, and copy |
| `gemini-3.6-flash` | 200 | Corrective test: correct content; JSON wrapped in Markdown |
| `gemini-3.5-flash` | 200 | Corrective test: correct content; JSON wrapped in Markdown |
| `gemini-3.5-flash-lite` | 200 | Correct visuals, speech transcription, and copy |
| `gemini-3.1-pro-preview` | 200 | Correct visuals, speech transcription, and copy |
| `gemini-3.1-flash-lite` | 200 | Correct visuals, speech transcription, and copy |
| `gemini-3-flash-preview` | 200 | Corrective test: correct content; JSON wrapped in Markdown |
| `gemini-2.5-flash` | 400 → 200 | Fixed node: correct visuals, speech transcription, and copy; JSON wrapped in Markdown |

All 9 models produced correct visual, speech, and product content, matching
`modelVersion`, and VIDEO/AUDIO usage in at least one actual node test. Four
returned Markdown fences despite the JSON-only instruction; their content
passed, but strict output formatting did not. The earlier truncations came from
the artificial 512-token test cap and do not indicate model incompatibility.
Results reflect this short synthetic English video and the configured Vapeur
account; long/noisy videos, all thinking settings, and the full 65,536-token
output limit were not live-tested. The prior 3.7 Flash 502 remains evidence of
an intermittent provider error, despite the successful fresh test.

### Agent node

For queued Agent execution outside the ComfyUI worker pool, use the new
`ComfyUI-LLM Agent Task` node and `start_agent_service.ps1` / `start_agent_service.sh`.
The independent service defaults to port **8195** and rejects ports 8180–8190.
It requires the matching Account Manager update. See
[独立 Agent 服务运行说明](workflow/独立Agent服务运行说明.md) for startup, task status,
recovery, and the task-ID output contract.

`ComfyUI-LLM Agent Node` discovers the workflows under `skills/`, selects one
from the prompt and input images, and executes it with the OpenAI Agents SDK
through Vapeur's `/v1/responses` route. Its controlled tools can:

- generate and edit images with Vapeur's OpenAI-compatible image endpoints;
- inspect generated images and build contact sheets;
- run Python scripts shipped inside the selected skill's `scripts/` directory;
- save full-resolution local artifacts and optionally publish temporary copies
  to Alibaba Cloud OSS.

The node exposes an `IMAGE` preview batch, text summary, and a `VIDEO` output.
Connect `video` to `ComfyUI-LLM Video Output` to automatically save MP4 files
under `output/video/` and preview them with their original audio. Multiple videos
are saved individually; image-only and text-only runs emit no videos.
The TikTok fashion video skill registers `final.mp4` from `download_video.py --run-dir`
inside the job output directory and records `state.json.delivery_mode` as `video`.
On Linux, its bundled browser collector can read the configured shop's exact PID
and download original product photos. Run `bash install_tiktok_browser.sh`, then
configure/login the persistent profile as described in
[browser setup and migration](skills/tiktok-fashion-video/references/browser-setup.md).
Runtime data defaults to the Git-ignored `.tiktok_browser/` directory; relative
paths in `config.local.json` move with the node. Agent prepares its own prompt and
the bundled API workflow, and uses the invoking Account Manager user's task session
for video submission. Login profiles and generation credentials are never committed.
A read-only cost
summary at the bottom of the node totals all GPT calls made by the agent. The
estimate excludes image-generation charges. The structured usage summary is
also persisted in `state.json`. Full-resolution
originals, `artifacts.json`, and `state.json` are saved together in the task's
job folder. With Account Manager enabled, the layout is
`output/YYYY-MM-DD/<username>/ComfyUI-LLM-Agent/<job_id>/`; otherwise it falls
back to `output/ComfyUI-LLM-Agent/<job_id>/`. Persisted artifact data excludes
OSS signed URLs.
`skill_override=auto` is the normal mode; select a skill explicitly only to
correct or debug routing.

The Agent node provides auto-growing `image0`, `image1`, ... inputs (up to 16).
Connect the edit base image to `image0`; it remains the authoritative aspect
ratio for `size=auto`. Each socket is saved independently, so references keep
their original dimensions instead of being resized into a ComfyUI image batch.
The separate `images` socket remains available only for existing batch-based
workflows.

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

`VAPEUR_API_KEY` can also be supplied as an environment variable. The same key is used
by `bananapro`, which supports Nano Banana text-to-image and reference-image editing
through Vapeur and defaults to 1K output. A legacy
generic `api_key` is accepted only when `api_provider` is explicitly
`vapeur`. The LLM nodes always call `https://api.vapeur.ai`; legacy Azure or
relay `base_url` values are ignored.

Provider LLM nodes retry connection/time-out failures and HTTP 502/503/504
using `request_retries` (additional attempts) and `retry_delay` (seconds).
The default retries once after 2 seconds; set `request_retries` to 0 to disable
retries. HTTP 400/401/403/429 errors are returned immediately. If the upstream
service remains unavailable, the node reports the original error and attempt
count; retrying cannot repair an unavailable provider channel.

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
| GPT | `/v1/chat/completions`; Codex/Pro: `/v1/responses` | Bearer |
| DeepSeek | `/v1/chat/completions` | Bearer |
| Claude | `/claude/v1/messages` | `x-api-key` |
| Gemini | `/gemini/v1beta/models/{model}:generateContent` | `x-goog-api-key` |
| Qwen 百炼 | `{BAILIAN_BASE_URL}/compatible-mode/v1/chat/completions` (stream); uploads: `/api/v1/uploads` | Bearer |
| Agent Node | `/v1/responses` | Bearer |
| Agent images (`gpt-image-2`) | `/v1/images/generations`, `/v1/images/edits` | Bearer |
| Agent images (`bananapro`) | `/gemini/v1beta/models/gemini-3-pro-image:generateContent` | `x-goog-api-key` |

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

## TikTok catalog and Excel export

The independent `tiktok-ops` backend owns the product/video database. Configure
`tiktok_ops` with `enabled`, `base_url`, `instance_id`, `token`, `sheet` and
`outbox` in `config.local.json`. CPU service URL: `http://127.0.0.1:8190`.
The node uses the authenticated executing account and submits generated videos
through the API. The local outbox retries failures without regenerating videos.

Chinese/English body copy comes directly from sections 8/7 of `prompt.txt`.
Posting captions and hashtags are generated alongside the script using
[editable posting rules](workflow/TikTok发布文案与标签规则.md) and saved in
`post-copy.json`. Completed videos await human confirmation; the automatic
TikTok workflow does not call Gemini for transcription or audio/visual QC.

```bash
python database_cli.py lookup --pid 1731312562904010825
python export_excel.py --output-dir data/exports
python ops_client.py status
python ops_client.py retry --force
```

Database migration, account import and backup run from `tiktok-ops`.
Original sheets/pictures are retained for export, and PIDs are written as text.
The permanent catalog video prefix is separate from temporary OSS outputs; do
not apply the temporary-output expiration policy to it. Back up SQLite through
the backend CLI before migrating; normal generation does not modify either original
workbook. See [database details](skills/tiktok-fashion-video/references/workbook.md).
