---
name: outfit-flatlay-stylist
description: 'Create complete fashion outfit plans and AI image prompts or generations from a single style, hero garment, SKU, or clothing photo; use when the user asks for 搭配, 穿搭, 服装搭配, 上下里外搭配, 配饰鞋帽搭配, 白底平铺图, or flat lay outfit images.'
---

# Outfit Flatlay Stylist

## Overview

Turn one style, hero garment, product photo, SKU, or mood phrase into a complete outfit system and a white-background editorial styling board. Match the bundled layout reference: magazine-like fashion trend board, clean white canvas, generous top whitespace, asymmetric product collage, thin warm-gold rules, bilingual heading blocks, LOOK number, product captions, realistic garment cutouts, soft shadows, no model.

For visual matching, read `references/flatlay-style-guide.md` before the first generation in a session or whenever the user asks to match the provided example layout.

## Workflow

1. Identify the anchor.
   - Extract the hero item or style: category, color, material, silhouette, season, gender/market, occasion, and price/style level.
   - If the user gives only a broad style, choose a commercially plausible hero item and state it briefly.
   - Ask only when the missing detail would materially change the outfit, such as gender/market, season, or product category.

2. Build the outfit around the anchor.
   - Include the full logic of 上下里外: top, bottom, inner layer, and outer layer whenever the season/style allows.
   - If the anchor is a top, choose bottom, inner/outer layer, shoes, bag, hat, socks, and accessories.
   - If the anchor is a bottom, choose top, inner/outer layer, shoes, bag, hat, socks, and accessories.
   - If the anchor is outerwear, choose inner top, bottom, shoes, bag, hat, socks, and accessories.
   - If the anchor is a one-piece item, add outer/inner styling, shoes, bag, hat, socks or legwear, and accessories.
   - Use 7-10 visible items total so the final image feels complete but not crowded.

3. Style the outfit.
   - Use one anchor color, 2-3 supporting neutrals, and optionally one small accent color.
   - Mix textures deliberately: knit with cotton, denim with leather, wool with polished metal, nylon with suede, etc.
   - Keep accessories coherent with the scene: bag, jewelry or watch, belt or sunglasses, socks, scarf, hair accessory, or small leather goods.
   - Include shoes and a hat/headwear unless they conflict with the requested style.
   - Avoid visible logos, brand marks, printed text, mannequins, hangers, bodies, props, labels, packaging, and busy backgrounds.

4. Compose the image prompt.
   - Write image prompts in English for better model reliability.
   - Specify: 4K vertical 3:4 composition by default when the user does not provide output specs, pure white seamless background, editorial fashion material board, realistic isolated product photography, soft studio shadows, natural fabric texture, no model.
   - Use the reference layout structure:
     - Top 18-24% of canvas stays mostly open white space.
     - Upper-left title block: bold Chinese trend title, smaller Chinese subtitle, thin warm-gold rule, uppercase English descriptor line.
     - Upper-right title block: large warm-gold serif `LOOK 01` style number, small uppercase style name, thin rule, small study/editorial line.
     - Main body: oversized hero top or outerwear on the left half, main bottom or dress tall on the right half, with accessories staggered between and around them.
     - Left lower/middle: bag and shoes stacked beneath the hero garment.
     - Right upper: eyewear, jewelry, hat, or small accessories above the main bottom.
     - Captions sit near each item, using short brand/category text and optional price lines.
     - Footer: thin warm-gold line at lower-left with archive/edit text, and small uppercase curator text at lower-right.
     - Optional left margin vertical warm-gold rule with tiny dot endpoints.
   - Keep each product fully visible with clean breathing room. Allow natural editorial overlap only when it improves hierarchy.
   - Avoid centered grid layouts; the board should feel like an airy luxury magazine collage.

5. Generate and save.
   - Use the output folder specified by the user. Do not hard-code a default output directory.
   - Use the available raster image generation tool for the final image. If image generation is unavailable, save the final prompt and outfit plan in the requested output folder and explain that generation could not be run.
   - Use filenames like `YYYYMMDD-HHMM_style-slug_flatlay.png`; save a matching `YYYYMMDD-HHMM_style-slug_prompt.md` containing the outfit plan and prompt.

## Prompt Template

Use this structure and fill every bracket:

```text
Top-down flat lay product photography of a complete [style/occasion/season] outfit on a pure white seamless background.
Hero item: [anchor item, color, material, silhouette].
Include: [outer layer], [inner/top], [bottom], [shoes], [bag], [hat/headwear], [socks/legwear], [accessories].
Palette: [anchor color], [supporting neutrals], [accent if any].
Composition: 4K vertical 3:4 by default unless the user specifies another output format, white luxury editorial fashion material board. Leave the top fifth mostly blank. Upper-left bilingual headline block with bold Chinese title, subtitle, thin warm-gold rule, and uppercase English descriptor. Upper-right large warm-gold serif LOOK number with small uppercase look name and rule. Oversized hero garment on the left, tall main bottom or dress on the right, accessories staggered around them, short item captions and optional price lines near products, thin footer rule and curator text, optional left vertical gold rule with dot endpoints. All items fully visible, no hard cropping.
Lighting and material: soft studio shadows, realistic textile texture, crisp product edges, high-key commercial catalog look, refined beige/black/warm-gold typography.
No model, no person, no mannequin, no hanger, no watermark, no packaging, no colored background, no clutter, no random decorative props. Avoid visible brand logos on products; editorial captions may include requested brand/category names.
```

## Outfit Plan Format

Before generating, produce a compact plan:

```text
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

## Quality Checklist

Before finishing, verify:

- White or near-pure white background.
- Editorial material-board layout with top whitespace, left title block, right LOOK block, main collage, captions, and footer.
- Top-down or front-facing isolated product photography, not worn by a person.
- Full outfit includes clothing, shoes, accessories, and hat/headwear when appropriate.
- 上下里外 logic is satisfied or the omission is intentional and explained.
- Objects are separated, uncropped, and visually balanced.
- No visible product logo, watermark, hanger, mannequin, packaging, or random decorative props.
- Text is intentional editorial typography only: title, LOOK number, short descriptors, item captions, and footer.
- Image and prompt file are saved in the requested output folder when generation succeeds.
