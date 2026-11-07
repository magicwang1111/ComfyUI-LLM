# 视频规则文件的维护与检查

每份视频规则独立保存为节点 `workflow/` 目录内的一份 Markdown 文件。新增规则只需新增 `.md`，无需注册表、JSON 配置或新的 Python 分支。默认仍使用 [欧美大码女装规范](../../../workflow/欧美大码女装_TikTok视频脚本_完整规范.md)，不复制正文。

在用户请求中单独写一行选择文件（相对于 `workflow/`，支持子目录）：

```text
规则文件：开箱视频规则.md
按照这份规则生成视频。
```

上面的开箱文件名仅为示例，需要先创建对应文件。也可指定 `workflow/` 内文件的绝对路径。没有指定文件时使用现有女装规范；指定文件不存在则报错，不回退到其他规则。一次任务选择一份规则。

Agent Node 每次执行都通过 `fashion_prompt.py` 读取所选文件全文并注入模型指令，自动将同一文件传给 prepare/submit。不要在 Agent 的脚本参数中重复添加 `--rules-file`。本次用户明确要求只覆盖对应部分。规则文件可使用各自的章节、语言和拍摄要求，不必统一为女装的十三部分。

独立命令在节点根目录运行：

```text
python fashion_prompt.py list
python fashion_prompt.py show --rules-file "开箱视频规则.md"
python fashion_prompt.py check --rules-file "开箱视频规则.md" --prompt RUN/prompt.txt --duration 15
```

独立 CLI 的 `run.py prepare` 同样支持 `--rules-file`；`run.py submit` 未传此参数时继承准备阶段的文件，显式换文件需重新 prepare。Agent 外部使用本技能时，也须先读取所选规范全文。

`prompt-review.json` 与 `prompt-submit-review.json` 保存所选文件名、规范全文及 SHA-256、提示词 SHA-256 和辅助检查结果。新增或修改 Markdown 无需重启，下一次执行读取最新内容。

辅助检查会识别 Markdown 中以“输出结构”结尾的二级标题，以及其中的 `1. 标题：说明` 或 `1. 标题` 列表；这只是可选的机器检查格式，不是所有规则必须采用的模板。只有文档列出的章节才参与检查；英文口播预算只检查文档定义的“英文口播”部分。未识别结构时会说明跳过检查，模型仍须审核全文。女装文档中的集中翻译要求按其中明确写出的句子检查，其他文档不自动继承。

结构检查是提示，不能证明 Hook、商品事实、去重或成片合规。历史去重使用可用 catalog 口播及历史脚本；无历史或记录不全须说明范围。实际时长、帧率、音频和视觉表现以成片检测为准。
