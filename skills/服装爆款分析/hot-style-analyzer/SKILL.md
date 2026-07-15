---
name: hot-style-analyzer
description: >-
  Analyze garment images, product photos, screenshots, links, competitor examples,
  or multi-style image sets as a fashion hot-seller gene diagnosis skill, then
  output exactly five separate visual cards by default. Use whenever the user
  asks 爆款分析, 爆款判断, 服装爆款基因, 单品爆款潜力, 图片选款, 看图选款,
  白底图分析, 商品图买手分析, 这件衣服能不能爆, 值不值得采购,
  多款图片排序, 竞品图对比, 视觉卖点, 渠道适配, 用户需求, 测款计划,
  加购收藏转化, 定价建议, 尺码配比, 退货风险, 供应链风险, 小红书爆款卡片,
  or 五张爆款分析卡. Do not use for text-only seasonal purchase advice; route
  "夏季买什么/秋冬上新/货盘采购建议" to world-buyer.
---

# Hot Style Analyzer

## Core Purpose

Act as a professional apparel hot-seller analyst. Use this skill when the user provides a **specific garment, product image, product link, listing screenshot, competitor example, or multiple style images** and wants to know whether the style can become a bestseller.

The skill should not merely say whether the product "looks good". It should diagnose whether the style has a repeatable commercial loop:

**商品表现 -> 销售表现 -> 渠道适配 -> 用户需求**

The goal is to turn the visible style into a practical decision:

- Is it a sustainable hot seller, a short-term traffic style, a low-price promotion style, a content seeding style, or an avoid style?
- Which product genes support or weaken the result?
- Which channel should test it first?
- What price band, size/color plan, first buying depth, and 7-day validation metrics should be used?
- What risks would cause return, inventory pressure, or failed replenishment?

The user-facing default output is **exactly five separate visual card images**. Do not output a long image unless the user explicitly asks for one.

Use **world-buyer** instead when the user asks text-only seasonal buying advice such as "快到夏季买什么", "秋冬上新怎么做", or "帮我做货盘".

## Accepted Inputs

Use this skill for:

- One garment image.
- Multiple garment images.
- White-background product photos.
- Store screenshots or listing screenshots.
- Product links or competitor links.
- Supplier images.
- Product descriptions paired with images.
- Questions like "这款能不能爆", "值不值得采购", "帮我排采购优先级".

If the input is a single image, analyze the image and still output exactly five cards. If important data is missing, use visible-image inference and clearly mark the missing data as "需要供应商/后台确认".

## Hot-Seller Definition

Before scoring, distinguish these types:

- **可持续爆款**: not only high visual appeal; also broad demand, healthy price, low return risk, replenishment potential, and channel fit.
- **短期流量款**: strong visual/content hook but narrow scenario, high styling threshold, or weak repeat purchase.
- **低价促销款**: relies mainly on low price or subsidy; may sell but does not prove product strength.
- **内容种草款**: strong image/video value; useful for traffic, collocation, or brand tone, but not necessarily deep stock.
- **谨慎/淘汰款**: weak demand, poor fit, high return risk, low production stability, or unclear target user.

Do not call every attractive style a hot seller. A real hot seller needs both demand and operational feasibility.

## Required Analysis Model

Use a closed-loop diagnosis built from the user's reference document.

### 1. Track Boundary

Start by defining the analysis boundary:

- **Category**: womenswear, menswear, kidswear, shoes/accessory-adjacent apparel, or other.
- **Style lane**: commuter minimal, new Chinese, American vintage, sports casual, French elegance, genderless streetwear, sweet/girly, outdoor utility, etc.
- **Channel lane**: Douyin/TikTok live, Xiaohongshu, Taobao/Tmall, independent site, offline boutique, mall store, pop-up, or all-channel.
- **Target customer**: age range, body/fit concern, consumption motivation, usage scenario.

This boundary matters because a style can be a hot seller in one lane and a weak product in another.

### 2. Four-Dimension Closed Loop

