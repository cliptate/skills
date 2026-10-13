#!/usr/bin/env python3
"""Render source ranges using Cliptate segment IDs, ASS subtitles, and FFmpeg."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from common import GENERATOR, SUPPORTED_GENERATORS, find_ffmpeg, number, probe, read_json, resolve, run, transcript_record


OUTPUTS = {"video.mp4", "subtitles.ass", "summary.txt", "cover.png", "preview-start.png",
           "preview-middle.png", "preview-end.png", "clip.json"}


def settings(raw):
    if not isinstance(raw, dict):
        raise ValueError("settings must be an object")
    values = dict(width=1080, height=1920, fps=30, layout="pad", font="Noto Sans CJK SC",
                  min_duration=30, max_duration=90, cover_delay=0.5)
    unknown = set(raw) - set(values)
    if unknown:
        raise ValueError(f"unknown settings: {sorted(unknown)}")
    values.update(raw)
    width, height = values["width"], values["height"]
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 180 or v % 2 for v in (width, height)):
        raise ValueError("resolution must use positive even integers of at least 180")
    if width * 16 != height * 9:
        raise ValueError("output resolution must have a 9:16 ratio")
    fps = number(values["fps"], "fps")
    if not 1 <= fps <= 60 or values["layout"] not in ("pad", "crop"):
        raise ValueError("fps must be 1..60 and layout must be pad or crop")
    low, high = [number(values[key], key) for key in ("min_duration", "max_duration")]
    delay = number(values["cover_delay"], "cover_delay")
    if not 0 < low <= high or not 0 <= delay < low:
        raise ValueError("duration limits must be positive and cover_delay less than min_duration")
    font = values["font"]
    if not isinstance(font, str) or not font.strip() or any(char in font for char in ",\n\r"):
        raise ValueError("font must be an ASS font family name")
    return values


def text(value, label, optional=False):
    if not isinstance(value, str) or (not optional and not value.strip()):
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def validate_clip(clip, segments, duration, config):
    if not isinstance(clip, dict):
        raise ValueError("clip must be an object")
    start, end = number(clip.get("start"), "clip start"), number(clip.get("end"), "clip end")
    if not 0 <= start < end <= duration + 0.001:
        raise ValueError("clip range must be within the source")
    if not config["min_duration"] <= end - start <= config["max_duration"]:
        raise ValueError("clip duration is outside configured limits")
    title = text(clip.get("title"), "title")
    deck = text(clip.get("deck", ""), "deck", optional=True)
    summary = text(clip.get("summary", title), "summary")
    if any("\n" in value or "\r" in value for value in (title, deck, summary)):
        raise ValueError("title, deck and summary must each be one line")
    tags = clip.get("hashtags")
    if not isinstance(tags, list) or not 5 <= len(tags) <= 8 or any(
        not isinstance(tag, str) or len(tag) < 2 or not tag.startswith("#") or
        any(char.isspace() for char in tag) for tag in tags
    ):
        raise ValueError("hashtags must contain 5..8 single-token #tags")
    selected = [item for item in segments if item["end"] > start and item["start"] < end]
    if not selected:
        raise ValueError("clip contains no transcript segments")
    for segment in selected:
        if segment["start"] < start - 0.01 or segment["end"] > end + 0.01:
            raise ValueError(f"clip cuts inside segment {segment['id']}; choose a complete segment boundary")
    translations = clip.get("translations")
    if translations is not None:
        if not isinstance(translations, dict) or set(translations) != {item["id"] for item in selected}:
            raise ValueError("translations must map every selected segment id, with no extra ids")
        for identifier, value in translations.items():
            text(value, f"translation {identifier}")
    return dict(clip, start=start, end=end, title=title, deck=deck, summary=summary), selected


def ass_time(seconds):
    ticks = round(seconds * 100)
    return f"{ticks // 360000}:{ticks // 6000 % 60:02d}:{ticks // 100 % 60:02d}.{ticks % 100:02d}"


def wrap(value, limit, max_lines):
    """Wrap on words/CJK characters without making up finer subtitle timestamps."""
    value = value.replace("\\", "＼").replace("{", "（").replace("}", "）")
    lines, current, count = [], "", 0
    tokens = re.findall(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]|[^\s\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]+|[ \t]+|\n", value)
    for token in tokens:
        units = sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in token)
        if token == "\n" or (current and count + units > limit and not token.isspace()):
            lines.append(current.strip())
            current, count = "", 0
        if token != "\n":
            current += token
            count += units
    if current.strip():
        lines.append(current.strip())
    if not lines or len(lines) > max_lines or any(
        sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in line) > limit for line in lines
    ):
        raise ValueError("subtitle/title exceeds safe layout; shorten translation/title or review transcript segmentation")
    return r"\N".join(lines)


def make_ass(clip, selected, config):
    width, height = config["width"], config["height"]
    scale = height / 1920
    duration = clip["end"] - clip["start"]
    header = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}",
              "WrapStyle: 2", "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"]
    for name, size, color, y in [("Title", 78, "&H0000FFFF&", 160), ("Deck", 46, "&H00FFFFFF&", 340),
                                 ("Translation", 56, "&H00FFFFFF&", 1460), ("Original", 42, "&H0000A5FF&", 1640)]:
        if name == "Original" and clip.get("translations") is None:
            color, y = "&H00FFFFFF&", 1460
        header.append(f"Style: {name},{config['font']},{size * scale:.2f},{color},{color},&H00000000&,&H80000000&,0,0,0,0,100,100,0,0,1,{2.5 * scale:.2f},0,8,{round(60 * scale)},{round(60 * scale)},{round(y * scale)},1")
    header.extend(["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"])
    def event(start, end, style, value):
        if round(end * 100) <= round(start * 100):
            return
        header.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},{style},,0,0,0,,{value}")
    event(0, duration, "Title", wrap(clip["title"], 23, 2))
    if clip["deck"]:
        event(0, duration, "Deck", wrap(clip["deck"], 36, 2))
    for item in selected:
        start = max(config["cover_delay"], item["start"] - clip["start"])
        end = min(duration, item["end"] - clip["start"])
        if end <= start:
            continue
        event(start, end, "Original", wrap(item["text"], 44, 2))
        if clip.get("translations") is not None:
            event(start, end, "Translation", wrap(clip["translations"][item["id"]], 34, 2))
    return "\n".join(header) + "\n"


def load_manifest(path, only=None):
    manifest = read_json(path)
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    base = path.parent
    source, transcript, output = [resolve(base, manifest.get(key)) for key in ("source", "transcript", "output")]
    if not source.is_file() or not transcript.is_file():
        raise ValueError("source and transcript must exist")
    duration, _, _ = probe(source)
    record = transcript_record(read_json(transcript), source)
    if max(item["end"] for item in record["segments"]) > duration + 0.25:
        raise ValueError("transcript extends beyond source duration")
    config = settings(manifest.get("settings", {}))
    clips = manifest.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("clips must be a non-empty list")
    if only is not None and not 1 <= only <= len(clips):
        raise ValueError("--only is a 1-based clip number")
    checked = []
    for number_, raw in enumerate(clips, 1):
        if only is not None and number_ != only:
            continue
        clip, selected = validate_clip(raw, record["segments"], duration, config)
        ass = make_ass(clip, selected, config)
        final = output / f"part{number_:03d}"
        if any(item == final or final in item.parents for item in (source, transcript, path)):
            raise ValueError("clip output directory contains an input")
        checked.append((number_, clip, selected, ass))
    return source, output, config, checked


def check_destination(final, force):
    if final.is_symlink():
        raise ValueError(f"output directory is a symlink: {final}")
    if not final.exists():
        return
    if not force:
        raise ValueError(f"output exists: {final}; use --force only to replace a generated clip")
    marker = final / "clip.json"
    if not final.is_dir() or not marker.is_file() or read_json(marker).get("generatedBy") not in SUPPORTED_GENERATORS:
        raise ValueError(f"refusing to replace an unrecognized directory: {final}")
    if any(item.name not in OUTPUTS or not item.is_file() or item.is_symlink() for item in final.iterdir()):
        raise ValueError(f"output contains extra files or symlinks; choose a new output: {final}")


def video_filter(config):
    width, height = config["width"], config["height"]
    if config["layout"] == "pad":
        box_height = math.floor(height * 0.52 / 2) * 2
        placement = math.floor(height * 0.22 / 2) * 2
        layout = (f"scale={width}:{box_height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
                  f"pad={width}:{box_height}:(ow-iw)/2:(oh-ih)/2:black,"
                  f"pad={width}:{height}:0:{placement}:black")
    else:
        layout = (f"scale={width}:{height}:force_original_aspect_ratio=increase:force_divisible_by=2,"
                  f"crop={width}:{height}")
    return f"setpts=PTS-STARTPTS,scale=trunc(iw*sar/2)*2:ih,setsar=1,{layout},setsar=1,ass=filename=subtitles.ass"


def render(path, only=None, force=False, check_only=False, ffmpeg=None):
    path = path.resolve()
    source, output, config, checked = load_manifest(path, only)
    executable = find_ffmpeg(ffmpeg)
    if check_only:
        print(f"OK: {len(checked)} clips validated; FFmpeg {executable}; no rendering performed")
        return
    for number_, *_ in checked:
        check_destination(output / f"part{number_:03d}", force)
    output.mkdir(parents=True, exist_ok=True)
    from validate_output import validate
    for number_, clip, selected, ass in checked:
        final = output / f"part{number_:03d}"
        duration = clip["end"] - clip["start"]
        with tempfile.TemporaryDirectory(prefix=".cliptate-long2shorts-", dir=output) as temporary:
            stage = Path(temporary) / "clip"
            stage.mkdir()
            (stage / "subtitles.ass").write_text(ass, encoding="utf-8")
            (stage / "summary.txt").write_text(clip["summary"] + "\n" + " ".join(clip["hashtags"]) + "\n", encoding="utf-8")
            run([executable, "-hide_banner", "-loglevel", "error", "-nostdin", "-ss", str(clip["start"]),
                 "-i", str(source), "-t", str(duration), "-map", "0:v:0", "-map", "0:a:0", "-sn", "-dn",
                 "-vf", video_filter(config), "-af", "asetpts=PTS-STARTPTS", "-r", str(config["fps"]),
                 "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", "-map_metadata", "-1", "-movflags", "+faststart", "video.mp4"], cwd=stage)
            for filename, seconds in [("cover.png", 0), ("preview-start.png", min(1, duration / 4)),
                                      ("preview-middle.png", duration / 2), ("preview-end.png", max(0, duration - 1))]:
                run([executable, "-hide_banner", "-loglevel", "error", "-nostdin", "-i", "video.mp4",
                     "-ss", str(seconds), "-frames:v", "1", filename], cwd=stage)
            metadata = dict(generatedBy=GENERATOR, schemaVersion=1, source=str(source), manifest=str(path),
                            sourceStart=clip["start"], sourceEnd=clip["end"], timingPrecision="segment",
                            segmentIDs=[item["id"] for item in selected], settings=config, clip=clip)
            (stage / "clip.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            validate(stage)
            # An existing complete clip stays intact until its replacement passes validation.
            check_destination(final, force)
            backup = Path(temporary) / "previous"
            if final.exists():
                os.rename(final, backup)
            try:
                os.rename(stage, final)
            except BaseException:
                if backup.exists():
                    os.rename(backup, final)
                raise
        print(f"OK: {final / 'video.mp4'}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--only", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--ffmpeg", help="explicit FFmpeg executable with libass")
    args = parser.parse_args()
    try:
        render(args.manifest, args.only, args.force, args.check_only, args.ffmpeg)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
