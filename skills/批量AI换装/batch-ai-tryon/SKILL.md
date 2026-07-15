---
name: batch-ai-tryon
description: Batch AI try-on workflow for turning a folder of clothing images into final model-wearing-clothing images using one reference model photo, with structured garment analysis, complex texture, small-detail and attachment-structure fidelity calibration, consistent model identity, and consistent footwear. Use when the user asks for 批量AI换装, 批量换装, 批量试衣, one model wearing many outfits, applying every clothing image in a folder to one model, or batch-generating fashion product model images. Prefer this skill even when the user does not explicitly say "try-on" but provides a model image plus a clothing folder and wants final outfit images.
---

# 批量AI换装

## Overview

Use this skill to batch-generate AI try-on images from one model image and a folder of clothing images. Keep the output folder clean: by default it must contain only final successful try-on images, not manifests, logs, temporary files, masks, crops, cache files, placeholders, or explanatory documents.

Core fidelity rule: preserve, do not exaggerate. Reproduce the garment and model as faithfully as the available references allow. Do not beautify the garment into a more luxurious style, add decorations that are not visible or strongly implied, change garment proportions or support structures for styling, or reshape the model's identity.

## Inputs

Collect or infer these inputs from the user:

1. Clothing image folder: contains clothing, outfits, tops, pants, skirts, dresses, suits, coats, or similar garment images.
2. Model image: the fixed person reference used for every generated result.
3. Output folder: use the user's path if supplied. If omitted, create a desktop folder named like `批量AI换装结果_YYYYMMDD_HHMMSS`.
4. Output specification: respect the user's requested size, aspect ratio, and orientation. If omitted, default to `4K`, `3:4`, vertical, with target dimensions `3072 x 4096 px`.
5. Footwear preference: use the user's requested shoes if supplied. If omitted, keep the model's existing shoes when they are clear and usable; otherwise use the default generated shoes described below.

Default to processing only images directly inside the clothing folder. Recurse into subfolders only when the user explicitly asks.

## Input Quality Rules

Support `.jpg`, `.jpeg`, `.png`, and `.webp` clothing images.

Prefer clothing images that are clear, complete, and product-like: clean or transparent backgrounds, front-facing garments, even lighting, realistic color, at least `512 x 512`, and one garment or one complete outfit per file.

Skip a clothing image when it seriously deviates from the task, including:

- The file cannot be opened, is corrupted, or has an unsupported format.
- The image has no recognizable clothing subject.
- The image is only fabric, buttons, sleeve cuffs, tags, or another local detail.
- The garment is severely cropped, blocked, covered by large text or watermark, or structurally unreadable.
- The image is a multi-style collage, poster, magazine page, complex scene, or ambiguous target where the intended garment cannot be identified.
- The image is too blurry, dark, overexposed, compressed, or low-resolution to identify the garment structure.

For skipped clothing images:

- Do not call the try-on tool.
- Do not output any image.
- Do not create blank, error, placeholder, or diagnostic files.
- Continue processing other valid clothing images.
- Report skipped filenames and concise reasons in the final chat response only.

## Model Image Gate

The model image is the shared reference for every result. Validate it before starting the batch.

Proceed only when the model image shows one clear person with the body area needed for the requested try-on. Prefer half-body or full-body images with visible torso and major limbs, stable lighting, and a pose that can plausibly wear clothing.

Stop the entire task before generation when the model image is seriously unsuitable, including:

- The image cannot be opened, is corrupted, or has an unsupported format.
- There is no clear recognizable person.
- Multiple people appear and the target model is ambiguous.
- The torso, clothing area, or major limbs are heavily hidden.
- The image is only a headshot, ID photo, or body part when the task requires half-body or full-body try-on.
- The image is extremely blurry, dark, overexposed, low-resolution, or uses an extreme pose that prevents natural garment fitting.

When stopping for model-image quality, do not generate output images. Tell the user what is wrong and what replacement image is needed.

## Batch Preparation Script

Use `scripts/prepare_batch.py` for deterministic folder scanning, basic image validation, default output folder creation, and final filename planning. The script writes no manifest, log, report, or cache file; it prints JSON to stdout.