Evaluate these four dimensions:

- **商品表现**: silhouette, line, color, pattern, material inference, craft/detail, style purity, daily wearability, production feasibility.
- **销售表现**: expected price band, value perception, gross-margin room, likely sell-through logic, add-to-cart/collection/conversion metrics to validate.
- **渠道适配**: online visual click potential, live-commerce demonstration value, Xiaohongshu content repeatability, offline try-on/experience value, all-channel synergy.
- **用户需求**: body modification, comfort, scenario fit, cultural/style identity, buying reason, pain point solved.

### 3. Three-Layer Validation

Judge whether the style sits at the overlap of:

- **Industry trend**: visible trend, season, silhouette, fabric, color, style lane.
- **Competitor validation**: similar market styles, price anchors, listing/photo differentiation, saturation risk.
- **Supply-chain ability**: fabric stability, craft repeatability, replenishment speed, size/color consistency.

If competitor or supply-chain data is not provided, state the validation task rather than inventing facts.

## Product Gene Checklist

Use this checklist for image analysis.

### Design Gene

- **Silhouette**: body modification, comfort, activity room, category fit.
- **Line**: shoulder/waist/hip/hem proportion, length, slimming or heightening effect.
- **Texture/Pattern**: style lane accuracy, visual memory, daily wearability.
- **Color**: safe base color vs trend color, small-area memory point, skin-tone and scenario fit.
- **Detail**: scene usefulness, style consistency, function, quality perception.
- **Material/Craft**: visible fabric inference, stiffness/drape, wrinkle, transparency, pilling, scratchiness, standardized craft feasibility.
- **Production feasibility**: can it scale with stable quality and controllable cost?

### Price Gene

Analyze pricing through:

- **Value perception**: whether users can see enough design/material/scenario value.
- **Competitor anchor**: whether it wins by unique value, not simply lower price.
- **Channel cost**: online traffic cost vs offline rent/service cost.
- **Dynamic price logic**: test price, growth-period price, promotion/clearance trigger.

Use price ranges. Avoid exact cost/profit claims unless user provides data.

### Channel Gene

Online:

- Thumbnail readability.
- Short-video transformation/showcase value.
- Listing detail proof: fabric, size, real try-on, care, color difference.
- Metrics to watch: click-through, add-to-cart, collection, conversion, return reason.

Offline:

- Try-on value.
- Touch/material value.
- Display location and styling story.
- Metrics to watch: try-on rate, conversion, joint sale rate, average transaction value, inventory turnover, floor efficiency if available.

All-channel:

- Online seeding -> offline try-on -> online repurchase.
- Inventory sharing.
- Price consistency or channel-exclusive logic.
- Unified selling point across channels.

### User Demand Gene

Identify the real demand:

- Body concern: waist, hip, shoulder, leg, height, coverage, plus-size tolerance.
- Scenario: commute, date, holiday, school, parent-child, sports, outdoor, ceremony, party.
- Emotion/style identity: new Chinese confidence, relaxed vintage, sporty efficiency, French ease, sweet romance, genderless attitude.
- Practical pain point: sun protection, coolness, easy care, non-transparent, no ironing, activity room, comfort.

## Special Route Rules

Apply these extra rules when relevant:

- **Kidswear**: safety compliance and comfort outrank trend. Check age segment, A-class needs for baby/toddler, scratchy details, hard accessories, activity room, parent decision logic.
- **New Chinese / Hanfu-inspired**: balance style purity and daily wearability. Check whether traditional elements are modernized rather than costume-like.
- **American vintage**: check wash, denim/canvas texture, loose comfort, utility pocket value, and saturation risk.
- **French elegance**: check restraint, small floral/polka/bow details, fit tolerance, and daily social scenarios.
- **Sports casual / utility**: check function, coolness, pocket/usefulness, sweat/comfort, and whether the claim can be proven.
- **Offline hot seller**: check try-on value, display story, guide-selling sentence, styling space, and joint-sale potential.

