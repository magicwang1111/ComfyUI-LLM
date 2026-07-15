---
name: print-pattern-derivation
description: >-
  Derive commercially usable fashion textile print variations from one or more
  reference images, motifs, artworks, fabric patterns, screenshots, or print
  briefs. Use whenever the user asks 印花衍生, 花型衍生, 图案衍生, 印花开发,
  面料花型开发, 花型变体, 印花系列, 图案二创, 小碎花, 大花, 新色系,
  companion print, 同系列印花, or wants a reference image turned into a
  selectable print-development family. Important: after a user provides an
  image, first ask them to choose one or more output modes from the seven-item
  menu unless they already explicitly requested a mode or full set; do not
  immediately generate images.
---

# Print Pattern Derivation

## 核心目标

把用户提供的一张或多张参考图，转化为可用于服装、面料、电商选款或花型开发的原创印花衍生方案。

这个 skill 不是普通图生图，也不是把参考图简单换色。它的重点是先提取参考图的“印花基因”，再按用户选择的方向生成可选花型：基因延展、新色系、小碎花、大花留白、几何抽象伴生、季节趋势、印花家族总览。

## 用户选择门槛

当用户上传一张图或指定图片，并调用本 skill 时，默认先停下来让用户选择本次要做什么。除非用户已经明确说了具体方向、编号或“全套”，否则不要直接生成图片、不要创建输出文件、不要开始批量处理。

先做轻量识别，只用一句话说明你看到的图适合作为哪类参考，例如“这张图可以作为花卉满印参考”或“这张图更像抽象几何印花参考”。然后展示以下菜单：

```text
请选择本次要生成的内容：

1. 基因延展款：保留原花型气质，但重新构图
2. 新色系款：同一图案家族的新配色
3. 小碎花密集款：适合连衣裙、衬衫、童装的小比例满印
4. 大花留白款：适合半裙、度假、女装主推款
5. 几何抽象伴生款：同色系 companion print，可做拼接/套系
6. 季节趋势款：按春夏、秋冬、度假、户外、少女、通勤等方向衍生
7. 印花家族总览：原图 + 衍生款放在一张总览板里

请回复编号，例如：1、2、5，或“全套”。
```

不要加入“无缝铺贴检查”“3x3 tile preview”“连续铺布预览”等选项。用户已明确不需要这一项。

如果用户回复编号：

- `1` 到 `6`：只生成用户选择的衍生款。
- `7`：如果已有衍生款，制作总览板；如果还没有衍生款，先询问是要上传已有衍生图，还是生成 1-6 后再做总览。
- `全套`、`全部`、`默认整套`、`1-7`：生成 1-6 六张衍生款，再制作 `00_印花家族总览.png`。
- 用户用自然语言指定方向，如“做小碎花”“换几个新色”“要度假风大花”，直接映射到对应模式，不必再次问菜单。
- 用户上传多张图时，先问“每张图单独衍生”还是“融合成一个印花家族”，除非用户已经说明。

## 输入类型判断

先判断输入图片的角色：

- **原始印花**：应保留主题元素、色彩气质、线条语言和图案节奏，但重新设计。
- **风格参考**：只学习风格、配色、密度、构图和工艺感，不复制具体图案。
- **竞品或品牌参考**：只提取可概括的印花基因，不照搬，不保留 logo、品牌符号、IP 角色或可识别专属元素。
- **服装上印花截图**：重点提取服装上的花型，不生成服装、模特、背景或拍摄场景，除非用户明确要 mockup。
- **文字 brief**：根据用户描述直接建立印花基因，不虚构用户没有要求的品牌、授权或真实销售数据。

如果输入不是印花、图案、纹样、插画、面料表面或可作为印花参考的视觉素材，先说明不适合直接做印花衍生，并询问是否要按色彩/情绪做原创花型。

## 印花基因提取

生成前建立一段内部 print gene brief。它不必作为正式报告保存，但必须用于提示词控制。

提取维度：