Example:

```bash
python scripts/prepare_batch.py --clothing-dir "C:\path\clothes" --model-image "C:\path\model.png"
```

Useful options:

- `--output-dir "C:\path\out"`: use a user-specified output folder.
- `--recursive`: include subfolders only when requested by the user.
- `--target-width 3072 --target-height 4096`: override default final dimensions.

The script performs only basic checks such as supported extension, openability, dimensions, and duplicate-safe output names. Still use visual judgment or available image-understanding tools to apply the semantic filtering rules above.

## Optional Detail Reference Board Script

For garments with dense texture, compression blur, low-contrast decorations, or multiple reference photos, use `scripts/detail_reference_board.py` when local image files are available and the generation tool can accept an additional visual reference. The script creates a temporary board containing the original garment image, a lightly enhanced faithful view, and high-detail crops. It is only a generation aid and must not be saved in the final output folder.

Example:

```bash
python scripts/detail_reference_board.py --input "C:\path\front.jpg" "C:\path\detail.jpg" --out "C:\path\temp\detail_board.jpg"
```

Use the board to help the model see small high-value details such as pearls, buttons, beads, rhinestones, studs, embroidery, applique, lace motifs, crochet flowers, bows, drawstrings, pendants, scalloped edges, trims, hardware, and same-color raised ornaments. The board is an identification aid only; it does not authorize increasing decoration density, brightness, size, regularity, or contrast. The board does not replace the original clothing reference; use it alongside the original whenever possible.

## Try-On Execution

Use any available AI try-on, image editing, or image generation capability in the environment that can accept the model image and clothing image as visual references. Do not require or assume a specific provider. Prefer a dedicated virtual fitting tool when one is available and working; otherwise use the best available general image editing/generation workflow that can preserve both references.

If one provider or API is unavailable, missing credentials, missing account privileges, out of credits, blocked by policy, or returns a service error, treat only that provider as failed. Fall back to another available capable tool when possible. Stop the task only when no usable generation capability is available.

## One-Pass Garment Analysis Strategy

Before generating each image, extract a structured garment description from the clothing reference. Do not send only vague instructions such as "use this garment" when a text prompt or control prompt is available. The goal is to make the first generation as close as possible and reduce retries.

Describe only the target garment or outfit. Ignore the clothing-reference model identity, face, hair, pose, phone, mirror, room, props, bags, hats, jewelry, socks, shoes, and background unless the user explicitly asks to keep an accessory. If the clothing image contains multiple garments, identify the main wearable garment or complete outfit before generation; skip the file if the target remains ambiguous.

Use this checklist for every valid clothing image:

- Garment category: dress, shirt dress, blouse, T-shirt, shirt, sweater, jacket, coat, suit, two-piece set, top plus skirt, top plus pants, pants, shorts, jumpsuit, romper, skirt, outerwear, or other.
- Outfit scope: single garment, coordinated set, layered outfit, top only, bottom only, full-body outfit.
- Color: primary color, secondary color, undertone, contrast level, trim color, button color, belt color, lining color when visible.
- Pattern: solid, vertical stripe, horizontal stripe, plaid, check, floral, dot, logo print, lace, embroidery, color block, texture-only, or other; include pattern scale, direction, spacing, and placement.
- Fabric and texture: cotton, linen, denim, knit, chiffon, satin, silk-like, velvet, leather, wool, tweed, mesh, lace, ribbed, pleated, crinkled, sheer, shiny, matte, structured, soft, stiff, lightweight, heavy, drapey, or crisp.
- Silhouette and fit: slim, straight, relaxed, oversized, fitted waist, loose waist, A-line, H-line, X-line, cocoon, flared, bodycon, trapeze, empire waist, high waist, drop waist, tailored, boxy, or layered.
- Neckline and collar: crew neck, V-neck, square neck, sweetheart, scoop, halter, one-shoulder, off-shoulder, stand collar, pointed shirt collar, Peter Pan collar, lapel, sailor collar, hood, tie neck, bow neck, no collar.
- Shoulder and sleeve: sleeveless, cap sleeve, short sleeve, elbow sleeve, three-quarter sleeve, long sleeve, rolled sleeve, puff sleeve, lantern sleeve, batwing, raglan, dropped shoulder, fitted cuff, elastic cuff, ruffle sleeve.
- Front construction: pullover, full button placket, half placket, zipper, wrap front, open front, double-breasted, hidden placket, center seam, princess seam, panel seams, pleats, tucks, ruching, smocking.
- Waist and belt: no waist detail, elastic waist, drawstring, narrow belt, wide belt, self-tie belt, front bow, side bow, back tie, sash, wrap waist, peplum, belt loops, waist seam, waist pleats.
- Length and proportions: crop, hip length, tunic, mini, above knee, knee length, below knee, midi, calf length, ankle length, floor length; for pants use shorts, cropped, ankle, full length, wide leg, straight leg, tapered, flared.
- Hem and skirt shape: straight hem, curved hem, shirt-tail hem, high-low hem, ruffle hem, tiered hem, pleated skirt, gathered skirt, flared skirt, pencil skirt, wrap skirt, slit, asymmetrical edge.
- Pockets and utility details: chest pocket, side pocket, patch pocket, flap pocket, cargo pocket, hidden pocket, pocket opening, belt loops, epaulets, tabs, drawcords.
- Closures and hardware: visible buttons, button count if clear, snaps, zipper, buckle, hooks, eyelets, metal rings, toggles; preserve placement, color, and the placket, seam, strap, edge, or channel that supports them when visible.
- Decorative details: chest emblem, logo patch, embroidery, lace trim, ruffle, bow, ribbon, piping, contrast trim, quilting, beading, sequins, pearls, rhinestones, studs, appliqué, crochet flowers, raised same-color ornaments, pendants, cutout, tassel, fringe; note what each decoration attaches to.
- Detail attachment/support structure: narrow or wide placket, seam, edge trim, lace opening, mesh ground, ribbed band, waistband, collar, cuff, pocket flap, strap, belt loop, drawstring channel, hem, panel, backing fabric, button stand, hook tape, or applique base; preserve its width, scale, openness, and placement.
- Transparency and layering: opaque, semi-sheer, lined, camisole layer, underskirt, visible lining, overlay, cardigan over inner top, jacket over dress.
- Condition and product constraints: wrinkles, fabric folds, drape, volume, symmetry, clean product look, no watermark, no text copied from screenshot.
- Reference artifacts to exclude: phone, selfie pose, face obstruction, mirror frame, room, furniture, floor, hanger, mannequin, other people, non-target accessories, original shoes, socks, hats, bags.
- Similarity warning: if this garment is visually similar to previous batch items, state exactly how it differs, such as "more ivory than pure white", "larger front bow", "shorter A-line skirt", "side waist knot instead of front knot", "gray-blue rather than powder blue", or "midi pink dress rather than shirt dress".

Use a compact garment description before generation, for example:

```text
Target garment analysis: <category>; <primary and secondary colors>; <pattern>; <fabric/texture>; <neckline/collar>; <sleeves>; <front construction>; <waist/belt>; <length>; <hem/skirt/pants shape>; <pockets/closures/decorative details>; <detail attachment/support structure>; <details to exclude>; <differences from similar batch items>.
```

Then use that analysis in the generation prompt. Explicitly say when the output must not become a generic white dress, generic blue dress, random shirt, shirt close-up, or another similar garment from the batch.

## Complex Texture and Small Detail Preservation

Enter detail-preservation mode before generation when a clothing reference has dense or high-relief texture, low contrast, compression blur, screenshot artifacts, or small decorations that could be mistaken for fabric noise. Typical triggers include crochet, openwork knit, lace, embroidery, tweed, ribbing, pleats, sequins, beads, pearls, rhinestones, studs, same-color raised ornaments, buttons, bows, drawstrings, pendants, scalloped edges, ruffles, trims, and appliqué.

When detail-preservation mode is active:

1. Separate the base fabric from high-value details. Do not describe small decorations as generic texture.
2. For each high-value detail, record its type, location, count or layout, color, material, reflectivity, relief or raised depth, symmetry, and relationship to seams, edges, plackets, waistlines, cuffs, hems, and panels.
3. Record the support structure that each detail attaches to, such as a narrow placket, open lace ground, mesh, ribbed band, waistband, seam, edge trim, pocket flap, collar, cuff, drawstring channel, strap, belt loop, hem, or backing panel.
4. For low-contrast or same-color decoration, explicitly state that the details are separate raised objects and must not be blurred into fabric texture, random noise, flat dots, generic highlights, printed patterns, or smooth cloth.
5. For reflective details, specify the material precisely: pearl, metal, rhinestone, bead, sequin, enamel, plastic, shell, or fabric-covered button. Avoid vague words such as "sparkles" unless the garment truly has glitter or sequins.
6. For repeated details, state the approximate count and arrangement when visible, such as "vertical center row of 9 pearl buttons", "two symmetric crochet flowers at the chest", "scattered pearl beads across the skirt", or "scalloped trim around every hem".
7. If the same outfit has multiple reference images, assign each image a role instead of averaging them. Use the clearest full image for silhouette and length, the clearest close-up for small details and hardware, and the clearest texture image for fabric. Do not let a blurry image erase details that are visible in another image.
8. If a detail reference board was created, mention it as a support reference for small details only; still use the original garment reference for color, silhouette, and garment structure.
9. Calibrate details and their supporting structures against the original reference. High-value details must remain visible but not stronger, larger, denser, brighter, more symmetrical, or more regular than the reference; their supports must not become wider, thicker, smoother, more solid, or more prominent than the reference.

Add a compact high-value detail line to the prompt, for example:

```text
High-value detail preservation: <detail type>; <location>; <count/layout>; <material/reflectivity>; <raised/flat>; must remain visible as separate objects, not merged into the base fabric texture.
```

Add a compact detail attachment map when decorations, closures, trims, or hardware attach to a visible support structure:

```text
Detail attachment map: <detail type>; <location>; <count/layout>; <support structure>; <support width/scale>; <surrounding fabric>; <what must not change>.
```

Add a compact fidelity calibration line when details could be over-amplified:

```text
Detail fidelity calibration: preserve the same visual scale, density, placement, reflectivity, and irregularity as the reference; do not add extra decorations or make the garment more luxurious, more regular, or more embellished than the original.
```

For difficult garments, the generation prompt must include both a positive constraint and a negative constraint, for example:

```text
Preserve the raised pearl buttons and same-color crochet flower appliqués as separate visible objects. Do not blur them into the knit holes, convert them into flat printed dots, random highlights, sequins, or generic texture.
```

## Detail Attachment Structure Fidelity

Attached details are part of a construction system, not floating decoration. When a garment has buttons, pearls, beads, rhinestones, studs, bows, pendants, embroidery, applique, lace trim, drawstrings, straps, toggles, buckles, eyelets, hook closures, pocket flaps, labels, charms, or raised same-color ornaments, preserve both the detail and the structure that carries it.

Use attachment-structure fidelity for any garment where preserving the detail could tempt the model to create a cleaner, wider, or more solid support area. This is especially important for lace, crochet, mesh, tulle, sheer fabric, openwork knit, ribbed bands, narrow plackets, scalloped edges, straps, seams, waistbands, cuffs, collars, hems, pockets, belt loops, drawstring channels, and hardware tabs.

When attachment-structure fidelity is active:

1. Identify the support under or beside each detail: narrow placket, button stand, edge trim, open lace ground, mesh, seam, waistband, ribbed band, strap, belt loop, drawstring channel, collar, cuff, pocket flap, hem, backing patch, or panel.
2. Record whether the support is narrow, medium, wide, raised, flat, transparent, openwork, solid, ribbed, scalloped, stitched, folded, bound, or layered.
3. Preserve the support's apparent width, scale, edge shape, openness, placement, and relationship to the surrounding fabric.
4. Do not widen, thicken, solidify, smooth, fill in, or replace the support structure just to make buttons, pearls, beads, hardware, bows, embroidery, or trim easier to see.
5. If details sit on open lace, crochet, mesh, tulle, or sheer fabric, keep the openings visible around the detail. Do not turn the surrounding area into a solid patch.
6. If details sit on a narrow placket, strap, seam, waistband, cuff, collar, or edge trim, keep that support close to the original width and position. Do not convert it into a broad center panel.
7. If a detail is attached to an edge, hem, scallop, pocket flap, drawstring channel, belt loop, or strap, keep it attached to that structure instead of moving it onto a plain fabric area.

