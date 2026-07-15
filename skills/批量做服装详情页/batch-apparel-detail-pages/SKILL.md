---
name: batch-apparel-detail-pages
description: "Use when the user asks 批量做服装详情页, 服装详情页批量替换, 模板不乱动, 模板相似度不够, 同款排版详情页, 数字人换服装详情页, 提供模板和产品素材后直接生成, 2K高清详情页, or wants one apparel detail-page template preserved while replacing content from product folders."
---

# 批量做服装详情页

## 定位

这是一个“模板保护型智能替换”技能。

目标不是重新设计详情页，而是让用户先指定一个商家详情页模板，再选中若干个产品素材文件夹批量生成。每个产品文件夹代表一个产品，里面放该产品的全部图片、文案、表格和说明。模板会被当成固定版式标准：排版、模块顺序、图片位置、文字位置、比例、留白、字体层级、颜色风格、装饰元素、尺码表样式和图标样式默认锁定，只替换用户素材和说明中明确需要替换的内容。

默认先生成 `template_replacement_plan.json`，再根据执行模式决定是否需要用户确认。用户已经提供模板和产品素材，并明确说“直接做”“不要中途问”“重新做”“我给了模板和素材就替换能替换的内容”时，进入 `direct_generation` 模式：仍然输出替换计划和风险标记，但不要把确认计划当作阻塞步骤。

## 核心原则

1. **模板不乱动**：不随意重排模块，不改图片框比例，不改文字区域，不改表格样式，不改整体视觉节奏。
2. **只替换该替换的内容**：logo、品牌名、产品标题、卖点文案、模特/数字人、服装图、细节图、面料图、颜色图、尺码表、参数、洗护和场景图等，必须来自当前产品资料或用户说明。
3. **素材自动读取和匹配**：读取每个产品素材文件夹里的图片、文案、表格和说明文件，按文件名、文件夹名、图片内容、文字内容和用户要求匹配到模板槽位。
4. **计划先行但不机械打断**：生成详情页前，必须记录每个模板槽位用什么素材替换、哪些保留模板原内容、哪些缺资料、哪些有事实风险；只有缺少模板/素材/目标路径，或事实类内容无法判断且用户没有授权直接生成时，才停下来问。
5. **事实内容不乱编**：尺码、面料、洗护、认证、检测、功效、价格、销量、评价、平台承诺等不能编造。
6. **缺失资料可保留但要标风险**：用户没提供某个槽位资料时，默认保留模板原内容或原版式，但必须在计划里标出风险；商品事实类内容要特别提示用户确认。
7. **数字人和服装替换优先贴近模板**：用户提供数字人和产品衣服时，优先生成或匹配成当前产品上身效果，姿势、构图、比例、光感和模板风格尽量一致。
8. **高清不是简单放大**：用户要求高清、2K、4K 或画面不糊时，必须输出原生高清母版；文字、表格、线条和图标要按高清尺寸重新绘制，不能只把低清 PNG 拉大。
9. **模板相似度优先于自由美化**：模板不是灵感板，而是版式合同。不能把云朵边、双图卡、圆形卖点、尺码表、参数卡、评论头像、生活照重复节奏等模板特征简化成另一套设计。

## 执行模式

### `confirm_plan`

当用户只给出初始需求，或素材/事实信息存在明显不确定性时使用。流程是解析模板、扫描素材、输出 `template_replacement_plan.json`，等待用户确认后生成。

### `direct_generation`

当用户已经给出模板和产品素材，并明确要求不要中途询问时使用。要求：

- 生成 `template_replacement_plan.json`，但 `status` 写为 `direct_generation_ready`，`requires_user_confirmation` 写为 `false`。
- 直接替换所有能替换的槽位，缺失或事实风险写入报告。
- 如果某个模板图片槽位无法直接使用现有素材，基于当前产品和模板风格生成同构图素材，不要白底硬贴。
- 最终答复汇总已替换、已生成、保留和风险项，不把“请确认计划”作为交付前置条件。

