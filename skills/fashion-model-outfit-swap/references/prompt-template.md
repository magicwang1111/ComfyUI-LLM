# Prompt template

Use only fields that are supported by visible evidence.

```text
Use case: identity-preserve
Asset type: vertical photorealistic fashion e-commerce image

Primary request: Edit Image 1. Replace the original person with the exact adult model shown in Images 3-5 and dress the model in the complete outfit shown in Image 2. Preserve Image 1's pose, scene, composition, camera, perspective, and lighting.

Output geometry: Use a maximum 2048 x 2048 pixel 2K canvas while preserving Image 1's exact width-to-height ratio. Fit proportionally with the long edge at 2048 pixels; do not force square output or stretch the image. Keep the head, feet, bag, accessories, and cast shadow inside the frame.

Input roles:
- Image 1: edit target; absolute reference for [scene], pose, framing, camera, perspective, and light direction.
- Image 2: wardrobe-only reference: [complete garment and accessory inventory]. Do not copy its person, room, hanger, or display background.
- Image 3: model full-body reference for identity and proportions.
- Image 4: model frontal close-up for facial identity.
- Image 5: model [angle] close-up matching the target head direction.

Identity: Preserve the model's recognizable [face shape, eyes, nose, lips, marks, skin tone] and [body proportions]. Render the same person, not a similar-looking person.

Hairstyle fidelity: Preserve the exact hairstyle from Images 3-5: [hair color], [hairline and forehead exposure], [center or side part and direction], [length and texture], [bangs and face-framing wisps], [tied or loose style], [bun or ponytail height, position, and volume], and [ear visibility]. Adapt only viewing-angle perspective, natural wind response, and scene lighting. Do not inherit Image 1's hairstyle, change hair length, move the bun or ponytail, add or remove bangs, or redesign the hairstyle.

Pose and composition: Match Image 1: [torso direction], [head direction and gaze], [left/right arm and hand interaction], [leg and foot placement], [body scale and location], [background landmarks].

Lighting and realism: Match Image 1's [source direction, softness, color temperature, rim light, facial fill, cast shadow]. Use natural skin texture, coherent contact shadows, realistic cloth folds, and editorial photography realism.

Wardrobe fidelity: [garment color and construction]. Include [shoes], [bag], [jewelry], and [accessories]. Make clothing fit the target pose naturally.

Bag fidelity: Render exactly [quantity] bag(s): [silhouette, size, material, color, handle count, strap, closures, pockets, hardware, decorative details]. Carry it [top-handle / shoulder / crossbody / clutch] with a natural grip and correct gravity. Keep every handle, strap, chain, and anchor physically connected.

Accessory placement: Render [exact earring pair] as one earring per ear. Place [bracelet count and allocation] on [frame-left wrist / frame-right wrist]. Prefer holding glasses or sunglasses naturally by one temple in the free or minimally adapted lowered hand, lenses facing down or outward; if that is impossible, hang them from the bag, then consider a discreet belt or garment-edge placement. Keep both eyes and defining facial features fully visible. Match accessory material, colors, stones or beads, silhouette, and scale to [Image 2 or accessory crop].

Constraints: Keep Image 1's background and geometry visually unchanged. Keep the exact model identity and hairstyle from Images 3-5. Change only person identity, clothing, shoes, bag, jewelry, and explicitly requested styling.

Avoid: Image 1's original face or hairstyle, hairstyle redesign, wrong hair color, wrong parting, changed hair length, moved bun or ponytail, missing characteristic wisps, [old outfit and accessories from base image], missing or wrong bag, incorrect handles or straps, face drift, generic beauty-filter face, incorrect garment color, missing accessories, malformed hands, extra fingers, fused limbs, distorted straps, floating objects, extra people, text, logos, and watermarks.
```

## Targeted revision form

```text
Revise the previous result only for [one defect].
[Exact correction with reference index].
Preserve everything else unchanged: model identity, pose, background, framing, lighting, garment color and silhouette, accessories, and camera perspective.
```
