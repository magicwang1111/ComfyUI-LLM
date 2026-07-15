---
name: batch-clothing-product-images
description: Batch-generate ecommerce main image sets for clothing/apparel products, especially when a fixed model must stay consistent, the second image should default to a back view, model footwear must stay consistent or be generated when absent, source garment details must be extracted before generation, supporting styling must stay consistent across the set, and unsupported garment construction details must not be invented. Use when the user asks for 批量生成服装电商主图, 批量服装主图, 批量商品主图, 服装商品图, 一个文件夹生成多个服装产品主图, 用指定模特生成服装主图, 保持同一个模特生成主图, 第二张背面图, 模特穿鞋, 鞋子保持一致, 没有鞋子生成一双, 源图保真, 整套搭配一致, 工艺保真, 禁止虚构工艺, 细节图不要乱加拉链, or to create 3-5 main images per clothing product for platforms such as 淘宝, 天猫, 抖音, Shopee, Amazon, or similar ecommerce channels.
---

# Batch Clothing Product Images

## Purpose

Create ecommerce-ready main image sets for clothing products in batches. Treat the task as product image production, not only virtual try-on: each product should receive a coherent 3-5 image set that can include model try-on, flat lay, detail, back/side, white-background, or scene images depending on the available source material and the user's target platform.

## Inputs and Defaults

Collect or infer these inputs before processing:

- **Product source folder**: Required. Contains clothing product images or product subfolders.
- **Model image**: Optional. When provided, enter fixed-model mode: use it as the only identity reference for all model-worn images, preserving face, body shape, age impression, hairstyle, skin tone, styling tone, and visual consistency. Product images are garment references only, even when they contain people.
- **Output folder**: Optional. If absent, create a desktop folder named like `服装电商主图_YYYYMMDD_HHMMSS`.
- **Images per product**: Optional. Support 3-5 images. Default to 3 images when the user is unsure or silent.
- **Output spec**: Optional. Default to `4K, 3:4, vertical`, with `3072 x 4096 px` as the preferred target when feasible.
- **Platform or style target**: Optional. If absent, use a clean mainstream ecommerce style suitable for 淘宝/天猫/抖音-style main images.

Do not ask the user for missing optional details when the defaults are sufficient to proceed. Ask only when the required product folder is missing, the requested product grouping is ambiguous enough to change outputs materially, or a model image is required by the user but not provided.

## Product Grouping

Determine products conservatively:

1. If the source folder contains product subfolders, treat each direct child folder as one product. Use images inside that product folder as references for the same product.
2. If the source folder contains only loose supported images, treat each image as one product.
3. If the source folder contains both product subfolders and loose images, process direct child folders as products and loose images as individual products.
4. Do not recurse beyond one product-folder level unless the user explicitly asks.
5. Name each output product folder with a stable index and product name, such as `001_连衣裙主图` or `001_original-file-name_主图`.

Use supported source images: `.jpg`, `.jpeg`, `.png`, `.webp`. Ignore unrelated files.

## Source Quality Rules

Accept product images when the clothing subject is recognizable and usable for generation:

- Clothing is visible, reasonably complete, and not severely obstructed.
- Colors, silhouette, major design lines, print, texture, and closures can be identified.
- Image is not badly corrupted, over-compressed, extremely blurry, too dark, or too bright.
- The product is a clothing item or complete outfit, such as tops, bottoms, dresses, coats, suits, activewear, sleepwear, or children's clothing.

Skip a product when no reliable clothing reference exists:

- No identifiable clothing subject.
- Only fabric swatches, buttons, tags, cuffs, packaging, or unrelated details.
- Complex collage, poster, screenshot, heavily watermarked image, or multi-style image where the target item cannot be determined.
- Severe cropping or occlusion hides the garment structure.
- Source file cannot be opened or is unsupported.

When a product has multiple images and only some are invalid, use the valid references and report the skipped files in the final chat summary.

