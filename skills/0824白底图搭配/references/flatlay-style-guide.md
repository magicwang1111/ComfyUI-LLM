# Text-Free White-Background Flatlay Style Guide

Use a clean commercial fashion flat lay with an airy asymmetric arrangement, realistic isolated product photography, and a uniform pure white background. Preserve the source outfit-building logic while removing the entire editorial text layer.

## Visual Rules

- Use a uniform pure white `#FFFFFF` seamless background, not a room, tabletop, colored paper, marble, wood, textile surface, gradient, or off-white panel.
- Show only the outfit products. Do not add typography, captions, titles, LOOK numbers, prices, footer copy, labels, borders, hairline rules, color blocks, icons, or decorative graphics.
- Prevent accidental pseudo-text: no visible brand logos, printed words, letter-like marks, watermarks, price tags, hang tags, or readable packaging.
- Use isolated product photography with a top-down flat-lay or front-facing catalog feel. Do not show a model, hands, body parts, mannequins, hangers, or retail packaging.
- Render realistic garment cutouts with natural fabric wrinkles, seams, ribs, buttons, zippers, pockets, stitching, and accurate material texture.
- Use subtle soft grey studio shadows directly beneath objects to ground them while keeping the overall image bright and white.
- Use a 4K vertical 3:4 canvas by default when the user does not provide output specs.
- Show each item as a distinct, fully visible object. Avoid piles, clutter, heavy overlap, or hard cropped edges.

## Layout Blueprint

- Place the hero garment prominently across the left half, occupying roughly 42-52% of the canvas width.
- Place the main bottom, dress, or skirt vertically on the right half, occupying roughly 30-38% of the canvas width.
- Place eyewear, jewelry, or another small accessory near the upper-right area.
- Place the handbag and shoes around the lower-left or lower-middle area without covering the hero item.
- Place remaining accessories in natural gaps to balance the composition.
- Maintain consistent outer margins and clean whitespace between objects.
- Distribute products across the canvas; do not reserve an empty header or footer for text.
- Avoid a rigid centered grid. Keep the composition asymmetric, deliberate, and easy to inspect.

## Styling Heuristics

- Keep the palette controlled: one anchor family, 2-3 supporting neutrals, and at most one restrained accent.
- Repeat colors across categories so the outfit feels intentional, such as headwear matching trousers or socks echoing an accent.
- Mix at least two textures, such as knit plus twill, denim plus leather, nylon plus suede, or wool plus metal.
- Include practical fashion-commerce categories: outerwear, inner or top, bottom, shoes, bag, headwear, socks or legwear, and jewelry, watch, or eyewear.
- Prefer timeless, easy-to-understand silhouettes over abstract fashion objects.

## Multiple-Output Variation

- Treat the outfit count in the user's prompt as dynamic `N`; never assume a fixed number of looks.
- Plan all `N` looks first, keeping the supplied hero item fixed while giving each look a distinct style direction or occasion.
- Between looks, change at least four meaningful dimensions: inner or top, bottom silhouette and color, footwear, bag, headwear, accessories, supporting palette, or material mix.
- Avoid producing the same silhouette and merely changing small colors or accessories.
- Write one self-contained prompt for each look. A prompt must contain only that look and must not reference the other requested looks.
- Generate each look in a separate image-tool call with `output_count=1`. Independent calls may be submitted in parallel, but never batch all looks into one generation call.
- Return exactly `N` separate image files.

## Fast Delivery Rule

Perform composition and constraint checks on the outfit plan and prompt before generation only. Once image generation succeeds, do not open or inspect the output, do not run image review, do not make a contact sheet, and do not regenerate merely to improve appearance. Deliver the generated file immediately unless the user explicitly asks for revisions.
