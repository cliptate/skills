---
name: cliptate
description: 通过 Cliptate macOS CLI 转写本地音视频、导出字幕、合成语音、管理识别词典或查询历史纠错记录。用户指定 Cliptate 或 cliptate 命令行自动化时使用；不用于修改 Cliptate 源码。
---

# Cliptate CLI

使用直装版 Cliptate 自带的 `cliptate` 命令完成用户任务。CLI 会按需在后台启动应用，共享应用的配置与模型运行时；不是独立推理程序。需要 Apple Silicon Mac、macOS 15 或更新版本及 GitHub/直接下载版应用。App Store 版不提供 CLI 服务。

## 确认可用入口

先执行以下只读命令，确认实际使用的版本和功能：

```sh
command -v cliptate
cliptate --version
cliptate --help
```

以当前可执行文件的帮助信息为准。旧版可能只有 `transcribe` 和 `dictionary`；`--version` 的协议号不能证明支持 TTS 或 history。需要 `tts` 或 `history` 时检查顶层帮助是否列出它们，子命令 `--help` 可能返回同一份全局帮助。缺少所需功能时说明需要更新直装版应用，并在更新后重启应用。

如果 PATH 中没有命令，可以直接调用已找到的应用内 helper，无需先修改 shell 配置：

```sh
"/Applications/Cliptate.app/Contents/Helpers/cliptate" --help
```

将示例路径换成实际应用路径。需要持久安装时，使用应用「设置 → 命令行」提供的命令：它把 helper 链接到 `~/.local/bin/cliptate`，保留已有命令。先把应用移到最终位置，再安装链接；必要时将 `~/.local/bin` 加入 PATH。

`CLIPTATE_APP` 选择连接的应用；它不替换正在执行的 CLI 二进制：

```sh
CLIPTATE_APP="/path/to/Cliptate Dev.app" cliptate dictionary list
```

嵌入式 helper 默认连接所在应用，独立 CLI 默认寻找生产应用。开发版与生产版的配置、词典、历史彼此独立。要使用新版命令和开发数据，优先调用开发应用自己的 helper，避免仅设置环境变量却仍执行旧命令。

## 按任务读取参考

| 用户目标 | 命令 | 读取参考 |
| --- | --- | --- |
| 转写音频/视频、批量转写、生成 SRT/VTT 或带时间戳文本 | `transcribe` | [转写与字幕](references/transcription.md) |
| 朗读文本、配音、指定说话人、声音设计或克隆声音 | `tts` | [语音合成](references/tts.md) |
| 增删/导入/导出识别词汇、查看历史、从纠错记录学习词汇 | `dictionary`、`history` | [词典与历史](references/dictionary-history.md) |

当前公开 CLI 没有剪辑视频、烧录字幕、导出 FCPXML、翻译、录音、触发 GUI 的 AI Cut 或修改持久模型配置的命令。这些目标应说明 CLI 的能力边界；不要套用另一套旧 `cut` CLI 的参数。SRT/VTT 导出只生成字幕文件。

## 调用与完成判断

- 路径、文本和词组作为独立参数传递；shell 中引用带空格的值。选项和值分开，例如 `--format json`。
- 自动化优先使用 JSON，分别捕获 stdout、stderr 和退出码。进度在 stderr，不能用 `2>&1` 混入 JSON。词典和历史命令本来就返回 JSON。
- 默认沿用应用设置，按用户需要使用单次覆盖参数。转写/TTS 的覆盖不更改保存的设置，也不新增项目或历史条目；词典增删/导入会持久保存。
- 缺失模型默认报错。需要下载时使用 `--download`；离线任务保留默认行为。该标志只允许按需下载，不是独立模型管理命令。
- 同一应用一次只运行一个 CLI 转写或 TTS 请求；串行安排推理，或把文件作为一次转写的多个输入。词典和历史读取可在推理期间使用。

| 退出码 | 处理 |
| --- | --- |
| `0` | 根据响应确认目标输出存在，并返回文件路径或请求的结果 |
| `1` | 执行/文件失败；批量转写可能部分成功，逐项检查 `files[].error` |
| `2` | 参数错误；对照当前帮助修正命令 |
| `130` | 已中断；保留已完成结果，不自动重新提交 |

转写没有固定执行超时，首次连接重试窗口约 30 秒。Ctrl+C/SIGTERM 协作取消；运行时退出前仍占用推理位置。连接中断后不要盲目重试词典写入，先读取当前词典核实是否已提交。输出覆盖使用 `--overwrite`，仅在用户目标包含替换该输出时添加。

## 维护依据

本技能根据 Cliptate 的 `docs/cli.md`、`Sources/CliptateCommand/CliptateCommand.swift` 和 `Sources/Cliptate/CLIShared/CLICommand.swift` 编写。维护时核对这些入口与实际 `cliptate --help`；本地版本可落后于源码。不要用 `Sources/Cliptate/Services/CliptateCLI.swift` 的旧参数替代公开 helper 的参数。