Use this prompt line for the general case:

```text
Detail attachment map: <detail type>; <location>; <count/layout>; <support structure>; <support width/scale>; <surrounding fabric>; do not widen, fill, smooth, or replace the support structure.
```

Example:

```text
Detail attachment map: pearl buttons; vertical center front; 6 buttons; attached to a narrow crochet placket; placket is slim, not a wide solid panel; surrounding fabric remains openwork lace; do not widen or fill the lace around the placket.
```

## Garment Proportion and Styling Lock

Do not let the generation tool restyle the garment to look more fashionable than the reference. Preserve the original category, construction, and proportions unless the user explicitly asks for a redesign.

Lock these proportional details when visible:

- Top length, hem position, crop amount, tuck, and waist exposure.
- Waistline height, belt or drawstring position, peplum depth, and sash placement.
- Skirt, dress, shorts, pants, and sleeve length.
- Fit level: loose, relaxed, fitted, bodycon, oversized, structured, or draped.
- Neckline depth, shoulder coverage, armhole shape, slit height, and opening width.
- Layering order and transparency coverage.

Do not transform the reference into a different styling category, such as turning a two-piece set into a dress, a vest into a camisole, a modest crop into a highly exposed crop, a casual knit into a formal gown, or a product-like garment into an embellished costume.

## Model Identity and Background Fidelity

Preserve the model reference as the same person and scene. Keep the original face shape, eye spacing, nose and lip proportions, makeup intensity, hairstyle, skin tone, body proportions, jewelry, tattoos, hand pose, posture, lighting direction, camera feel, and background relationship as much as the tool allows.

Allowed improvements: clarity, natural completion of cropped body areas, and realistic clothing integration.

Not allowed: generic beauty-face drift, stronger makeup, changed facial proportions, smoothed identity, changed hairstyle, changed jewelry or tattoos, changed pose, changed scene, or restaged lighting unless the user explicitly asks.

## Batch Consistency Rules

Keep the batch visually consistent. Across all successful outputs, preserve the same model identity, face, hair, body proportions, pose, camera angle, background, lighting, and footwear style. Only the clothing should change unless the user explicitly asks for other changes.

The model must wear shoes in every final image:

- Use the same shoes across the whole batch.
- If the model reference image already has clear usable shoes, preserve those shoes in every output.
- If the model is barefoot, feet are cropped, shoes are hidden, or the shoes are unsuitable, generate one simple neutral pair and use it consistently across every output.
- Default generated shoes: clean white low-top sneakers with minimal details, no visible brand logo, natural fit, realistic shadows, and consistent scale.
- Do not change shoe style to match each garment unless the user explicitly asks.
- Do not output barefoot images.
- Do not crop the feet or shoes.

For each valid clothing image:

1. Extract the structured garment analysis above.
2. If complex texture or small decorations are present, run detail-preservation mode and include the high-value detail, detail attachment map, and fidelity calibration lines in the prompt.
3. Build the generation prompt from the garment analysis, the high-value detail line when present, the detail attachment map when needed, the fidelity calibration line when needed, plus the batch consistency and footwear rules.
4. Keep the same model identity, facial features, hair, body proportions, pose, camera angle, background, lighting, footwear, and general style as much as the tool allows.
5. Preserve the clothing category, color, silhouette, pattern, material, neckline or collar, sleeve length, front construction, waist details, pockets, closures, decorative details, decoration support structures, garment length, and distinctive differences from similar batch items.
6. Generate one final try-on image for that garment or outfit.
7. Fit the result to the target output specification as a full-body vertical catalog image with feet and shoes fully visible.
8. Save only the final image to the output folder using the planned filename.

