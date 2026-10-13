"""Shared I/O and Cliptate transcript validation; Python standard library only."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def resolve(base, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("paths must be non-empty strings")
    path = Path(value).expanduser()
    return (path if path.is_absolute() else base / path).resolve()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run(command, **kwargs):
    result = subprocess.run(command, capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise ValueError(f"{Path(str(command[0])).name} failed ({result.returncode}):\n{result.stderr[-6000:]}")
    return result


def probe(path):
    executable = shutil.which("ffprobe")
    if not executable:
        raise ValueError("ffprobe is required")
    data = json.loads(run([
        executable, "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,sample_aspect_ratio",
        "-of", "json", str(path),
    ]).stdout)
    duration = number(float(data.get("format", {}).get("duration", "nan")), "media duration")
    if duration <= 0:
        raise ValueError("media duration must be positive")
    video = next((item for item in data.get("streams", []) if item.get("codec_type") == "video"), None)
    audio = next((item for item in data.get("streams", []) if item.get("codec_type") == "audio"), None)
    if not video or not audio:
        raise ValueError("shorts require both a video stream and an audio stream")
    return duration, video, audio


def find_ffmpeg(explicit=None):
    candidates = [explicit] if explicit else [
        shutil.which("ffmpeg"),
        "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
        "/usr/local/opt/ffmpeg-full/bin/ffmpeg",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            filters = run([candidate, "-hide_banner", "-filters"]).stdout
            if re.search(r"\s+ass\s+", filters):
                return str(Path(candidate).resolve())
    raise ValueError("No FFmpeg with the libass 'ass' filter found; provide --ffmpeg PATH")


def transcript_record(payload, source):
    if not isinstance(payload, dict) or not isinstance(payload.get("files"), list) or len(payload["files"]) != 1:
        raise ValueError("expected one Cliptate files[] result for this source")
    record = payload["files"][0]
    if not isinstance(record, dict) or "error" in record:
        raise ValueError(f"Cliptate transcription failed: {record}")
    filename = record.get("file")
    if not isinstance(filename, str) or not Path(filename).is_absolute() or Path(filename).resolve() != source.resolve():
        raise ValueError("transcript file does not match the source; use its original absolute file path")
    segments = record.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("no usable transcript segments")
    ids, previous = set(), -1.0
    for segment in segments:
        if not isinstance(segment, dict):
            raise ValueError("segments must be objects")
        identifier = segment.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
            raise ValueError("each transcript segment needs a unique non-empty id")
        ids.add(identifier)
        start = number(segment.get("start"), "segment start")
        end = number(segment.get("end"), "segment end")
        if start < previous or start < 0 or end <= start:
            raise ValueError("segment times must be ordered, non-negative, and have start < end")
        previous = start
        if not isinstance(segment.get("text"), str) or not segment["text"].strip():
            raise ValueError("segment text must be non-empty")
    return record


def analysis_windows(record, seconds=300):
    segments = record["segments"]
    end = max(item["end"] for item in segments)
    return [{
        "start": offset, "end": min(offset + seconds, end),
        "segments": [item for item in segments if item["end"] > offset and item["start"] < offset + seconds],
    } for offset in range(0, math.ceil(end), seconds)]


def write_json(path, payload, force=False):
    """Publish only complete JSON; link prevents races from overwriting an existing file."""
    data = (json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    try:
        if force:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
