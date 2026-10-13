#!/usr/bin/env python3
"""Use the real Cliptate CLI once, keeping progress separate from transcript JSON."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from common import analysis_windows, probe, read_json, transcript_record, write_json


def transcribe(args):
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().absolute()
    windows = output.with_name(output.stem + ".windows.json")
    if not source.is_file():
        raise ValueError(f"source is missing: {source}")
    for path in (output, windows):
        if path.resolve() == source or path.is_symlink():
            raise ValueError("transcript outputs cannot replace source files or symlinks")
        if path.exists() and not args.force and not args.reuse and not args.check_only:
            raise ValueError(f"output exists: {path}; use --reuse or --force")
    media_duration, _, _ = probe(source)
    if args.reuse:
        if args.model or args.language or args.download:
            raise ValueError("--reuse cannot change transcription options; retranscribe with --force")
        record = transcript_record(read_json(output), source)
    else:
        cli = shutil.which(args.cli)
        if not cli:
            raise ValueError("Cliptate CLI not found; use --cli /path/to/Cliptate.app/Contents/Helpers/cliptate")
        env = os.environ.copy()
        # Instrumented development helpers otherwise leave default.profraw in the project.
        env.setdefault("LLVM_PROFILE_FILE", os.devnull)
        if args.app:
            env["CLIPTATE_APP"] = str(args.app.expanduser().resolve())
        help_text = subprocess.run([cli, "--help"], capture_output=True, text=True, env=env, check=True).stdout
        if "transcribe" not in help_text or "--format" not in help_text:
            raise ValueError("this executable does not expose the public Cliptate transcribe command")
        if args.check_only:
            print(f"OK: CLI {cli}; source {media_duration:.2f}s; no inference or model download performed")
            return
        command = [cli, "transcribe", str(source), "--format", "json"]
        for flag, value in (("--model", args.model), ("--language", args.language)):
            if value:
                command.extend([flag, value])
        if args.download:
            command.append("--download")
        # stderr stays live for model/inference progress. Never combine it with JSON.
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, env=env)
        if result.returncode:
            raise ValueError(f"Cliptate exited {result.returncode}; no new transcript published")
        payload = json.loads(result.stdout)
        record = transcript_record(payload, source)
    if max(item["end"] for item in record["segments"]) > media_duration + 0.25:
        raise ValueError("transcript extends beyond source duration")
    if args.check_only:
        print(f"OK: cached transcript contains {len(record['segments'])} segments")
        return
    if not args.reuse:
        write_json(output, payload, force=args.force)
    write_json(windows, analysis_windows(record), force=args.force or args.reuse)
    print(f"OK: {output}\nAnalysis windows: {windows}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cli", default="cliptate")
    parser.add_argument("--app", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--language")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--reuse", action="store_true", help="use an existing transcript, rebuild analysis windows")
    parser.add_argument("--force", action="store_true", help="replace transcript outputs after successful transcription")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    try:
        transcribe(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
