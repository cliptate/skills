# Cliptate Skills

Agent skills for using [Cliptate](https://github.com/cliptate/cliptate) through its macOS command line interface.

**Languages:** English · [简体中文](docs/README.zh.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Deutsch](docs/README.de.md)

## Available skill

| Skill | Capabilities |
| --- | --- |
| [cliptate](cliptate/SKILL.md) | Transcribe local audio/video, export subtitles, synthesize speech, manage recognition vocabulary, and query history/correction evidence |
| [cliptate-shorts](cliptate-shorts/SKILL.md) | Turn long videos into portrait highlights with Cliptate transcription, agent-selected clips/translations, and FFmpeg rendering |

The skill includes command examples, JSON handling, pagination, partial failures, and version checks. Its instructions are currently written in Simplified Chinese; an agent can use them to handle requests in other languages. This repository provides agent instructions; install the Cliptate app separately.

## Requirements

- Apple Silicon Mac running macOS 15 or later.
- GitHub/direct-download Cliptate app. The App Store build does not provide the CLI service.
- A CLI version whose `cliptate --help` lists the required command. Older versions may lack `tts` or `history`.
- Required models already downloaded, or `--download` when model downloads are intended.
- For `cliptate-shorts`: Python 3.9+, ffprobe, FFmpeg with libass, and a subtitle font; yt-dlp for YouTube sources.

## Install and use

Clone this repository and copy the entire folder for each desired skill into `~/.codex/skills/` for Codex: `cliptate/` or `cliptate-shorts/`. Keep all included `references/`, `agents/`, and `scripts/` subfolders together. Each skill can be installed independently. If the destination already exists, inspect it before replacing it. For other agents, use their supported skill directory. Skills will be available to Codex on the next turn.

In Cliptate, open **Settings → Command Line** and use the installation command to add the helper to `~/.local/bin`. Ensure that directory is in PATH, or invoke the helper directly inside the app bundle. Check the installed command:

```sh
cliptate --version
cliptate --help
```

Example agent requests:

```text
Use $cliptate to transcribe interview.mp4 and save interview.srt.
Use $cliptate to synthesize narration.txt into narration.wav.
Use $cliptate to analyze recent correction history and add reliable new terms to the dictionary.
Use $cliptate-shorts to turn interview.mp4 into three 30–90 second portrait clips with Chinese and English subtitles; preview the first clip first.
```

The public CLI exports SRT/VTT files; it does not cut video or burn subtitles into video. Commands use the selected app's settings. Transcription and speech synthesis do not create history entries; dictionary changes are persisted.

`cliptate-shorts` adds video cutting and subtitle rendering through FFmpeg. It preserves the full source frame with padding by default and delivers MP4, ASS, a two-line summary, cover/preview images, and source-range metadata. Cliptate CLI exposes segment timestamps; the workflow does not claim word-level timing or publish to platforms.

## Reference files

- [Skill entry point](cliptate/SKILL.md): discover the CLI, select a workflow, and interpret results.
- [Transcription and subtitles](cliptate/references/transcription.md): inputs, formats, output paths, and batch JSON.
- [Speech synthesis](cliptate/references/tts.md): text sources, model families, voice design/cloning, and WAV output.
- [Dictionary and history](cliptate/references/dictionary-history.md): vocabulary operations, history pagination, and learning from corrections.
- [Short-video workflow](cliptate-shorts/SKILL.md), [runtime setup](cliptate-shorts/references/runtime.md), and [render manifest](cliptate-shorts/references/manifest.md).

For maintenance, check the actual helper's help output against the [upstream CLI guide](https://github.com/cliptate/cliptate/blob/main/docs/cli.md) and command parser. Features in current source may be newer than the installed application.
