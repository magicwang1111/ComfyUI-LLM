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

## Hairstyle identity

- Hair color, hairline shape and height, forehead exposure, and parting direction match the model references.
- Hair length, texture, bangs, face-framing wisps, and tied or loose construction match the model references.
- Bun or ponytail height, position, scale, and volume match the target-angle and full-body references.
- Ear visibility agrees with the hairstyle and head angle; hair does not unnecessarily hide defining facial features or required earrings.
- Only perspective, natural wind response, and scene-light highlights differ. The result does not inherit the base person's hairstyle or redesign the model's hair.

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

Before approval, zoom in and explicitly verify the face, hairstyle, bag, and every listed accessory; do not infer their presence from the prompt. Revise only the highest-impact failed category. Treat hairstyle drift, a missing or wrong bag, missing paired earrings, incorrect jewelry colors or geometry, all bracelets collapsing onto one wrist, or identity-obscuring eyewear as required failures rather than harmless minor differences.