## 必填输入

执行默认流程前必须确认：

1. **模板详情页图片**：用户自己的标准详情页长图、截图或参考图，只需要一套模板。
2. **产品素材文件夹列表**：用户选中的一个或多个文件夹；每个文件夹必须只对应一个产品，并包含该产品的全部图片、文案、表格和说明。
3. **目标路径**：保存模板解析、批量替换计划和生成结果的位置；如果用户未指定，可建议使用一个新的任务输出目录。
4. **用户说明文件**：推荐放在每个产品文件夹内，例如 `说明.txt`、`要求.txt`、`requirements.txt`、`产品信息.txt`。没有说明文件时，也要根据素材自动生成初步计划，但要提示用户确认。

如果模板图、产品素材文件夹列表或目标路径缺失，先询问缺失项。不要从历史目录、zip 所在目录或当前目录自行猜测。不要把“产品数量”作为默认输入要求；批量数量应由用户选中的产品文件夹数量决定。

## 推荐素材组织

推荐结构：

```text
模板：
└── 模板详情页.png

用户选中的产品文件夹：
├── 01_产品名称/
│   ├── 说明.txt
│   ├── logo.png
│   ├── 数字人.png
│   ├── 衣服.png
│   ├── 主图.png
│   ├── 面料细节.png
│   ├── 颜色图.png
│   ├── 尺码表.xlsx
│   └── 场景图/
└── 02_产品名称/
    └── ...
```

也可以把所有产品文件夹放在一个总目录下，或从不同位置选择多个产品文件夹。技能需要自动扫描每个被选中的产品文件夹，但文件名越清楚，匹配越准确。

常用说明文件名：

- `说明.txt`
- `要求.txt`
- `产品信息.txt`
- `requirements.txt`
- `copy.txt`
- `text.txt`
- `尺码表.csv`
- `size.csv`

## 模板解析

拿到模板详情页后，先用视觉理解能力解析，不要套固定模块。

解析内容包括：

- 页面尺寸、长图高度、分屏位置和模块顺序。
- 每个模块的作用，例如首屏、品牌说明、面料、细节、尺码、参数、洗护、场景、模特图。
- 图片槽位：位置、尺寸比例、裁剪方式、主体安全区、是否可替换。
- 文字槽位：位置、字号比例、字重、颜色、对齐方式、行距、最大行数、是否可替换。
- logo/品牌槽位：位置、尺寸、颜色限制和替换规则。
- 表格槽位：表头、列宽、行高、线条、颜色、文字样式和数据来源。
- 装饰元素：线条、圆角、图标、标签、底纹、背景块、留白和分割节奏。
- 原模板内容的处理策略：替换、保留、缺失时保留但标风险、禁止复制。

必须生成 `template_slot_map`。它不是普通文字说明，而是后续套版的约束清单，至少包含：

- `section_order`：模板模块顺序和每段起止位置。
- `section_bbox`：每个模块在整张长图中的大致坐标或比例。
- `image_slot_bbox`、`text_slot_bbox`、`logo_slot_bbox`、`table_slot_bbox`：图片、文字、logo、表格槽位的位置、比例、裁切方式和主体安全区。
- `decoration_shapes`：云朵边、圆形标签、卡片圆角、线条、图标、底纹、色块等装饰形状。
- `module_shape_tags`：给每个模块贴形态标签，例如 `hero_lifestyle_close_crop`、`soft_text_block`、`fabric_full_bleed`、`scallop_edge`、`dual_image_cards`、`circle_benefits`、`size_chart`、`comment_bubbles`、`lifestyle_sequence`。

`module_shape_fidelity` 是硬门槛：生成图每个模块要先对齐模板的外形、比例、留白和装饰，再替换内容。页面如果看起来像重新设计，而不是模板替换，必须返工。

解析结果保存为：

```text
目标路径/
└── 详情页标准解析/
    ├── 标准详情页原图/
    ├── 标准详情页解析.json
    └── 模板说明.txt
```

