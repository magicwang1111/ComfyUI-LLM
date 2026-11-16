# TikTok 发布文案与标签规则

本文件控制数据库“文案”和“标签 tag”的生成，可直接修改，下一次任务读取最新内容。它独立于视频脚本规范，不决定人物、镜头或口播，也不进入 WAN 的视频提示词。

核心目标：不是单纯描述衣服，而是用美国消费者熟悉的表达方式，让她们产生共鸣、喜欢这套穿搭，并愿意点击购买。

## 来源与历史风格

2026-11-07 对现有数据库未删除记录进行统计：161条记录中140条有文案或标签，来自 bnmb（75条）和 wset（65条）。140条发布文案中122条含 emoji，英文长度中位数约25词；138条使用5个标签，另2条使用4个标签。样本没有发布效果数据，以下总结代表历史写法，不代表流量或转化效果。

历史主要有两种写法：

- 痛点或发现式：先提出具体穿衣顾虑或表达发现新搭配的惊喜，再写一两个可见设计和适合的场景。早期部分文案较长。
- 生活场景式：一句轻松的日常体验，配一个相关 emoji。例如 wset/B64 的 “A sun hat, a flowy dress, and nowhere to rush 👒”，以及 wset/B66 的 “Coffee stop, outfit check, back to exploring ☕”。例子只展示语气，不作为固定句式或其他商品的事实。

历史常见标签包括 #PlusSizeFashion、#OutfitInspo、#PlusSizeStyle、#OOTD、#EverydayStyle、#FashionFinds、#CasualStyle 和 #TikTokShop。历史也有笼统的 #FYP、夸大显瘦或未经确认的面料描述，后续不机械沿用。

## 写作前的分析

文案在视频生成前、与脚本同时创作，分析对象是已核验的商品信息、商品裁剪图和本次视频脚本，不是成片。写作前在内部完成以下判断，分析过程不写进文案，需要留档时写入 `execution-notes.md`：

- 服装识别：品类、颜色、可见面料外观、版型、设计细节和特色卖点。
- 人物表现：脚本中人物的身材、穿着效果、动作、表情和展示方式。
- 视频内容：脚本的场景、剧情、镜头和展示重点。
- 目标受众：结合服装风格判断适合的美国女性消费群体；大码女装优先考虑 Curvy / Plus Size 人群。
- 营销切入点：找到最能吸引消费者的一个卖点或场景，而不是简单复述画面。

## 发布文案

### 语言风格

- 平台为 TikTok，面向美国受众，使用地道、口语化、有情绪、有感染力的美式英语。
- 像美国本土穿搭博主分享好物，而不是品牌官方广告。
- 可以适当使用 OMG、WAIT、LOOK、Obsessed、NEED 等情绪表达，个别词可全大写强调；同一表达不要在相邻几条文案中反复出现。
- 全部使用英文，不输出中文翻译。

### 长度与 emoji

- 默认15–40个英文词，1–3句话；适合生活场景时可写8–15词的短句。不必每条凑成同样长度。
- 每条有1–3个与商品、情绪或场景相关的 emoji，例如 😍、✨、💕、💚、👒、☕。放在自然的停顿或句末，不用一长串符号代替文字。

### 开头 Hook

第一句话必须吸引注意力，不能平淡地介绍商品。根据商品和脚本选择切入方式，不固定套用同一个开头：

- 情绪惊喜：OMG, I am OBSESSED!
- 强烈推荐：Girl, you NEED to see this!
- 细节吸引：WAIT, can we talk about these sleeves?!
- 人群共鸣：Curvy girls, LOOK at this!
- 场景切入：Your next date-night outfit is HERE!
- 生活场景：Errands, but make it cute 💚
- 穿衣顾虑：先点出具体顾虑，再用可见设计回应。

以上句子只示范方向，不直接照抄；参照当前能取得的历史文案，变化开头句式。

### 核心卖点

- 只挑视频中最有吸引力的1–3个卖点，与脚本中的场景和情绪一致。
- 描述具体的服装细节，例如版型、腰线、裙摆、袖型、刺绣、图案、可见面料纹理，而不是泛泛地说漂亮。
- 把服装特点转化为消费者能感受到的穿搭价值，例如适合的场合、整体轮廓、搭配的轻松程度。
- 不复述全部分镜，不直接粘贴整段对白，不写型号、PID、核验和执行状态。
- 不虚构面料成分、柔软透气、保暖等级、弹性、尺码或其他无法从图片和已核验资料确认的特点；不做减重、改变体型等承诺，不使用身材羞辱。
- 人物和受众描述遵循实际参考与商品定位；只有商品或受众定位适合时才使用 Curvy / Plus Size 相关描述。

