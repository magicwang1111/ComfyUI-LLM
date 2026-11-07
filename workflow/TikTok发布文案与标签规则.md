# TikTok 发布文案与标签规则

本文件控制数据库“文案”和“标签 tag”的生成，可直接修改，下一次任务读取最新内容。它独立于视频脚本规范，不决定人物、镜头或口播，也不进入 WAN 的视频提示词。

## 来源与历史风格

2026-11-07 对现有数据库未删除记录进行统计：161条记录中140条有文案或标签，来自 bnmb（75条）和 wset（65条）。140条发布文案中122条含 emoji，英文长度中位数约25词；138条使用5个标签，另2条使用4个标签。样本没有发布效果数据，以下总结代表历史写法，不代表流量或转化效果。

历史主要有两种写法：

- 痛点或发现式：先提出具体穿衣顾虑或表达发现新搭配的惊喜，再写一两个可见设计和适合的场景。早期部分文案较长。
- 生活场景式：一句轻松的日常体验，配一个相关 emoji。例如 wset/B64 的 “A sun hat, a flowy dress, and nowhere to rush 👒”，以及 wset/B66 的 “Coffee stop, outfit check, back to exploring ☕”。例子只展示语气，不作为固定句式或其他商品的事实。

历史常见标签包括 #PlusSizeFashion、#OutfitInspo、#PlusSizeStyle、#OOTD、#EverydayStyle、#FashionFinds、#CasualStyle 和 #TikTokShop。历史也有笼统的 #FYP、夸大显瘦或未经确认的面料描述，后续不机械沿用。

## 发布文案

- 平台为 TikTok，面向美国受众，使用自然、口语化的英语。
- 默认15–35个英文词，1–2句话；适合生活场景时可写8–15词的短句。不必每条凑成同样长度。
- 每条必须有1–3个与商品、情绪或场景相关的 emoji，例如 💚、✨、🐾、👒、☕。让 emoji 出现在自然的停顿或句末，不用一长串符号代替文字。
- 优先选择“生活场景＋商品细节”或“具体穿衣顾虑＋可见设计回应”。开头有明确内容，避免每条重复 “Obsessed”“Must-have”“The perfect…” 等泛化说法。
- 只挑一两个当前商品的可见亮点，配合脚本中的场景和情绪。不要复述全部分镜，不直接粘贴整段对白，不写型号、PID、核验和执行状态。
- 购买引导按语境选用；可自然邀请查看链接，不要求每条必须带CTA，不虚构链接位置、限时、折扣、价格或库存。
- 人物描述遵循实际参考和任务要求，不自动把所有角色写成欧美大码女性。只有商品或受众定位适合时才使用大码相关描述。
- 不宣称未经确认的面料成分、柔软透气、保暖等级、弹性或功能性；不做减重、改变体型等承诺，不使用身材羞辱。
- 参照当前能取得的历史文案，变化开头、亮点、句式及 emoji。历史不足时在 execution-notes.md 说明，不在发布文案里说明。

## 标签 tag

- 默认恰好5个英文 hashtag，每项以 `#` 开头，项内无空格，彼此不重复。
- 优先覆盖商品品类、具体设计或风格、视频场景、适用受众和穿搭发现；维度可按商品调整，不为凑齐类别添加无关词。
- 至少2个标签体现当前商品或视频场景，避免整组都是 #Fashion、#OOTD、#FYP 之类宽泛标签。
- 大码、季节、节日、旅行和宠物标签必须与商品或脚本真实相关。宠物店拍猫咪毛衣可以用 #CatSweater，普通卫衣不要借用猫咪或宠物标签。
- 大小写优先使用易读的词首大写，例如 #StripedSweatshirt、#ErrandOutfit；历史大小写不一致不必照搬。
- #TikTokShop / #TikTokShopFinds 只在明确属于 TikTok Shop 商品时选用；#FYP 等泛标签不是必选，不宣称标签能保证推荐或销量。
- 文案和标签分别保存，不把 hashtag 再重复写进文案正文。

## 写法示例

以下为依据规则整理的创作示例，不是历史成片效果结论。每次必须根据当前商品和脚本重新创作。

**条纹卫衣／出门办事**

文案：Errands, but make it cute 💚 A longer hem, green stripes, and shoulder buttons give this everyday sweatshirt a little extra personality.

标签：#StripedSweatshirt #ShoulderButtons #ErrandOutfit #CasualStyle #OutfitInspo

**猫咪毛衣／宠物店偶遇**

文案：Came for cat toys, stayed for the sweater 🐾 Those little cat faces and the black-and-gray color blocking deserve a closer look.

标签：#CatSweater #CatLoverStyle #ColorBlockSweater #PetStoreOutfit #OutfitInspo

## 输出与保存

由撰写视频脚本的 Agent 同时创作文案和标签，不调用 Gemini 分析视频来生成。

- 文案通过 `run.py prepare --caption-text "英文发布文案"` 传入。
- 标签通过 `--hashtags "#TagOne" "#TagTwo" "#TagThree" "#TagFour" "#TagFive"` 传入。
- 两者单独保存到 `post-copy.json` 的 `caption_english` 和 `hashtags`，后者为字符串数组；同时保存本规则文件名和 SHA-256 供追溯。
- 修改脚本涉及商品、场景或卖点时，同步更新发布文案与标签。
- “主体文案（英）”直接取 `prompt.txt` 第7部分“完整英文口播”正文；“主体文案（中）”直接取第8部分“完整中文参考”正文。去除章节标题，保留说话者、原文和换行，不翻译、不改写、不从成片反推。
- 视频生成后交由人工确认；不自动做 Gemini 音画质检，也不把未审核视频标记为审核通过。