`标准详情页解析.json` 推荐结构：

```json
{
  "template_name": "商家标准详情页",
  "page": {
    "width": 790,
    "height": 21463,
    "layout_lock": true,
    "style_summary": "柔和童装风、留白充足、浅色背景、圆润标签、图文长图节奏"
  },
  "sections": [
    {
      "number": "01",
      "section_name": "首屏主视觉",
      "folder_name": "01_首屏主视觉",
        "layout_summary": "顶部品牌文字，下方大幅场景图，整体位置和比例锁定。",
      "module_shape_tags": ["hero_lifestyle_close_crop", "small_logo", "title_below_image"],
      "template_slot_map": {
        "section_bbox": [0, 0, 790, 1500],
        "image_slot_bbox": [83, 166, 625, 1125],
        "logo_slot_bbox": [318, 38, 155, 58],
        "text_slot_bbox": [0, 1428, 790, 76],
        "crop_mode": "cover",
        "subject_safe_zone": "人物主体居中偏下，顶部留白按模板保留但不能过多"
      },
      "replacement_policy": {
        "layout_locked": true,
        "missing_material_strategy": "keep_template_with_risk_flag",
        "requires_user_confirmation": true
      },
      "upload_slots": [
        {
          "slot_name": "logo或品牌名",
          "type": "logo",
          "required": false,
          "replaceable": true,
          "guide": "上传自己的 logo 或品牌名。没有提供时保留模板位置并标记风险。"
        },
        {
          "slot_name": "首屏场景主图",
          "type": "model_scene_image",
          "required": true,
          "replaceable": true,
          "guide": "上传当前产品数字人/模特和服装素材，按模板构图生成或替换。"
        }
      ]
    }
  ]
}
```

## 素材扫描与智能匹配

扫描每个产品文件夹时要读取：

- 图片：`.jpg`、`.jpeg`、`.png`、`.webp`
- 文案：`.txt`、`.md`
- 表格：`.csv`、`.tsv`、`.xlsx`、`.xls`
- 文档：`.docx`、`.doc`、`.pdf`

匹配依据按优先级：

1. 用户说明文件里的明确要求。
2. 文件夹名和文件名关键词，例如 logo、品牌、数字人、模特、衣服、主图、面料、细节、颜色、尺码、参数、洗护、场景。
3. 图片内容视觉判断，例如人物图、服装单品图、面料特写、色卡、表格截图。
4. 文本内容判断，例如尺码数据、面料成分、卖点文案、洗护说明。
5. 模板槽位类型和模块语义。

不能确定的素材不要硬塞进槽位，应放入 `unmapped_materials`，让用户确认。

## 替换计划

生成详情页之前，必须输出：

```text
产品文件夹/
└── 生成文件/
    └── template_replacement_plan.json
```

总览计划可输出到：

```text
目标路径/
└── 详情页标准解析/
    └── template_replacement_plan.json
```

计划结构必须包含：

```json
{
  "status": "needs_user_confirmation",
  "approval_mode": "confirm_plan",
  "template_locked": true,
  "missing_material_strategy": "keep_template_with_risk_flag",
  "products": [
    {
      "product_name": "01_产品名称",
      "product_dir": "C:/path/01_产品名称",
      "replacement_summary": {
        "replace_count": 8,
        "keep_template_count": 3,
        "missing_required_count": 1,
        "risk_count": 2
      },
      "replacements": [
        {
          "section_number": "01",
          "section_name": "首屏主视觉",
          "slot_name": "首屏场景主图",
          "slot_type": "model_scene_image",
          "action": "replace",
          "matched_materials": [
            {
              "path": "C:/path/01_产品名称/数字人.png",
              "role": "digital_human",
              "score": 92
            }
          ],
          "adaptation_rules": [
            "保持模板图片框位置和比例",
            "主体居中，不变形，不遮挡重要服装细节",
            "光感、背景和构图贴近模板"
          ],
          "risk_flags": []
        }
      ],
      "unmapped_materials": [],
      "requires_user_confirmation": true
    }
  ]
}
```

