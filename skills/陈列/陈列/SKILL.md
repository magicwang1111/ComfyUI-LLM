---
name: clothing-display-image-to-image
description: >-
  Create exactly one image-to-image output that turns one or more uploaded
  clothing images into a premium physical apparel display, visual merchandising
  poster, showroom rack scene, boutique wall display, window display, ordering
  booth, product display campaign, or Xiaohongshu-style clothing display image.
  Use this skill for 服装陈列, 衣服陈列, 陈列模板, 按模板生成陈列, 商品图改陈列,
  平铺服装改展厅, 杂乱衣服整理陈列, 实体陈列宣传图, 小红书服装陈列海报,
  图生图陈列, showroom rack, visual merchandising, boutique apparel campaign,
  and one-image clothing display generation. If the user provides a display
  template, reference layout, style sample, 陈列样张, or target effect image,
  prioritize that user template over the built-in default style.
---

# Clothing Display Image-to-Image

## 核心目标

把用户上传的一张或多张服装图片，通过图生图方式，生成**一张**高质量实体服装陈列图或陈列宣传海报。

这个 skill 的第一原则是：**用户模板优先**。如果用户提供陈列模板、样张、参考版式、目标效果图或风格图，必须优先按照用户模板的构图、陈列方式、空间比例、视角、灯光、道具、文字区和整体气质生成。内置默认高端 showroom 模板只在用户没有提供模板时使用。

最终结果应像真实品牌陈列、视觉营销物料、订货会展位、橱窗陈列或精品店陈列拍摄出来的一张商业图，而不是普通换背景、白底商品图、随意拼贴或多方案拼图。

## 硬规则

- 最终只输出一张图。多图输入也只融合成一张完整陈列图。
- 用户给了陈列模板时，按用户模板生成；不要强行回到内置弧形银色挂杆 showroom 模板。
- 用户没有给模板时，必须使用原始默认高端 showroom 挂杆陈列模板：竖版 3:4、弧形银色金属挂杆、木衣架、5-8 件成套服装、展厅墙面、右侧 look sheet、前景石材/面料卡、顶部高级系列标题。
- 默认不要主动切换到墙面陈列、橱窗、货架、岛台、叠装等变体；这些只在用户明确给模板、明确要求换风格，或明确说不要原默认模板时使用。
- 优先保留用户服装的品类、主色、轮廓、材质和关键细节。
- 如果用户给的是模板/风格参考图，只学习陈列结构、空间、灯光、道具和版式，不复制模板图里的衣服。
- 如果原图衣服很多、很乱、遮挡严重，也要尽力选出主要 5-8 件，整理成可用陈列。
- 默认不要让真人模特成为主体，除非用户模板或用户要求明确包含模特。
- 不要把所有输出固定成针织/羊绒 A/W collection、弧形银色挂杆、look sheet、石材台这一种样式。
- 不要使用真实品牌名、机构名或模板图里的品牌字样，除非用户明确要求。

## 输入角色判断

开始生成前，先判断每张图片的角色：

- **服装源图**：需要保留的衣服。识别品类、颜色、材质、廓形、图案、结构细节。
- **陈列模板图**：用户指定的陈列方式或目标效果。只学习构图、空间、灯光、挂架、台座、道具、标题区和版式。
- **风格参考图**：提供氛围、材质、色彩或商业质感。不要照搬其衣服或品牌。
- **混合参考图**：既有衣服又有陈列效果。先确认或合理推断哪些是服装源、哪些是模板参考。
- **杂乱单图**：一张图里很多衣服、截图、堆放或摆放不整齐。选择最清楚的核心款整理陈列。

如果多张图片角色不清，按这个优先级推断：

1. 用户最新明确指向的图片优先。
2. 含清晰单品、平铺、白底、衣服主体占比高的图片优先作为服装源。
3. 含完整空间、挂架、橱窗、展台、门店、海报版式的图片优先作为陈列模板。
4. 如果仍不确定，用“源图 + 模板图”的方式写入提示词，要求保留用户服装并学习参考陈列。

## 用户模板优先流程

当用户提供陈列模板、样张、参考图、目标效果图、模板文件或类似表达时，执行这个流程：

1. 先描述模板的关键视觉结构。
2. 从模板中提取陈列方式，而不是套用内置默认样张。
3. 把用户服装重组进模板结构中。
4. 保留模板的空间比例、视角、主次关系、道具密度和商业质感。
5. 只在不冲突时补充必要细节，避免把模板改成另一种风格。
6. 出图后检查是否仍像用户模板，而不是退回固定 showroom rack。

