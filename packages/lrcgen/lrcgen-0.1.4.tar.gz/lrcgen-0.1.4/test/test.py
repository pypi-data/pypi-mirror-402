import os
import re
import subprocess
import sys
import unittest


class TestPackageBasics(unittest.TestCase):
    def test_version_string(self):
        import lrcgen

        self.assertIsInstance(lrcgen.__version__, str)
        self.assertRegex(lrcgen.__version__, r"^\d+\.\d+\.\d+$")

    def test_api_import_is_light(self):
        # Should import without forcing whisper/openai at import-time.
        from lrcgen.api import generate_lrc_sync, generate_lrc_batch_sync

        self.assertTrue(callable(generate_lrc_sync))
        self.assertTrue(callable(generate_lrc_batch_sync))


class TestCliEntry(unittest.TestCase):
    def _run(self, args):
        return subprocess.run(
            [sys.executable, "-m", "lrcgen", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def test_help(self):
        p = self._run(["--help"])
        self.assertEqual(p.returncode, 0)
        self.assertIn("usage:", p.stdout.lower())

    def test_version(self):
        p = self._run(["--version"])
        self.assertEqual(p.returncode, 0)
        self.assertRegex(p.stdout.strip(), r"^lrcgen\s+\d+\.\d+\.\d+$")


class TestCorrectorInternals(unittest.TestCase):
    def test_parse_numbered_lines(self):
        from lrcgen.corrector import _parse_numbered_lines

        text = """
1: 第一行
2: 第二行
3: 第三行
""".strip()
        out = _parse_numbered_lines(text, 3)
        self.assertEqual(out, ["第一行", "第二行", "第三行"])

    def test_guardrail_merge_rejects_big_changes(self):
        from lrcgen.corrector import _guardrail_merge

        original = ["年过花 热了白", "月下举杯 尽沧海"]
        candidate = ["这是完全不同的一句话", "月下举杯 尽沧海"]
        merged = _guardrail_merge(original, candidate)
        self.assertEqual(merged[0], original[0])
        self.assertEqual(merged[1], original[1])

    def test_guardrail_merge_accepts_small_fix(self):
        from lrcgen.corrector import _guardrail_merge

        original = ["年过花 热了白"]
        candidate = ["年过花 落了白"]
        merged = _guardrail_merge(original, candidate)
        # Should allow a single-character correction by default.
        self.assertEqual(merged, candidate)


class TestLyricsAligner(unittest.TestCase):
    def test_parse_lyrics_accepts_lrc(self):
        from lrcgen.lyrics_aligner import parse_lyrics_text

        text = """
[ti:Song]
[ar:Someone]
[00:01.00]第一句
[00:02.00]第二句
""".strip()

        self.assertEqual(parse_lyrics_text(text), ["第一句", "第二句"])

    def test_align_out_of_order(self):
        from lrcgen.lyrics_aligner import align_transcript_lines

        transcript = ["第二句", "第一句"]
        lyrics = "第一句\n第二句\n"
        aligned, stats = align_transcript_lines(transcript, lyrics, min_score=0.8)
        self.assertEqual(aligned, ["第二句", "第一句"])
        self.assertEqual(stats.matched, 2)

    def test_align_can_cut_segments(self):
        from lrcgen.lyrics_aligner import align_transcript_lines

        transcript = ["第二句"]
        lyrics = "第一句，第二句，第三句\n"
        aligned, stats = align_transcript_lines(transcript, lyrics, min_score=0.8)
        self.assertEqual(aligned, ["第二句"])
        self.assertEqual(stats.matched, 1)


if __name__ == "__main__":
    unittest.main()