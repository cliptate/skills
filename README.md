# Cliptate Skills

Agent skills for [Cliptate](https://github.com/cliptate/cliptate) transcription, short-video production, and Final Cut Pro FCPXML workflows.

**Languages:** English · [简体中文](docs/README.zh.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Deutsch](docs/README.de.md)

## Available skills

| Skill | Capabilities |
| --- | --- |
| [cliptate](cliptate/SKILL.md) | Transcribe local audio/video, export subtitles, synthesize speech, manage recognition vocabulary, and query history/correction evidence |
| [cliptate-long2shorts](cliptate-long2shorts/SKILL.md) | Turn long videos into portrait highlights with Cliptate transcription, agent-selected clips/translations, and FFmpeg rendering |
| [fcpxml](fcpxml/SKILL.md) | Draft and validate FCPXML, package portable media bundles, rough-cut with Cliptate transcription, and import into Final Cut Pro |

The skill includes command examples, JSON handling, pagination, partial failures, and version checks. Instructions are written in Simplified Chinese or English; agents can use them for requests in other languages. This repository provides agent instructions; install the Cliptate app separately.

## Requirements

The Cliptate requirements below apply to transcription. `fcpxml` scripts need Python 3.9+, `xmllint`, and an exact matching DTD. Import and automatic DTD discovery need Final Cut Pro. Install Cliptate only when generating a new transcript.

- Apple Silicon Mac running macOS 15 or later.
- GitHub/direct-download Cliptate app. The App Store build does not provide the CLI service.
- A CLI version whose `cliptate --help` lists the required command. Older versions may lack `tts` or `history`.
- Required models already downloaded, or `--download` when model downloads are intended.
- For `cliptate-long2shorts`: Python 3.9+, ffprobe, FFmpeg with libass, and a subtitle font; yt-dlp for YouTube sources.

## Install and use

### Install with npx

With Node.js and npm installed, use the [skills CLI](https://github.com/vercel-labs/skills) to select skills and target agents interactively:

```sh
npx skills add cliptate/skills
```

To install both skills globally for Codex:

```sh
npx skills add cliptate/skills --agent codex --global --skill cliptate --skill cliptate-long2shorts
```

`--global` makes the skills available across projects; omit it for installation in the current project. To install only `cliptate`, omit `--skill cliptate-long2shorts`. For `cliptate-long2shorts`, install both skills because it uses `cliptate` for transcription. For other agents, select them interactively or change `--agent` to their supported identifier.

Install `fcpxml` on its own for inspection, validation, packaging, or import:

```sh
npx skills add cliptate/skills --agent codex --global --skill fcpxml
```

For new rough-cut transcription, also install `--skill cliptate` and keep `cliptate/` beside `fcpxml/`. With an already aligned transcript, Cliptate is optional. Manual installation copies the complete `fcpxml/` folder, including scripts and references.

### Manual installation

Clone this repository and copy the entire folder for each desired skill into `~/.codex/skills/` for Codex: `cliptate/`, `cliptate-long2shorts/`, or `fcpxml/`. Keep all included `references/`, `agents/`, and `scripts/` subfolders together. `cliptate` works on its own. For `cliptate-long2shorts`, install both folders side by side: it reuses the `cliptate` skill for transcription. If the destination already exists, inspect it before replacing it. For other agents, use their supported skill directory. Skills will be available to Codex on the next turn.

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
Use $cliptate-long2shorts to turn interview.mp4 into three 30–90 second portrait clips with Chinese and English subtitles; preview the first clip first.
Use $fcpxml to rough-cut interview.fcpxmld using Cliptate transcription and deliver a validated portable bundle.
```

The public CLI exports SRT/VTT files; it does not cut video or burn subtitles into video. Commands use the selected app's settings. Transcription and speech synthesis do not create history entries; dictionary changes are persisted.

`cliptate-long2shorts` adds video cutting and subtitle rendering through FFmpeg. It preserves the full source frame with padding by default and delivers MP4, ASS, a two-line summary, cover/preview images, and source-range metadata. Cliptate CLI exposes segment timestamps; the workflow does not claim word-level timing or publish to platforms.

## Reference files

- [Skill entry point](cliptate/SKILL.md): discover the CLI, select a workflow, and interpret results.
- [Transcription and subtitles](cliptate/references/transcription.md): inputs, formats, output paths, and batch JSON.
- [Speech synthesis](cliptate/references/tts.md): text sources, model families, voice design/cloning, and WAV output.
- [Dictionary and history](cliptate/references/dictionary-history.md): vocabulary operations, history pagination, and learning from corrections.
- [Short-video workflow](cliptate-long2shorts/SKILL.md), [runtime setup](cliptate-long2shorts/references/runtime.md), and [render manifest](cliptate-long2shorts/references/manifest.md).
- [FCPXML workflow](fcpxml/SKILL.md), [rough cuts with Cliptate](fcpxml/references/rough-cut.md), [validation](fcpxml/references/validation.md), and [portable packaging](fcpxml/references/portability.md).

For maintenance, check the actual helper's help output against the [upstream CLI guide](https://github.com/cliptate/cliptate/blob/main/docs/cli.md) and command parser. Features in current source may be newer than the installed application.
