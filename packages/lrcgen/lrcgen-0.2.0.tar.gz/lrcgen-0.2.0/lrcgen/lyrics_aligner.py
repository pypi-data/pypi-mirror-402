from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable, List, Optional, Tuple

try:
    # Optional: includes OpenCC t2s when installed
    from .utils import basic_clean as _basic_clean
except Exception:  # pragma: no cover
    def _basic_clean(text: str) -> str:  # type: ignore
        return text


_LRC_TIME_PREFIX_RE = re.compile(r"^\s*\[[0-9]{1,2}:[0-9]{2}(?:\.[0-9]{1,3})?\]\s*")
_LRC_META_RE = re.compile(r"^\s*\[[a-zA-Z]{1,3}:[^\]]*\]\s*$")


def _strip_lrc_tags(line: str) -> str:
    line = line.strip("\ufeff").strip()
    if not line:
        return ""

    # Drop [ti:..] etc
    if _LRC_META_RE.match(line):
        return ""

    # Drop one or multiple time tags at beginning: [00:12.34][00:15.00]
    while True:
        new_line = _LRC_TIME_PREFIX_RE.sub("", line, count=1)
        if new_line == line:
            break
        line = new_line
    return line.strip()


def parse_lyrics_text(text: str) -> List[str]:
    """Parse user-provided full lyrics into candidate lines.

    Accepts plain text or .lrc-like text. Strips metadata/time tags and empty lines.
    """

    out: List[str] = []
    for raw in (text or "").splitlines():
        line = _strip_lrc_tags(raw)
        if not line:
            continue
        out.append(line)
    return out


_SPLIT_RE = re.compile(r"[，。！？、；：/|\\]+")


def _segments(line: str) -> List[str]:
    # Split a long lyric line into smaller chunks so we can "截选".
    # We also split on multiple spaces.
    parts: List[str] = []
    for p in _SPLIT_RE.split(line):
        p = p.strip()
        if not p:
            continue
        # further split by 2+ spaces
        for q in re.split(r"\s{2,}", p):
            q = q.strip()
            if q:
                parts.append(q)
    # Keep original if splitting produces nothing
    return parts or [line.strip()]


def _normalize(s: str) -> str:
    # Aggressive normalization for matching.
    s = s.strip().lower()
    # Remove spaces
    s = re.sub(r"\s+", "", s)
    # Remove common punctuation/symbols
    s = re.sub(r"[\[\]（）()《》<>“”\"'‘’·.,!?;:，。！？、；：/|\\]+", "", s)
    return s


def _normalize_for_match(s: str) -> str:
    # Apply conservative cleaning (incl optional t2s) for matching only.
    return _normalize(_basic_clean(s))


def _similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


@dataclass(frozen=True)
class LyricsAlignStats:
    total: int
    matched: int
    effective_min_score: float
    target_coverage: Optional[float] = None

    @property
    def coverage(self) -> float:
        return (self.matched / self.total) if self.total else 0.0


def _align_once(
    transcript_lines: List[str],
    candidates: List[str],
    candidate_norm: List[str],
    *,
    min_score: float,
    allow_reuse_score: float,
) -> Tuple[List[str], int]:
    used = [False] * len(candidates)
    aligned: List[str] = []
    matched = 0

    for t in transcript_lines:
        t_norm = _normalize_for_match(t)
        if not t_norm or not candidates:
            aligned.append(t)
            continue

        best_i: Optional[int] = None
        best_score = -1.0
        best_i_any: Optional[int] = None
        best_score_any = -1.0

        for i, c_norm in enumerate(candidate_norm):
            score = _similarity(t_norm, c_norm)

            # Strong signal: substring match (helps when lyric line is longer than transcript)
            if t_norm and c_norm and (t_norm in c_norm or c_norm in t_norm):
                if len(t_norm) >= 4 or len(c_norm) >= 4:
                    score = max(score, 0.95)
                else:
                    score = min(1.0, score + 0.08)

            if score > best_score_any:
                best_score_any = score
                best_i_any = i

            if used[i]:
                continue
            if score > best_score:
                best_score = score
                best_i = i

        chosen_i = best_i
        chosen_score = best_score

        if chosen_i is None:
            chosen_i = best_i_any
            chosen_score = best_score_any
        elif chosen_i is not None and chosen_score < min_score:
            chosen_i = best_i_any
            chosen_score = best_score_any

        if chosen_i is None or chosen_score < min_score:
            aligned.append(t)
            continue

        if used[chosen_i] and chosen_score < allow_reuse_score:
            aligned.append(t)
            continue

        aligned.append(candidates[chosen_i])
        if not used[chosen_i]:
            used[chosen_i] = True
        matched += 1

    return aligned, matched


def align_transcript_lines(
    transcript_lines: List[str],
    lyrics_text: str,
    *,
    min_score: float = 0.50,
    allow_reuse_score: float = 0.88,
    target_coverage: Optional[float] = 0.90,
    min_score_floor: float = 0.45,
    step: float = 0.03,
) -> Tuple[List[str], LyricsAlignStats]:
    """Align Whisper transcript lines to canonical lyrics.

    The lyrics can be out-of-order. We greedily pick the best matching lyric line (or a
    segment of a lyric line) for each transcript line.

    - If best score >= min_score: use the lyric candidate.
    - If the best candidate was already used, allow reuse only when score >= allow_reuse_score.
    - Otherwise, fall back to the original transcript line.

    Returns (aligned_lines, stats).
    """

    lyrics_lines = parse_lyrics_text(lyrics_text)

    # Allow callers/CLI to disable target coverage via 0.
    if target_coverage is not None and target_coverage <= 0:
        target_coverage = None

    # Build candidates (full lines + segments) but keep displayed text.
    candidates: List[str] = []
    candidate_norm: List[str] = []
    for line in lyrics_lines:
        for seg in _segments(line):
            seg = seg.strip()
            if not seg:
                continue
            candidates.append(seg)
            candidate_norm.append(_normalize_for_match(seg))

    if not candidates:
        return transcript_lines, LyricsAlignStats(
            total=len(transcript_lines),
            matched=0,
            effective_min_score=float(min_score),
            target_coverage=target_coverage,
        )

    # If user requests a target coverage (e.g. 0.90), we can relax min_score gradually
    # until the target is reached or we hit a safety floor.
    effective = float(min_score)
    if target_coverage is not None:
        if not (0.0 <= target_coverage <= 1.0):
            raise ValueError("target_coverage must be between 0 and 1")
        effective = max(min(1.0, effective), 0.0)

    aligned, matched = _align_once(
        transcript_lines,
        candidates,
        candidate_norm,
        min_score=effective,
        allow_reuse_score=allow_reuse_score,
    )

    if target_coverage is not None and transcript_lines:
        target = float(target_coverage)
        floor = max(0.0, float(min_score_floor))
        step = max(0.001, float(step))

        while (matched / len(transcript_lines)) < target and effective > floor:
            effective = max(floor, effective - step)
            aligned, matched = _align_once(
                transcript_lines,
                candidates,
                candidate_norm,
                min_score=effective,
                allow_reuse_score=allow_reuse_score,
            )

    return aligned, LyricsAlignStats(
        total=len(transcript_lines),
        matched=matched,
        effective_min_score=effective,
        target_coverage=target_coverage,
    )