模板解析清单：

- 画幅比例：竖版、横版、方图、海报、近景、全景。
- 视角：正面、轻微侧角、俯视、橱窗外视角、门店内视角。
- 陈列载体：挂杆、墙挂、货架、展台、岛台、模特架、橱窗、look wall、叠装台。
- 服装数量：单件主推、3-4 件组合、5-8 件系列、密集货架。
- 排布节奏：对称、错落、居中主视觉、左右分区、上挂下叠、前后层次。
- 背景空间：showroom、精品店、展厅、橱窗、订货会展位、纯色影棚、艺术装置。
- 道具：石材、金属、木质、亚克力、面料卡、植物、灯箱、标识牌、陈列桌。
- 灯光：自然光、展厅射灯、柔光棚拍、暗调戏剧光、橱窗灯带。
- 色彩：低饱和、暖灰、黑白、品牌色、季节色、强对比。
- 文字区：顶部标题、底部信息条、侧边标签、无文字、品牌识别位。

## 用户模板提示词模板

用户有陈列模板时，使用这个结构组织图生图提示词：

```text
Create exactly one physical clothing display image using the uploaded clothing source image(s) as the garments and the uploaded display template/reference image as the layout and merchandising template.

Garment source to preserve: [list source garment categories, dominant colors, silhouettes, materials, and key details].

Template to follow: [describe the user template's aspect ratio, display structure, rack/shelf/plinth/window/wall system, camera angle, spacing, lighting, props, typography area, and mood].

Restage the source garments into the template's display system. Keep the template's composition, spatial hierarchy, display furniture, viewing angle, prop density, lighting mood, and commercial styling logic.

Important: do not copy the garments, logos, brand names, or exact text from the template image unless the user explicitly asks. Replace the template garments with the user's source garments while preserving the user's garment categories, colors, silhouettes, fabrics, and signature details.

Output one coherent premium apparel visual merchandising image only.
```

再补充模板锁定约束：

```text
Follow the provided display template first. Do not force the result into the built-in curved chrome rack showroom style unless the user template already uses that structure.
```

## 无模板默认模板

用户没有提供陈列模板、样张、参考版式或明确变体要求时，默认必须回到原始高端 showroom 挂杆陈列模板。这个默认模板是普通“服装陈列”请求的保底标准，不要因为服装是通勤、基础款、女装、裤装或套装就自动改成墙面精品店陈列。

默认视觉公式：

1. **竖版海报构图**：默认 4K、3:4、竖屏画幅，正面或轻微侧角商业摄影。
2. **顶部标题区**：画面上方留 10%-18% 空间，放少量高级感标题，如 `2026 A/W COLLECTION`、`PIONEER COLLECTION`、`AUTUMN / WINTER`。用户未提供品牌名时，使用通用系列名。
3. **中部主陈列**：一根轻微弯曲的抛光银色金属挂杆横贯画面，5-8 件服装用浅木衣架均匀悬挂。挂钩、夹子、裤夹要真实。
4. **服装排列**：按系列搭配排序，通常是外套/上衣、开衫/毛衣、衬衫/背心、裤/裙、连衣裙/套装。高低错落但不能乱。
5. **右侧企划板**：挂一张被金属夹夹住的白色 look sheet 或设计草图板，不要用装饰性金框画架。板内可包含小人穿搭缩略图、面料色块、款式线稿、材质图和 01-06 产品编号。
6. **前景展台**：下方或前景加入石材台、圆形展台、粗石块、混凝土块、银色金属托盘、纱线筒、面料样卡、透明亚克力说明牌。前景要像展陈物料区，不要像家居茶几摆设。
7. **空间质感**：奶油白、浅灰、米色、水泥灰、暖灰墙面；弧形墙、壁龛、暗藏灯带、斜射阳光或柔和展厅灯。
8. **系列气质**：安静奢华、自然肌理、先锋工艺、艺术服装陈列、订货会陈列、趋势企划。

如果源服装不是针织或羊绒，不要强行改成针织。保留原服装材质，只借用这套“高端展陈海报”的空间、挂杆、道具和版式标准。

## 可选变体模板池

这些变体只在以下情况使用：用户提供的模板本身就是该结构；用户明确要求“换风格”“做橱窗”“做墙面陈列”“做货架陈列”“不要默认 showroom 挂杆”；或用户明确要求按另一种陈列场景生成。普通无模板请求不要主动选择这些变体。

