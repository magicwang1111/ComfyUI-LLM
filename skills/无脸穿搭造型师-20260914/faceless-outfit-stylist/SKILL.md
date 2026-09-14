---
name: faceless-outfit-stylist
description: Create exactly three separate product-only flat-lay outfit images in three distinct styles on a mandatory pure-white background around one uploaded hero garment, using a strict 90-degree overhead view with every item fully visible, uncropped, separate, unobstructed, and realistically scaled. Use for 三种搭配, 三套单品搭配, 单品搭配, 服装白底平铺搭配, 90度俯拍穿搭, 穿搭板, 造型板, or when the user wants three styling options for one garment. Never inherit the reference background or include people, body parts, mannequins, hangers, lifestyle props, or a three-look collage.
---

# Three-Style Flat-Lay Outfit Stylist

## Core Goal

Turn one uploaded hero garment into exactly three coherent, commercially wearable outfits in three distinct styling directions. Deliver three separate product-only flat-lay images, one style per image, photographed from directly overhead at a true 90-degree angle. Every item must be complete, uncropped, independent, unobstructed, and realistically scaled. Never include a person, mannequin, body form, human body part, hanger, or lifestyle prop.

Default result:

- exactly three separate images and three coordinated outfits;
- one clearly named style direction per image;
- the same uploaded hero garment appears once in each image and remains the primary visual anchor; a naturally longer supporting garment may occupy more area when realistic scale requires it;
- supporting clothing, footwear, bag, and one or two style-appropriate wearable accessories are separately visible;
- uniform pure-white `#FFFFFF` background only;
- vertical 3:4 by default;
- premium editorial ecommerce / Xiaohongshu styling;
- realistic product photography with soft contact shadows;
- strict 90-degree straight-down overhead camera with no oblique perspective;
- every product fully inside the frame with clear separation and ample negative space;
- no model, try-on, human presence, hanger, or lifestyle prop.

Never combine the three styles into one collage, triptych, grid, comparison board, or multi-panel image. Generate each image as a separate image-generation call so the user receives three actual image files.

## Mandatory Camera and Product-Only Rules

These rules are non-negotiable for every output:

- Background must be seamless, uniform pure white (`#FFFFFF`) across the entire canvas. Do not use off-white, warm white, cream, ivory, light gray, beige, tinted, gradient, textured, shadow-vignette, or environmental backgrounds.
- Treat the input image background as irrelevant source noise. Reference only the hero garment; never sample, inherit, match, imitate, or adapt the input background color, tone, texture, lighting falloff, or border.
- Camera is directly above the layout at exactly 90 degrees, lens axis perpendicular to the background.
- Use a true straight-down bird's-eye flat-lay view. No three-quarter angle, diagonal camera, horizon, wall, floor perspective, depth scene, or eye-level view.
- Show merchandise only. Exclude people, models, mannequins, dress forms, heads, faces, hair, hands, arms, legs, feet, skin, hangers, racks, furniture, plants, books, cups, flowers, food, cosmetics, electronics, travel objects, decorative objects, and all other lifestyle props.
- Every garment, shoe, bag, and accessory must be completely visible inside the canvas. No edge may touch or cross the frame boundary.
- Do not crop, fold out of frame, partially hide, stack, layer, overlap, or occlude any product.
- Keep a visible gap between every separate product. Items may be coordinated spatially but must not touch or cover one another.
- Give every individual product its own exclusive white-space occupancy zone. The visible silhouette and soft shadow of one product must not enter another product's zone; use compact, consistent gutters of roughly 1.5–2.5% of the shorter canvas edge wherever practical.
- Treat the two shoes in a pair as two individual products: show both shoes completely and keep a visible white gap between them. Do not cross, nest, stack, or overlap the pair.
- Preserve realistic relative size: main garments larger than shoes and bags; accessories smaller; paired shoes remain a believable matched pair without oversized or miniature scaling.
- Fill the canvas efficiently with a tidy compact arrangement. Keep enough white space to separate products, but avoid oversized empty zones, sparse scattering, or one blank region dominating the composition. If the layout becomes crowded, remove optional accessories rather than overlap products or distort scale.

## Inputs and Defaults

Required:

- one hero garment image or one clearly identified hero garment.

Optional:

- target gender and age;
- season and occasion;
- platform or style direction;
- output ratio;
- must-use or forbidden item categories;
- three requested style directions;
- whether editorial text or style labels are wanted.

Infer missing optional details from the garment and proceed. Ask only when the hero garment is ambiguous or requested directions materially conflict.

## Hero Garment Lock

Preserve the uploaded garment's visible evidence as the highest priority in all three images:

- color and color blocking;
- silhouette, length, volume, fit, and proportions;
- collar, neckline, hood, sleeves, cuffs, and hem;
- pockets, placket, zipper, buttons, drawstrings, and hardware;
- seams, stitching, quilting, ribbing, pleats, and panels;
- print, embroidery, trim, and visible logo placement;
- fabric texture, thickness, sheen, transparency, and drape.

Do not redesign, recolor, simplify, lengthen, shorten, or cover the hero garment. Do not invent hidden construction. Show it fully and unobstructed as a clean product object. Keep its product identity consistent across the three images.

