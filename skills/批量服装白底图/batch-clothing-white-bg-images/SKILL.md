---
name: batch-clothing-white-bg-images
description: "Use when the user needs clothing white-background product main images, front flat-lay/straight-hanging catalog photos, model removal, floor flat-lay cleanup, wrinkle smoothing, 主图修平整, 褶皱修少一点, 批量服装白底图, 白底平铺图, 挂拍白底图, 服装白底主图, or 电商白底图."
---

# Batch Clothing White Background Images

## Purpose

Create ecommerce-ready clothing white-background main images in batches. Treat every supported input image as one independent production task: one input image produces exactly one final image.

The required final style is a **front-facing flat-lay or straight-hanging product catalog main image** on a pure white background. The garment must look like an inspectable, sellable marketplace main image: complete, centered, naturally spread, visually tidy, front or back view as appropriate, and not worn by a person.

This skill is not for simple model cutouts. A white-background image that still preserves a model-worn pose, hollow body, ghost-mannequin torso, skin holes, hand/arm/leg gaps, shoes, face, hair, or body silhouette is a failed output.

This skill is also not only a background-removal skill. If the source is a casual floor flat-lay, wrinkled sample photo, or rough cutout, the final should be polished into a cleaner product main image when the visible garment supports it.

## Inputs and Defaults

Collect or infer these inputs before processing:

- **Input images or folder**: Required. Accept one uploaded image, multiple uploaded images, or a user-specified folder.
- **Folder scan rule**: When a folder is provided, find every supported image in that folder and its child folders unless the user asks to limit scanning.
- **Output folder**: Optional. If absent, create a desktop folder named like `服装平铺白底图_YYYYMMDD_HHMMSS`.
- **Output spec**: Default to `1:1 square, 2000 x 2000 px, pure white #FFFFFF background`.
- **Output polish**: Default to sellable ecommerce main-image polish when the source has messy wrinkles, uneven hems, rough edges, floor shadows, or when the user says 主图, 好看, 修平整, 细节修补, or 褶皱太多.
- **Output count**: Fixed at one final image per input image.

Supported source image types: `.jpg`, `.jpeg`, `.png`, `.webp`. Ignore unsupported files and non-image files.

Ask only when no valid image or folder is provided, the target garment is ambiguous enough to change the output materially, or the user requests a special mode that conflicts with the one-image-one-output rule.

## Required Visual Target

Every final image must match these rules:

- Product appears as a front-facing flat-lay or straight-hanging catalog item, not a model-worn photo.
- Garment or outfit is complete, centered, upright, naturally opened/spread, and commercially inspectable.
- Garment should look like a polished ecommerce main image, not a raw floor photo. Reduce distracting wrinkles, lumpy bulges, twisted edges, jagged cutout artifacts, and uneven silhouette while preserving natural fabric texture and construction.
- Sleeves, cuffs, shoulders, neckline, collar, placket, waistband, hem, trouser legs, skirt body, dress body, and visible trims are reconstructed into a clean product shape when the source was model-worn.
- Smooth and regularize expected product lines: sleeves, cuffs, shoulders, collar/neckline, waistband, hem, trouser legs, skirt body, and side seams should look tidy and reasonably symmetric for a catalog image.
- Symmetry may be used to reasonably complete left/right garment parts hidden by arms, hands, pose, or body, as long as the visible design is preserved.
- Source color, fabric texture, print scale, motif placement, ribbing, lace, mesh, buttons, zippers, belt, pockets, drawstrings, seams, pleats, and hems must remain faithful.
- Background is pure white `#FFFFFF` or visually pure white, with no wall, floor, room, prop, hanger, mannequin stand, watermark, text, or logo overlay.
- Use soft minimal studio shadow only when needed to separate pale fabric from white background.

Do not output:

- A model/person on a white background.
- A cutout that keeps the human pose.
- Ghost-mannequin, hollow-body, empty torso, detached sleeves caused by removed arms, or white holes where hands/body used to be.
- Cropped fragments when the final product can be reasonably reconstructed.
- Extra front/back/detail/color variants unless explicitly requested.
- Raw-looking outputs that technically have a white background but still show excessive random wrinkles, floor-photo distortion, dirty edge residue, or obvious cutout artifacts.
- Over-smoothed outputs that erase fabric texture, ribbing, seams, pleats, lace, mesh, pale trims, labels, or visible construction.

## One Image, One Output

Apply these rules strictly:

- One input image produces one final image.
- Do not split one input into multiple outputs.
- Do not merge multiple input images into one output.
- Do not infer product sets across files. Treat each input image independently.
- If a source shows a front view, create a front-view flat product image.
- If a source clearly shows a back view, create a back-view flat product image and preserve rear details.
- If a source is side, three-quarter, or strongly posed, normalize it into the most faithful front/back product presentation supported by visible evidence rather than preserving the body pose.

## Main Product Selection

Before generation or editing, identify the main clothing subject from the current image only.

Use this priority order:

1. **Single complete garment**: Generate that garment as one flat product image.
2. **Complete top + bottom outfit**: If both are visible and read as one coordinated set, generate the full outfit as one flat product image.
3. **One-piece garment**: For a dress, jumpsuit, romper, long coat, robe, or similar item, generate the complete one-piece product.
4. **Outerwear with inner layer**: If the main product is jacket, blazer, coat, cardigan, vest, or overshirt over an inner layer, generate only the outerwear unless the image clearly presents the full outfit as the product.
5. **Bottom-only or top-only product**: If the source focuses on pants, skirt, shorts, shirt, blouse, sweater, or top, generate only that product.
6. **Ambiguous multi-product image**: If unrelated products, collage panels, piles, or side-by-side items make the target unclear, skip or ask for a clearer target.

Do not add unrelated styling pieces, accessories, shoes, bags, hats, jewelry, or props unless the visible source product is explicitly a coordinated outfit.

## Person and Model Removal

If the source contains a person, model, mannequin body, visible skin, face, hair, hands, arms, legs, feet, shoes, jewelry, bag, phone, pose, or lifestyle styling, treat those elements as non-product context.

Apply these rules strictly:

- Remove all body parts: face, hair, neck/head, skin, arms, hands, legs, feet, and body silhouette.
- Remove shoes and non-product accessories unless they are the explicit product.
- Reconstruct the garment into a complete flat-lay or straight-hanging product shape.
- Do not preserve the model pose as garment geometry when it makes sleeves, legs, waist, or skirt shape unnatural.
- Do not leave holes where body parts were removed. Fill occluded garment areas using faithful reconstruction from visible fabric, symmetry, seams, print, texture, and silhouette.
- If too much of the product is hidden to reconstruct responsibly, skip or report the limitation rather than outputting a poor model cutout.

## Category-Specific Rules

Use a square 2000 x 2000 canvas with balanced margins. Keep the item large enough for ecommerce browsing while preserving the whole product.

- **Dress**: Show complete neckline, sleeves or straps, bodice, waist, skirt volume, fabric drape, and hem. Reconstruct a clean symmetric product shape from model-worn poses.
- **Shirt, blouse, T-shirt, sweater, vest, cardigan, jacket, or coat**: Preserve collar/neckline, shoulders, sleeve length, cuffs, opening/closure, placket, buttons/zipper, pockets, texture, and hem. Arrange sleeves naturally down or slightly outward in catalog style.
- **Pants or shorts**: Preserve waistband, fly/closure, belt if product-relevant, pockets, pleats, side seams, leg width, and hems. Remove feet/shoes and complete leg openings cleanly.
- **Skirt**: Preserve waistband, pleats, panels, volume, trim, and hem. Remove legs and reconstruct the skirt front as a product.
- **Complete outfit or set**: Keep relative top/bottom proportions, but present the outfit as a clean flat product set rather than a body pose.
- **Back-view product**: Preserve rear construction such as back seam, zipper, collar, yoke, rear pockets, waistband, or back print. Do not invent front details.
- **Pale, white, lace, mesh, chiffon, satin, or glossy garments**: Keep background pure white while preserving off-white tone variation, lace holes, mesh structure, seams, folds, and edge contrast.