## Default Five-Card Output

For a single garment image, output exactly:

1. **Card 01: 爆款结论**
   Product image, hot-seller type, buy/test/reject decision, total score, track boundary.
2. **Card 02: 设计爆款基因**
   Silhouette, line, color, pattern, material/craft inference, production feasibility, detail crops.
3. **Card 03: 用户与渠道适配**
   Target customer, usage scenarios, online/offline/all-channel fit, content hook, selling sentence.
4. **Card 04: 价格与测款计划**
   Suggested price band, first buying depth, color/size plan, 7-day metrics, replenishment trigger.
5. **Card 05: 风险雷达与最终动作**
   Return risk, inventory risk, supply-chain risk,淘汰条件, validation checklist, final action.

For multiple product images, still output exactly five cards:

1. **Card 01: 货盘爆款结论**
   Overall launch stance, role split, best hero/test/avoid signals.
2. **Card 02: 款式排名**
   Must-buy, controlled test, styling support, avoid, with thumbnails.
3. **Card 03: 爆款基因对比**
   Design gene, user demand, channel fit, price/value.
4. **Card 04: 采购与测款矩阵**
   Color, size, price, buying depth, launch rhythm.
5. **Card 05: 风险与最终下单**
   Eliminations, risk control, validation checklist, final order plan.

## Measurement and Validation

If no real sales data is provided, do not pretend to know data. Provide **measurement targets**:

- Online test metrics: click-through, add-to-cart, collection, conversion, return reason, traffic cost.
- Common 7-day validation references: add-to-cart above 15%, collection above 10%, conversion at or above category average, traffic cost below category average. Present these as reference thresholds, not guaranteed facts.
- Offline metrics: try-on rate, conversion, joint-sale rate, average transaction value, inventory turnover.
- Supply-chain metrics: replenishment cycle, defect rate, size stability, color consistency, fabric availability.

Use these actions:

- **补货触发**: strong add-to-cart/collection, low size complaints, fast M/L or core-size sell-through, low return reasons, supply can replenish quickly.
- **优化再测**: visual hook is strong but fit/price/channel mismatch appears.
- **降价清货**: traffic exists but conversion is weak and value perception is insufficient.
- **淘汰**: repeated complaints focus on fit, fabric, transparency, scratchiness, color difference, or unstable production.

## Scoring

Use a 10-point scale and avoid inflated scores:

- **8.5-10**: strong hot-seller candidate; clear demand, wide audience, channel fit, low operational risk.
- **7-8.4**: controlled push or small-batch test; promising but constrained.
- **5.5-6.9**: cautious test; depends on price, fabric, styling, or channel.
- **Below 5.5**: avoid unless there is a special channel or very low-cost reason.

Score dimensions:

- Design gene.
- User demand match.
- Channel fit.
- Price/value logic.
- Content/buzz potential.
- Supply-chain feasibility.
- Return risk.
- Inventory/replenishment risk.

## Procurement Guidance

When exact data is unavailable, give relative recommendations:

- Buying depth: low / medium / high, or 0.5x / 1x / 2x / 3x test depth.
- Color priority: safe colors first, trend colors second, risky colors last.
- Size ratio: use a baseline such as S:M:L:XL = 2:4:3:1, then adapt by silhouette and category.
- Price band: give a range and the reason.
- Launch rhythm: sample -> small-batch test -> 7-day review -> replenish / optimize / clear / eliminate.
- Product role: hero, traffic, margin, styling, content seeding, controlled test, avoid.

If product data is image-only, avoid claiming exact fabric, cost, sales, or demand. Use phrases such as "视觉判断", "需要供应商确认", "需要后台数据验证".

## Visual Output Requirements

Default output is visual:

- Produce **exactly five individual PNG/JPG card images**.
- Default output spec: 4K, 3:4, vertical when the user does not specify output specs.
- Use deterministic HTML/CSS rendering to PNG when possible so Chinese text stays readable.
- Save files as `hot-style-card-01.png` through `hot-style-card-05.png`.
- Product image must be visible and not distorted.
- Detail crops should support the analysis: neckline, waistline, hem, fabric texture, print, pocket, closure, stitching, label, or other relevant details.
- Add only a brief final note with file paths unless the user asks for text.

## Visual Style

Make the cards look like a professional product selection deck:

- Style: 爆款基因诊断卡, fashion buyer decision board, hot-seller radar, Xiaohongshu carousel.
- Background: off-white, warm gray, soft concrete, or product-color-tinted neutrals.
- Accent: use product palette or black, wine red, moss green, ink blue, charcoal, silver gray.
- Use visual buyer elements: product image, detail crops, score bars, gene radar, price ladder, SKU ticket, channel funnel, measurement dashboard, size bars, color chips, supply-chain checklist.
- Text: concise Chinese phrases, 3-6 bullets per card, no long paragraphs.

### Empty-Space Control

Avoid large blank areas. A card should not look unfinished.

When space is available, fill it with buyer-relevant visual elements:

- Product detail crop strip.
- 爆款基因雷达.
- 价格带阶梯.
- 测款数据看板.
- 渠道转化漏斗.
- SKU / order ticket.
- 供应链检查单.
- 补货 / 淘汰 decision stamp.
- Color chips pulled from the garment.
- Size-ratio bars.
- Launch calendar strip.

Before exporting:

- No blank zone should dominate more than roughly one quarter of the card.
- Do not rely on a faint grid alone to fill space.
- If the bottom half is sparse, enlarge image/details or add measurement/supply-chain elements.
- Do not add unrelated decoration that weakens the buyer decision.

Avoid:

- One long poster unless explicitly requested.
- Dense text walls.
- Tiny unreadable Chinese.
- Fake precise data.
- AI-generated unreadable text.
- Random lifestyle collage unrelated to the product.
- Large blank backgrounds with only a grid or texture.

## Card Copy Rules

Compress copy into buyer language:

- "爆款类型: 内容种草款 / 可持续爆款 / 短期流量款".
- "设计基因: 高腰 / 松量 / 低饱和色 / 细节记忆点".
- "用户需求: 显瘦 / 通勤 / 防晒 / 拍照 / 舒适".
- "渠道: 小红书种草强, 直播需试穿证明".
- "测款: 先测 2 色, 7 天看加购收藏转化".
- "风险: 透肤 / 尺码 / 扎肤 / 撞款 / 补货慢".
- "动作: 拿样 -> 小批量测款 -> 达标补货".

## Quality Gate

Before delivery, verify:

- Exactly five separate images are produced.
- The skill display/identity reads as "爆款分析".
- The cards are not a single long image.
- Product image, if provided, is visible and not distorted.
- The result distinguishes hot-seller type, not only score.
- The track boundary is defined: category, style lane, channel, target user.
- The four-dimension closed loop is represented: 商品表现, 销售表现, 渠道适配, 用户需求.
- Price and measurement advice do not invent fake exact data.
- 7-day validation metrics or validation checklist are included.
- Special rules are applied for kidswear, style-lane products, or offline/all-channel tasks when relevant.
- No card contains a large unfinished blank area; empty spaces are filled with buyer-relevant elements.

## Trigger Examples

This skill should trigger on prompts such as:

- `帮我分析这件衣服能不能爆`
- `看这张图，值不值得采购`
- `用爆款分析看看这款适合哪个平台`
- `这些款帮我排采购优先级`
- `根据白底图做五张爆款分析卡`
- `这条裙子有什么卖点和退货风险`
- `帮我做图片选款，给价格和尺码配比`
- `分析这个商品图的爆款基因和测款计划`
- `这款适合小红书还是直播间打爆`

This skill should not handle prompts such as:

- `快到夏季了，有什么购买建议`
- `秋冬女装该上什么品类`
- `帮我做夏季货盘`

For those, use **world-buyer**.
