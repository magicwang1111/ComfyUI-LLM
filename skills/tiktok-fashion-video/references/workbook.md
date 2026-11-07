# Database and Excel export

The independent tiktok-ops backend owns the live SQLite product/video store. Both original workbooks are imported once, including every sheet, row, original OOXML part and native image. Node runtime lookup, recording and exports use its API.

The `products` table uses exact text PID keys and includes SPU, category, historical prices/stock and product image URL. When a source PID was rounded, import repairs it only through a unique SPU match to an exact PID from another sheet. Original values remain in `source_rows` and `workbook_parts`; `cell_overrides` documents export normalization. Unresolved values are preserved, never guessed.

The `videos` table contains channel sheet/sequence, PID, original row values and new generation metadata. New rows include the original first product photo and video location. Column G (主体文案（中）) is section 8 of `prompt.txt`; H (主体文案（英）) is section 7. Chapter headings are excluded; speaker labels and line breaks are preserved. These are planned script lines, not video transcripts. J (文案) and K (标签 tag) come from `post-copy.json`, generated using `workflow/TikTok发布文案与标签规则.md`. Missing source fields stay empty and never fall back to Gemini output. Videos await human confirmation; no automated Gemini review is required. Generation IDs are unique; SQLite transactions serialize concurrent sequence allocation. Imported pictures are indexed by workbook, sheet and row in `images`, with bytes in `workbook_parts`.

Agent lookup: `catalog.py --pid EXACT_PID`. The node records generated videos after publication when `tiktok_ops.enabled` is configured. It uses the configured channel sheet and the authenticated executing queue owner's fixed ID. Backend mapping determines attribution. The configured channel catalog is shared; do not put unrelated private data in it.

Run these from the ComfyUI-LLM directory:

```bash
python database_cli.py lookup --pid 1731312562904010825
python export_excel.py --output-dir data/exports
python export_excel.py --kind videos --output-dir data/exports
python ops_client.py status
python ops_client.py retry --force
```

`config.local.json` selects `tiktok_ops.base_url`, `instance_id`, `token`, `enabled`, `sheet` (default `bnmb`) and `outbox` (default `data/ops-outbox.sqlite3`). Export reads one consistent backend database snapshot, preserves old pictures/sheets/styles, appends generated rows with embedded original photos, and writes PIDs as text. The source workbooks are not edited by normal runtime or default export.

For migration, use the backend backup command and transfer that snapshot, private configuration and necessary runtime dependencies. Update the backend URL on the new node server and also transfer its local outbox and task directories. The database contains the Excel template parts and pictures. Do not copy only the main SQLite file while writers are running: use SQLite backup to include committed WAL data. Database files, generated exports and credentials are excluded from Git.

The node publishes catalog videos under the configured permanent public OSS prefix, verifies an unsigned GET against the file hash, and stores `publication.json` before recording the row. Do not configure temporary object expiration for this prefix. If publication is disabled/fails, the database keeps the local/OSS location and reports the limitation; it does not invent a public link or lose the video.
