#!/usr/bin/env bash
set -euo pipefail
plugin_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v node >/dev/null || { echo 'Install Node.js 20+ and npm first.' >&2; exit 1; }
command -v npm >/dev/null || { echo 'Install npm first.' >&2; exit 1; }
node -e 'if (Number(process.versions.node.split(".")[0]) < 20) process.exit(1)'
browser_root="$plugin_root/.tiktok_browser"
mkdir -p "$browser_root/profile" "$browser_root/browsers"
npm install --prefix "$browser_root" --no-audit --no-fund --save-exact playwright@1.65.0-alpha-2026-10-30
export PLAYWRIGHT_BROWSERS_PATH="$browser_root/browsers"
node "$browser_root/node_modules/playwright/cli.js" install chromium
echo 'Browser installed. See skills/tiktok-fashion-video/references/browser-setup.md for login and migration.'