1. **精品店墙面陈列**：墙挂、层板、侧挂、叠装、干净门店灯光。
2. **橱窗展台主推款**：橱窗、台座、聚光灯、品牌季节氛围，适合单件或少量主推款。
3. **订货会展位陈列**：展位背景墙、样衣杆、产品编号、面料卡、趋势企划板。
4. **服装系列企划板陈列**：look sheet、色卡、材质板、线稿、编号，但文字要少。
5. **极简画廊式展陈**：少道具、大留白、强灯光，适合高级感单品或结构感服装。
6. **货架/叠装/挂装结合陈列**：真实零售陈列秩序，适合休闲、运动、童装、基础款或多 SKU。
7. **户外/工装主题展陈**：粗石、金属夹、帆布、砂岩、苔藓或干草，但不遮挡衣服。

## 无模板默认提示词模板

用户没有模板时，使用这个结构。除非用户明确要求变体，否则 `Chosen display direction` 必须写原始默认高端 showroom 挂杆陈列。

```text
Create exactly one premium physical apparel visual merchandising image using the uploaded clothing reference image(s) as the product source.

Preserve the source garments: [list garment categories, colors, silhouettes, materials, and key details].

Chosen display direction: original premium vertical showroom rack display, 4K vertical 3:4 campaign poster, high-end fashion trend forecast showroom / ordering booth.

Restage these garments as a refined real-world clothing display, not a flat lay, not a white-background ecommerce image, and not a redesign.

Composition: one slightly curved polished chrome garment rail across the upper-middle of the image, realistic hooks, pale wooden hangers, 5 to 8 coordinated garments evenly spaced, tidy height rhythm. Hang skirts and pants from the chrome rail with realistic clips or lower secondary hangers; keep them part of the lineup, not a single oversized hero piece on a pedestal.
Environment: warm off-white / greige / soft concrete showroom wall, curved architectural background, subtle cove lighting, soft gallery spotlights, realistic shadows, exhibition-booth clarity.
Props: foreground sculptural stone or plaster plinth, rough rock blocks, brushed silver metal tray or platform, fabric swatches, yarn cones or folded textile, acrylic material cards, small concept boards.
Right side: one clipped white hanging look sheet board with tiny outfit thumbnails, fabric texture blocks, line sketch panels, color chips, and 01-06 product references; do not use a decorative framed easel.
Typography: minimal premium collection title such as 2026 A/W COLLECTION, AUTUMN / WINTER, PIONEER COLLECTION; keep text sparse and elegant.

Keep the source garments recognizable. Do not change the main clothing categories, dominant colors, silhouettes, material textures, or signature details.
Output one coherent commercial clothing display image only.

Do not switch to boutique wall display, window display, shelf display, product island, or retail rack variant unless the user explicitly asks or provides that template.
```

## 杂乱单图模板

当用户只上传一张很乱的图：

```text
From the uploaded messy clothing image, identify the clearest main garments and convert them into one refined physical clothing display image.

Remove clutter, floor mess, unrelated objects, hands, people, mirrors, screenshots, and background noise.
Preserve the dominant garment colors, categories, silhouettes, and fabric mood.

If a user display template is provided, arrange the cleaned garments according to that template. If no template is provided, choose the most suitable display direction from the default template pool.

Output one coherent apparel visual merchandising image only.
```

## 服装保留优先级

按这个顺序保留：

1. 品类：外套、马甲、开衫、毛衣、衬衫、T 恤、卫衣、裤子、半裙、连衣裙、帽子、包、配饰。
2. 主色：米白、卡其、黑、灰、蓝、粉、绿、紫、牛仔蓝等色系必须接近原图。
3. 廓形：长短、宽松度、领型、袖型、裤腿、裙长、肩线、下摆。
4. 材质：针织、羊绒、羊羔绒、棉布、工装斜纹、牛仔、皮革、尼龙、蕾丝、雪纺、毛呢等。
5. 细节：纽扣、拉链、抽绳、口袋、波浪纹、肌理、拼接、罗纹、印花、腰带。

看不清时，保留“大类 + 主色 + 风格”，不要编成无关衣服。

## 道具选择

道具只服务陈列，不要遮挡衣服。用户模板中有明确道具时，优先延续模板道具类型。

无模板时可按服装风格选择：

- 针织/羊绒：纱线团、纱线筒、针织面料卡、织片小样、羊毛色卡。
- 工装/户外：粗石块、苔藓、干草、帆布、金属夹、砂岩台面。
- 轻奢女装：洞石、米白石膏、透明亚克力牌、银色金属托盘、低饱和色卡。
- 暗色/先锋：黑色亮面雕塑、银色褶皱金属片、暗灰墙面、强斜光。
- 清浅通勤：奶油白圆台、浅木、亚麻布、柔和自然光、低饱和色卡。
- 运动/休闲：模块货架、灯箱、干净地台、简洁品牌色块。

