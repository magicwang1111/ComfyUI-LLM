# Operations

Paths, host, model, workflow, workbook and face are configurable. `RUN` is an isolated directory and `BASE` a Comfy endpoint. Credentials: `COMFY_USERNAME` / `COMFY_PASSWORD`. Never echo them or save login responses/cookies. Vapeur uses `VAPEUR_API_KEY` from env or config; OSS uses configured credential fields.

## Linux-first browser

The verified environment used SSH alias `goumei`, persistent Chrome profile `/mnt/tiktok-browser-probe/profile`, user `tiktok-browser`, and Node `/mnt/tiktok-browser-probe/runtime/bin`. Parameterize these for another host. The parent verified login persistence after a browser restart; this video run reused its cached original photos.

```bash
ssh goumei 'cd /mnt/tiktok-browser-probe; runuser -u tiktok-browser -- env PATH=/mnt/tiktok-browser-probe/runtime/bin:/usr/bin:/bin npm exec --yes --package @playwright/cli -- playwright-cli -s=tiktok-probe snapshot'
```

Search exact PID, require one result, inspect title, extract at most nine original photo URLs. Do not save/update/publish product pages. Keep bytes, URLs and verification in a manifest. OTP remains a manual gate. No browser revisit is needed when verified cached inputs suffice.

On Linux use server-local Comfy directly. From Windows, the tested endpoint was `http://127.0.0.1:18183`, tunneled to remote `127.0.0.1:8183`. Check the listener first. If needed:

```powershell
Start-Process ssh -WindowStyle Hidden -ArgumentList '-N','-L','18183:127.0.0.1:8183','-o','ExitOnForwardFailure=yes','goumei'
```

## Crop, submit and resume

Crop bounds apply to the EXIF-oriented original. Inspect the output. These sample bounds are specific to the verified image:

```text
python scripts/crop_garment.py --source ORIGINAL_01 --output CROP.jpg --bounds 0 0.21 1 1 --metadata RUN/crop.json
python scripts/run.py submit --run-dir RUN --base-url BASE --workflow API_WORKFLOW.json --face FACE.jpg --garment CROP.jpg --prompt PROMPT.txt --pid EXACT_19_DIGITS --duration 15 --model 3.0-prime
python scripts/run.py poll --run-dir RUN --base-url BASE
python scripts/download_video.py --run-dir RUN --base-url BASE
```

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

Raw Gemini `overall_pass` may disagree with shot-count/speech defects. Keep a separate review of concrete deviations and preserve `[unclear]`. ffprobe establishes actual duration, fps, dimensions and audio; prompts do not.
