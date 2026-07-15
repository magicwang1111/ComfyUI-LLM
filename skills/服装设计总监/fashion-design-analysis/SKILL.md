---
name: fashion-design-analysis
description: >-
  Generate photorealistic fashion design deliverables from text design briefs,
  single reference images, multiple reference images, folders of brand element
  images, or same-style garment photos. Use for 服装设计分析, 服装设计生成, 款式设计,
  品牌元素设计, 品牌风格提取, 文件夹图片分析, 样品图改设计, 款式分析, 设计拆解,
  实物款式图, 实物样衣图, 服装白底图, 真实服装图, 服装结构分析, 工艺拆解,
  细节标注, 模特实穿三视图, 正侧后三视图, 同款多图分析, and creating exactly
  three final realistic garment images: a white-background real garment style
  image, a real-detail design breakdown board, and a white-background real model
  front/side/back three-view.
---

# Fashion Design Analysis

## Core Purpose

Create one new or analyzed fashion design and output exactly three **photorealistic** design images:

1. **实物款式图**: white-background real garment sample image, usually front and back.
2. **实物设计拆解图**: real garment main image plus real-looking detail closeups and concise callouts.
3. **模特实穿三视图**: white-background real model or realistic mannequin front / side / back view sheet.

This skill supports both **new design generation** and **existing garment design analysis**. The output is design-facing, but it must look like real physical garments, not hand-drawn sketches.

## Realism Rule

Prioritize physical sample realism over illustration.

Always prompt for:

- photorealistic studio product photography
- real garment sample / physical prototype
- real fabric texture, thickness, drape, wrinkles, and seams
- visible stitching, buttons, zippers, snaps, embroidery, pleats, washing, piping, binding, labels, trims, and construction details
- soft studio lighting and subtle natural shadows
- commercial sample-room realism, not concept art

Always avoid:

- illustration, drawing, sketch, hand-drawn, watercolor, manga, cartoon
- CAD line art, vector flat, technical linework, fashion illustration
- painted fabric, fake texture pasted onto flat shapes
- overly smooth AI surfaces, plastic clothing, unrealistic folds
- ecommerce lifestyle scenes, runway scenes, retail posters, hanger displays

Use words like `款式图` only as a deliverable name. Do not interpret it as a line drawing.

## Input Modes

### Mode 1: Text Design Brief

Use when the user describes what they want to design without giving images.

Examples:

- `我想设计一款夏季亚马逊风格的连衣裙`
- `设计一款适合小红书的法式碎花吊带裙`
- `做一款适合 TikTok Shop 的度假风套装`
- `设计一款汉服`

Extract design conditions from the text:

- Category: dress, shirt, jacket, skirt, pants, set, hanfu, kidswear, etc.
- Season and climate: summer, winter, resort, lightweight, warm, sun protection.
- Platform or channel: Amazon, Xiaohongshu, TikTok Shop, offline boutique.
- Target customer: young women, commuter women, kids, plus-size, mature, resort, outdoor.
- Style: French, minimalist, romantic, utility, quiet luxury, sweet-cool, traditional-modern.
- Functional needs: breathable, washable, easy fit, sun protection, comfort, low-return.
- Commercial constraints: price band, production complexity, bestseller potential if stated.

Then generate a new garment design that fits the brief as a realistic physical sample.

### Mode 2: Brand Element Design

Use when the user provides a sample image, multiple reference images, or a folder of images to define brand style. These images are **brand element references**, not exact-copy instructions.

The key rule:

- Extract brand elements and design language.
- Do not copy one reference garment exactly.
- Do not create a replica of a sample image.
- Design a new garment that feels like it belongs to the same brand world.
- Render the result as a realistic sampled garment, not a sketch.

For folder input:

- Look for common image formats such as `.png`, `.jpg`, `.jpeg`, `.webp`.
- If there are many images, sample enough representative files to infer the brand language.
- Group repeated elements instead of describing every image.
- If the folder contains unrelated styles, prioritize the most repeated style or the user-specified direction.

### Mode 3: Same-Style Garment Analysis

Use when the user provides one or more images of the same existing garment and wants a design analysis rather than a new style.

In this mode:

- Preserve the source garment closely.
- Use reference details to improve fabric, seams, trims, and construction.
- Infer missing views conservatively.
- Keep all three outputs photorealistic.
- Do not redesign into a new style unless the user asks.

## Brand Element Extraction

When references are used as brand elements, extract:

1. **Color language**: main colors, accent colors, saturation, warm/cool tendency, contrast style.
2. **Silhouette language**: slim, loose, A-line, H-line, X-line, cropped, longline, flared, layered, structured, draped.
3. **Structure language**: neckline, collar, sleeve, closure, waistline, seam placement, paneling, pockets, vents, pleats, drawstrings.
4. **Material language**: knit, chiffon, cotton-linen, denim, twill, satin, lace, mesh, nylon, wool, rib, sheer, textured fabric.
5. **Craft language**: pleating, embroidery, lace insertion, stitching, binding, gathering, washing, quilting, patchwork, raw edge.
6. **Physical realism needs**: fabric thickness, stiffness, drape, wrinkle scale, wash effect, trim material, hardware reflectivity.
7. **Brand tone**: romantic, practical, youthful, quiet luxury, outdoor, resort, utility, feminine, minimal, retro, futuristic.
8. **Commercial fit**: platform, audience, price band, production complexity, fit risk, bestseller potential.

Use the extracted elements to create a **new physical-looking design**, not a copy.

## Hard Requirements

- Output exactly three final images.
- If the user does not specify output specs, default each final image to 4K, 3:4, vertical.
- All three images must look like real garment photography or realistic physical sample renders.
- The **实物款式图 must use a pure or near-pure white background**.
- The **模特实穿三视图 must use a pure or near-pure white background**.
- The design breakdown image may use white, off-white, or light gray design-board styling, but its main garment and detail boxes must be photorealistic.
- Keep the same final garment design across all three images.
- Do not output extra variations unless the user explicitly asks.
- Do not create ecommerce lifestyle scenes, runway images, hanger displays, retail posters, or decorative moodboards.
- If the task is brand element design, do not copy any single reference garment exactly.
- If the task is same-style analysis, preserve the source garment as closely as possible.

## Design Decision Workflow

1. Identify the input mode: text brief, brand element image(s), brand element folder, or same-style analysis.
2. Extract category, customer, season, platform, style, function, and commercial constraints.
3. If brand references exist, extract shared brand elements and physical material cues.
4. Define the final garment: category, silhouette, length, fit, color, fabric, structure, hardware, trims, and key craft details.
5. Generate image 1: white-background real garment style image.
6. Generate image 2: real-detail design breakdown board.
7. Generate image 3: white-background real model front/side/back three-view.
8. Check all outputs against the realism quality gate.

## Output 1: 实物款式图

Create a real garment sample image, not a drawing.

Required:

- Pure or near-pure white background.
- Show the garment front and back when useful.
- Use realistic flat-lay, ghost mannequin, or lightly suspended product-photography style.
- Show fabric thickness, seams, stitching, closure, pockets, waistband, hem, trims, pleats, embroidery, and hardware.
- Use subtle natural shadows to prove physical depth.
- Keep the garment centered and easy to inspect.

Do not use:

- linework, technical drawing, fashion illustration, watercolor, CAD flat, vector flat
- model, hanger, scene, props, decorative background

Prompt direction:

```text
Create a photorealistic white-background garment sample image. Show the final garment front and back like a real physical prototype in a fashion sample room. Use realistic fabric texture, thickness, seams, stitching, wrinkles, closure, pockets, trims and hardware. Product photography lighting, subtle natural shadow, no model, no hanger, no props, no illustration, no line drawing.
```

## Output 2: 实物设计拆解图

Create a design breakdown board using realistic garment imagery.

Required:

- Use a photorealistic garment image as the center.
- Add 5-10 numbered callouts with arrows or leader lines.
- Include real-looking macro detail boxes for important features.
- Use short Chinese labels; avoid long paragraphs.
- Include material swatch blocks or physical texture closeups when useful.
- Keep the board like a fashion sample-room analysis sheet, not an advertisement.

Suitable labels:

- 领型结构
- 门襟设计
- 袖型松量
- 袖口工艺
- 腰线比例
- 贴袋结构
- 分割线
- 下摆处理
- 面料肌理
- 拼接工艺
- 褶皱量
- 装饰细节
- 五金细节
- 品牌元素转化

Prompt direction:

```text
Create a clean fashion design breakdown board using photorealistic garment imagery. Put the real-looking garment sample in the center. Add numbered callouts, arrows, realistic macro detail closeups, fabric swatches, and short Chinese labels for key construction details. Keep text sparse and readable. No illustration, no drawn garment, no poster styling.
```

## Output 3: 模特实穿三视图

Create a white-background real model or realistic mannequin three-view sheet.

Required:

- Pure or near-pure white background.
- One consistent model body, shown in front, side, and back views.
- Three views aligned side by side at the same scale.
- Use neutral standing poses with minimal pose variation.
- Preserve garment color, material, thickness, fit, length, sleeve shape, collar, closure, pockets, hem, trims, pleats, embroidery, and back details.
- Show real drape and wearer interaction: folds at elbows, waist, hip, hem, and side seams.

Do not use:

- fashion editorial scene, runway, lifestyle photo, dramatic pose, props, extra accessories, illustrated model