## Styling Analysis

Identify the garment category, season, target age, occasion, visual weight, dominant color, neutral support colors, and plausible style lanes. Then design three intentionally different outfits while keeping the hero garment faithful and recognizable in every image.

Read `references/outfit-styling-rules.md` when category-specific styling or layout guidance is needed.

## Three-Style Set

Use the user's three named styles when provided. Otherwise infer three distinct, garment-appropriate directions. A reliable default is:

1. polished: commuter, quiet luxury, refined feminine/masculine, or smart casual;
2. relaxed: weekend, minimal casual, soft layered, retro casual, or vacation;
3. energetic: light sport, outdoor, street, youthful, or city athleisure.

Adapt or replace any lane that conflicts with the garment. The three outputs must differ materially in bottoms, footwear, bag/accessory logic, color strategy, and occasion—not merely swap one small accessory. Keep season and target customer coherent across the set unless the user requests otherwise.

## Outfit Construction

For each style, choose relevant supporting categories only:

- one inner layer when useful;
- one bottom or coordinated dress layer;
- one pair of shoes;
- one bag when it improves the outfit;
- at least one and normally no more than two restrained wearable accessories, unless the user explicitly requests no accessories. Suitable options include a watch, earrings, necklace, bracelet, belt, hat, scarf, socks, or eyewear.

Choose accessories for a clear styling purpose: reinforce the occasion, repeat one controlled color, balance material, or clarify the intended wearer. Do not add random filler. Vary the main accessory category across the three looks when credible—for example, a watch for polished styling, a hat or eyewear for casual styling, and a belt or compact jewelry item for a directional look. Avoid accessory checklists and visual clutter. Use at least one clear styling idea per image: proportion balance, tonal dressing, controlled contrast, material contrast, light layering, or one repeated accent color. Each result must look wearable and shoppable rather than costume-like. Do not repeat the same supporting product design in more than one style unless the user requests continuity.

## Flat-Lay Composition

- Use a true 90-degree straight-down overhead camera only.
- Use a seamless, evenly lit, uniform pure-white (`#FFFFFF`) background only, regardless of the input image background.
- Keep the hero garment fully visible as the primary visual anchor. Do not force it to be geometrically larger than a naturally long dress, coat, skirt, or trouser.
- Present every item separately as a product cutout or carefully arranged flat-lay object.
- Prefer a compact, tidy two-column asymmetrical layout with moderate consistent gutters. Align major top edges and neighboring vertical axes so the composition feels orderly. When product shapes permit, use the preferred occupancy pattern from `references/outfit-styling-rules.md`: hero garment in the left main zone, inner top in the upper-right zone, bottom or long supporting garment below it in the right main zone, shoes aligned at the lower-left, and bag at the lower-right. Avoid both rigid equal boxes and loose scattered placement.
- Keep natural product scale relationships; do not enlarge small accessories or shrink main garments to make the layout fit.
- Keep every product fully within frame with a clear outer margin on all sides.
- Never overlap, stack, touch, or obscure products. Maintain a visible gap around each item.
- Allocate one non-intersecting layout cell to every individual garment, shoe, bag, and accessory. Product silhouettes, straps, sleeves, trouser legs, hems, and contact shadows must remain inside their own cells.
- Pair shoes together as one category, but treat each shoe as an independent object: both shoes must be fully visible with white background between their silhouettes. Place the required one or two accessories in genuine residual gaps, grouped neatly but with visible white separation between individual pieces and every nearby product.
- Use soft studio light and subtle realistic shadows so items feel physical, not pasted on.
- Keep a consistent overall photography standard across the three images while allowing each style its own layout rhythm and accent palette.
- Add magazine-style rules, fine divider lines, captions, or style labels only when the user requests text. Otherwise generate no text.

Strictly exclude people, faces, heads, hands, arms, legs, feet, skin, models, mannequins, dress forms, hangers, worn garments, lifestyle scenes, and lifestyle props of any kind.

## Generation Workflow

1. Analyze the hero garment once and define three distinct style briefs before generating.
2. Generate Style 1 as one independent image.
3. Generate Style 2 as a second independent image with different supporting products.
4. Generate Style 3 as a third independent image with different supporting products.
5. Inspect all three outputs for garment fidelity, human absence, single-look composition, and meaningful style differentiation.
6. If one output fails, revise only that image. Do not regenerate acceptable images unnecessarily.

## Default Image Direction

Generate exactly three separate vertical 3:4 premium product-only flat-lay outfit images on a seamless, evenly lit, uniform pure-white (`#FFFFFF`) background. Ignore the reference image background completely and do not inherit its color or tone. Use an exact 90-degree straight-down overhead view in every image. Each image contains one style and one outfit only. Use a compact tidy two-column asymmetrical composition whenever product geometry permits: hero garment in the left main zone, inner top at upper right, bottom or long supporting garment directly below it in the right main zone, shoes aligned along the lower left, and bag at lower right. Fill the usable canvas evenly with moderate consistent gutters and visually aligned edges; do not leave a large empty central or lower zone. Every product must remain fully visible, uncropped, separate, unobstructed, realistically scaled, and divided by visible pure-white spacing. Use clean magazine-inspired spacing, realistic product textures, soft studio daylight, and subtle contact shadows immediately beneath products only; the overall background must remain pure white without gray or colored cast.