### 情绪与转化

- 文案要有种草感，让人产生购买兴趣；不要过度堆砌卖点，保持自然流畅。
- 根据脚本场景融入约会、派对、日常、通勤、度假、节日等穿搭场景，季节和节日必须与商品或脚本真实相关。
- 可以适当加入购买引导，例如 “Tap the orange cart”（仅限 TikTok Shop 上架商品）、“Check the link”、“Add this to your cart”。CTA 不固定，不要求每条都带，避免与近期文案使用相同结尾。
- 不虚构限时、折扣、价格或库存。

## 标签 tag

- 每条文案配一组5–7个英文 hashtag，默认5–6个；每项以 `#` 开头，项内无空格，彼此不重复。
- 按以下维度组合，具体标签根据每条视频内容动态选择，不机械复制；维度可按商品调整，不为凑齐类别添加无关词：

| 类型 | 作用 | 示例 |
|---|---|---|
| 商品品类 | 精准识别商品 | #MaxiDress |
| 服装特点 | 突出设计 | #FloralEmbroidery |
| 风格定位 | 覆盖穿搭兴趣 | #VintageFashion |
| 目标人群 | 精准触达用户 | #PlusSizeFashion |
| 穿搭场景 | 扩大搜索范围 | #DateNightOutfit |
| 平台购物 | 商品转化 | #TikTokShop |

- 至少2个标签体现当前商品或视频场景，避免整组都是 #Fashion、#OOTD、#FYP 之类宽泛标签。
- 大码、季节、节日、旅行和宠物标签必须与商品或脚本真实相关。宠物店拍猫咪毛衣可以用 #CatSweater，普通卫衣不要借用猫咪或宠物标签。
- 大小写优先使用易读的词首大写，例如 #StripedSweatshirt、#ErrandOutfit；历史大小写不一致不必照搬。
- #TikTokShop / #TikTokShopFinds 只在明确属于 TikTok Shop 商品时选用；#FYP 等泛标签不是必选，不宣称标签能保证推荐或销量。
- 文案和标签分别保存，不把 hashtag 再重复写进文案正文。

## 写法示例

以下为依据规则整理的创作示例，不是历史成片效果结论。每次必须根据当前商品和脚本重新创作。

**碎花长裙／约会**

文案：OMG, this dress is EVERYTHING! 😍 The floral embroidery and that flowing maxi silhouette make it such a dreamy pick for your next date night ✨

标签：#PlusSizeFashion #FloralMaxiDress #VintageStyle #DateNightOutfit #TikTokShop

**条纹卫衣／出门办事**

文案：Errands, but make it cute 💚 A longer hem, green stripes, and shoulder buttons give this everyday sweatshirt a little extra personality.

标签：#StripedSweatshirt #ShoulderButtons #ErrandOutfit #CasualStyle #OutfitInspo

**猫咪毛衣／宠物店偶遇**

文案：Came for cat toys, stayed for the sweater 🐾 Those little cat faces and the black-and-gray color blocking deserve a closer look.

标签：#CatSweater #CatLoverStyle #ColorBlockSweater #PetStoreOutfit #OutfitInspo

## 输出限制

- 每个视频只生成1条文案和1组标签，不提供多个版本供选择。
- 文案和标签全部使用英文，不输出中文翻译，不输出分析过程。
- 不重复使用套路化开头和结尾，根据每条视频的商品和脚本独立创作。
- 历史文案不足以对照时在 `execution-notes.md` 说明，不在发布文案里说明。

## 输出与保存

由撰写视频脚本的 Agent 同时创作文案和标签，不调用 Gemini 分析视频来生成。

- 文案通过 `run.py prepare --caption-text "英文发布文案"` 传入。
- 标签通过 `--hashtags "#TagOne" "#TagTwo" "#TagThree" "#TagFour" "#TagFive"` 传入，每个标签一个参数。
- 两者单独保存到 `post-copy.json` 的 `caption_english` 和 `hashtags`，后者为字符串数组；同时保存本规则文件名和 SHA-256 供追溯。
- 修改脚本涉及商品、场景或卖点时，同步更新发布文案与标签。
- “主体文案（英）”直接取 `prompt.txt` 第7部分“完整英文口播”正文；“主体文案（中）”直接取第8部分“完整中文参考”正文。去除章节标题，保留说话者、原文和换行，不翻译、不改写、不从成片反推。
- 视频生成后交由人工确认；不自动做 Gemini 音画质检，也不把未审核视频标记为审核通过。