Prompt direction:

```text
Create a photorealistic white-background model fitting three-view sheet. Show the same model wearing the final garment in front view, side view, and back view, aligned side by side at equal scale. Use real studio photography, natural fabric drape, visible seams and trims, accurate fit and garment thickness. No scene, no props, no illustration, no editorial pose.
```

## Prompt Additions For Realism

Add these lines to every image-generation prompt unless they conflict with the task:

```text
Photorealistic physical garment sample, real fabric texture, real stitching, natural wrinkles, accurate material thickness, soft studio product photography, high-resolution commercial sample-room realism.
Shot like a real photo on Sony A7R IV, 85mm f/1.4 lens, natural light or soft studio daylight, ultra-realistic, sharp textile detail, high resolution, realistic depth and subtle physical shadows.
Avoid illustration, drawing, sketch, CAD, vector flat, painted texture, cartoon, watercolor, anime, fashion illustration, fake flat graphic, plastic-looking fabric, over-smoothed AI texture.
```

For the first and third outputs, prefer this camera-realism line:

```text
Real photographed garment sample, Sony A7R IV camera look, 85mm f/1.4 lens, natural daylight, crisp seams and fabric fibers, realistic color, soft shadows, high-end sample-room photography, no illustration.
```

For the breakdown board, use the same realism but keep the layout clean:

```text
Use real-looking macro photos for detail boxes, sharp stitching and fabric closeups, natural texture, realistic hardware highlights, clean white design-board layout, sparse Chinese labels.
```

For denim:

```text
Visible denim twill weave, wash variation, worn seams, tan topstitching, metal hardware, realistic pocket thickness and folded hems.
```

For knitwear:

```text
Visible yarn fibers, ribbing, loop texture, cable or jacquard structure, soft thickness, natural stretch and gravity.
```

For hanfu or traditional-modern garments:

```text
Real textile drape, woven fabric surface, physical knot buttons, embroidered threads, layered garment thickness, skirt pleat depth, respectful modern interpretation.
```

For chiffon, lace, or sheer fabrics:

```text
Real transparency, layered edge thickness, soft folds, sewn lace insertion, delicate but physically plausible hem and seam finishing.
```

## Mode-Specific Rules

### Text Brief Design

- Follow the user's requested category and style.
- Fill missing design details with commercially reasonable choices.
- Do not over-design unless the user asks for avant-garde or runway style.
- Keep the design manufacturable and realistic as a sample garment.

### Brand Element Design

- Keep the new design "same brand feeling, different garment".
- Use repeated elements from the reference set.
- If only one image is provided, use it as style direction, not exact structure.
- If the user specifies a category, design that category using the brand elements.
- If no category is specified, choose a category that best expresses the extracted brand language.
- Render the new design with the same level of physical realism as a product sample.

### Same-Style Analysis

- Preserve the original garment as closely as possible.
- Use detail images to improve seams, trims, fabric, and construction.
- Infer missing side/back views conservatively.
- Do not redesign into a new style unless the user asks.
- Keep the garment photorealistic in every output.

## Quality Gate

Before finalizing:

- Exactly three images are produced.
- The first image is a white-background realistic garment sample image.
- The second image is a readable real-detail design breakdown board.
- The third image is a white-background real model front/side/back three-view.
- All three images show the same final garment design.
- Fabric has visible material texture, thickness, seams, trims, and physical drape.
- Hardware, buttons, embroidery, lace, ribbing, pleats, and stitching look physically attached, not painted on.
- The output does not look like watercolor, line art, CAD, cartoon, fashion illustration, or flat vector art.
- If mode is text brief, the design clearly answers the user's design request.
- If mode is brand element design, the output reflects the reference brand language without copying a single sample.
- If mode is same-style analysis, the source garment identity is preserved.
- Text labels in the breakdown image are short and not visually overwhelming.
- No ecommerce scene, runway scene, lifestyle scene, hanger display, or marketing poster appears.

If any output fails, retry with stronger constraints:

```text
Make this look like a real photographed garment sample, not an illustration. Increase real fabric texture, seam depth, wrinkles, hardware realism, stitching detail, and studio product photography lighting. Keep white background and the same garment design.
```

## Trigger Examples

This skill should trigger on prompts such as:

- `我想设计一款夏季亚马逊风格的连衣裙`
- `根据这个样品图的品牌元素设计一款新衣服`
- `分析这个文件夹里的图片，提取品牌元素，设计一款新服装`
- `用这几张同款图片做服装设计分析`
- `生成实物款式图、设计拆解图、模特三视图`
- `帮我把这件衣服拆解成实物设计稿`
- `输出真实服装质感的三张图`
- `用 $fashion-design-analysis 做品牌元素服装设计并输出三张实物图`
