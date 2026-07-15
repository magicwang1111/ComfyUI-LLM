---
name: world-buyer
description: >-
  Global fashion buyer product discovery and product-card analysis. Use when
  the user asks 世界买手, 全球服装买手, 买手找款, 找世界上有价值的服装产品,
  全球找产品, 服装选品, 买手采购分析, 单品买手分析, 根据图片找款,
  根据文件夹找款, 参考图片找相似/同风格产品, 品牌/市场/趋势/爆款采购建议,
  season/category/platform assortment planning, or when the expected output is
  six buyer output images: five product analysis cards plus one contact-sheet
  thumbnail overview. Supports text briefs, single images, multiple
  images, folders of product/reference images, and mixed image+text inputs.
  Default output is exactly six visual images: five separate buyer product
  cards plus one contact-sheet thumbnail overview. Each product card must
  analyze one distinct real or clearly labeled buyer-inferred product.
---

# World Buyer

## Core Purpose

Act as a professional global fashion buyer who **finds products**, not only trends.

Use this skill to turn a user request, product image, reference-image folder, category brief, seasonal need, platform plan, or style direction into **five distinct buyer product cards** plus one **contact-sheet thumbnail overview**.

Default deliverable:

- Output exactly **six PNG/JPG images** by default: five separate product card images plus one contact-sheet overview image.
- Each product card corresponds to **one product only**.
- The sixth image is a formal contact-sheet / thumbnail preview showing all five product cards together.
- The five products must be meaningfully different.
- Each product must include buyer analysis, not just a picture.

If the user explicitly asks for text only, a table, or a different number of products or output images, follow that request. Otherwise, keep the six-image default: five product cards plus one contact sheet.

## What Counts As a Product

A product can be:

- A real product found from a brand, retailer, buying platform, marketplace, editorial market report, or user-provided image source.
- A user-provided product image treated as one product candidate.
- A buyer-inferred product direction only when current verification is unavailable; label it clearly as `买手推断款`, not as a real sourced product.

Do not fabricate product names, brand names, prices, URLs, rankings, sales numbers, or platform performance.

## Accepted Inputs

Use this skill for:

- Text briefs: `帮我找全球有价值的男士夹克`, `今年秋冬女装买什么`.
- Image references: `根据这张图找类似但更有价值的产品`.
- Product image sets: `这些图片帮我做买手分析`.
- Folders: `分析这个文件夹，找 5 个值得买的产品`.
- Mixed inputs: image/folder plus category, season, price band, platform, audience, or style.
- Market and assortment questions: brand watch, trend watch, bestseller directions, color priority, price bands, size ratio, launch rhythm, purchase depth.

If a task is purely about generating a new garment design from references, use a fashion-design skill instead. If the user asks to rank many product photos by bestseller potential without global buying context, a hot-style/bestseller analysis skill may be a better fit.

## Input Modes

### Mode 1: Text Brief To Global Product Discovery

Use when the user gives a category, season, platform, price band, or audience without images.

Workflow:

1. Define scope: gender, category, season, region, price band, platform, customer, and style.
2. Search or otherwise gather current global product examples when possible.
3. Select five real products with different brands, silhouettes, materials, price tiers, or styling roles.
4. If current browsing/product verification is unavailable, state that the products are buyer-inferred directions and avoid fake source claims.
5. Render five product cards plus one contact-sheet thumbnail overview.

### Mode 2: Reference Image To Global Product Discovery

Use when the user provides one or more images as style reference.

Workflow:

1. Extract the image style: category, silhouette, fabric, color, detail, occasion, brand tone, and customer.
2. Treat the reference as direction, not an exact-copy requirement.
3. Find five global products that share useful buying value with the reference but are not duplicate copies.
4. Explain what each product contributes: silhouette, fabric, pocketing, trim, color, styling, margin, trend, or commercial scenario.
5. Render one card per product, then render one contact-sheet thumbnail overview of all five cards.

### Mode 3: Product Image Set Or Folder

Use when the user provides multiple product images or a folder.

Workflow:

1. Inspect common image formats: `.png`, `.jpg`, `.jpeg`, `.webp`.
2. Treat each product image as a candidate product unless the user says the folder is only mood/reference material.
3. If there are more than five candidates, select the five strongest and most different products.
4. If there are exactly five product images, map one image to one card.
5. If there are fewer than five products and the user still expects five cards, supplement with globally sourced or buyer-inferred related products and label the source type.

## Product Selection Rules

The five products must not be near-duplicates.

Prefer diversity across:

- Category role: hero item, traffic item, margin item, styling item, test item.
- Silhouette: cropped, longline, oversized, fitted, A-line, H-line, layered, modular.
- Material: wool, leather, denim, nylon, cotton, knit, tweed, lace, mesh, technical fabric.
- Detail: pockets, collar, closure, quilting, splicing, pleating, drawcord, embroidery, hardware.
- Price tier: entry, mid-market, premium, designer, niche boutique.
- Channel fit: Xiaohongshu, Douyin, Tmall/Taobao, TikTok Shop, Amazon, boutique, offline showroom.