## Product Fidelity Brief

Before generating each product, inspect the available product references and create a concise internal product brief. This brief is for prompt control and does not need to be saved as a report unless the user asks.

The brief should capture only visible or reasonably confirmed product facts:

- Product category and whether it is a single garment or complete outfit.
- Primary color, secondary color, pattern, print placement, contrast panels, and obvious color blocking.
- Silhouette, fit, length, waist position, shoulder shape, volume, and overall proportion.
- Fabric impression, texture, thickness, sheen, transparency, stretch, drape, and seasonality.
- Neckline, collar, sleeve type, cuff, hem, closure, buttons, zipper, pockets, belt, waistband, pleats, drawstrings, hood, lining, and other visible construction details.
- Visible front details, visible back details, source-visible construction details, and unknown or unsupported areas.

Use the product fidelity brief in the generation prompts. Do not rely on a generic category name such as "dress" or "jacket" when source-specific details are available. If references conflict, use the clearest current-product reference and skip ambiguous details. If a product image includes a person, ignore that person's identity but preserve the garment facts.

Separate confirmed construction from assumed construction. A detail is confirmed only when it is directly visible in the current product reference, such as a visible zipper, button, pocket, seam, overlock stitch, binding, label, neck tape, hanging loop, lining, or inner facing. If it is not visible, mark it as unknown and do not include it in any prompt as a plausible or ordinary garment feature.

For front-only or flat-lay references, treat the reverse side, garment interior, inside neckline, back-neck construction, seam allowances, closures, labels, and finishing methods as unknown unless the source image clearly shows them.

## Batch Isolation

Treat each direct product or loose image as an isolated production unit. Previous products may not donate color, pattern, outfit pieces, garment category, back details, props, or scene ideas to the next product.

At the start of each product, state the current product index/name in the working context and reset all product-specific garment and styling assumptions. The only cross-product information that may persist is an explicitly provided fixed model reference, a user-approved global styling direction, and a deliberately chosen global footwear rule when appropriate.

After every generation, accept only images that match the current product brief and planned image slot. Discard and regenerate any candidate that appears to show an older product, another garment, a wrong color/pattern, a previous background concept, or an unrelated image-tool output. If multiple generated-image folders or same-time candidates exist, save only the outputs that visibly belong to the current product plan.

## Model Image Rules

If the user provides a model image, validate it before batch work:

- It should show one clear person, preferably half-body or full-body.
- Face, torso, and target clothing area should be visible enough for coherent try-on.
- Lighting, pose, and resolution should be usable for image generation.

Pause the entire task and ask for a better model image if it is severely unsuitable: no clear person, multiple people with no target, only a face/headshot for a body try-on task, major body occlusion, extreme pose, corrupted file, or very low quality.

If no model image is provided, generate product images using flat lay, hanger, mannequin, cropped model without identity, or clean product-display styles as appropriate.

## Model Consistency Strategy

When a model image is provided, treat the task as fixed-model product-image production.

Use the model image as the identity, face, body, age impression, hairstyle, skin tone, posture baseline, and overall styling reference for every model-worn image in the batch. Use product images only as garment references. Do not copy or inherit the face, hair, body type, ethnicity, pose, age impression, makeup, expression, or styling from product-source model photos.

If both product images and the model image contain people, the product-image person is not the target model. Extract the garment design from the product images and dress the provided model in that garment.

Keep the same person across all generated model-worn images:

- Same face shape, facial features, age impression, skin tone, hair color, hair length, and hairstyle.
- Same body proportions, height impression, shoulder width, and general build.
- Same clean ecommerce styling tone unless the user asks for a change.
- Same model identity across products, angles, and scenes; the garment changes, not the person.

The pose, camera angle, crop, and background may vary for commercial usefulness, but identity must not drift. If model consistency conflicts with pose variety, prioritize model consistency and use a simpler pose.