Do not stretch people or garments to force a size. Use the tool's high-quality output, upscale, crop, extend, or pad as needed to reach the requested ratio while keeping natural body and clothing proportions.

Quality-check the first generation before saving it as final. If a generated image is barefoot, changes the agreed shoe style, hides the shoes, crops the feet, changes the model identity more than the tool reasonably requires, becomes a close-up, copies the clothing-reference background/person, restyles the garment category or proportions, changes the support structure under visible details, or loses essential garment details from the structured analysis, treat that generation as failed and retry once before counting it as a successful final image.

For detail-preservation mode, also treat the generation as failed when high-value details are missing or downgraded, including pearls or buttons disappearing, beads becoming flat dots, rhinestones becoming random highlights, embroidery becoming printed blur, crochet flowers or appliqués merging into base texture, lace holes becoming smooth cloth, scalloped edges disappearing, drawstrings or pendants being omitted, or same-color raised ornaments being averaged away. The retry should be a targeted detail-repair prompt: preserve the already-correct model identity, pose, background, footwear, and garment silhouette, and repair only the missing or softened high-value details.

Also treat the generation as failed when high-value details are over-amplified, including extra pearls or beads beyond the reference, decorations becoming larger or brighter than the reference, lace or crochet becoming too uniform or costume-like, rhinestones or sequins appearing where the reference has pearls or fabric details, or the garment becoming more luxurious, more symmetrical, more exposed, tighter, shorter, or more stylized than the original. The retry should be a targeted calibration prompt: reduce only the over-amplified details and restore the original scale, density, placement, reflectivity, irregularity, garment length, and fit.

Also treat the generation as failed when the detail is present but its support structure is wrong. Examples include buttons, pearls, beads, or rhinestones preserved but the placket widened, thickened, or turned into a solid panel; lace, crochet, mesh, tulle, or sheer fabric filled in around decorations; trim moved away from an edge or hem; hardware moved off a seam, strap, waistband, cuff, collar, pocket flap, belt loop, or drawstring channel; a new backing patch or broad fabric panel appearing where the reference has none; or the support becoming smoother, cleaner, more regular, or more prominent than the original. The retry should be a targeted attachment-repair prompt: keep the model, pose, background, shoes, garment color, silhouette, and already-correct details, and repair only the support structure under the decorations. Restore the original narrow placket, openwork lace, edge trim, seam, waistband, strap, cuff, collar, pocket flap, hem, or channel structure. Reduce any widened, solidified, filled, smoothed, or over-thickened support area back to the reference scale.

## Output Rules

Default output specification:

- 4K quality
- 3:4 aspect ratio
- Vertical orientation
- Target dimensions: `3072 x 4096 px`

Specification priority:

1. User-specified size, aspect ratio, and orientation override defaults.
2. If the user specifies only part of the output spec, keep that part and use defaults for the rest.
3. If the AI tool cannot produce exact 4K output, generate the highest available quality and then upscale, crop, naturally extend, or export to approximate the target spec.

When extending an image to meet the output ratio or to reveal feet and shoes, prefer natural scene extension that matches the original background, ground plane, lighting, camera perspective, and shadows. Do not use obvious black, white, gray, blurred, or solid-color side bars in final deliverables. If natural extension is not possible, preserve the most natural crop rather than adding hard borders.

The output folder must contain only final successful try-on images unless the user explicitly asks for records or diagnostics.

Never keep these files in the final output folder by default:

- Intermediate images
- Temporary images
- Masks
- Crops
- Cache files
- Logs
- `manifest.csv`
- `manifest.json`
- README or explanation documents
- Error images
- Blank images
- Placeholder images

Suggested final filename format:

```text
001_original-file-stem_tryon.png
```

If temporary files are required by a tool or API, put them outside the final output folder and delete them before finishing.

## Final Response

After the batch finishes, summarize in chat only:

- Total clothing images detected
- Successful final images saved
- Skipped images
- Failed images
- Skipped or failed filenames with brief reasons
- Footwear used and whether it came from the model reference or was generated by default
- Final output folder path
- Output specification used

Do not save this summary as a file unless the user explicitly asks for a processing table, failure list, manifest, or report.
