from __future__ import annotations

import re
import asyncio
import sys
import os
from difflib import SequenceMatcher
from openai import OpenAI
from .config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    MAX_LLM_CONCURRENCY,
)

# ===== OpenAI Client =====
client = None
if OPENAI_API_KEY:
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )

_semaphore = asyncio.Semaphore(MAX_LLM_CONCURRENCY)


def _similarity(a: str, b: str) -> float:
    # 0..1, higher means more similar
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _guardrail_merge(original: list[str], candidate: list[str]) -> list[str]:
    """Keep candidate only when it's a small, likely-safe correction.

    This prevents the LLM from paraphrasing/reformatting lines (which often
    makes lyrics worse). Lines that change too much are reverted to original.
    """

    min_sim = float(os.getenv("LRCGEN_LLM_MIN_SIM", "0.78"))
    max_len_delta = int(os.getenv("LRCGEN_LLM_MAX_LEN_DELTA", "6"))

    out: list[str] = []
    for o, c in zip(original, candidate):
        o2 = o.strip()
        c2 = c.strip()

        # Never allow empty replacements
        if not c2:
            out.append(o)
            continue

        # If the model changed the line too much, keep the original
        if abs(len(o2) - len(c2)) > max_len_delta:
            out.append(o)
            continue

        if _similarity(o2, c2) < min_sim:
            out.append(o)
            continue

        out.append(c2)

    return out


def _guardrail_merge_with_stats(
    original: list[str],
    candidate: list[str],
) -> tuple[list[str], int, int, int]:
    """Return (merged_lines, proposed_changes, accepted_changes, rejected_changes)."""

    proposed_changes = sum(
        1 for o, c in zip(original, candidate) if o.strip() != c.strip()
    )

    merged = _guardrail_merge(original, candidate)
    accepted_changes = sum(
        1 for o, m in zip(original, merged) if o.strip() != m.strip()
    )
    rejected_changes = max(0, proposed_changes - accepted_changes)
    return merged, proposed_changes, accepted_changes, rejected_changes


_LINE_RE = re.compile(r"^\s*(\d+)\s*[\.|:：\)]\s*(.*)$")


def _parse_numbered_lines(text: str, n: int) -> list[str] | None:
    """Parse lines in format like '1: ...' .. 'n: ...' (order can vary)."""

    mapping: dict[int, str] = {}
    for raw in text.splitlines():
        m = _LINE_RE.match(raw)
        if not m:
            continue
        idx = int(m.group(1))
        if 1 <= idx <= n and idx not in mapping:
            mapping[idx] = m.group(2).strip()

    if len(mapping) != n:
        return None

    return [mapping[i] for i in range(1, n + 1)]


def needs_llm_fix(lines: list[str]) -> bool:
    """
    判断是否值得花钱纠错
    """
    if len(lines) < 8:
        return False

    total = len(lines)
    short = sum(1 for l in lines if len(l) <= 2)
    trad = sum(1 for l in lines if re.search(r"[裏爲妳祢著]", l))

    if short / total > 0.3:
        return True
    if trad / total > 0.2:
        return True

    return False


async def llm_fix(lines: list[str]) -> list[str]:
    """
    二次纠正（失败自动回退）
    """
    if not client:
        print(
            "[lrcgen] LLM correction skipped: OPENAI_API_KEY not set.",
            file=sys.stderr,
        )
        return lines

    async with _semaphore:
        try:
            numbered = "\n".join(f"{i+1}: {l}" for i, l in enumerate(lines))
            prompt = f"""
你是一个非常保守的中文歌词纠错器。目标：只做“确定无疑”的错别字/同音字修正。

硬性规则（必须严格遵守）：
1) 修正明显错别字、同音字（例如：热了白→落了白）；
2) 不允许改写句子、调整语序、增删标点/空格风格、替换近义词
3) 必须逐行对齐：输入有 {len(lines)} 行，你也必须输出 {len(lines)} 行
4) 每行必须带行号，格式必须是："<行号>: <内容>"，行号从 1 开始
5) 除了这 {len(lines)} 行之外，不要输出任何解释、标题、空行
6) 大多给你的都是已有的流行歌曲，请先检索出歌曲正确歌词，尽量参考正确歌词拼写

输入歌词：
{numbered}
""".strip()

            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )

            content = (resp.choices[0].message.content or "").strip()
            parsed = _parse_numbered_lines(content, len(lines))
            if not parsed:
                print(
                    "[lrcgen] LLM correction ignored: failed to parse numbered output",
                    file=sys.stderr,
                )
                return lines

            # Guardrails: keep only safe/small corrections per line
            merged, proposed, accepted, rejected = _guardrail_merge_with_stats(
                lines, parsed
            )
            print(
                f"[lrcgen] LLM changes: proposed={proposed}, accepted={accepted}, rejected={rejected}",
                file=sys.stderr,
            )
            return merged

        except Exception as e:
            print(f"[lrcgen] LLM correction failed: {e}", file=sys.stderr)
            return lines
