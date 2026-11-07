# Operations

Paths, host, model, workflow, workbook and face are configurable. `RUN` is an isolated directory and `BASE` a Comfy endpoint. Agent Node injects the current task owner session and instance URL; omit `--base-url` there. Standalone CLI credentials: `COMFY_USERNAME` / `COMFY_PASSWORD`, with an explicit `COMFY_BASE_URL` or `--base-url`. Never echo them or save login responses/cookies. Vapeur uses `VAPEUR_API_KEY` from env or config; OSS uses configured credential fields.

## Linux browser

`collect_product.py` and `browser_collect.cjs` are shipped with the node and use a configured persistent shop login profile. See [browser-setup.md](browser-setup.md) for portable installation/migration. The historical `/mnt/tiktok-browser-probe` profile can be selected in private config; it is not a required path or an SSH service.

The collector visits the exact 19-digit PID detail page, checks the returned PID/title and extracts at most nine original main photos. It saves bytes, image hashes and verification in `RUN/product/manifest.json`. A valid manifest in the same run is reused. It does not edit or publish products. OTP remains an operator step.

In Agent Node, omit `--base-url` so the authenticated task's actual instance is used. Standalone scripts need their own explicitly configured endpoint and login.

## Crop, submit and resume

Crop bounds apply to the EXIF-oriented original. Inspect the output. These sample bounds are specific to the verified image:

```text
python scripts/crop_garment.py --source ORIGINAL_01 --output CROP.jpg --bounds 0 0.21 1 1 --metadata RUN/crop.json
python scripts/run.py submit --run-dir RUN --base-url BASE --workflow API_WORKFLOW.json --face FACE.jpg --garment CROP.jpg --prompt PROMPT.txt --pid EXACT_19_DIGITS --duration DURATION_SECONDS --model 3.0-prime
python scripts/run.py poll --run-dir RUN --base-url BASE
python scripts/download_video.py --run-dir RUN --base-url BASE
```

DURATION_SECONDS is the duration chosen from the current request or selected Markdown, not a fixed 15. When submitting RUN/workflow.json from prepare, omit --duration to inherit its duration. An explicit --duration overrides the workflow, so keep the prompt timing consistent.

Review existing intents for the product/run before submission. The helper guards one directory, not a global deduplication database. Intent without `job.json` means outcome may be unknown. Reconcile the saved client ID/fingerprint against queue/history/scheduler. Do not repeat `/prompt` to find out. Inspect definite validation rejection before any newly authorized attempt.

`/login` requires form data, not JSON. Tested account-manager code mapped JWT identity automatically. Dispatch may use another worker port; ingress history aggregates it. Do not patch service code or restart services for caller issues.

The generalized CLI wraps the real run's submission path. Polling and existing-intent prevention were checked after parameterization; no second paid submit tested the CLI.

## Analysis and publication

```text
python scripts/gemini_qc.py --video RUN/final.mp4 --face FACE.jpg --garment CROP.jpg --config CONFIG.json --output RUN/gemini-response.json --model gemini-3.8-flash --base-url https://api.vapeur.ai/gemini/v1beta
python scripts/publish_oss.py --video RUN/final.mp4 --config CONFIG.json --key Goumee-ComfyUI-Server-Data/public/servers/HOST/tiktok-fashion/RUN/PID/JOB.mp4 --output RUN/publication.json
```

Gemini uses `x-goog-api-key` with full MP4 and separate reference photos. Verified usage included AUDIO and VIDEO modalities. Analysis failure does not authorize video regeneration. Existing analysis responses are guarded against overwrite.

The publisher changes only the new object's ACL to public-read, never bucket ACL. Existing-key reuse requires matching SHA-256 metadata; public GET verifies exact bytes. Configure the authorized bucket/endpoint. Custom-domain and STS-only setups were not tested.

Raw Gemini `overall_pass` may disagree with shot-count/speech defects. Keep a separate review of concrete deviations and preserve `[unclear]`. PyAV establishes actual duration, fps, dimensions and audio and writes the workbook-compatible `ffprobe.json`; prompts do not. Rerun `download_video.py --run-dir RUN` to inspect/register an existing MP4 without downloading or generating again.

QC preserves the original MP4 and uses a full-length compressed copy when the inline request exceeds 12 MiB. HTTP 413 gets a smaller copy, while 429, 500/502/503/504 and connection/timeouts get bounded backoff. There are at most three HTTP attempts per invocation; authentication/other permanent errors stop immediately. Attempt metadata is saved beside the response. Do not add an outer retry loop. Reusing an existing raw response only parses it locally. Compression can limit visual detail; report that uncertainty rather than claiming the original has a compression defect.
