# Cliptate Skills

用于 [Cliptate](https://github.com/cliptate/cliptate) 转写、短视频制作及 Final Cut Pro FCPXML 工作流的 agent 技能。

**语言：** [English](../README.md) · 简体中文 · [日本語](README.ja.md) · [한국어](README.ko.md) · [Deutsch](README.de.md)

## 可用技能

| 技能 | 功能 |
| --- | --- |
| [cliptate](../cliptate/SKILL.md) | 转写本地音视频、导出字幕、合成语音、管理识别词典、查询历史与纠错证据 |
| [cliptate-long2shorts](../cliptate-long2shorts/SKILL.md) | 把长视频转为竖屏亮点短片：Cliptate 转写、agent 选段与翻译、FFmpeg 渲染 |
| [fcpxml](../fcpxml/SKILL.md) | 构建与校验 FCPXML、便携媒体打包、基于 Cliptate 转写粗剪、导入 Final Cut Pro |

技能包含命令示例、JSON 处理、分页、部分失败处理和版本检查。技能说明使用简体中文或英文编写，agent 可以据此处理其他语言的请求。本仓库提供 agent 指令，Cliptate 应用需单独安装。

## 运行要求

以下 Cliptate 要求适用于转写。`fcpxml` 脚本需要 Python 3.9+、`xmllint` 和精确匹配的 DTD；导入及自动查找 DTD 需要 Final Cut Pro。只有新生成转写时才需要 Cliptate。

- Apple Silicon Mac，macOS 15 或更新版本。
- GitHub/直接下载版 Cliptate；App Store 版不提供 CLI 服务。
- `cliptate --help` 中包含所需命令的 CLI 版本；旧版可能没有 `tts` 或 `history`。
- 所需模型已下载；允许下载模型的任务可使用 `--download`。
- `cliptate-long2shorts` 还需 Python 3.9+、ffprobe、带 libass 的 FFmpeg 及字幕字体；YouTube 来源另需 yt-dlp。

## 安装与使用

### 使用 npx 安装

安装 Node.js 和 npm 后，可以通过 [skills CLI](https://github.com/vercel-labs/skills) 交互选择技能和目标 agent：

```sh
npx skills add cliptate/skills
```

为 Codex 全局安装两个技能：

```sh
npx skills add cliptate/skills --agent codex --global --skill cliptate --skill cliptate-long2shorts
```

`--global` 让技能可在所有项目中使用；省略该参数则安装到当前项目。只需要 `cliptate` 时，去掉 `--skill cliptate-long2shorts`。使用 `cliptate-long2shorts` 时需同时安装两个技能，因为它依赖 `cliptate` 转写。其他 agent 可通过交互选择，或将 `--agent` 改为对应的受支持标识。

检查、校验、打包或导入 FCPXML 时，可单独安装 `fcpxml`：

```sh
npx skills add cliptate/skills --agent codex --global --skill fcpxml
```

粗剪需要新转写时，再添加 `--skill cliptate`，将 `cliptate/` 与 `fcpxml/` 安装到同一技能目录；已有对齐转写时无需 Cliptate。手动安装时复制完整的 `fcpxml/` 文件夹，包含脚本和参考文档。

### 手动安装

克隆本仓库，把需要的完整技能文件夹 `cliptate/`、`cliptate-long2shorts/` 或 `fcpxml/` 复制到 Codex 的 `~/.codex/skills/`，保留其中所有 `references/`、`agents/`、`scripts/` 子目录。`cliptate` 可独立使用；`cliptate-long2shorts` 复用 `cliptate` skill 转写，需要将两个文件夹安装到同一技能目录。如果目标已存在，先检查内容再决定是否替换。其他 agent 使用各自支持的技能目录。Codex 会在下一轮对话中发现技能。

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
使用 $fcpxml，结合 Cliptate 转写粗剪 interview.fcpxmld，交付已校验的便携工程包。
```

公开 CLI 导出 SRT/VTT 字幕文件，不提供视频剪辑或字幕烧录。命令使用选定应用的设置；转写和语音合成不新增历史记录，词典修改会持久保存。

`cliptate-long2shorts` 用 FFmpeg 补齐视频剪辑与字幕渲染，默认保留完整源画面并填充竖屏，交付 MP4、ASS、两行摘要、封面/预览截图及来源区间元数据。Cliptate CLI 提供段落时间戳，流程不宣称逐词精度，也不发布到平台。

## 参考文档

- [技能入口](../cliptate/SKILL.md)：确认 CLI、选择工作流、判断结果。
- [转写与字幕](../cliptate/references/transcription.md)：输入、格式、输出路径与批量 JSON。
- [语音合成](../cliptate/references/tts.md)：文本来源、模型族、声音设计/克隆与 WAV 输出。
- [词典与历史](../cliptate/references/dictionary-history.md)：词汇操作、历史分页与纠错学习。
- [短视频工作流](../cliptate-long2shorts/SKILL.md)、[运行环境](../cliptate-long2shorts/references/runtime.md)与[渲染清单](../cliptate-long2shorts/references/manifest.md)。
- [FCPXML 工作流](../fcpxml/SKILL.md)、[Cliptate 转写粗剪](../fcpxml/references/rough-cut.md)、[校验](../fcpxml/references/validation.md)与[便携打包](../fcpxml/references/portability.md)。

维护时将实际 helper 的帮助信息与[上游 CLI 文档](https://github.com/cliptate/cliptate/blob/main/docs/cli.md)及参数解析器对照；当前源码中的功能可能尚未包含在已安装的应用中。