计划里的 `action` 只能使用：

- `replace`：有明确素材，建议替换。
- `keep_template`：缺少素材，保留模板原内容或原版式。
- `needs_confirmation`：素材可能匹配，但不够确定。
- `skip`：用户说明要求删除或该槽位不适用于当前产品。

## 缺失资料策略

默认策略是 `keep_template_with_risk_flag`：

- 缺图片：保留模板原图或原图片区结构，并标记缺失。
- 缺普通文案：保留模板文字或留空，但要在计划中说明。
- 缺 logo：保留模板位置，可保留原模板文字作为占位，但要提示用户。
- 缺尺码、面料、洗护、参数：不能静默沿用，必须标记为商品事实风险，生成前让用户确认是否允许保留模板内容。
- 缺认证、检测、销量、评价、价格：默认不保留，不生成，除非用户提供真实资料并明确要求。

## 智能适配规则

图片替换：

- 保持模板图片框的位置、宽高比例、圆角、遮罩和边距。
- 自动裁剪、缩放、居中或补背景，但不能拉伸变形。
- 人物和服装主体不能被裁掉；服装细节优先完整可见。
- 面料、细节、颜色图要贴合原槽位视觉密度。
- 如果图片方向不合适，优先补背景或生成同构图替代图，而不是破坏版式。

风格与色调：

- `style_tone_lock`：先从模板提取主背景色、强调色、文字深浅、logo视觉重量、卡片/圆角/留白节奏。
- 产品颜色可以真实呈现，但页面 UI 色调要贴近模板；深色产品不能把整个详情页拖成沉重灰黑风。
- logo 和品牌标识按模板的小尺寸、轻量感和出现频次处理；不能让新 logo 反复放大抢版面。
- 若模板是奶油白、柔粉、暖棕、浅木光，生成页的背景、标签、文案块和装饰色要保持同一温柔色系。

文字替换：

- 保持模板原字号层级、字重、颜色、行距、对齐和文字框位置。
- 自动换行、压缩字号或删减冗余词，不能溢出、重叠或遮挡图片。
- 文案必须来自用户说明或当前产品资料；没有事实依据不要编写具体参数。

表格替换：

- 保持模板表格样式，包括表头、列宽、行高、线条、底色、字号和对齐。
- 用户提供 `.csv`、`.xlsx` 或截图时，按模板样式重排数据。
- 数据列不一致时优先保留模板的列结构，并在计划中提示需要确认。

数字人/模特换装：

- 如果用户提供数字人和服装素材，优先生成当前产品上身图。
- `model_scene_quality_gates`：生成或替换前先把模板人物图拆成姿势、神态、视线、动作、镜头远近、主体占比、背景、光线方向、景深和道具，再逐项复刻。
- `candidate_pool_selection`：每个模板人物姿势至少生成 4 张候选，做拼图或并排复核；只选最贴近模板的一张。不能把第一张能用但呆板的候选直接放入长图。
- 当前产品服装必须真实上身到模特身上，不能只是把人物替换到场景里，不能穿模板原商品或其他款。
- 背景必须贴近模板场景；模板是室内暖木窗光，就不能交付白底、纯棚拍或无环境人物图。
- 光线要有真实相机感，优先写实摄影、自然窗光、柔和阴影、真实布料纹理和皮肤质感；避免塑料皮肤、过度磨皮、假景深、手指异常、衣服边缘融化。
- 用户要求“索尼相机、写实、不要 AI 感”时，按全画幅相机写实质感生成，生成后筛掉呆板表情、直视硬摆、构图过远/过近、光线方向不一致的图。
- 不能把模板原模特、原商品图当成当前产品事实来源。
- 生成后要检查脸部、手部、服装结构、图案文字和衣物边缘是否异常。

不可直接使用的素材：

