# 语音合成

先确认实际 `cliptate --help` 中有 `tts`。所有调用需要输出 `.wav`，文本来源三选一：`--text TEXT`、`--text-file PATH`、`--text-file -`（stdin）。

## 常用调用

```sh
# 沿用应用的 TTS 模型与适用的声音设置
cliptate tts --text "你好，欢迎使用 Cliptate。" --language zh -o "speech.wav" --format json

# 从 UTF-8 文件或 stdin 读取
cliptate tts --text-file "narration.txt" -o "narration.wav" --format json
printf '%s' 'Hello world.' | cliptate tts --text-file - -o "hello.wav" --format json

# CustomVoice：指定说话人及情绪
cliptate tts --text "Hello!" -o "cheerful.wav" \
  --model qwen3-tts-0.6b-customvoice-8bit --language en \
  --voice Ryan --emotion "cheerful" --download --format json

# VoiceDesign：自然语言描述声音
cliptate tts --text "欢迎收听。" -o "designed.wav" \
  --model qwen3-tts-1.7b-voicedesign-8bit --language zh \
  --voice "A warm, calm narrator" --download --format json

# Base：明确提供参考音频及其中实际说出的文字
cliptate tts --text "A new sentence." -o "cloned.wav" \
  --model qwen3-tts-0.6b-base-8bit --language en \
  --reference-audio "reference.wav" \
  --reference-text "The words spoken in reference.wav." --download --format json
```

将克隆示例的参考文字替换成实际音频的逐字内容。应用已保存的 GUI 参考音频不会隐式用于 CLI。

## 参数与模型族

| 参数 | 含义 |
| --- | --- |
| `-o` / `--output` | 必填 `.wav` 路径，父目录必须存在，不支持 `-` 输出音频 |
| `--model` / `--tts-model` | TTS 模型 ID、对应的 `ModelVariant` ID 或 Hugging Face 仓库；默认应用设置 |
| `--language` | `auto`、`en`、`zh`、`ja`、`ko`、`de`、`fr`、`ru`、`pt`、`es`、`it` |
| `--variant` | `automatic`、`short`、`extended`，默认应用设置；不是固定时长保证 |
| `--voice` | CustomVoice 的说话人名，或 VoiceDesign 的描述 |
| `--emotion` | CustomVoice 的情绪/风格描述 |
| `--reference-audio` + `--reference-text` | Base 克隆声音，必须成对提供 |
| `--download` | 允许下载缺失 TTS 模型 |
| `--overwrite` | 合成成功后替换已有输出 |
| `--format json` | 输出音频元数据 JSON；不指定则打印绝对输出路径 |

CustomVoice 说话人：`Vivian`、`Serena`、`Uncle_Fu`、`Dylan`、`Eric`、`Ryan`、`Aiden`、`Ono_Anna`、`Sohee`。VoiceDesign 的 `--voice` 是描述，不是枚举值。Base 不提供参考音频时使用默认声音；克隆参数不能与 `--voice` 或 `--emotion` 合用。按模型族选择参数，不能把旧 CLI 的 `--lang-code`、`--prompt-text`、`--speed` 等参数混入这里。

## 输入和完成判断

文本必须是非空 UTF-8，最大 1 MiB，可带 UTF-8 BOM。输出为模型原生采样率的单声道 float32 WAV。现有输出默认受保护；文本文件和参考音频不能被输出覆盖，包括符号链接别名。失败或取消保留已有输出。

成功 JSON 示例：

```json
{"file": "/absolute/speech.wav", "model": "qwen3-tts-0.6b-customvoice-8bit", "bytes": 123456}
```

检查退出码、绝对 `file` 路径和实际文件大小，向用户提供 WAV 路径。JSON 不包含音频内容。进度/错误在 stderr；Ctrl+C/SIGTERM 在读 stdin 时也可取消并返回 `130`。CLI 合成不会新增历史记录或更改保存的 TTS 设置。