For prompts, state the hierarchy clearly: model image controls the person; product image controls the garment; platform/style target controls the scene.

## Styling and Footwear Consistency

Model-worn ecommerce images should use shoes by default, and the shoe choice must stay consistent across the image set.

If the model reference already shows shoes, preserve the same shoe style, color, height, sole shape, material impression, and overall footwear impression across all model-worn images. Do not change sneaker color, shoe type, heel height, sole thickness, sock visibility, or footwear styling from image to image.

If the model reference is barefoot, cropped above the feet, or the shoes are not clearly visible, generate one simple commercially neutral pair of shoes and keep that same pair across the full image set. Choose footwear that supports the garment without competing with it:

- Casual menswear or womenswear: clean low-profile white, black, gray, or neutral sneakers.
- Formalwear or suits: simple black or dark brown dress shoes or loafers.
- Dresses and skirts: simple flats, low heels, loafers, or clean minimal shoes that match the styling tone.
- Sportswear or activewear: clean athletic sneakers.
- Children's clothing: simple age-appropriate sneakers or flats.

Do not change shoes between Image 1, Image 2, and any other model-worn image where feet are visible. Do not add visible brand logos, exaggerated soles, bright decorative patterns, attention-grabbing socks, platform shoes, sandals, boots, or footwear that changes the product's market positioning unless the user asks for that styling.

If the feet are cropped out, shoe consistency does not need to be visible, but the crop must not imply a different styling direction. Avoid alternating between cropped feet and visible shoes in a way that makes the set feel inconsistent.

When writing prompts for full-body images, explicitly lock footwear, such as "same simple white low-profile sneakers across all images" or "preserve the exact black loafers from the model reference." If the reference is barefoot or shoes are unclear, state the chosen generated shoe once, then reuse that shoe description for every model-worn image.

Supporting outfit pieces must also stay consistent within the same product image set. When Image 1 establishes an inner layer, pants, skirt, socks, shoes, hairstyle, basic pose style, or other neutral styling support, reuse that same support styling in Image 2 and any other model-worn image unless the user asks for a styling change.

For upper-body products, keep the lower garment, visible inner layer, socks, and shoes consistent between front and back images. Do not switch black trousers to white trousers, chinos to denim, skirt to pants, or tucked to untucked styling unless the product itself requires it and the source references support it. For lower-body products, keep the top, shoes, and visible accessories consistent. For dresses, coats, sets, and complete outfits, avoid adding competing support garments that change the market positioning.

Supporting outfit items should be plain, minimal, logo-free, and secondary to the product. Do not add bags, hats, jewelry, sunglasses, watches, scarves, belts, props, or dramatic styling pieces unless they are in the source reference or the user explicitly requests them.

## Main Image Set Strategy

Generate the requested number of final images per product. Default to 3 images:

- **Image 1: Click-focused hero image**. Show the front full view of the garment. Prefer the specified model wearing it when a valid model image is available; otherwise use a clean flat lay, hanger, mannequin, or product-only composition.
- **Image 2: Back-view fit image**. By default, show the garment from the back. Use a back-facing model, back-view mannequin, hanger back view, or flat-lay back view depending on the available material. The purpose is to show the rear silhouette, back length, back waist, back pockets, back collar, back yoke, hem, and overall rear fit. Do not replace this slot with a side view unless the user explicitly asks or a back-view image would be misleading.
- **Image 3: Truthful detail image**. Emphasize source-confirmed fabric texture, print, stitching, zipper, buttons, pockets, collar, cuffs, craftsmanship, or the most visible design highlight. If source-confirmed construction is limited, prefer a clean crop of the visible outer surface instead of inventing workmanship.
- **Image 4: Supplemental image when requested**. Add styling atmosphere, outfit matching, size/fit impression, seasonal use, movement, or another commercially useful angle based on available references.
- **Image 5: White-background product image when requested or useful**. Use a clean white or transparent-looking background, no watermark, no text, no logo, suitable for platform event traffic capture or product pools.