- 如果用户素材尺寸、角度、背景或风格放不进模板槽位，先生成同构图替代素材，再套版。
- 生成素材必须使用当前产品的颜色、款式、细节和说明；不确定的商品事实保持风险标记。
- 生成候选图要做筛选，至少保留最像模板的一张，不把第一张明显呆板或 AI 感强的图直接交付。

生活场景变化：

- `lifestyle_scene_variation`：当模板下半段有多张模特生活图时，要逐张对应模板参考裁切生成不同镜头，避免用同一张图反复裁切。
- 至少覆盖坐姿互动、举手/动作、双人站立、单人窗边、半身近景或局部构图等模板已有节奏。
- 每张生活图都要记录对应的模板参考槽位；如果复用同一素材，必须是模板本身也在重复同一画面节奏。

## 高清输出

`native_2k_master` 是高清详情页的默认交付策略：

- 常规交付至少输出模板原尺寸长图和预览图。
- 用户要求 2K/高清时，输出宽度至少 2160px 的原生高清母版；高度按模板比例等比放大。
- 高清版要重新绘制文字、表格、边框、圆角、图标和矢量/形状元素。
- 位图素材可按最高可用分辨率适配并轻微锐化，但不能只把已经合成好的低清整图拉大后交付。
- 输出命名建议：`00_详情页长图.png`、`00_详情页长图_预览.jpg`、`00_详情页长图_2k.png` 或 `00_详情页长图_2k_native.png`。

## 视觉相似度复核

`visual_similarity_audit` 必须在交付前完成：

1. 导出整图预览和关键裁切：首屏、面料大图、云朵/双图卡、圆形卖点、尺码表、参数卡、人物生活照、底部重复模块。
2. 与模板逐项对比：模块顺序、槽位位置、模块形状、图片密度、色调、字体层级、生活照节奏。
3. 如果某段只保留了大概顺序，但外形已经变成另一套设计，视为不通过。
4. 如果人物照片重复明显、logo过大、首图主体远近不对、色调明显偏离模板，先修再交付。

## 脚本用法

使用 `scripts/prepare_detail_pages.py` 做确定性的建夹、扫描和替换计划。脚本不负责视觉解析模板，也不负责最终视觉生成；这些由 Codex 根据模板和计划完成。

初始化模板工作区：

```bash
python scripts/prepare_detail_pages.py --input-dir "C:\path\target" --mode standard --init-standard --standard-image "C:\path\template.png"
```

可选：如果用户还没有整理素材，可以根据 `标准详情页解析.json` 创建空的产品资料文件夹。默认批量流程不需要这一步：

```bash
python scripts/prepare_detail_pages.py --input-dir "C:\path\target" --mode standard --template-json "C:\path\target\详情页标准解析\标准详情页解析.json" --product-count 3 --product-names "01_粉色卫衣|02_白色衬衫|03_针织开衫" --create-products
```

扫描同一总目录下的多个产品文件夹并生成替换计划：

```bash
python scripts/prepare_detail_pages.py --input-dir "C:\path\target" --mode standard --template-json "C:\path\target\详情页标准解析\标准详情页解析.json" --build-replacement-plan
```

如果素材在独立目录：

```bash
python scripts/prepare_detail_pages.py --input-dir "C:\path\target" --mode standard --template-json "C:\path\target\详情页标准解析\标准详情页解析.json" --materials-root "C:\path\materials" --build-replacement-plan
```

如果用户从不同位置选中了多个产品文件夹，使用多个 `--product-dir`：

```bash
python scripts/prepare_detail_pages.py --input-dir "C:\path\target" --mode standard --template-json "C:\path\target\详情页标准解析\标准详情页解析.json" --product-dir "D:\产品素材\01_粉色卫衣" --product-dir "E:\新款素材\02_白色衬衫" --build-replacement-plan
```

用户已经授权不要中途确认时，使用 `direct_generation`：

