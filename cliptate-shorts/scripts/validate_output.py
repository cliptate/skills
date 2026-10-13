#!/usr/bin/env python3
"""Check encoded streams, relative subtitle timing and generated deliverables."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import probe, read_json


def ass_seconds(value):
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def validate(directory):
    from render_clips import OUTPUTS, settings
    for name in OUTPUTS:
        path = directory / name
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty output: {path}")
    metadata = read_json(directory / "clip.json")
    if metadata.get("generatedBy") != "cliptate-shorts" or metadata.get("schemaVersion") != 1:
        raise ValueError("unrecognized clip metadata")
    config = settings(metadata["settings"])
    duration, video, audio = probe(directory / "video.mp4")
    expected = metadata["sourceEnd"] - metadata["sourceStart"]
    tolerance = max(0.12, 2 / config["fps"])
    if abs(duration - expected) > tolerance:
        raise ValueError(f"encoded duration {duration:.3f}s differs from planned {expected:.3f}s")
    if not config["min_duration"] - tolerance <= duration <= config["max_duration"] + tolerance:
        raise ValueError("encoded duration is outside configured limits")
    if (video["width"], video["height"]) != (config["width"], config["height"]):
        raise ValueError("encoded resolution differs from manifest")
    if video["codec_name"] != "h264" or audio["codec_name"] != "aac" or video.get("sample_aspect_ratio") != "1:1":
        raise ValueError("output must be H.264/AAC with square pixels")
    summary = (directory / "summary.txt").read_text(encoding="utf-8").splitlines()
    if len(summary) != 2 or not all(line.strip() for line in summary):
        raise ValueError("summary.txt needs exactly two non-empty lines")
    if summary != [metadata["clip"]["summary"], " ".join(metadata["clip"]["hashtags"])]:
        raise ValueError("summary differs from clip metadata")
    content = (directory / "subtitles.ass").read_text(encoding="utf-8")
    dialogue_styles = set()
    for line in content.splitlines():
        if not line.startswith("Dialogue: "):
            continue
        fields = line.removeprefix("Dialogue: ").split(",", 9)
        start, end = map(ass_seconds, fields[1:3])
        style = fields[3]
        if not 0 <= start < end <= expected + 0.011:
            raise ValueError("ASS timing is invalid or extends beyond clip")
        if style in ("Original", "Translation"):
            if start < config["cover_delay"] - 0.011:
                raise ValueError("dialogue overlaps the cover window")
            dialogue_styles.add(style)
    required = {"Original", "Translation"} if metadata["clip"].get("translations") is not None else {"Original"}
    if dialogue_styles != required:
        raise ValueError("missing expected subtitle events")
    for style in ("Title", "Deck", "Original", "Translation"):
        if f"Style: {style},{config['font']}," not in content:
            raise ValueError("ASS font differs from manifest")
    return duration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        duration = validate(args.directory.resolve())
        print(f"OK: {duration:.3f}s; streams, subtitle times, metadata and preview files validated")
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
