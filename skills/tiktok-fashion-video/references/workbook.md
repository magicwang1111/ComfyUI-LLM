# BC workbook append

Append after the last populated record on the selected sheet. Styled blank rows are not product records. END append does not mean modifying an earlier matching PID. Sequence follows the prior A label (`A73` became `A74`).

| Column | Value |
|---|---|
| A | Next sequence |
| B | Exact 19-digit PID as text |
| C | Exact TikTok title |
| D, E | Blank |
| F | Original first product photo, regardless of crop |
| G, H | Chinese translation and English transcription of actual speech |
| I | Durable verified OSS URL |
| J, K | Actual-video English caption and hashtags |
| L, M, N | Blank |

Read the available spreadsheet skill; prefer Artifact Tool for ordinary edits. On this workbook export failed with `Arg_OutOfMemoryException`, so the authorized limited ZIP/XML fallback preserved native images and untouched workbook parts.

`append_workbook.py` supports the inspected BC layout: shared strings, existing drawings/hyperlinks, A-number sequence, BC style indexes. It asserts preconditions. Reinspect/adapt another template instead of guessing. Workbook, sheet, photo and run paths are configurable.

Required RUN files: `analysis.json` with exact `pid` and `title`; actual-video `qc.json` with `transcript_english`, `translation_chinese`, `caption_english`, `hashtags`; `ffprobe.json`; `final.mp4`; `publication.json` with `url` and `public_unauthenticated_get_verified=true`.

```text
python scripts/append_workbook.py --workbook WORKBOOK.xlsx --sheet bnmb --run-dir RUN --photo ORIGINAL_01.jpg
python scripts/append_workbook.py --workbook WORKBOOK.xlsx --sheet bnmb --run-dir RUN --photo ORIGINAL_01.jpg --commit
```

First invocation backs up and stages. Review staged row, XML types and image. Second commits the authorized append after verifying source hash stability. Existing committed receipt prevents duplication. Locks preserve the staged candidate; do not force-close Excel.

Verify unchanged old row XML, image hashes, other sheet parts, old styles and anchors. New B must be `inlineStr` with `@` format. Artifact renderer still displayed this string in scientific notation; direct `inspect` returned exact digits. Native XML/readback establishes precision. Do not convert the PID to a number to repair a preview.

Imported no-fill cells rendered black. A disposable in-memory white-background preview made the row readable without exporting those preview changes. Native Excel visual verification was not performed; do not claim it from a preview.