If the source material does not show the back, create a conservative back-view image that only infers the broad rear silhouette from the visible garment type. Keep the back construction-minimal and plain. Do not invent special back prints, embroidery, straps, cutouts, logos, hardware, pleats, labels, decorative seams, visible center-back seams, center-back zippers, hidden closures, neck tape, hanging loops, inner facings, overlock stitching, seam allowances, reinforcement patches, lining, or unusual closures. For uncertain back details, keep the back clean and mention the limitation in the final summary.

For detail images, show only details that are visible or strongly supported by the product references. If a specific detail is not visible, use a conservative and truthful crop of the visible outer fabric, print, neckline edge, armhole, sleeve, cuff, hem, waistband, pocket, placket, button, or source-confirmed seam instead of inventing a selling point.

Do not use detail images to show the garment interior, reverse side, back-neck area, inside collar, inside waistband, lining, labels, hanging loops, neck tape, overlock stitching, seam allowances, inner facings, center-back seams, center-back zippers, invisible zippers, hidden closures, reinforcement patches, or other finishing construction unless those exact features are clearly visible in the current source reference. These details often look realistic, but they are still incorrect when the source does not confirm them.

Do not fabricate logos, embroidery, hardware, premium labels, unusual fasteners, decorative back elements, or close-up details that the source images do not support.

If the user asks for 4 or 5 images but the source references cannot support every slot literally, prioritize accurate product fidelity over filling a rigid template. Replace unsupported slots with truthful alternatives and mention the limitation in the final response.

For model-worn sets, Image 1 and Image 2 should use the same model identity. In Image 2, the face may be hidden because the model is back-facing; preserve identity through the same body proportions, height impression, hair length/color, skin tone, posture style, and styling state. Detail images may crop out the face, but any visible skin, hands, neck, hair, feet, footwear, or body proportions should still match the fixed model. If a detail image does not need a person, prefer a garment-only crop rather than introducing another model.

## Generation Standards

Maintain ecommerce realism and product fidelity:

- Use the product fidelity brief as the controlling garment description for every image in that product set.
- Preserve garment color, pattern, silhouette, fabric feel, neckline, sleeves, hem, waist, length, closures, pockets, and visible decorations.
- Avoid changing the category, season, gender presentation, or core style of the item.
- Avoid adding platform text, price tags, watermarks, logos, fake labels, badges, or promotional copy unless the user explicitly asks.
- Keep backgrounds clean and commercial. Use simple studio, white background, light lifestyle, or platform-appropriate ecommerce scenes.
- Keep the product prominent and uncrowded; the first image should make the garment immediately recognizable.
- When using a model reference, keep the same model across products and avoid face drift, body distortion, mismatched limbs, or implausible garment fit.
- Avoid model drift across the set: do not switch to a different face, hairstyle, body shape, age impression, skin tone, expression style, or source-product model. Do not let the garment reference model override the provided model reference.
- Avoid styling drift across the set: preserve or choose one neutral supporting outfit and keep it consistent between front, back, and other model-worn images. Preserve the provided footwear when visible; otherwise create one neutral ecommerce-appropriate shoe pair and keep it consistent across the set. Do not add unrequested bags, hats, jewelry, sunglasses, watches, scarves, or other accessories.
- Avoid batch-context bleed: do not reuse a previous product's colors, patterns, supporting outfit, pose concept, background, or detail claims unless the user explicitly requested a shared direction.
- When the product source image has a strong original model, explicitly separate garment extraction from identity transfer. Preserve the clothing design without borrowing the source model's personhood.
- Do not invent hidden details or selling points such as a back print, embroidery, lining, logo, label, zipper, pocket, button set, or hardware that the source images do not support.
- Avoid construction hallucinations. Do not add visible center-back seams, center-back zippers, invisible zippers, back-neck openings, inner facings, neck tape, hanging loops, overlock stitching, seam allowances, labels, lining, reinforcement patches, or other inside/reverse-side workmanship unless these exact construction features are directly visible in the current product reference.
- When a prompt needs to describe an unsupported area, use wording such as "plain construction-minimal back" or "visible outer fabric crop only" instead of "ordinary garment construction," because ordinary construction can cause the image model to invent plausible but false workmanship.

