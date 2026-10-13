# Cliptate Skills

通过 macOS 命令行调用 [Cliptate](https://github.com/cliptate/cliptate) 的 agent 技能。

**语言：** [English](../README.md) · 简体中文 · [日本語](README.ja.md) · [한국어](README.ko.md) · [Deutsch](README.de.md)

## 可用技能

| 技能 | 功能 |
| --- | --- |
| [cliptate](../cliptate/SKILL.md) | 转写本地音视频、导出字幕、合成语音、管理识别词典、查询历史与纠错证据 |
| [cliptate-long2shorts](../cliptate-long2shorts/SKILL.md) | 把长视频转为竖屏亮点短片：Cliptate 转写、agent 选段与翻译、FFmpeg 渲染 |

技能包含命令示例、JSON 处理、分页、部分失败处理和版本检查。目前技能说明使用简体中文编写，agent 可以据此处理其他语言的请求。本仓库提供 agent 指令，Cliptate 应用需单独安装。

## 运行要求

- Apple Silicon Mac，macOS 15 或更新版本。
- GitHub/直接下载版 Cliptate；App Store 版不提供 CLI 服务。
- `cliptate --help` 中包含所需命令的 CLI 版本；旧版可能没有 `tts` 或 `history`。
- 所需模型已下载；允许下载模型的任务可使用 `--download`。
- `cliptate-long2shorts` 还需 Python 3.9+、ffprobe、带 libass 的 FFmpeg 及字幕字体；YouTube 来源另需 yt-dlp。

## 安装与使用

克隆本仓库，把需要的完整技能文件夹 `cliptate/` 或 `cliptate-long2shorts/` 复制到 Codex 的 `~/.codex/skills/`，保留其中所有 `references/`、`agents/`、`scripts/` 子目录。两项技能可独立安装。如果目标已存在，先检查内容再决定是否替换。其他 agent 使用各自支持的技能目录。Codex 会在下一轮对话中发现技能。

在 Cliptate 中打开「**设置 → 命令行**」，使用面板提供的安装命令，将 helper 链接到 `~/.local/bin`。确保该目录位于 PATH，或直接调用应用包内的 helper。检查实际命令：

```sh
cliptate --version
cliptate --help
```

调用示例：

```text
使用 $cliptate 转写 interview.mp4，并保存为 interview.srt。
使用 $cliptate 将 narration.txt 合成为 narration.wav。
使用 $cliptate 分析最近的历史纠错记录，把可信的新词加入词典。
使用 $cliptate-long2shorts 将 interview.mp4 做成三段 30–90 秒的竖屏双语短片，先预览第一段。
```

公开 CLI 导出 SRT/VTT 字幕文件，不提供视频剪辑或字幕烧录。命令使用选定应用的设置；转写和语音合成不新增历史记录，词典修改会持久保存。

`cliptate-long2shorts` 用 FFmpeg 补齐视频剪辑与字幕渲染，默认保留完整源画面并填充竖屏，交付 MP4、ASS、两行摘要、封面/预览截图及来源区间元数据。Cliptate CLI 提供段落时间戳，流程不宣称逐词精度，也不发布到平台。

## 参考文档

- [技能入口](../cliptate/SKILL.md)：确认 CLI、选择工作流、判断结果。
- [转写与字幕](../cliptate/references/transcription.md)：输入、格式、输出路径与批量 JSON。
- [语音合成](../cliptate/references/tts.md)：文本来源、模型族、声音设计/克隆与 WAV 输出。
- [词典与历史](../cliptate/references/dictionary-history.md)：词汇操作、历史分页与纠错学习。
- [短视频工作流](../cliptate-long2shorts/SKILL.md)、[运行环境](../cliptate-long2shorts/references/runtime.md)与[渲染清单](../cliptate-long2shorts/references/manifest.md)。

维护时将实际 helper 的帮助信息与[上游 CLI 文档](https://github.com/cliptate/cliptate/blob/main/docs/cli.md)及参数解析器对照；当前源码中的功能可能尚未包含在已安装的应用中。
