# Cliptate Skills

macOS のコマンドラインから [Cliptate](https://github.com/cliptate/cliptate) を操作するエージェントスキルです。

**言語：** [English](../README.md) · [简体中文](README.zh.md) · 日本語 · [한국어](README.ko.md) · [Deutsch](README.de.md)

## 利用できるスキル

| スキル | 機能 |
| --- | --- |
| [cliptate](../cliptate/SKILL.md) | ローカル音声・動画の文字起こし、字幕出力、音声合成、認識辞書の管理、履歴と修正記録の取得 |
| [cliptate-long2shorts](../cliptate-long2shorts/SKILL.md) | Cliptate の文字起こし、エージェントによる場面選択と翻訳、FFmpeg の描画で長い動画を縦型の短編に変換 |

コマンド例、JSON の処理、ページ分割、一部失敗時の処理、バージョン確認を含みます。スキルの指示は現在、簡体字中国語で記述されていますが、エージェントは他の言語の依頼にも利用できます。このリポジトリはエージェント向けの指示を提供します。Cliptate アプリは別途インストールしてください。

## 動作要件

- macOS 15 以降を搭載した Apple Silicon Mac。
- GitHub または直接ダウンロード版の Cliptate。App Store 版には CLI サービスがありません。
- 必要なコマンドが `cliptate --help` に表示される CLI バージョン。古い版には `tts` や `history` がない場合があります。
- 必要なモデルをダウンロード済みであること。モデルのダウンロードが必要な場合は `--download` を使用します。
- `cliptate-long2shorts` には Python 3.9+、ffprobe、libass 対応 FFmpeg、字幕フォントも必要です。YouTube 素材には yt-dlp を使用します。

## インストールと使い方

このリポジトリをクローンし、必要なスキルのフォルダ `cliptate/` または `cliptate-long2shorts/` 全体を Codex の `~/.codex/skills/` にコピーします。含まれる `references/`、`agents/`、`scripts/` サブフォルダも保持してください。`cliptate` は単独で利用できます。`cliptate-long2shorts` は文字起こしに `cliptate` スキルを使うため、両方のフォルダを同じスキルディレクトリにインストールしてください。コピー先が存在する場合は、上書き前に内容を確認します。他のエージェントでは対応するスキルディレクトリを使用します。Codex では次のターンから利用できます。

Cliptate の「**設定 → コマンドライン**」で表示されるインストールコマンドを使い、helper を `~/.local/bin` にリンクします。このディレクトリを PATH に含めるか、アプリ内の helper を直接実行します。実際のコマンドを確認してください。

```sh
cliptate --version
cliptate --help
```

依頼の例：

```text
$cliptate を使って interview.mp4 を文字起こしし、interview.srt に保存してください。
$cliptate を使って narration.txt から narration.wav を生成してください。
$cliptate を使って最近の修正履歴を分析し、信頼できる新しい用語を辞書に追加してください。
$cliptate-long2shorts を使って interview.mp4 から 30–90 秒の縦型動画を 3 本作り、中英字幕を付けてください。まず 1 本目をプレビューしてください。
```

公開 CLI は SRT/VTT 字幕ファイルを出力します。動画編集や字幕の焼き込みには対応していません。選択したアプリの設定を使用します。文字起こしと音声合成は履歴に追加されませんが、辞書の変更は保存されます。

`cliptate-long2shorts` は FFmpeg で動画の切り出しと字幕描画を行います。既定では元の画面全体を保持して余白を追加し、MP4、ASS、2 行の概要、表紙・プレビュー画像、元動画の区間情報を出力します。CLI の時刻情報はセグメント単位です。単語単位の精度やプラットフォームへの投稿は提供しません。

## 参考資料

- [スキルの入口](../cliptate/SKILL.md)：CLI の確認、処理の選択、結果の判定。
- [文字起こしと字幕](../cliptate/references/transcription.md)：入力、形式、出力先、バッチ JSON。
- [音声合成](../cliptate/references/tts.md)：テキスト入力、モデル種別、音声設計・クローン、WAV 出力。
- [辞書と履歴](../cliptate/references/dictionary-history.md)：用語管理、履歴のページ分割、修正記録からの学習。
- [短編動画のワークフロー](../cliptate-long2shorts/SKILL.md)、[実行環境](../cliptate-long2shorts/references/runtime.md)、[描画マニフェスト](../cliptate-long2shorts/references/manifest.md)。

メンテナンス時は実際の helper のヘルプを[上流の CLI ガイド](https://github.com/cliptate/cliptate/blob/main/docs/cli.md)および引数パーサーと照合してください。現在のソースにある機能が、インストール済みのアプリにはまだ含まれていない場合があります。
