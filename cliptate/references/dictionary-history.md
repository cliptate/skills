# 词典与历史

## 识别词典

```sh
cliptate dictionary list
cliptate dictionary add "Cliptate" "Ada Lovelace"
cliptate dictionary remove "Ada Lovelace"
cliptate dictionary import "selected-terms.txt"
cliptate dictionary import "selected-terms.json"
cliptate dictionary export
```

所有成功命令都返回完整的当前 JSON 字符串数组。`list` 与 `export` 读取相同数据；保存导出时将 stdout 写入选定文件，注意 shell 的 `>` 会替换已有文件，不受 CLI `--overwrite` 控制。

import 接受 UTF-8 每行一个词/词组，或 JSON 字符串数组，例如 `["Cliptate", "SwiftUI"]`。导入是追加，不替换已有词典。应用会裁剪两端空白、丢弃空项、忽略大小写和变音符号去重，保留首次拼写及顺序；remove 使用相同比较规则。

词典是识别词汇列表，不是错误拼写到正确拼写的替换映射。写入会修改并持久保存选定应用的配置。连接丢失后先 `dictionary list` 核对结果，再决定是否需要补写。

## 查询历史

先确认顶层帮助列出 `history`。用真实返回的 session UUID 替换示例 UUID：

```sh
cliptate history list --limit 50
cliptate history list --corrections-only --source fileTranscription --limit 50
cliptate history show 00000000-0000-0000-0000-000000000001 --limit 100
cliptate history corrections --source fileTranscription --since 2026-10-01T00:00:00+08:00
cliptate history corrections --search "Cliptate"
cliptate history corrections --session 00000000-0000-0000-0000-000000000001
```

始终返回 JSON，`--format json` 可选。响应形状：

```json
{"schemaVersion": 1, "sessions": [], "lines": [], "corrections": [], "nextCursor": "opaque-token"}
```

| 命令 | 内容及筛选 |
| --- | --- |
| `list` | 会话摘要：ID、来源、日期、模型/语言、行数/纠错数、160 字符预览；按会话开始时间排序/过滤 |
| `show UUID` | 单会话摘要，以及先转写行、后纠错记录的分页；ID 后只接受 `--limit`、`--cursor`、`--format json` |
| `corrections` | 直接返回纠错证据；按纠错时间排序/过滤 |

`list` 与 `corrections` 支持 `--source voiceDictation|fileTranscription|ttsSynthesis`、`--session UUID`、`--since ISO-8601`、`--until ISO-8601`、`--search TEXT`。`--corrections-only` 用于 `list`。时间边界包含端点，必须带时区；按用户所在时区转换条件，返回时间是带毫秒的 UTC ISO-8601。

所有命令支持 `--limit 1..200`（默认 50）与 `--cursor TOKEN`。保存原命令及筛选，将响应的 `nextCursor` 原样作为下一页参数，直到该字段不存在。后续页可修改 limit，其他条件保持一致。不要根据条目数少于 limit 判定结束：响应另有 8 MiB 大小限制。`show` 期间会话文本变更会使游标失效，需从第一页重读。

不存在/过期的 show ID 返回退出码 `1`；空 list/corrections 返回成功和空数组。历史不包含录音、音频路径、安全书签、词级时间或内部编辑状态，不能从这里恢复音频。听写保留 24 小时，文件/TTS 保留 30 天；父会话删除或过期时，相应纠错记录一起移除。旧会话可能没有纠错证据。

## 从纠错证据学习词汇

用户要求根据历史完善词典时：

1. 分页读取相关 `history corrections`，并读取 `dictionary list`。历史查询本身不调用 AI，由当前 agent 分析证据。
2. 按纠错事件 `id` 去重。一条事件可能关联多个 `relatedSessionIDs`，不要重复计算。
3. 优先分析 `status: applied` 的证据，排除 `reverted` 和 `superseded`。`applied` 表示当时应用过编辑，不代表用户批准或当前文字仍包含它。
4. `kind: phrase` 提供实际应用的词/词组修改；从 `corrected` 及上下文选择可信的专有名词、技术词。`kind: dictation` 是整段前后文字，先分析具体词汇，避免把整句、风格变化或语法润色加入词典。
5. 按词典的比较规则过滤现有词，得到新增正确词汇。用户请求只是分析时返回建议；请求包含词典更新时使用 `dictionary add/import` 完成写入，并核对返回数组。

批量候选保存为 JSON 字符串数组再导入；保留已有词典。不要把错误拼写、错误到正确的对象映射或 AI 助手回答当成词汇证据。报告实际加入的词汇及筛选范围；没有可信新增词时说明结果。
