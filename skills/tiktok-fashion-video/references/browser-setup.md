# Linux browser setup and migration

The collector is shipped with this node: `scripts/collect_product.py` runs `browser_collect.cjs`. It does not depend on SSH, a developer desktop, a Codex session, or a running playwright-cli daemon. Node.js 20+ and npm are prerequisites. From the ComfyUI-LLM directory, run:

```bash
bash install_tiktok_browser.sh
```

Run this as the same OS user that will run the collector. If Playwright reports missing system libraries, an administrator can run `node .tiktok_browser/node_modules/playwright/cli.js install-deps chromium`. Installation never logs in automatically.

Default runtime data lives under `.tiktok_browser/`, which is excluded from Git. In `config.local.json`, `tiktok_browser.profile_dir` and `tiktok_browser.playwright_module` resolve relative to the ComfyUI-LLM directory unless absolute. `node_executable` defaults to Node.js on PATH; `channel` is empty for installed Chromium or `chrome` for system Google Chrome. `run_as_user` is optional, for an existing dedicated browser OS account when ComfyUI runs as root. It is unrelated to the ComfyUI account that owns the generation task.

For first login, use a trusted desktop/virtual display on the server and the ComfyUI Python environment:

```bash
python skills/tiktok-fashion-video/scripts/collect_product.py --login
```

Complete login/OTP, then close that browser before running the collector. This command uses the same profile, executable, channel and OS user configuration as collection; DISPLAY access must be available to that user. Existing authenticated profiles can be selected in config without moving them. The collector opens the exact PID detail page and only reads product data; it never saves product edits. Calls sharing a profile are serialized. A login challenge or inaccessible PID is reported, not bypassed.

To migrate:

1. Finish active collector tasks and close any login browser.
2. Copy the node and `config.local.json`; transfer the authenticated profile directory through the server administration channel. Do not commit it. Browser profile reuse on another machine may still require login again.
3. Install Node.js and rerun `install_tiktok_browser.sh` on the destination. Reinstall browser binaries/dependencies there instead of copying old npm caches or OS executables.
4. Point the profile setting to the migrated folder, preferably the default relative `.tiktok_browser/profile`, and check ownership for the configured OS user. Update any absolute overrides. ComfyUI generation credentials continue to come from each executing task's Account Manager session.
5. Verify an exact PID with `collect_product.py --pid PID --run-dir RUN --output RUN/product-contact-sheet.jpg`. This only reads/downloads product data and incurs no video generation charge.

The shop login profile serves the configured shop's product lookup. It is not a shared ComfyUI generation account; video ownership and account limits remain per caller.