Avoid:

- Same product in multiple colors.
- Five products from one brand unless the user asks for one-brand buying.
- Only aesthetic picks with no commercial reason.
- Picking products only because they look unusual.

## Global Buyer Watches

Evaluate each candidate through four watches:

- **Brand watch**: major brands, designer labels, high-street brands, boutique brands, or platform leading sellers.
- **Trend watch**: color, fabric, silhouette, detail, occasion, styling formula, seasonal movement.
- **Buzz watch**: social exposure, creator repetition, search/comment language, visual spread, saturation risk.
- **Bestseller watch**: broad scenarios, easy styling, low return risk, replenishment potential, price acceptance.

If current market claims, live prices, brand movement, bestseller data, social buzz, or product availability matter, browse or use user-provided data. If not verified, label the conclusion as buyer inference.

## Per-Product Analysis

Each card must analyze one product using concise Chinese copy.

Include most of these fields:

- `产品`: product name or descriptive name.
- `来源`: brand/retailer/platform/user image/inferred direction.
- `买手评分`: 10-point score; do not score everything high.
- `买点`: why it is worth attention.
- `设计亮点`: silhouette, structure, fabric, trim, color, craft.
- `趋势价值`: why it matches current or emerging trend.
- `人群`: target customer and wearing scenario.
- `平台`: best channel fit.
- `价格带`: recommended retail or procurement band; use ranges, not fake precision.
- `采购深度`: buy / controlled push / small test / styling support / avoid.
- `风险`: fit, fabric, return, duplication, seasonality, production complexity, inventory.
- `可借鉴元素`: what can be learned for design or buying.

Keep copy short. Prefer buyer shorthand:

- `买点: 短款比例 / 低退货 / 易搭配`
- `风险: 面料扎肤 / 撞款高 / 尺码波动`
- `动作: 先测 2 色, 7 天看收藏转化`

## Scoring

Use a 10-point buyer score:

- **8.5-10**: strong buy; clear demand, trend fit, broad audience, manageable risk.
- **7-8.4**: good controlled push or serious test.
- **5.5-6.9**: cautious small test; depends on price, fabric, styling, or channel.
- **Below 5.5**: avoid unless the user has a special channel or very low sourcing cost.

Score across:

- Trend fit.
- Design value.
- Commercial breadth.
- Platform buzz potential.
- Bestseller potential.
- Margin possibility.
- Styling/cross-selling power.
- Return and inventory risk.

## Procurement Guidance

Use practical relative advice instead of fake precision:

- Buying depth: low / medium / high, or `1x / 2x / 3x`.
- Product role: hero / traffic / margin / styling / test / avoid.
- Color priority: safe colors first, trend colors second, risky colors last.
- Size ratio: start from `S:M:L:XL = 2:4:3:1`, then adapt by category.
- Price band: give a range and one reason.
- Launch rhythm: first wave / test wave / replenishment trigger.

## Visual Output

Default visual output:

- Produce exactly six PNG/JPG images by default.
- Use filenames such as `world-buyer-product-01.png` through `world-buyer-product-05.png`, plus `world-buyer-contact-sheet.png`.
- Each product card should default to 4K, 3:4, vertical unless the user specifies otherwise.
- The contact sheet should also default to 4K, 3:4, vertical unless the user specifies otherwise, usually as a clean 2x3 grid showing all five product cards large enough that product shape, title, score, price/action, and card distinction are visible in a file-manager thumbnail.
- Treat the contact sheet as a **formal deliverable**, not only an internal QA artifact.
- Use deterministic HTML/CSS rendering to PNG when possible so Chinese text stays readable.
- Each card must include one product visual area and one compact analysis area.
- For a real sourced product, the visual area must use a real product image, official/retailer product photo, user-provided product photo, or clearly attributed product-page screenshot. Do not replace real products with simple self-drawn clothing outlines, generic icons, abstract vector garments, or placeholder illustrations.
- If a usable real product image cannot be embedded, either use a source-page screenshot with the source label visible, or label the card as `买手推断款` and make clear that the image is a reference/concept visual rather than a verified real product.
- If the user supplied product images, use them as the product visual when appropriate.
- If product images come from web sources, keep a small source label or source URL in the card or final note.
- Do not remove watermarks from user-provided or sourced images.

Card structure:

- Product image or product visual as the main focal area.
- Product name/source line.
- Buyer score chip.
- 3-6 concise analysis bullets.
- One or more buyer visual elements: color chips, material tags, price ladder, score bar, risk chip, platform chip, order-depth tag.
- Product visual must remain recognizable in a file-manager thumbnail. It should normally occupy 40-55% of card height and not be cropped by price bars, analysis blocks, or decorative elements.
- Body copy must stay sparse enough for thumbnail preview: prefer 4 short bullets, each no more than 22 Chinese characters after the label. Put longer reasoning in a companion `.md` source/notes file, not on the card.
- Title, product image, price band, buyer score, and one key action must be readable at about 25% display scale.

