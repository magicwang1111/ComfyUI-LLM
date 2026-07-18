---
name: fashion-model-outfit-swap
description: Create photorealistic fashion outfit-swap images from a fixed input pattern of one base scene image, one outfit or styling image, and multiple identity photos of the same model. Use when the user asks to 换装, 换衣服, 替换模特, 模特穿搭合成, 电商主图换装, preserve a base image's pose/background/lighting while changing the person and wardrobe, or repeatedly produce consistent model fashion images from multi-angle references.
---

# Fashion Model Outfit Swap

Produce identity-consistent fashion composites while preserving the base image's scene, pose, framing, and lighting. Use the built-in image generation/editing tool; also follow the installed `imagegen` skill for tool and save-path rules.

## Input contract

Identify these roles before editing:

1. **Base image**: edit target; controls scene, pose, framing, camera, perspective, and lighting.
2. **Outfit image**: wardrobe-only reference; may contain clothing, shoes, bag, jewelry, and accessories in a collage.
3. **Model images**: identity references of the same adult model from full-body and multiple face angles.

If a role is genuinely ambiguous, ask one concise question. Otherwise proceed and state the role assignment in commentary.

## Reference selection

Inspect every local input with `view_image` before generation.

The built-in editor accepts at most five local reference paths. Select exactly these when available:

1. Base image.
2. Outfit image.
3. Model full-body frontal image for proportions.
4. Model frontal close-up for identity.
5. Model close-up whose head direction most closely matches the base image.

Use a different third model view only when it better resolves an occluded feature. Do not combine contact sheets unless the user asks for preprocessing. Explain briefly which images were selected; use unselected angles only for visual verification.

For an accessory-focused revision, replace the full-body model image with the user's accessory crop or the outfit image's clearest accessory detail. Keep the edit target, outfit image, frontal face, and matching-angle face. This makes small jewelry geometry and color a first-class reference while retaining identity.

## Workflow

1. Inspect all inputs and assign roles.
2. Read `references/prompt-template.md` and build one structured edit prompt.
3. Extract the complete outfit inventory: garment type, color, neckline, sleeves, silhouette, length, waist details, fabric behavior, shoes, bag, jewelry, and other accessories. Record accessory count, pair/set membership, material, color, geometry, scale, and intended body location. For every bag, separately record quantity, silhouette, size, material, color, handles, shoulder or crossbody strap, closures, pockets, hardware, decorative details, and carry mode.
4. Separate controls explicitly:
   - base image controls pose, environment, composition, and lighting;
   - model images control identity, body proportions, skin tone, and hairstyle;
   - outfit image controls wardrobe and accessories only.
5. Generate one high-quality first pass with the built-in image editing tool. Explicitly request the base image's aspect ratio and full-body framing.
6. Inspect the result at original detail and apply `references/quality-checklist.md`.
7. If acceptable, run `scripts/normalize_2k.py --base <base-image> --input <generated-image> --output <final-image>` and copy the normalized result non-destructively into the task's user-facing output directory.
8. If unacceptable, identify the single highest-impact defect and run one targeted revision. Repeat invariants in every revision. Do not rewrite unrelated details.

## Preservation hierarchy

Resolve conflicts in this order:

1. Model identity and recognizable facial structure.
2. Correct anatomy and plausible interaction with clothing/accessories.
3. Base pose, framing, perspective, scene, and light direction.
4. Outfit silhouette, color, construction, and complete accessory set.
5. Minor fabric texture and styling details.

## Output geometry

- Treat 2K as a maximum 2048 x 2048 pixel canvas while preserving the base image's exact width-to-height ratio.
- Fit the image proportionally inside that canvas: set the long edge to 2048 pixels and calculate the short edge from the base image ratio. Do not force a square image unless the base image is square.
- Never stretch the image. After generation, run `scripts/normalize_2k.py` to apply the smallest centered crop needed to restore the base ratio, then resize with high-quality Lanczos resampling.
- Verify final pixel dimensions and aspect ratio before delivery. Keep the head, feet, bag, accessories, and cast shadow inside the crop; revise the generation instead of cutting off required content.

Never let the outfit reference replace the model's face or let the base image's original person identity survive the edit.

## Prompt discipline

- Use `identity-preserve` as the imagegen use case.
- Describe image roles by index.
- State invariants twice: once in the primary request and once in constraints.
- Use frame-relative directions such as `frame left`; avoid ambiguous `her left`.
- Describe visible garment construction rather than guessing brands or fabrics.
- Preserve real skin texture; prohibit generic beauty-filter faces.
- Include explicit negatives for the base model's old clothing and accessories.
- Do not claim pixel-exact background preservation; request visually unchanged background, camera, and geometry.

## Accessory fidelity

- Treat jewelry, glasses, belts, and bag hardware as independent required objects, not optional styling prose.
- For paired earrings, require one correct earring on each ear. Allow the far earring to be partly occluded by head angle or hair, but do not omit it or place both on one side.
- For multi-piece bracelets or bangles, match the visible count and construction. Unless the reference clearly shows a single inseparable stack, distribute pieces naturally across both wrists when both wrists are visible; state the exact left/right allocation in frame-relative terms.
- Keep accessory colors, stones, beads, metal finish, silhouette, and relative scale faithful to the clearest reference or crop.
- Protect facial identity from occlusion. By default, do not wear any glasses or sunglasses over the eyes in identity-sensitive outputs. Apply a fashion-styling placement hierarchy: hold eyewear naturally by one temple in the free or minimally adapted lowered hand; otherwise hang it from the bag; otherwise clip it discreetly to a belt or garment edge; use the neckline only when it does not compete with garment construction, graphics, or the face. Only cover the eyes when the user explicitly asks for worn eyewear. Prefer a clean editorial silhouette over rigidly preserving a hand's original fabric-pinching action.
- Do not let a bag, crossbody strap, or wrist stack hide important garment construction unnecessarily.

## Bag fidelity

- Treat every bag as a required product component, not a background prop.
- Match bag quantity, silhouette, relative size, material, color, handle count and length, strap type, closures, pockets, hardware finish, embroidery or ties, and other visible details.
- Preserve the intended carry mode: top-handle in hand, shoulder bag on shoulder, crossbody bag across the torso, or clutch in hand. Adapt the nearest free hand only when required for a natural grip.
- Require correct contact and gravity: fingers wrap the handle, straps connect to anchors, chains hang downward, and the bag does not float, fuse with clothing, or intersect the body.
- If the outfit reference shows both handles and a detachable strap, preserve both when visually important and physically plausible.

## Revision policy

Prioritize revision defects in this order: identity drift or face occlusion, anatomy/hands, missing or wrong bag, wrong garment, wrong pose, required accessory mismatch, lighting mismatch, background drift, optional minor detail. Change one category per revision prompt.

When identity is weak, strengthen face geometry and the matching-angle reference; do not add more wardrobe prose. When clothing is weak, restate garment construction and negatives without altering identity instructions. When hands are weak, specify the exact hand-object interaction and preserve everything else.

## Delivery

Use a descriptive Chinese filename when the task is Chinese. Never overwrite the base image unless explicitly requested. In the final response, show the result inline, link the saved output, state whether it was a one-pass result or revised, report final pixel dimensions, and summarize the final prompt.

Deliver exactly one image: the normalized final image produced by `normalize_2k.py`. All pre-review generations and revision candidates are intermediate working files, not additional deliverables.
