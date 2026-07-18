# Quality checklist

Inspect the generated image at original detail. Approve only when no high-impact defect remains.

## Output geometry

- Width-to-height ratio matches the base image exactly after normalization.
- Output fits within a 2048 x 2048 pixel 2K canvas with the long edge at 2048 pixels and the short edge derived from the base ratio.
- Image is not stretched or forced square; head, feet, bag, accessories, and cast shadow remain inside the frame.

## Identity

- Same recognizable adult model, not merely similar.
- Face shape, eye spacing, nose, lips, skin tone, and distinctive marks agree with references.
- Head angle remains plausible for the target pose.
- Hair color, short/medium/long length class, loose/tied/updo construction, and overall silhouette remain close to the model reference. Short hair becoming long, long hair becoming short, or tied/up hair becoming loose long hair is a high-impact identity failure. Do not fail fine differences in hairline, parting, flyaways, individual wisps, or exact volume.

## Base-image preservation

- Scene, framing, camera height, perspective, subject scale, and major landmarks remain visually stable.
- Torso, head, arms, hands, legs, feet, and gaze follow the target pose.
- Light direction, rim light, facial fill, cast shadow, and contact shadow agree with the scene.

## Outfit

- Garment category, color, neckline, sleeves, waist construction, length, and silhouette match the outfit image.
- Shoes, bag, jewelry, and requested accessories are complete and correctly colored.
- Cloth folds respond to the pose; straps and hems connect naturally.

## Bag

- Required bag is present in the correct quantity and carried in the intended way.
- Silhouette, relative size, material, color, handle count, strap or chain type, closures, pockets, hardware, embroidery, ties, and other visible details match the reference.
- Hand grip is plausible; handles, straps, chains, and anchors remain connected and obey gravity.
- Bag does not float, intersect the body, fuse with clothing, hide key garment construction, or inherit the base image's old bag.

## Accessories and identity visibility

- Paired earrings appear as one correct piece per ear; partial far-ear occlusion is plausible and not an omission.
- Earring shape, bead or stone colors, metal finish, and scale match the clearest reference.
- Bracelet or bangle count and construction match the reference; pieces are not all placed on one wrist unless the reference clearly requires a single stack.
- Glasses and sunglasses do not cover the model's eyes by default. Prefer a natural one-temple handhold with a clean editorial silhouette; otherwise hang or clip them without floating, deforming clothing, obscuring graphics, or cluttering the neckline.
- Bag straps, jewelry, and glasses do not obscure defining facial features or key garment construction.

## Anatomy and polish

- Hands have plausible finger count and grip.
- Arms and legs do not fuse with clothing or props.
- Feet align with shoes and ground plane.
- No floating accessories, extra people, unintended text, logos, or watermarks.

## Revision decision

Perform this checklist only once per task. Before approval, zoom in and explicitly verify the face, coarse hairstyle identity, bag, and every `confirmed` accessory; do not infer an accessory's category, count, or presence from the prompt. Treat face drift, a major hairstyle class change, a missing or wrong required bag, missing confirmed paired earrings, incorrect confirmed jewelry colors or geometry, all confirmed bracelets collapsing onto one wrist, or identity-obscuring eyewear as failures. Do not fail or regenerate for an `ambiguous` accessory, a fine hairstyle difference, a tiny detail that cannot be resolved at the available image size, or source fidelity that cannot be compared because the review lacks its original reference. Only a confirmed high-impact facial-identity, coarse-hairstyle, anatomy, main-garment, or required-bag defect may trigger one fresh regeneration; do not review the replacement.