- 主题元素：花卉、叶片、果实、动物、海洋、几何、民族风、抽象线条、涂鸦、水彩、复古图案等。
- 图案结构：满印、散点、团花、定位花、边框、条纹、格纹、对称、自由排布、块面拼贴等。
- 图案尺度：小比例、中比例、大比例、局部主视觉、密集或留白。
- 色彩基因：主色、辅助色、底色、明度、饱和度、冷暖、对比强度。
- 线条和笔触：手绘、扁平、油画感、水彩晕染、蜡笔、版画、数码矢量、刺绣感、颗粒感。
- 商用品类：连衣裙、衬衫、童装、半裙、泳装、家居服、户外、围巾、裤装、套装拼接等。
- 风格气质：清新、复古、甜美、度假、通勤、民族、艺术、运动、户外、轻奢、少女、成熟女装等。

把已确认和推断分开。看不清的部分只写“大致印象”，不要编成具体花材、品牌故事或工艺证明。

## 七种输出模式

### 1. 基因延展款

目标：保留原花型气质，但重新构图。适合用户想要“像同一个系列，但不是同一张图”。

生成策略：

- 保留主题元素、色彩气质、图案密度和风格语言。
- 改变元素组合、方向、大小节奏和画面构图。
- 避免把参考图当底图描摹。
- 文件名：`01_基因延展款.png`。

### 2. 新色系款

目标：同一图案家族的新配色。适合快速扩色、做色组、做订货会备选。

生成策略：

- 保留图案类型、元素关系和整体尺度。
- 改成新的商业色系，如奶油粉、雾蓝、鼠尾草绿、复古棕、黑白、度假亮色、秋冬暖色等。
- 避免只粗暴调色；要让底色、花色、叶色和点缀色重新协调。
- 文件名：`02_新色系款.png`。

### 3. 小碎花密集款

目标：适合连衣裙、衬衫、童装的小比例满印。

生成策略：

- 缩小元素比例，增加分布均匀度。
- 花、叶、点状元素要细而清楚，避免大块主视觉。
- 画面应像可大面积铺在布料上的小碎花，而不是单张插画。
- 文件名：`03_小碎花密集款.png`。

### 4. 大花留白款

目标：适合半裙、度假、女装主推款的大比例印花。

生成策略：

- 放大核心花型或主要图案元素。
- 增加呼吸感和留白，形成更强主视觉。
- 适合裙摆、度假衬衫、围巾、沙滩裙、女装主推款。
- 文件名：`04_大花留白款.png`。

### 5. 几何抽象伴生款

目标：同色系 companion print，可做拼接、套系、内外搭、边饰或系列搭配。

生成策略：

- 从原图提取色彩、线条、节奏或局部元素，转化为更抽象的点、线、条、格、波浪、块面或符号。
- 不要做成完全无关的新图案。
- 应能和主花型放在同一服装系列中搭配使用。
- 文件名：`05_几何抽象伴生款.png`。

### 6. 季节趋势款

目标：按春夏、秋冬、度假、户外、少女、通勤等方向做趋势化衍生。

生成策略：

- 如果用户指定季节或人群，按用户指定方向。
- 如果用户未指定，可根据参考图自动选择最合理的趋势方向，并在最终回复中说明。
- 趋势可以改变色温、元素密度、材质感和商业气质，但仍应能看出与参考图属于同一个印花家族。
- 文件名：`06_季节趋势款.png`。

### 7. 印花家族总览

目标：把原图和已生成的衍生款放在一张总览板里，方便选款。

生成策略：

- 总览板不是新衍生款，而是整理交付图。
- 包含原图缩略图和已生成的 1-6 衍生款。
- 每个缩略图下方使用短中文标题：原图、基因延展、新色系、小碎花、大花留白、伴生款、季节趋势。
- 版式干净，像花型开发看板或选款板，不要像海报广告。
- 文件名：`00_印花家族总览.png`。

## 图像生成提示词结构

图像生成提示词优先使用英文，以提高图像模型稳定性。可以按这个结构组织：

```text
Create an original commercial textile print pattern inspired by the uploaded reference image.

Reference gene to preserve: [theme elements, mood, color family, line language, density, scale, rhythm].
Derivative direction: [selected mode].
Commercial use: fashion textile print for [garment category or market].
Design changes: [how this output must differ from the reference].
Composition: square print artwork, flat textile pattern view, clean full-frame pattern, no garment, no model, no room, no photography scene.
Color: [palette].
Style: [hand-painted / watercolor / vector-flat / vintage / abstract / etc.].

Keep it original and commercially usable. Do not copy the exact reference layout, do not include logos, trademarks, brand letters, characters, watermarks, signatures, text, labels, mockup clothing, fabric folds, or product photography background.
```

