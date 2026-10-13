#!/usr/bin/env python3
"""Regression and real FFmpeg smoke checks. Synthetic media only; no app or model calls."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common import find_ffmpeg, read_json, run, transcript_record
from render_clips import check_destination, make_ass, render, settings, validate_clip
from validate_output import validate


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("ffprobe"):
            raise unittest.SkipTest("ffprobe required for smoke tests")
        try:
            cls.ffmpeg = find_ffmpeg()
        except ValueError as error:
            raise unittest.SkipTest(str(error))
        cls.temporary = tempfile.TemporaryDirectory(prefix="cliptate-long2shorts-test-")
        cls.base = Path(cls.temporary.name)
        cls.source = cls.base / "source with spaces.mp4"
        run([cls.ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
             "color=c=red:s=160x90:r=10:d=4", "-f", "lavfi", "-i",
             "color=c=blue:s=160x90:r=10:d=36", "-f", "lavfi", "-i",
             "sine=frequency=440:duration=40", "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
             "-map", "[v]", "-map", "2:a:0", "-c:v", "libx264", "-preset", "ultrafast",
             "-pix_fmt", "yuv420p", "-c:a", "aac", str(cls.source)])

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(dir=self.base))
        self.record = dict(file=str(self.source), segments=[
            dict(id="a", text="Hello world.", start=4.0, end=10.0),
            dict(id="b", text="A complete thought.", start=10.0, end=24.0),
            dict(id="c", text="Here is the conclusion.", start=24.0, end=36.0),
        ])
        self.payload = dict(files=[self.record])
        self.transcript = self.work / "transcript.json"
        self.transcript.write_text(json.dumps(self.payload))
        self.clip = dict(start=4, end=36, title="完整观点", deck="访谈精华", summary="一个完整的观点",
                         hashtags=["#访谈", "#观点", "#思考", "#学习", "#分享"],
                         translations=dict(a="你好，世界。", b="一个完整的观点。", c="这里是结论。"))
        self.manifest = self.work / "manifest.json"
        self.manifest.write_text(json.dumps(dict(source=str(self.source), transcript="transcript.json",
            output="clips", settings=dict(width=360, height=640, fps=10), clips=[self.clip])))

    def test_rejects_wrong_source_duplicate_ids_and_nonfinite_times(self):
        for change in ("source", "id", "nan"):
            payload = copy.deepcopy(self.payload)
            if change == "source":
                payload["files"][0]["file"] = str(self.work / "other.mp4")
            elif change == "id":
                payload["files"][0]["segments"][1]["id"] = "a"
            else:
                payload["files"][0]["segments"][0]["end"] = float("nan")
            with self.subTest(change=change), self.assertRaises(ValueError):
                transcript_record(payload, self.source)

    def test_rejects_partial_segment_or_wrong_translation_mapping(self):
        for override in (dict(start=5), dict(translations={"a": "你好。"}), dict(end=100), dict(start=float("nan"))):
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_clip(dict(self.clip, **override), self.record["segments"], 40, settings({}))

    def test_subtitles_shift_to_clip_time_and_keep_gaps(self):
        segments = copy.deepcopy(self.record["segments"])
        segments[0]["end"] = 7
        content = make_ass(self.clip, segments, settings({}))
        self.assertIn("0:00:00.50,0:00:03.00,Original", content)
        self.assertIn("0:00:06.00,0:00:20.00,Translation", content)
        self.assertNotIn("0:00:00.00,0:00:03.00,Original", content)
        # A segment entirely inside the cover window must not create an inverted event.
        segments[0]["end"] = 4.4
        content = make_ass(self.clip, segments, settings({}))
        self.assertNotIn("你好", content)

    def test_single_language_and_ass_control_text(self):
        clip = dict(self.clip)
        del clip["translations"]
        clip["title"] = "{观点}\\提示"
        content = make_ass(clip, self.record["segments"], settings({}))
        self.assertNotIn(",Translation,,", content)
        self.assertIn("（观点）＼提示", content)

    def test_check_only_is_read_only(self):
        inputs = [self.source, self.transcript, self.manifest]
        previous = {path: path.read_bytes() for path in inputs}
        render(self.manifest, check_only=True)
        self.assertFalse((self.work / "clips").exists())
        for path in inputs:
            self.assertEqual(path.read_bytes(), previous[path])

    def test_render_real_video_precise_seek_and_protected_replacement(self):
        render(self.manifest)
        directory = self.work / "clips" / "part001"
        self.assertAlmostEqual(validate(directory), 32, delta=0.2)
        metadata = read_json(directory / "clip.json")
        self.assertEqual(metadata["generatedBy"], "cliptate-long2shorts")
        metadata["generatedBy"] = "cliptate-shorts"
        (directory / "clip.json").write_text(json.dumps(metadata))
        validate(directory)
        check_destination(directory, force=True)
        # The source turns blue at 4s. Clip frame zero must already be blue.
        frame = subprocess.run([self.ffmpeg, "-v", "error", "-i", str(directory / "video.mp4"),
            "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"], check=True, capture_output=True).stdout
        offset = (300 * 360 + 180) * 3
        red, green, blue = frame[offset:offset + 3]
        self.assertLess(red, 25)
        self.assertGreater(blue, 200)
        previous = (directory / "video.mp4").read_bytes()
        with self.assertRaises(ValueError):
            render(self.manifest)
        self.assertEqual((directory / "video.mp4").read_bytes(), previous)
        # Failure while producing a replacement must leave all old artifacts intact.
        with patch("render_clips.run", side_effect=ValueError("simulated encoding failure")):
            with self.assertRaises(ValueError):
                render(self.manifest, force=True)
        self.assertEqual((directory / "video.mp4").read_bytes(), previous)
        manifest = read_json(self.manifest)
        manifest["clips"][0]["title"] = "更新标题"
        self.manifest.write_text(json.dumps(manifest))
        render(self.manifest, force=True)
        self.assertNotEqual((directory / "video.mp4").read_bytes(), previous)
        self.assertEqual(read_json(directory / "clip.json")["clip"]["title"], "更新标题")
        validate(directory)
        (directory / "user-notes.txt").write_text("keep")
        with self.assertRaises(ValueError):
            render(self.manifest, force=True)
        self.assertEqual((directory / "user-notes.txt").read_text(), "keep")

    def test_preview_only_does_not_render_other_clips(self):
        manifest = read_json(self.manifest)
        manifest["clips"].append(self.clip)
        self.manifest.write_text(json.dumps(manifest))
        render(self.manifest, only=1)
        self.assertTrue((self.work / "clips" / "part001" / "video.mp4").is_file())
        self.assertFalse((self.work / "clips" / "part002").exists())


if __name__ == "__main__":
    unittest.main()