The card must read as a **global fashion buying product sheet**, not a generic poster.

### Douyin Live-Room / Low-Return Briefs

When the user asks for Douyin, TikTok Shop, livestream, low return, easy explanation, or low price:

- Treat the output as a **live-room product selection sheet**, not a global brand moodboard.
- Each card must explicitly include: `低退货原因`, `直播间讲解点`, `建议直播价`, `采购深度`, and `主要风险`.
- Prefer products with low fit complexity: elastic waist, regular/relaxed fit, outerwear, basic tops, adjustable details, or forgiving fabrics.
- Avoid items likely to create returns: tight tailoring, very thin/transparent light colors, complex pants sizing, scratchy fabric, high-maintenance linen-only fabric, heavy wrinkles, difficult care, or vague functional claims.
- Do not claim actual Douyin sales, return rate, bestseller rank, or platform heat unless verified from data. Use `买手推断` for unverified commercial judgments.

## Five-Card + Contact-Sheet Structure

Default:

1. **Card 01: Product 1** - strongest hero or highest-confidence buy.
2. **Card 02: Product 2** - trend or silhouette opportunity.
3. **Card 03: Product 3** - commercial broad-audience product.
4. **Card 04: Product 4** - margin, fabric, detail, or styling value.
5. **Card 05: Product 5** - test product, niche direction, or risk-controlled novelty.
6. **Contact Sheet: All 5 Cards** - thumbnail overview for quick file-manager review and delivery preview.

For exactly five input product images, preserve the one-image-to-one-card mapping unless a product is unusable.

## Empty-Space Control

Avoid unfinished blank cards.

When a card feels sparse, fill space with buyer-relevant elements:

- Color swatch ladders.
- Fabric/material tags.
- Price-band staircase.
- Size-ratio bars.
- Mini SKU/order ticket.
- Trend radar.
- Platform channel chips.
- Launch calendar strip.
- Score bars and risk labels.

Do not fill blank space with unrelated lifestyle decoration.

## Analysis Workflow

1. Identify input mode: text brief, reference image, product images, folder, or mixed input.
2. Define scope and assumptions.
3. Gather product candidates from user images and/or global market research.
4. Select five distinct products using buyer value, diversity, and risk control.
5. Analyze each product with the per-product schema.
6. Compress analysis into concise card copy.
7. Render exactly five separate product cards.
8. Render one contact-sheet thumbnail overview from the five final cards.
9. Verify readability, product distinction, source discipline, empty-space control, and contact-sheet thumbnail clarity.
10. Final response should briefly list saved paths and mention whether products are sourced from user images, web sources, or buyer inference.

## Source Discipline

When browsing or using public market information:

- Prefer official brand pages, retailer product pages, reputable buying platforms, editorial market reports, and current marketplace listings.
- Record product name, brand/source, URL, access date, visible price, and image source when available.
- Do not claim sales rank, sell-through, or platform heat unless the data is available.
- If using social buzz language without verified metrics, say `声量判断: 买手推断`.
- If a product cannot be verified, label it as `未核验` or `买手推断款`.

## Quality Gate

Before delivery, verify:

- Exactly six images are produced by default: five product cards plus one contact-sheet overview.
- Each of the five product card images corresponds to one product only.
- Five products are different enough to justify separate buying decisions.
- Every card includes analysis, not just a product photo.
- Real product claims have source support or are labeled as inference.
- Buyer score and procurement advice are actionable.
- Chinese text is readable and not overly dense.
- No card has a large unfinished blank area.
- Product image, analysis, score, risk, and action are visually connected.
- Real sourced products use real product visuals or attributed product-page screenshots; cards do not use generic line-art placeholders unless explicitly labeled as `买手推断款`.
- The contact sheet is included as the sixth formal output image and previews all five cards clearly.
- Inspect the OS thumbnail view or the generated contact sheet before final delivery. If product shape, title, score, and price/action are not clear in thumbnail view, enlarge the product visual and reduce copy density.
- Open at least one generated card at full size and the contact-sheet output before final response; fix cropped garments, overlapping text, tiny body copy, and low-contrast labels before delivery.

## Trigger Examples

Use this skill for prompts such as:

- `用世界买手帮我找 5 个全球有价值的男装产品`
- `根据这张图片，找世界上值得参考的同风格产品`
- `分析这个文件夹，每张图一个产品，输出五张买手卡和一张缩略图总览`
- `我要找不同款式的女装外套，每个产品都要有分析`
- `帮我做全球买手选品，默认输出六张图片`
- `找小红书/抖音/TikTok Shop 适合上的服装产品`
- `秋冬男装夹克有什么值得买的产品`
- `给每个产品买手评分、设计亮点、采购建议和风险点`