```bash
python scripts/prepare_detail_pages.py --input-dir "C:\path\target" --mode standard --template-json "C:\path\target\详情页标准解析\标准详情页解析.json" --product-dir "D:\产品素材\01_粉色卫衣" --build-replacement-plan --approval-mode direct_generation
```

扫描已有产品资料状态：

```bash
python scripts/prepare_detail_pages.py --input-dir "C:\path\target" --mode standard --template-json "C:\path\target\详情页标准解析\标准详情页解析.json" --scan-products
```

兼容旧逻辑：

- `--mode simple`：旧的散图简单模式。
- `--mode advanced`：旧的 17 模块资料文件夹模式。

默认优先使用 `standard` 模式。只有用户明确要求“简单模式”“17 模块”“高级模式”时，才进入旧兼容模式。

## 生成流程

确认替换计划后，逐个产品生成：

1. 读取 `标准详情页解析.json`。
2. 逐个读取用户选中的产品文件夹。
3. 读取每个产品的 `template_replacement_plan.json`。
4. `confirm_plan` 模式执行确认过的 `action`；`direct_generation` 模式执行计划中可确定的 `action`，并把风险写入报告。
5. 按模板原位置、比例、文字框、表格样式和视觉节奏替换。
6. 在每个产品的 `生成文件/` 输出 `00_详情页长图.png`。
7. 必要时输出分模块图，例如 `01_首屏主视觉.png`。
8. 用户要求高清时输出 `native_2k_master`。
9. 输出或更新替换报告，记录实际替换、生成、保留和风险项。

## 合规与真实性

不要从模板图复制到新产品中：

- 未授权品牌 logo、店铺名、商标。
- 原商品图片、原模特图、买家秀。
- 价格、促销、销量、评价、排名。
- 认证、检测报告、质检图片。
- 售后承诺、运费险、退换货政策。
- 大段原商家文案。

可以学习和保留：

- 布局比例。
- 模块顺序。
- 字体层级。
- 标签样式。
- 背景、线条、卡片、留白。
- 图文比例和视觉节奏。
- 用户明确允许保留的模板占位内容。

## 质量检查

交付前检查：

- 已先生成 `template_replacement_plan.json`；`confirm_plan` 模式已确认，`direct_generation` 模式已记录无需确认的依据。
- 已生成 `template_slot_map`，并按 `module_shape_fidelity` 复刻模块外形。
- 生成页与模板在布局、元素位置、排版和节奏上高度一致。
- 已执行 `visual_similarity_audit`，整图和关键裁切没有“重新设计感”。
- 所有替换内容来自当前产品资料或用户明确说明。
- 缺失资料、保留模板内容和事实风险已经标出。
- 中文没有乱码、方框、重叠或过小。
- 图片主体没有明显错位、畸形、遮挡或变款。
- 数字人/模特图通过 `model_scene_quality_gates`：姿势、神态、动作、镜头远近、背景、光线方向和服装款式都贴近模板与当前产品。
- 人物图已执行 `candidate_pool_selection`；下半段生活图满足 `lifestyle_scene_variation`，没有明显素材重复感。
- 没有白底人物硬贴、成人误图、错款衣服、呆板表情、塑料 AI 感或明显假光。
- 尺码表、参数表和颜色表样式贴近模板。
- `preview_and_crop_qa`：交付前查看整图预览，并抽查首屏、面料/细节、尺码表、人物场景、底部重复模块等关键裁切。
- 高清交付已验证宽度、高度、文件存在和清晰度；2K/高清需求必须交付 `native_2k_master`。
- 最终文件只放在每个产品的 `生成文件/`。

## 最终回复

任务结束后简洁汇总：

- 解析出多少个模板模块和槽位。
- 扫描了多少个产品素材文件夹。
- 每个产品建议替换、保留、缺失、需确认的数量。
- `template_replacement_plan.json` 保存在哪里。
- 已生成或计划生成的详情页保存在哪里。
- 哪些商品事实资料需要用户确认。

除非用户明确要求，不额外生成无关日志、报告或说明文档。
