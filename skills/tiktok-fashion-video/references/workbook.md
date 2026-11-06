# Database and Excel export

SQLite is the live product/video record store. Both original workbooks are imported once, including every sheet, row, original OOXML part and native image. The originals remain backups; runtime lookup and recording do not read or overwrite them.

The `products` table uses exact text PID keys and includes SPU, category, historical prices/stock and product image URL. When a source PID was rounded, import repairs it only through a unique SPU match to an exact PID from another sheet. Original values remain in `source_rows` and `workbook_parts`; `cell_overrides` documents export normalization. Unresolved values are preserved, never guessed.

The `videos` table contains channel sheet/sequence, PID, original row values and new generation metadata. New rows include the original first product photo, actual Chinese/English speech, caption, hashtags, QC and video location. Generation IDs are unique; SQLite transactions serialize concurrent sequence allocation. Imported pictures are indexed by workbook, sheet and row in `images`, with bytes in `workbook_parts`.

Agent lookup: `catalog.py --pid EXACT_PID`. The node records generated videos after publication when `tiktok_database.enabled` is configured. It uses the configured channel sheet, not a username guessed from the prompt. Generation account ownership continues to come from Account Manager. The configured channel catalog is shared; do not put unrelated private data in it.

Run these from the ComfyUI-LLM directory:

```bash
python database_cli.py import --videos 'workflow/BC渠道号视频.xlsx' --products 'workflow/PID查询表格.xlsx'
python database_cli.py lookup --pid 1731312562904010825
python export_excel.py --output-dir data/exports
python export_excel.py --kind videos --output-dir data/exports
python database_cli.py backup --output /backup/tiktok.sqlite3
```

`config.local.json` selects `tiktok_database.path` (default `data/tiktok.sqlite3`, relative to the node), `enabled`, and `sheet` (default `bnmb`). Export reads one consistent database snapshot, preserves old pictures/sheets/styles, appends generated rows with embedded original photos, and writes PIDs as text. Existing export files are atomically replaced. The source workbooks are not edited by normal runtime or default export.

For migration, use the backup command and transfer that snapshot, private configuration and necessary runtime dependencies. Update the configured path on the new server. The database contains the Excel template parts and pictures, so the original spreadsheets are not required for export. Do not copy only the main SQLite file while writers are running: use SQLite backup to include committed WAL data. Database files, generated exports and credentials are excluded from Git.

The node publishes catalog videos under the configured permanent public OSS prefix, verifies an unsigned GET against the file hash, and stores `publication.json` before recording the row. Do not configure temporary object expiration for this prefix. If publication is disabled/fails, the database keeps the local/OSS location and reports the limitation; it does not invent a public link or lose the video.
