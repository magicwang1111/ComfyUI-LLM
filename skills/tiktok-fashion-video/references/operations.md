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

## Human review and publication

```text
python scripts/publish_oss.py --video RUN/final.mp4 --config CONFIG.json --key Goumee-ComfyUI-Server-Data/public/servers/HOST/tiktok-fashion/RUN/PID/JOB.mp4 --output RUN/publication.json
```

The automatic workflow ends video processing after download and returns the video for human confirmation. Do not call Gemini for audio/visual QC, transcription, captions or tags. Historical Gemini helpers and run evidence are not instructions to execute them in new tasks.

The publisher changes only the new object's ACL to public-read, never bucket ACL. Existing-key reuse requires matching SHA-256 metadata; public GET verifies exact bytes. Configure the authorized bucket/endpoint. Custom-domain and STS-only setups were not tested.

PyAV reads duration, fps, dimensions and audio metadata locally into `ffprobe.json`; this is not an AI quality review. Rerun `download_video.py --run-dir RUN` to register an existing MP4 without downloading or generating again.

The database receives section 8/7 of `prompt.txt` as Chinese/English body copy and `post-copy.json` as the posting caption and hashtags. Prepare posting copy using `workflow/TikTok发布文案与标签规则.md` before submission. Keep execution notes in their separate file and do not represent the planned script as a verified transcript.
