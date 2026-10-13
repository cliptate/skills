---
name: cliptate-long2shorts
description: 使用 Cliptate CLI 转写本地或 YouTube 长视频，由 agent 选择完整亮点并用 FFmpeg 生成带字幕的竖屏短视频。用户要求基于 Cliptate 把访谈、播客或长视频转成 Shorts、Reels、抖音或视频号短片时使用。
---

# Cliptate Long2Shorts

把长视频转成可交付的短片。Cliptate 负责本地转写，当前 agent 负责选段、翻译和文案，随附的 Python 标准库脚本用 FFmpeg 渲染、校验。不依赖 pycut，不把它的 `cut` 参数套给 Cliptate。

## 默认交付

- 每段 30–90 秒，按完整观点和句子边界剪切；用户指定的时长、数量和语言优先。随附渲染器支持 9:16，其他画幅需求需调整渲染方案，不强行套用默认画幅。
- 以 300 秒转写窗口辅助阅读，跨窗口保留上下文。选择最有价值且互不重复的观点，不要求每个窗口都产出短片。
- 1080×1920，保留完整源画面并填充竖屏；中心裁剪仅用于用户明确要求裁剪的任务。
- 英文来源默认加简体中文翻译，中文在上、白色，英文在下、橙色。中文来源默认原文字幕；其他语言按用户目标决定是否翻译。单语字幕为白色。
- 标题从首帧显示；对白字幕默认 0.5 秒后出现。参考风格使用 `Noto Sans CJK SC`，可改为已安装且覆盖目标文字的字体。
- 每段提供 MP4、ASS、两行 `summary.txt`（标题及 5–8 个标签）、封面、开头/中间/结尾截图和包含来源时间及段落 ID 的 `clip.json`。工作文件保存在用户选定的输出目录。

## 1. 确认输入和运行环境

读取 [运行环境与素材](references/runtime.md)，确认直装版 Cliptate、实际 helper 的 `--help`、Python 3.9+、ffprobe、带 libass 的 FFmpeg 和字体。用户只给 YouTube 链接时使用 yt-dlp 下载本地素材；已经提供本地视频时直接使用。模型和输出放在项目之外的合适目录，不进入技能仓库。

明确来源语言、输出位置及用户给出的限制。缺少可选偏好时采用上述默认值，告知关键假设即可。创建新项目目录以避免覆盖已有素材。

## 2. 用 Cliptate 转写一次

`SKILL_DIR` 指此 SKILL.md 所在文件夹，`SOURCE_VIDEO` 指绝对来源路径，`PROJECT_DIR` 指项目目录。脚本运行前将这些变量设为实际路径：

```sh
python3 "$SKILL_DIR/scripts/transcribe.py" "$SOURCE_VIDEO" \
  --output "$PROJECT_DIR/transcript.json" --check-only

python3 "$SKILL_DIR/scripts/transcribe.py" "$SOURCE_VIDEO" \
  --output "$PROJECT_DIR/transcript.json" --language en
```

默认使用应用 ASR 模型、VAD、分段和对齐设置；按需要传入 `--model`、`--language`、`--cli`、`--app`。模型下载通过显式 `--download` 允许，不另行下载 Qwen/Python 权重。`--check-only` 不启动推理，也不能证明模型已经可用。

脚本保存 Cliptate 原始 `{files:[...]}` JSON 和 `transcript.windows.json`。复用已有转写时用 `--reuse`，修改模型/语言时重新转写。失败不会发布新的转写文件；进度在 stderr。CLI 转写不新增应用历史记录。

**时间精度：** 公开 CLI 的 JSON 只有段落 `id/text/start/end`，没有词级时间戳；即使应用开启了对齐，也不能把输出宣称为逐词时间轴。保留来源绝对时间和原始段落 ID，优先把切点放在完整段落外的停顿。先听看候选的开头和结尾，确认没有切掉词语或必要语境。

## 3. 选取亮点并完成字幕

读完整的分析窗口及相邻上下文；优先选择独立成立的观点、冲突、具体故事、惊人事实或清晰结论。避免重复观点、脱离上下文的指代，以及停在铺垫、连词、问题或半句话上的结尾。不要拼接无关句子制造原视频没有表达的意思。

为每个候选记录来源起止时间、选取理由、标题和标签。当前 agent 在邻近上下文中直接翻译，保持专有名词、语义和口语节奏，不把润色后的句子当成原话。译文按原始段落 ID 映射，不能依赖数组位置；段落跨 300 秒窗口时只计算一次。

渲染器拒绝从段落内部切断，也会拒绝超出安全字幕区域的长文本。需要更细字幕时，先核对音频并改进应用的分段设置后重新转写，或人工核准更细的时间轴；不要把长段落平均分配时间伪造词级对齐。

## 4. 清单驱动渲染

读取 [渲染清单](references/manifest.md)，按真实段落 ID 写 `render_manifest.json`。所有相对路径从清单所在目录解析。只预览第一段的请求使用 `--only 1`，不要继续渲染其他段：

```sh
python3 "$SKILL_DIR/scripts/render_clips.py" "$PROJECT_DIR/render_manifest.json" --check-only
python3 "$SKILL_DIR/scripts/render_clips.py" "$PROJECT_DIR/render_manifest.json" --only 1
# 用户需要所有短片时：
python3 "$SKILL_DIR/scripts/render_clips.py" "$PROJECT_DIR/render_manifest.json"
```

脚本精确定位来源区间并重新编码为 H.264/AAC，减去片段起点后生成相对时间字幕，一次编码完成画面和字幕渲染。默认保护已有输出，`--force` 只替换可识别的本技能产物；渲染和自动校验成功后才发布。再次渲染全清单时已有短片会报错，若需要替换它们须使用 `--force`，或用 `--only` 渲染尚未生成的段落。

## 5. 复核后交付

```sh
python3 "$SKILL_DIR/scripts/validate_output.py" "$PROJECT_DIR/clips/part001"
```

自动校验检查视频/音频流、分辨率、时长、字幕时间、摘要及预览文件；它不能证明翻译正确、实际字形无缺失或剪辑语意完整。

查看封面与开头/中间/结尾截图，确认字体、行宽、配色、字幕上下顺序、主体未被裁掉、首帧无对白字幕。听看开头和结尾，确认切点、音画同步和观点完整。长字幕或密集对话还需抽查相应时段。发现错误先修清单、字幕或转写，再重渲染受影响的短片。

交付视频、summary.txt、代表截图的可点击链接，说明每段来源区间及已完成的检查。只生成或预览，不发布到平台。没有合适的完整片段、下载失败或模型不可用时，报告实际阻碍及已有有效产物。
