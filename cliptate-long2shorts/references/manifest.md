# 渲染清单

转写由 [cliptate skill](../../cliptate/SKILL.md) 提供，清单中的 `transcript` 指向保存的原始 JSON。相对路径从 JSON 清单目录解析。脚本必须能读到原始 Cliptate 单文件结果，且该结果的绝对 `files[0].file` 与来源一致。转写段落需有唯一 ID、非空文字、有效且按开始时间排序的秒数。

以下是完整形状示例。`seg-01`、`seg-02` 为说明用 ID，实际用原始 JSON 中的 ID，时间和文字均按素材替换：

```json
{
  "source": "source/video.mp4",
  "transcript": "transcript.json",
  "output": "clips",
  "settings": {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "layout": "pad",
    "font": "Noto Sans CJK SC",
    "min_duration": 30,
    "max_duration": 90,
    "cover_delay": 0.5
  },
  "clips": [
    {
      "start": 112.6,
      "end": 154.14,
      "title": "极致富足",
      "deck": "AI十年后的世界",
      "summary": "AI十年后的世界：人人都能拥有想要的一切",
      "reason": "完整解释一个明确观点，开头直接进入主题，结尾给出结论。",
      "hashtags": ["#人工智能", "#AI未来", "#科技趋势", "#访谈", "#未来生活"],
      "translations": {
        "seg-01": "最可能的结果，是一个极度富足的时代。",
        "seg-02": "人们将拥有以前难以想象的机会。"
      }
    }
  ]
}
```

## 范围和文字

- `start/end` 为来源视频的绝对秒数，必须在源视频内，默认相差 30–90 秒。可在 `settings` 中调整用户指定的时长限制。
- 与片段相交的段落必须完整包含在区间内，允许在段落前后的停顿留少量余量。渲染器不会从半段文字推断句中切点。
- `title` 必填；`deck` 可省略；`summary` 可省略并使用 title。它们均为非空单行文字（deck 可为空）。`reason` 推荐记录选段理由。
- `hashtags` 为 5–8 个不含空格的 `#标签` 字符串。`summary.txt` 第一行使用 summary，第二行使用空格分隔的标签。
- `translations` 可省略，生成单语字幕。提供时必须是所选全部段落 ID 到非空译文的映射，不允许缺失、多余 ID 或位置数组。原文直接取自转写。
- 需要换行时在 JSON 字符串中使用 `\n`；不要用 ASS 的 `\N` 或插入样式控制代码。脚本会自动在词语/CJK 字符间换行，转义 ASS 控制字符。

脚本分别使用段落自己的 start 和 end，不把字幕延长到下一段，也不会生成伪造的逐词时间戳。片段内字幕时间是来源时间减去 `clip.start`，对白起点再限制到 `cover_delay`。在封面窗口内已经结束的字幕被省略，避免倒序事件。

## 画面和安全区域

`settings` 整体可省略。默认保留原画面，将视频缩放进竖屏中间区域，上方留标题、下方留字幕。使用 `layout: crop` 时中心裁剪至完整 9:16，须先确认用户需要裁剪，并在截图中检查访谈人物；脚本不做人脸跟踪。

width/height 必须是偶数且保持 9:16，如 720×1280。fps 可设 1–60。字体名使用已安装 family；脚本不下载字体。

默认字幕上方译文可容纳每行约 17 个 CJK 字符、最多两行；下方原文每行约 44 个拉丁字符、最多两行。标题和副标题也受区域限制。这个计数是排版预检查，不是实际字形测量。超出时脚本报错：缩短标题/译文，或回到音频复核更细的转写分段。不要丢弃原文来掩盖溢出。

## 执行及替换

```sh
python3 "$SKILL_DIR/scripts/render_clips.py" "$PROJECT_DIR/render_manifest.json" --check-only
python3 "$SKILL_DIR/scripts/render_clips.py" "$PROJECT_DIR/render_manifest.json" --only 1
python3 "$SKILL_DIR/scripts/render_clips.py" "$PROJECT_DIR/render_manifest.json" --only 2
python3 "$SKILL_DIR/scripts/render_clips.py" "$PROJECT_DIR/render_manifest.json" --only 1 --force
```

`--check-only` 检查输入、范围、字幕映射/排版和 FFmpeg 能力，不创建输出，也不检查替换权限或证明实际字体效果。`--only` 为从 1 开始的清单序号，输出命名始终是 `partNNN`。

已有输出默认报错。`--force` 仅替换带 `generatedBy: cliptate-long2shorts` 元数据、且没有额外文件或符号链接的产物目录，也兼容更名前的 `cliptate-shorts` 标记；遇到用户额外文件时选择新目录。每段在同一输出文件系统的临时目录渲染，自动校验成功后才发布；失败保留旧短片。批量中的前几段已经完成时，后续失败不会回滚有效输出。

脚本没有上传、平台发布、自动选段或翻译服务。真正的选段判断、译文、视觉检查和音画复核由调用此技能的 agent 完成。
