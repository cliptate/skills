# 运行环境与素材

## 本地依赖

转写的应用与 CLI 环境由 [cliptate skill](../../cliptate/SKILL.md) 管理；需要生成转写时读取其 [转写说明](../../cliptate/references/transcription.md)。本技能的渲染脚本需要 Python 3.9+，只用标准库，另外需要 ffprobe、带 libass 的 FFmpeg 和字幕字体。

```sh
python3 --version
ffprobe -version
ffmpeg -hide_banner -filters
fc-match -f '%{family}\n%{file}\n' 'Noto Sans CJK SC'
```

渲染器检测 PATH 中的 FFmpeg 及 Homebrew 的稳定 `opt/ffmpeg-full/bin/ffmpeg` 路径，选择具备 libass `ass` 滤镜的版本。也可以用 `render_clips.py --ffmpeg /absolute/path/to/ffmpeg`。优先检查现有安装，缺少依赖时再按当前环境安装，避免硬编码 Cellar 版本。

确认字体查询返回的实际 family，不要把字体回退当成指定字体已经安装。没有 fc-match 时可在系统字体目录检查，并在预览中核对实际字形。字体缺失时安装目标字体，或在清单 `settings.font` 选择覆盖目标文字的现有字体。字体名的自动校验不能证明 libass 实际没有回退。

## 素材与目录

本地来源优先。YouTube 来源用 yt-dlp 下载最高 1080p，保留源 URL 和视频 ID；输出目录由用户选择，未指定时创建带时间戳的独立项目目录。

下列命令中的 `PROJECT_DIR` 为项目目录的绝对路径，`YOUTUBE_URL` 为用户提供的视频链接；运行前设为实际值。

```sh
mkdir -p "$PROJECT_DIR/source"
yt-dlp --no-playlist \
  -f 'bv*[height<=1080][vcodec^=avc1]+ba[acodec^=mp4a]/bv*[height<=1080]+ba/b[height<=1080]' \
  --merge-output-format mp4 \
  -o "$PROJECT_DIR/source/%(id)s.%(ext)s" \
  "$YOUTUBE_URL"
```

根据实际生成的文件设定 `SOURCE_VIDEO`，不要假定所有格式回退都产生同一编码。用 ffprobe 确认音频流、视频流和时长。如果下载失败，检查 yt-dlp 错误中的认证、网络或格式问题；需要账号操作时留给用户，不自动读取浏览器 cookies 或重复重试登录受限请求。

典型项目产物：

```text
project/
├── source/video.mp4
├── transcript.json
├── render_manifest.json
└── clips/part001/
    ├── video.mp4
    ├── subtitles.ass
    ├── summary.txt
    ├── cover.png
    ├── preview-start.png
    ├── preview-middle.png
    ├── preview-end.png
    └── clip.json
```

渲染器会校验转写的来源路径；文件在同一路径被替换时，路径检查无法证明内容没有变。复用转写前确认来源内容和转写设置均未变。转写或渲染中断后先检查已经发布的文件，不盲目重复整条流水线。