## Product Fidelity Brief

For each input image, create a concise internal brief before generation or editing:

- Main product type: single garment, full outfit, outerwear, top, bottom, dress, set, or unknown.
- Desired product presentation: front flat-lay, back flat-lay, or straight-hanging catalog view.
- Primary/secondary colors, print, stripe direction, motif placement, and color blocking.
- Silhouette, fit, length, neckline, collar, sleeve, shoulder, waist, hem, volume, and proportion.
- Fabric impression, knit/woven texture, lace, crochet, mesh, sheen, transparency, thickness, drape, and structure.
- Visible construction: buttons, zipper, pockets, belt, waistband, pleats, drawstrings, cuffs, trim, embroidery, scallop edge, closures, and seams.
- Main-image polish plan: which wrinkles, lumpy areas, twisted edges, asymmetric sleeves/legs, uneven hems, or cutout defects should be cleaned up; which natural folds and texture should remain.
- Person/model context to remove and garment areas that need reconstruction.
- Edge/exposure risk for pale or transparent fabric.
- Unknown areas that must not receive unsupported decorative details.

Do not invent logos, labels, prints, pocket shapes, trims, embroidery, back details, or hardware not visible or strongly supported by the current image. Reasonable completion of hidden plain fabric, sleeve continuation, waistband continuation, skirt volume, and symmetric garment structure is allowed when needed to make a clean product image.

## Mode Selection

Choose the lowest-change method that can satisfy the required flat product target:

- **Cleanup and resize mode**: Use only when the input is already a clean front-facing flat-lay, straight-hanging, hangerless, or product-only white-background image.
- **Background replacement mode**: Use when the source already shows product-only flat clothing but the background is not pure white.
- **Product main-image retouch mode**: Use when the source is product-only but looks like a casual floor flat-lay, has many distracting wrinkles, uneven pose, rough cutout edges, floor shadows, or the user asks for 主图, 好看, 修平整, 细节修补, or fewer wrinkles. Retouch the garment into a cleaner, smoother, more symmetric catalog main image while preserving the same product identity and visible construction.
- **Flat product regeneration mode**: Use by default for model-worn/person photos. Convert the clothing reference into a complete front-facing flat-lay or straight-hanging product image. Do not merely cut out the model pose.
- **Outerwear extraction mode**: Use when outerwear is the main product. Remove the inner layer unless the full outfit is explicitly the product, and reconstruct the outerwear as a flat product.

If the available tool cannot perform product regeneration or main-image retouching and can only mask/cut out the garment, do not claim that the output meets this skill. Report the limitation or switch to an AI image generation/editing tool.

## AI Generation Prompt Requirements

When using AI generation or AI editing, include these protection lines in every prompt:

```text
生成“正面平铺/正挂拍衣服白底商品图”，不是“模特穿着白底图”，也不是 ghost-mannequin / hollow-body。去除人物、脸、头发、皮肤、手臂、手、腿、脚、鞋、首饰、包和所有道具，只保留衣物产品本体。
衣服必须完整、对称、自然展开，按电商商品平铺图方式重建被身体、手臂、手、腿、姿势遮挡的袖子、门襟、腰部、裤腿、裙摆和下摆；不能留下人体空洞、断袖、断腿、皮肤残留或穿着姿势轮廓。
边缘锐利清晰，衣物与背景边界分明，无杂色噪点；背景纯白 #FFFFFF；避免白色过曝和高光溢出，保留衣物褶皱、缝线、领口、袖口、门襟、口袋、纹理和面料层次。
```

For ecommerce main-image polish, also add:

```text
按“电商商品主图”标准精修：减少杂乱褶皱、鼓包、扭曲边缘和不规则阴影；修顺袖子、裤腿、袖口、裤脚、腰头、下摆、领口、肩线、侧缝和轮廓，让衣服更平整、对称、干净、可上架。
不要改变商品款式、颜色、面料、版型、罗纹、缝线、口袋、图案、浅色拼接、装饰件或可见结构；保留自然面料纹理和少量真实折痕，不能修成塑料感或全新设计。
```

