---
name: outfit-white-background-stylist-0824
description: 'Create complete fashion outfit plans and fast, text-free AI flat-lay images on a pure white background from a style, hero garment, SKU, or clothing photo. Use for 0824白底图搭配, 无字搭配图, 纯白底搭配图, 服装搭配, 上下里外搭配, 配饰鞋帽搭配, or text-free white-background outfit flat lays.'
---

# 0824 White Background Outfit Stylist

## Overview

Turn one style, hero garment, product photo, SKU, or mood phrase into a complete outfit system and a clean product flat lay on a pure white background. Keep the source skill's outfit logic, realistic product cutouts, soft studio shadows, asymmetric composition, and no-model presentation.

The generated image must contain products only: no title, caption, label, LOOK number, price, footer, decorative line, watermark, logo, or any other visible text or graphic layout element.

Read `references/flatlay-style-guide.md` before the first generation in a session or whenever composition guidance is needed.

## Workflow

1. Determine the requested output count.
   - Read the number of outfit sets or images from the user's current prompt and call it `N`.
   - Never assume a fixed multi-image count. If the user requests `N` sets, create exactly `N` distinct outfit plans and exactly `N` image files.
   - If the user does not specify a count, default to one outfit and one image.

2. Identify the anchor.
   - Extract the hero item or style: category, color, material, silhouette, season, gender or market, occasion, and price or style level.
   - If the user gives only a broad style, choose a commercially plausible hero item and state it briefly.
   - Ask only when a missing detail would materially change the outfit, such as gender or market, season, or product category.

3. Build each outfit around the anchor.
   - Include the full logic of 上下里外: top, bottom, inner layer, and outer layer whenever the season and style allow.
   - If the anchor is a top, choose a bottom, inner or outer layer, shoes, bag, hat, socks, and accessories.
   - If the anchor is a bottom, choose a top, inner or outer layer, shoes, bag, hat, socks, and accessories.
   - If the anchor is outerwear, choose an inner top, bottom, shoes, bag, hat, socks, and accessories.
   - If the anchor is a one-piece item, add outer or inner styling, shoes, bag, hat, socks or legwear, and accessories.
   - Use 7-10 visible items total so the image feels complete but not crowded.
   - For multiple outputs, design all `N` looks before generation and make them clearly different. Keep only the user's anchor item fixed; vary at least four of these dimensions between looks: style direction or occasion, inner or top, bottom silhouette and color, shoes, bag, headwear, accessories, supporting palette, and material mix.
   - Do not produce minor color swaps or near-duplicate accessory substitutions unless the user explicitly requests close variants.

4. Style each outfit.
   - Use one anchor color, 2-3 supporting neutrals, and optionally one small accent color.
   - Mix textures deliberately, such as knit with cotton, denim with leather, wool with polished metal, or nylon with suede.
   - Keep accessories coherent with the scene: bag, jewelry or watch, belt or sunglasses, socks, scarf, hair accessory, or small leather goods.
   - Include shoes and a hat or headwear unless they conflict with the requested style.
   - Avoid visible logos, brand marks, printed text, mannequins, hangers, bodies, props, labels, packaging, and busy backgrounds.

5. Compose one independent image prompt per outfit.
   - Write image prompts in English for better model reliability.
   - Specify 4K vertical 3:4 by default when the user does not provide output specs, a uniform pure white seamless background, realistic isolated product photography, soft grey studio shadows, natural fabric texture, and no model.
   - Arrange the hero garment prominently on the left and the main bottom or one-piece item on the right, with accessories staggered through the remaining whitespace.
   - Keep every product fully visible, clearly separated, and away from hard canvas crops. Allow only slight natural overlap when it improves hierarchy.
   - Fill the canvas evenly with clean breathing room. Do not reserve space for headings or captions.
   - Explicitly prohibit all letters, words, numerals, symbols used as text, captions, prices, logos, watermarks, tags, borders, rules, color blocks, and decorative graphics.
   - Avoid centered grids; preserve the airy asymmetric fashion flat-lay composition.
   - Each prompt must describe exactly one look and must not mention, summarize, or combine any of the other looks.

6. Generate and save using the fast path.
   - Use the output folder specified by the user. Do not hard-code a default output directory.
   - For `N` requested looks, make `N` independent image-tool calls and set `output_count=1` on every call. Never request all variants from one call with `output_count=N`.
   - Reuse the same reference image for each independent call when the user supplies an anchor image.
   - Submit the independent calls in parallel when the runtime supports parallel tool calls, so stronger variation does not add unnecessary waiting time.
   - Give every call only its own single-look prompt. Do not place several outfit descriptions in one image prompt.
   - Use the available raster image generation tool. If image generation is unavailable, save the final prompt and outfit plan in the requested output folder and explain that generation could not be run.
   - Use distinct filenames such as `YYYYMMDD-HHMM_look-01_style-slug_flatlay.png` through `look-NN`; save matching prompt files when the workflow supports them.
   - After generation succeeds, return the saved result immediately. Do not open, reload, inspect, review, score, or visually verify the generated image. Do not create a contact sheet and do not run a second image-generation pass unless the user explicitly requests it or the generation call fails.

## Prompt Template

Fill every bracket:

```text
Top-down flat lay product photography of a complete [style/occasion/season] outfit on a uniform pure white (#FFFFFF) seamless background.
Hero item: [anchor item, color, material, silhouette].
Include: [outer layer], [inner/top], [bottom], [shoes], [bag], [hat/headwear], [socks/legwear], [accessories].
Palette: [anchor color], [supporting neutrals], [accent if any].
Composition: 4K vertical 3:4 by default unless the user specifies another format. Airy asymmetric commercial fashion flat lay, prominent hero garment on the left, main bottom or one-piece item on the right, accessories naturally staggered around them. Every product is fully visible, clearly separated, and uncropped. Use the canvas evenly with clean breathing room and no reserved text areas.
Lighting and material: high-key catalog lighting, subtle soft grey studio shadows, realistic textile texture, crisp product edges, accurate product colors.
Products only. Absolutely no text, letters, words, numbers, captions, titles, LOOK number, prices, labels, tags, logos, brand marks, watermarks, borders, lines, color blocks, icons, or decorative graphics anywhere in the image. No model, person, body part, mannequin, hanger, packaging, colored background, room, tabletop texture, or unrelated prop.
```

## Outfit Plan Format

Before generating, produce this compact plan separately for every requested look:

```text
Look [index] of [N]:
Anchor:
Outer:
Inner/Top:
Bottom:
Shoes:
Bag:
Hat:
Accessories:
Socks/Legwear:
Palette:
Image Prompt:
Output Path:
```

## Preflight Checklist

Check the plan and prompt once before generation:

- Require a uniform pure white background with products only.
- Prohibit every form of visible text, logo, label, number, watermark, border, line, or decorative graphic.
- Use isolated top-down or front-facing product photography, not clothing worn by a person.
- Include a complete outfit with clothing, shoes, accessories, and headwear when appropriate.
- Satisfy the 上下里外 logic or make an intentional style-appropriate omission.
- Keep objects separated, uncropped, balanced, and free of hangers, mannequins, packaging, and unrelated props.
- Match the user's requested count exactly and keep every look materially different from the others.
- Use one single-look prompt and one `output_count=1` image-tool call per look; never batch multiple variants into one generation call.
- After generation, skip all image review and deliver the result immediately.
