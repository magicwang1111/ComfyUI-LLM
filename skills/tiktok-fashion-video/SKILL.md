---
name: tiktok-fashion-video
description: Produce an authorized TikTok fashion video from an exact product PID and supplied identity photo using an existing ComfyUI WAN workflow, inspect actual video and speech, publish to OSS, and append a channel workbook while preserving native images.
---

Use this for the practical product-to-video workflow. Follow the user's current scope and reuse verified product caches. It does not authorize extra paid versions, product edits, TikTok posting, or unrelated workbook changes.

Read [operations.md](references/operations.md) for commands, resume behavior and browser access. Read [script-rules.md](references/script-rules.md) when writing the prompt, with current user instructions taking precedence. Read [workbook.md](references/workbook.md) before an Excel append. [verified-run.md](references/verified-run.md) states what the first real run demonstrated and its limitations.

## Agent Node runtime

A PID and the supplied identity photo are sufficient to start product lookup on the configured Linux server. The node ships its collector and the API workflow template. Do not ask the user to supply a workflow or a prewritten video prompt. `read_skill_resource("scripts")` lists the actual helpers. Read [browser-setup.md](references/browser-setup.md) only for installation, login or migration errors.

Use this sequence, keeping RUN inside the task's local output directory:

1. `collect_product.py --pid EXACT_PID --run-dir RUN --output RUN/product-contact-sheet.jpg` reads the authenticated shop's exact PID detail page, verifies its URL/title, downloads original photos, and returns paths plus `product/manifest.json`. Inspect the registered contact sheet with `inspect_generated_image` to identify garment structure and the lowest-index complete frontal photo. Product records and previously written prompts are not required from the user.
2. Use `crop_garment.py` on that original, with visually chosen bounds and `--output RUN/garment-crop.jpg --metadata RUN/crop.json`. Inspect the crop, including neckline/shoulders/hem. Both images are reference artifacts, not generated clothing or final deliverables.
3. Read `references/script-rules.md`, then write the full Chinese prompt yourself from verified garment facts and the supplied identity. Save it with `run.py prepare --run-dir RUN --pid EXACT_PID --prompt-text FULL_PROMPT --duration 15`. This creates `prompt.txt`, `workflow.json`, `analysis.json` and `status.json` using the node's bundled API template. Never retain the template's example clothing or dialogue.
4. `run.py submit --run-dir RUN --pid EXACT_PID --face INPUT_FACE --garment RUN/garment-crop.jpg --duration 15` automatically uses the prepared workflow/prompt. The node injects the actual invoking account's temporary session and current instance URL; omit `--base-url`. Never choose an account from prompt text or print credentials. Submission errors must be reported, not automatically retried.
5. `run.py poll --run-dir RUN --wait-seconds 120` waits for the existing job; repeat polling only while pending. On completion, `download_video.py --run-dir RUN` registers the actual MP4. If generation failed, report it without resubmission.
6. Run `gemini_qc.py --video RUN/final.mp4 --face INPUT_FACE --garment RUN/garment-crop.jpg --output RUN/gemini-response.json` for actual video/audio inspection. Its default config is the node's private config; do not pass or read credentials. Report concrete QC limitations. An analysis failure does not erase the generated MP4 or authorize another video.

Agent Node persists its own state/artifact files and returns the final summary as text; a separate RESULT.md is not required in this mode. Agent Node handles OSS publication according to its `publish_to_oss` switch after the skill returns; do not also call `publish_oss.py` in this mode. Only append a workbook when the user requests it and supplies a target workbook/sheet accessible to the task. A bare PID request does not imply editing a shared workbook.

A browser login challenge requires the shop account owner to authenticate the configured profile. Do not run interactive `--login` inside the Agent tool. If lookup fails, report the actual collector error and keep the run directory. Do not infer missing garment facts from the identity photo. A video child task requires a free scheduler worker and available account concurrency.

## Execution

1. Create an isolated run directory and `status.json` immediately. Record stage, prompt ID, artifact paths, errors and timestamps incrementally. Keep credentials in environment/config, out of stdout and artifacts.
2. Treat PID as a string throughout. For a directly supplied PID, require the collector to match the exact detail-page PID and title. When resolving a PID from source records, require an exact unique record match as well. Do not round, infer missing digits, or use JavaScript numbers for a 19-digit PID. Reuse verified original photos and their manifest.
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