For model/person sources, also add:

```text
不要生成或保留模特、真人、脸、头发、手、手臂、腿、脚、鞋、皮肤、人体轮廓、ghost mannequin、hollow body 或穿着姿势；如果结果只是人物白底照或模特姿势抠图，则视为失败，需要重新生成平铺商品图。
```

For white, cream, pale pastel, lace, mesh, chiffon, satin, or glossy garments, add:

- Keep the background pure white `#FFFFFF`, but do not turn the garment into blank pure white.
- Preserve natural fabric tone variation and low-contrast construction details.
- Use subtle edge contrast or very soft shadow only where needed to separate pale fabric from the white background.
- Do not erase pale sleeves, collars, cuffs, hems, lace holes, mesh openings, embroidery, or transparent structure into the background.

## Batch Isolation

Treat each image as an isolated task:

- Reset assumptions for every input.
- Do not copy garment type, color, print, construction, or view angle from previous images.
- Do not use previous outputs as references for the next image unless the user explicitly says the files are one product set.
- Reject and redo any candidate that resembles a previous input, changes the product type, keeps a person, or fails the flat product target.

## Output Rules

Create one clean output root folder. Save one final image for each successful input image.

Recommended structure:

```text
服装平铺白底图_YYYYMMDD_HHMMSS/
  001_original-file-name_白底图.png
  002_original-file-name_白底图.png
  003_original-file-name_白底图.png
```

If filename collisions occur, keep the stable index prefix and original base name. Do not overwrite outputs from another input image.

Do not keep intermediate files in the final output folder. Do not create logs, masks, cropped sources, cache files, manifests, blank images, error images, or placeholders unless the user explicitly asks.

## Workflow

1. Read the uploaded images or user-specified folder.
2. Build an input queue from every supported image in stable folder/path order.
3. Apply defaults: one output per input, `1:1`, `2000 x 2000 px`, pure white `#FFFFFF`.
4. Inspect the current source image and identify the main product, desired flat product presentation, visible details, and reconstruction needs.
5. Skip or ask when the target is ambiguous, unrelated multi-product, unusable, or unsupported.
6. Write the internal product fidelity brief.
7. Choose cleanup, background replacement, flat product regeneration, or outerwear extraction mode.
8. If product main-image retouch mode applies, generate or edit a cleaner catalog-ready version before final sizing: reduce distracting wrinkles, tidy silhouette, remove edge/floor artifacts, and keep product identity faithful.
9. Generate or edit exactly one final front-facing flat-lay or straight-hanging white-background product image.
10. Inspect before saving:
   - exactly one output;
   - 2000 x 2000;
   - pure white background;
   - correct current garment or outfit;
   - complete flat product shape;
   - sellable main-image polish when requested or needed: tidy silhouette, reduced distracting wrinkles, clean cuffs/waistband/hem/legs/sleeves, and no raw floor-photo look;
   - no person, face, hair, skin, hands, arms, legs, feet, shoes, props, model pose, ghost mannequin, hollow body, or body holes;
   - no invented unsupported decoration;
   - no lost pale details, erased ribbing, missing seams, changed print, or over-smoothed fabric;
   - crisp edges and readable fabric details.
11. Reject and regenerate any candidate that is merely a model cutout on white, a raw cutout with floor residue, or a technically white-background image that still looks unsuitable as a product main image after the user asked for polish.
12. Save with stable index and source filename.
13. Continue until every valid input image has one output or a recorded skip reason.
14. Reply with a concise batch summary.

## Final Chat Summary

Report only useful operational results:

- Number of input images detected.
- Number of successful flat white-background product images.
- Number of skipped or failed images with short reasons.
- Final output path.
- Output spec: `1:1, 2000 x 2000 px, #FFFFFF`.
- Whether the batch included single garments, complete outfits, outerwear extraction cases, pale-fabric cases, product main-image retouch cases, or ambiguous skips.
- Any important fidelity limitations, such as incomplete source visibility or areas reconstructed from symmetry.

Do not write a separate report file unless the user explicitly asks for one.
