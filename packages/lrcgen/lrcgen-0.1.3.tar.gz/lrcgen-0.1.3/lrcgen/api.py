from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .whisperer import WhisperRecognizer

AUDIO_EXTS: Tuple[str, ...] = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


@dataclass(frozen=True)
class GenerateResult:
    audio_path: str
    out_path: str
    used_llm: bool
    line_count: int


async def generate_lrc(
    audio_path: str,
    out_path: str,
    *,
    mode: str = "auto",
    recognizer: Optional["WhisperRecognizer"] = None,
    model_name: str = "medium",
    language: str = "zh",
) -> GenerateResult:
    """Generate a single .lrc file.

    mode: "offline" | "online" | "auto"
    """

    if mode not in {"offline", "online", "auto"}:
        raise ValueError(f"invalid mode: {mode}")

    if recognizer is None:
        try:
            from .whisperer import WhisperRecognizer
        except ModuleNotFoundError as e:
            if e.name == "whisper":
                raise RuntimeError(
                    "missing dependency 'openai-whisper'. Install with: pip install openai-whisper"
                )
            raise
        recognizer = WhisperRecognizer(model_name=model_name, language=language)

    times, lines = recognizer.transcribe(audio_path)

    used_llm = False
    if mode == "online":
        used_llm = True
        from .corrector import llm_fix

        lines = await llm_fix(lines, require=True)
    elif mode == "auto":
        from .corrector import needs_llm_fix

        if not needs_llm_fix(lines):
            used_llm = False
        else:
            used_llm = True
            from .corrector import llm_fix

            lines = await llm_fix(lines, require=False)

    title = os.path.splitext(os.path.basename(audio_path))[0]

    from .utils import format_time

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"[ti:{title}]\n[ar:Unknown]\n[al:Unknown]\n\n")
        for t, l in zip(times, lines):
            f.write(f"{format_time(t)}{l}\n")

    return GenerateResult(
        audio_path=audio_path,
        out_path=out_path,
        used_llm=used_llm,
        line_count=len(lines),
    )


async def generate_lrc_batch(
    input_dir: str,
    output_dir: str,
    *,
    mode: str = "auto",
    recognizer: Optional["WhisperRecognizer"] = None,
    model_name: str = "medium",
    language: str = "zh",
) -> List[GenerateResult]:
    """Generate .lrc files for all supported audio files under input_dir."""

    if mode not in {"offline", "online", "auto"}:
        raise ValueError(f"invalid mode: {mode}")

    os.makedirs(output_dir, exist_ok=True)
    if recognizer is None:
        try:
            from .whisperer import WhisperRecognizer
        except ModuleNotFoundError as e:
            if e.name == "whisper":
                raise RuntimeError(
                    "missing dependency 'openai-whisper'. Install with: pip install openai-whisper"
                )
            raise
        recognizer = WhisperRecognizer(model_name=model_name, language=language)

    results: List[GenerateResult] = []
    for name in os.listdir(input_dir):
        if not name.lower().endswith(AUDIO_EXTS):
            continue
        in_path = os.path.join(input_dir, name)
        out_path = os.path.join(output_dir, os.path.splitext(name)[0] + ".lrc")
        results.append(
            await generate_lrc(
                in_path,
                out_path,
                mode=mode,
                recognizer=recognizer,
                model_name=model_name,
                language=language,
            )
        )

    return results


def generate_lrc_sync(
    audio_path: str,
    out_path: str,
    *,
    mode: str = "auto",
    model_name: str = "medium",
    language: str = "zh",
) -> GenerateResult:
    import asyncio

    return asyncio.run(
        generate_lrc(
            audio_path,
            out_path,
            mode=mode,
            recognizer=None,
            model_name=model_name,
            language=language,
        )
    )


def generate_lrc_batch_sync(
    input_dir: str,
    output_dir: str,
    *,
    mode: str = "auto",
    model_name: str = "medium",
    language: str = "zh",
) -> List[GenerateResult]:
    import asyncio

    return asyncio.run(
        generate_lrc_batch(
            input_dir,
            output_dir,
            mode=mode,
            recognizer=None,
            model_name=model_name,
            language=language,
        )
    )