If the available AI image tool cannot directly produce the requested resolution, generate the highest reliable quality first, then use sensible upscale, crop, pad, or extend operations. Do not stretch the person or clothing unnaturally.

## Output Rules

Create one clean output root folder. For each successful product, create one child folder containing only final images for that product.

Recommended naming:

```text
服装电商主图_YYYYMMDD_HHMMSS/
  001_product-name_主图/
    001_hero.png
    002_back.png
    003_detail.png
```

For 4-5 image sets, continue with `004_scene.png` and `005_white-bg.png` or equivalent descriptive names.

Do not keep intermediate files in the final output folders. Do not create or retain logs, cache files, masks, cropped sources, temporary files, `manifest.csv`, `manifest.json`, README files, blank images, error images, or placeholders unless the user explicitly asks for them.

## Workflow

1. Read the product source folder, optional model image, optional output folder, requested image count, target platform, and output spec.
2. Apply defaults for missing optional values.
3. Validate the model image if provided; pause if it is unsuitable.
4. Group products by direct child folders or loose images.
5. Inspect and filter product references.
6. For each valid product, reset product-specific context and create the internal product fidelity brief from the current source references.
7. Plan the 3-5 image set using the source material actually available. Choose and lock any neutral supporting outfit and footwear needed for the current product before generating Image 1.
8. If a model image is provided, write generation prompts with the identity hierarchy: fixed model controls the person; product references control only garment design; the locked support styling controls shoes and non-product clothing.
9. Generate final images with the current available AI image, virtual try-on, product rendering, or editing capability, using the current product fidelity brief in every prompt.
10. Inspect the full image set before finalizing. Confirm that each image belongs to the current product, Image 2 is a back-view image by default, the same model identity is maintained, the supporting outfit is consistent, footwear is present and consistent across all model-worn images where feet are visible, and Image 3 uses only source-confirmed or conservative visible-surface detail crops. Also confirm that no image invents unsupported inside/reverse-side construction such as center-back seams, back-neck zippers, invisible zippers, labels, neck tape, hanging loops, overlock stitching, seam allowances, inner facings, lining, or reinforcement patches. If Image 2 is not a back view, if shoes or support garments differ between images, if shoes are missing in a full-body model-worn image, if the footwear looks too decorative, if a model-worn image shows a different person, if a detail image invents unsupported selling points or unsupported garment construction, or if any candidate appears to come from another product or previous task, discard it and regenerate with stricter product-brief, construction-minimal, visible-surface-only detail, back-view, identity-lock, footwear-lock, support-styling-lock, and batch-isolation wording before saving it as final.
11. Normalize each successful image to the target spec without distorting the garment or model.
12. Save only final images in the product's output folder.
13. Clean temporary work files before finishing.
14. Reply in chat with the batch summary.

## Final Chat Summary

Report only the useful operational summary:

- Number of detected products.
- Number of successful products.
- Number of images generated per successful product.
- Skipped or failed products and short reasons.
- Final output path.
- Output spec used.
- Whether the same model was maintained across model-worn images when a model image was provided.
- Whether Image 2 was produced as a back-view image by default.
- Whether footwear was preserved from the model reference or generated, and whether it stayed consistent across model-worn images.
- Whether supporting outfit styling stayed consistent across front/back model-worn images.
- Any important source-fidelity limitations, such as missing back/detail/construction references, conservative inferred areas, visible-surface-only detail choices, or discarded wrong-product candidates.

Do not write a processing report file unless the user explicitly asks for one.