除非用户模板或用户要求明确包含，否则避免花瓶、珍珠托盘、丝带碗、窗帘、书架、蜡烛、金色画框、复古闺房道具等容易把画面带成家居软装的元素。

## 文字策略

文字是加分项，不是保底项。模型文字不稳定时，宁愿少写。

- 如果用户模板有明确标题区，保留相同的信息层级和位置，但不要复制模板品牌名。
- 如果用户提供品牌名、系列名、季节或口号，可以少量使用。
- 如果用户没有提供文字，使用通用系列名或干脆减少文字。
- 大标题最多 1-2 行，例如 `2026 A/W COLLECTION`、`PIONEER COLLECTION`、`UTILITY FIELD SERIES`。
- 小字可以做成模糊但高级的排版块、编号、材质说明、色卡标签。
- 不要大面积乱码，不要密集长段落，不要随机品牌 logo。

## 负面约束

按场景加入适合的负面提示：

```text
Do not output multiple images, collage panels, before-and-after comparisons, or separate variations.
Do not create a plain ecommerce white-background product layout unless the user explicitly asks.
Do not ignore the user's display template.
Do not force every output into a curved chrome rack showroom style.
Do not copy garments, brand names, logos, or exact text from the style/template reference image unless explicitly requested.
Do not change jackets into sweaters, pants into skirts, dresses into coats, or alter the main color palette.
Do not put full-size human models as the main subject unless the user asks or the template clearly requires it.
Avoid chaotic spacing, crowded piles, distorted hangers, broken rails, melted clothing, duplicated sleeves, extra collars, unreadable large text, random brand logos, fake plastic texture, blurry fabric detail, toy-like miniature scale, and cheap store interior.
```

如果用户模板偏家居、橱窗、门店或软装风格，不要一刀切排除这些元素；只排除与用户目标冲突、遮挡衣服或降低商业质感的杂物。

## 保底优先级

如果无法一次实现全部标准，按这个顺序保底：

1. 一张图。
2. 用户模板存在时，整体构图和陈列方式接近用户模板。
3. 用户服装主色、品类、轮廓不严重跑偏。
4. 陈列真实，有明确挂装、叠装、展台、货架、墙面或橱窗逻辑。
5. 空间、灯光、比例和阴影合理。
6. 道具服务服装，不遮挡主体。
7. 文字少而高级，没有明显乱码。

宁愿减少道具和文字，也要先保证：**模板像、衣服像、陈列真实、画面高级**。

## 质量检查

出图后检查：

- 是否只出一张图。
- 如果用户提供模板，是否贴近用户模板的构图、陈列方式、视角、空间和氛围。
- 用户没有提供模板时，是否使用了原始默认高端 showroom 挂杆模板。
- 用户没有提供模板时，是否错误切换成墙面精品店、橱窗、货架、岛台或叠装变体。
- 是否保留了用户服装，而不是复制模板图里的衣服。
- 服装品类、主色、轮廓、材质是否仍接近用户源图。
- 空间是否真实：墙、地、挂架、货架、台面、衣架、阴影、比例合理。
- 陈列是否有商业逻辑：不是乱堆、不是普通换背景、不是廉价店铺截图。
- 文字是否少而高级；若乱码严重，下次提示减少文字。
- 道具是否提升质感，没有遮挡主体服装。

失败修正：

- 忽略用户模板：强化“follow the provided display template first; preserve its composition, display structure, camera angle, lighting, prop density, and typography area”。
- 无模板却没有回到默认挂杆模板：强化“when no user display template is provided, use the original premium vertical showroom rack display by default: curved polished chrome rail, pale wooden hangers, 5-8 garments, look sheet board, stone plinth, greige showroom wall, top collection typography”。
- 用户有模板却回到固定挂杆模板：强化“follow the provided display template first; do not force curved chrome rack showroom style unless the template uses it”。
- 衣服变款：强化“preserve source garments, do not redesign, keep categories/colors/silhouettes/material details”。
- 复制模板衣服：强化“replace template garments with source garments; do not copy garments from template image”。
- 太普通：强化“premium physical apparel visual merchandising, real retail display, commercial campaign photography, refined lighting and spacing”。
- 太乱：减少到 3-6 件核心款，移除多余道具和长文字。
- 太像电商图：加入真实陈列载体，如 wall display、rack、plinth、shelf、window display、ordering booth、gallery lighting。