Use one separate image-generation call for each style. Do not create a combined three-look image. Do not generate a person, try-on, mannequin, body part, multi-look collage, split comparison, duplicate hero garment within an image, random logo, watermark, or text unless explicitly requested.

## Per-Image Prompt Template

Repeat this prompt separately for Style 1, Style 2, and Style 3. Use the uploaded garment image as the only design reference for the hero garment.

Create exactly one vertical 3:4 premium editorial product-only flat-lay outfit composition for [style name and occasion] on a seamless, evenly lit, uniform pure-white (`#FFFFFF`) background. Ignore the reference image background completely; use the input only for the hero garment. Do not sample, inherit, match, imitate, or adapt any source background color or tone. Use a true 90-degree straight-down overhead camera, with the lens perpendicular to the surface and no oblique perspective. This image contains one outfit only. The hero garment must remain fully visible as the primary visual anchor. Prefer a compact tidy two-column asymmetrical occupancy pattern: hero garment in the left main zone; inner top in the upper-right zone; bottom or longest supporting garment directly below it in the right main zone; the two shoes neatly aligned in separate lower-left positions; bag in the lower-right position; one or two required wearable accessories placed neatly in genuine residual gaps. Align nearby top edges, centerlines, and lower anchors while preserving natural item shapes. Fill the usable canvas evenly and avoid any oversized blank central, side, or lower region. Adapt this pattern only when product geometry requires it. Arrange all supporting items as separate product objects: [inner layer], [bottom], [shoes], [bag], and [one or two required style-appropriate wearable accessories]. Every item must be complete, fully inside the canvas, uncropped, unobstructed, realistically scaled, and placed in its own non-intersecting white-space zone. Use compact consistent gutters of roughly 1.5–2.5% of the shorter canvas edge and preserve clearly visible pure-white background between every two complete silhouettes, including the two shoes of a pair and each accessory. No garment edge, sleeve, trouser leg, shoe, strap, bag handle, accessory, or contact shadow may touch, overlap, stack on, cross into, cover, or sit beneath another product. Preserve a consistent compact outer margin around the entire layout.

Hero garment lock: preserve its visible color, silhouette, proportions, texture, neckline or hood, sleeves, cuffs, hem, pockets, seams, stitching, closures, hardware, print, trim, and logo placement. Do not redesign, recolor, reshape, simplify, overlap, or cover important details.

Set position: image [1/2/3] of 3. Styling direction: [occasion, age, style lane, season]. Make this outfit materially different from the other two through its bottom, footwear, bag/accessory logic, palette, and occasion. Palette: [dominant], [neutrals], [optional accent]. Styling idea: [proportion/material/layer/color-repeat idea]. Use realistic product photography, natural item scale, soft studio daylight, subtle contact shadows, and generous editorial whitespace.

Show merchandise only. No person, model, face, head, hair, hands, arms, legs, feet, skin, mannequin, dress form, hanger, worn clothing, lifestyle scene, furniture, plant, flower, book, cup, food, cosmetic, electronic device, or decorative prop. One outfit only; no multiple looks, triptych, grid, split layout, duplicate garments, random logos, watermark, or text unless requested.

## Quality Gate

Before delivery, confirm:

- exactly three separate images, each containing exactly one outfit;
- every image has a seamless uniform pure-white (`#FFFFFF`) background with no inherited source color, tint, gradient, texture, or vignette;
- every image uses a true 90-degree straight-down overhead view with no visible perspective angle;
- the three style directions are named and visually distinct;
- the hero garment is recognizable, faithful, unobstructed, and functions as the primary visual anchor in every image, without unrealistic size inflation;
- the composition is compact, tidy, and efficiently filled, with aligned edges and consistent moderate gutters rather than oversized blank zones or loose scattering;
- the preferred two-column pattern is used whenever compatible: left hero, upper-right inner top, right-side bottom/long garment, lower-left shoes, lower-right bag;
- every product is complete, uncropped, fully inside the frame, realistically scaled, and surrounded by clear space;
- no products touch, overlap, stack, hide, or obstruct one another;
- every individual item has its own non-intersecting white-space zone, with visible pure-white separation between all product silhouettes and between both shoes;
- no person, body part, mannequin, hanger, try-on state, lifestyle scene, or lifestyle prop appears;
- categories, target age, season, and occasion are coherent within each style;
- bottoms, shoes, bags/accessories, and color strategies differ meaningfully across the set;
- accessories remain restrained and layouts are not crowded;
- every image includes at least one style-appropriate wearable accessory unless the user explicitly forbids accessories;
- accessories serve a visible styling purpose, differ across the set when credible, remain realistically scaled and are fully separated from every other product;
- ratios and optional text match the request;
- no combined three-look collage, duplicate items within an image, random logos, watermarks, or malformed product shapes.

If garment fidelity conflicts with styling novelty, preserve the garment and simplify the composition.
