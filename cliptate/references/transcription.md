# 转写与字幕

## 常用调用

```sh
# 使用应用当前设置，输出纯文本
cliptate transcribe "interview.mp4"

# 获取可分析的分段结果
cliptate transcribe "interview.mp4" --format json

# 单文件字幕
cliptate transcribe "interview.wav" --format srt --output "interview.srt"

# 多文件分别生成字幕；输出目录会自动创建
cliptate transcribe "a.wav" "b.mp4" --format vtt --output-dir "subtitles"

# 单次指定中文模型，允许下载所需 ASR、VAD、对齐模型
cliptate transcribe "recording.wav" --model qwen3-asr-0.6b-8bit --language zh --download

# 禁用本次词典，或处理以连字符开头的文件名
cliptate transcribe "recording.wav" --language auto --no-dictionary
cliptate transcribe --format json -- -recording.wav
```

输入必须是可读的本地音频/视频路径，如 WAV、MP3、MP4。转写不接收 URL 或 stdin；远程媒体需要先按用户任务取得本地文件。相对路径按调用时的工作目录解析。

## 参数选择

| 参数 | 用途与限制 |
| --- | --- |
| `-f` / `--format` | `text`（默认）、`json`、`srt`、`vtt`、`markdown` |
| `-o` / `--output` | 单个输入的输出文件；不能和 `--output-dir` 合用 |
| `--output-dir` | 每个输入生成一份文件；多输入 SRT/VTT 必须使用 |
| `--overwrite` | 允许替换已有输出；输入文件始终受保护 |
| `--model` | ASR 的原始 `ModelVariant` ID，如 `qwen3-asr-0.6b-8bit`、`parakeet-v3`；不是显示名或 Hugging Face 仓库路径 |
| `--language` | 应用语言代码，如 `auto`、`en`、`zh`、`ja`、`ko`、`de`、`es`、`fr`；选定模型必须支持它 |
| `--no-dictionary` | 跳过本次识别词典 |
| `--download` | 允许下载缺失的推理依赖模型 |
| `--` | 后续参数全部作为输入路径，其他选项放在它前面 |

分段、VAD、强制对齐和说话人信息沿用应用的现有管线。需要精确词级时间时先确认应用的对齐设置；CLI 没有单独的对齐、声道或说话人命名参数。Whisper 需要明确支持的语言，不能假定每个模型都支持 `auto`。

默认把结果写入 stdout。指定 `--output` 或 `--output-dir` 后，结果写文件，stdout 不再提供对应的结果 JSON。目录输出使用输入 basename 加 `.txt`、`.json`、`.srt`、`.vtt`、`.md`；例如 `a.wav` 和 `a.mp4` 会发生 basename 冲突，需要调整命名或分开调用。单个输出的父目录应事先存在。

`text` 给出纯转写内容；`markdown` 给出时间戳及管线可用的说话人信息。多输入 text/markdown 在 stdout 带文件标题。字幕只有时间与文字，不能据此声称已完成视频剪辑。

## 解析 JSON 与部分失败

单文件、多文件以及保存的 JSON 都使用 `files` 数组：

```json
{
  "files": [
    {
      "file": "/path/to/interview.wav",
      "model": "qwen3-asr-0.6b-8bit",
      "duration": 1.42,
      "segments": [
        {"id": "segment-id", "text": "你好。", "start": 0, "end": 1.42, "speakerId": 0}
      ]
    },
    {"file": "/path/to/missing.wav", "segments": [], "error": "File not found"}
  ]
}
```

`start`、`end`、`duration` 单位是秒；`speakerId` 从 0 开始。`model`、`duration`、`speakerId`、`error` 可能缺省，不能强制要求存在。

需要自动化时直接捕获进程结果，不把 CLI 管道接到其他命令后只检查最后一段退出码。例如 Python：

```python
import json
import subprocess

result = subprocess.run(
    ["cliptate", "transcribe", "a.wav", "b.mp4", "--format", "json"],
    capture_output=True, text=True,
)
payload = json.loads(result.stdout) if result.stdout.strip() else None
files = payload["files"] if payload else []
successful = [item for item in files if "error" not in item]
failed = [item for item in files if "error" in item]
# 联合 result.returncode、failed 和 result.stderr 判断，保留 successful。
```

stdout 的批量 JSON 在所有输入处理完后才输出。退出码 `1` 可能包含成功条目；初始化失败可能没有 JSON。中断后的 JSON 只含已完成的输入，正在取消的输入没有条目。记录请求的输入清单，才能识别尚未完成的文件。需要重试时只重新提交确认失败且仍需处理的输入。
