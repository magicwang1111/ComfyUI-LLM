---
name: tiktok-fashion-video
description: Produce an authorized TikTok fashion video from an exact product PID and supplied identity photo using an existing ComfyUI WAN workflow, inspect actual video and speech, publish to OSS, and append a channel workbook while preserving native images.
---

Use this for the practical product-to-video workflow. Follow the user's current scope and reuse verified product caches. It does not authorize extra paid versions, product edits, TikTok posting, or unrelated workbook changes.

Read [operations.md](references/operations.md) for commands, resume behavior and browser access. Read [script-rules.md](references/script-rules.md) when writing the prompt, with current user instructions taking precedence. Read [workbook.md](references/workbook.md) before an Excel append. [verified-run.md](references/verified-run.md) states what the first real run demonstrated and its limitations.

## Agent Node runtime

Inside Agent Node, `read_skill_resource("scripts")` lists the actual helpers. The shipped scripts are `run.py`, `crop_garment.py`, `download_video.py`, `gemini_qc.py`, `publish_oss.py`, and `append_workbook.py`; there is no bootstrap or product-discovery script.

The Agent Node tools cannot run SSH/browser commands or create arbitrary scripts. The browser procedure in `operations.md` requires a separate browser-capable environment. A PID and identity photo alone do not supply verified garment photos, an API workflow, or a saved prompt file. If these prerequisites are unavailable, explain exactly what is missing in the final Chinese response instead of guessing helper filenames or claiming that generation was submitted.

For submission, use `run.py submit` with `--run-dir`, `--workflow`, `--face`, `--garment`, `--prompt`, and `--pid` as documented in `operations.md`. Agent Node automatically supplies the executing task owner's temporary session and current instance URL; omit `--base-url`. Never select a username from the prompt, use a shared account, or print credentials. Missing task identity is an error. A video child task needs another scheduler worker and free concurrency for the same account; a rejection must be reported, not retried. Script completion with a nonzero exit code is a failure, not a completed generation.

## Execution

1. Create an isolated run directory and `status.json` immediately. Record stage, prompt ID, artifact paths, errors and timestamps incrementally. Keep credentials in environment/config, out of stdout and artifacts.
2. Treat PID as a string throughout. Require an exact unique match in source records and TikTok. Do not round, infer missing digits, or use JavaScript numbers for a 19-digit PID. Reuse verified original photos and their manifest.
3. Choose the lowest-index valid frontal image with the complete garment. Use Pillow cropping only, retaining shoulders, neckline and hem while removing eyes/nose/mouth. Save normalized and pixel bounds, preserve the original, and visually inspect the result. A detail shot is not a complete garment reference.
4. Keep identity and clothing images separate. Identity comes from the supplied face and visible proportions; clothing comes from the cropped product image. Do not substitute a generic Western model or invent unseen body proportions. Write the requested full Chinese prompt, with dialogue translations only in section 8. For 15 seconds use roughly 30–36 natural English words and synchronize prompt timing with node duration. Claims require visible structure or verified facts.
5. Authenticate ComfyUI using the injected task session in Agent Node; standalone CLI uses form-encoded `/login` and `jwt_token`. Upload inputs and validate against authenticated `/object_info`. Preserve the original workflow. Tested bindings: face 79, garment 78, generation 61, preview 77. Tested settings: 15 seconds, `3.0-prime`, 720P, 9:16, audio enabled, prompt enhancement disabled. Current user choices override defaults and the reference document's 60 fps preference; report measured frame rate only.
6. Submit within existing user authorization. Before `/prompt`, persist the rendered workflow, SHA-256 intent and client ID. Write returned prompt ID immediately. Never automatically retry an unknown POST, a failed paid job, or a disappointing result. Resume existing history/task. Do not delete the intent guard to make a retry work.
7. Download actual output and run ffprobe. Send the complete MP4 including audio as Gemini `inlineData`; silent frames cannot transcribe speech. Save raw response and parsed QC. Keep unclear words marked. Derive workbook speech, translation, caption and tags from actual video, not the planned prompt.
8. Inspect duration, framing, garment, identity, shot count, mouth synchronization and prohibited text/music. Separate generation success from creative acceptance. A model's `overall_pass` cannot override concrete missed requirements. Preserve the single output and report issues unless another paid run is authorized.
9. Prefer a verified existing public Comfy output. Otherwise publish the final asset to configured OSS public storage and verify unauthenticated GET, MIME type and exact bytes/hash. An expiring signed URL is not a permanent publication URL.
10. After successful generation, back up the workbook, stage the exact append, verify old rows/media and read back new values, then commit the already-authorized append. If locked, preserve staged output and report the lock. Write `RESULT.md` with video URL/path, IDs, QC, row/backup, skill path and limitations.

## Human-dependent boundaries

Persisted TikTok login can expire and OTP may require the account owner. Do independent cached-input work while blocked. Use existing authorization without an extra approval ceremony; seek new authorization only outside that scope. Quality defects may need human acceptance, especially unclear speech or identity mismatch. One completed run does not establish general unattended reliability.

Helpers need Python with requests, Pillow, lxml and oss2, plus ffprobe. `append_workbook.py` is deliberately limited to the inspected BC layout. Check its documented preconditions instead of treating it as a general spreadsheet editor.