为每个模式补充具体方向：

- 基因延展：`same print family mood, redesigned motif placement, new layout, not a copy`
- 新色系：`new coordinated colorway, same family, refined commercial palette`
- 小碎花密集：`small-scale dense allover floral, evenly scattered, suitable for dresses and shirts`
- 大花留白：`large-scale floral placement, airy negative space, resort and skirt-friendly`
- 几何抽象伴生：`abstract geometric companion print, same color family, suitable for mix-and-match panels`
- 季节趋势：`trend-adapted seasonal textile print for [season/market], still related to the reference`

## 输出规格和目录

除非用户指定，默认：

- 单张衍生图：正方形 PNG。
- 建议尺寸：高质量 2048x2048 或更高；工具支持时优先 4096x4096。
- 总览板：横版或方形 PNG，确保缩略图和中文标题可读。

如果用户没有指定输出目录，创建一个干净结果文件夹：

```text
印花衍生_YYYYMMDD_HHMMSS/
  01_基因延展款.png
  02_新色系款.png
  03_小碎花密集款.png
  04_大花留白款.png
  05_几何抽象伴生款.png
  06_季节趋势款.png
  00_印花家族总览.png
```

只保存用户选择的正式结果。不要在最终结果目录保留临时图、失败图、日志、manifest、提示词草稿、缓存、裁剪图、蒙版图或空白占位图，除非用户明确要求。

## 批量处理规则

用户给文件夹时，先问处理方式：

```text
检测到这是多图/文件夹任务。请选择：
1. 每张图单独衍生
2. 多张图融合成一个印花家族
```

每张图单独衍生时：

- 每张输入图重置上下文。
- 不把上一张图的花材、颜色、构图带到下一张图。
- 每张图输出到独立子文件夹。
- 总览板只包含当前图的原图和当前图的衍生款。

融合成一个印花家族时：

- 先说明会提取多图共同基因。
- 忽略冲突严重、质量太差或不是印花参考的图片。
- 衍生结果应像同一系列，而不是拼贴杂图。

## 原创和版权边界

参考图可以提供方向，但最终图案必须是原创衍生。

不要生成：

- 可识别品牌 logo、商标、品牌字母组合。
- 已知 IP 角色、卡通人物、艺术家专属图案、球队队徽或授权图案。
- 与竞品图几乎一样的构图、元素位置和细节。
- 水印、签名、图片平台字样、价格标签、店铺名。

如果用户明确要求“照着这个品牌一模一样做”，改为提供同风格原创衍生，不复制受保护元素。

## 质量检查

交付前检查：

- 如果用户还没选模式，没有开始生成。
- 没有输出无缝铺贴检查或 `3x3_tile_preview.png`。
- 文件数量和用户选择一致。
- 每张图都是平面印花 artwork，不是衣服、模特、海报、详情页或场景摄影。
- 衍生款和参考图属于同一审美家族，但不是照搬。
- 1-6 之间有明确差异，不只是同一图轻微换色。
- 色彩适合商业服装开发，不脏、不灰、不荧光失控，除非用户要求。
- 图案元素完整，边缘没有明显残缺主体或无意义裁断。
- 没有文字、乱码、logo、水印、签名、品牌名。
- 总览板标题清晰，缩略图不变形，不遮挡。

失败修正：

- 太像原图：增加“redesigned motif placement, different composition, original derivative, not copied layout”。
- 跑题太远：强化原始主题元素、色彩家族、线条语言和图案密度。
- 像海报/插画：强化“flat textile print artwork, full-frame pattern, no poster, no scene, no model, no garment”。
- 太乱：减少元素种类，统一底色和主辅色，控制密度。
- 差异不明显：明确改变比例、构图、色组、节奏或元素抽象程度。
- 出现文字或 logo：强化“no text, no letters, no logo, no watermark, no signature”。

## 最终回复

完成后用简短中文汇总：

- 用户选择了哪些模式。
- 成功生成哪些文件。
- 跳过或失败的模式及原因。
- 最终保存路径。
- 如果某些内容是根据参考图推断的，简单说明。

不要把大段提示词、内部 print gene brief 或生成过程说明塞进最终回复，除非用户要求查看。
