import argparse
import asyncio
import os
import sys

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


def main():
    parser = argparse.ArgumentParser("lrcgen")
    # Back-compat positional args (older usage: lrcgen input_dir output_dir)
    parser.add_argument("input", nargs="?", help="音频文件或目录（兼容旧版：目录）")
    parser.add_argument("output", nargs="?", help="输出文件或目录（兼容旧版：目录）")
    # Flag-style args (new usage: --audio <file/dir> --output <file/dir>)
    parser.add_argument("--audio", dest="audio", help="音频文件或目录")
    parser.add_argument("--output", dest="out", help="输出文件或目录")
    parser.add_argument("--offline", action="store_true", help="完全离线")
    parser.add_argument("--online", action="store_true", help="强制联网纠错")
    args = parser.parse_args()

    input_path = args.audio or args.input
    output_path = args.out or args.output

    if not input_path or not output_path:
        parser.error("missing input/output: use positional 'input output' or flags '--audio/--output'")

    if not os.path.exists(input_path):
        parser.error(f"input not found: {input_path}")

    if args.offline:
        mode = "offline"
    elif args.online:
        mode = "online"
    else:
        mode = "auto"

    if mode == "online":
        from .config import OPENAI_API_KEY

        if not OPENAI_API_KEY:
            parser.error(
                "--online requires OPENAI_API_KEY. Set it in .env or environment variables."
            )

    is_input_dir = os.path.isdir(input_path)
    if is_input_dir:
        os.makedirs(output_path, exist_ok=True)
    else:
        out_parent = os.path.dirname(output_path)
        if out_parent:
            os.makedirs(out_parent, exist_ok=True)

    try:
        from .whisperer import WhisperRecognizer
    except ModuleNotFoundError as e:
        if e.name == "whisper":
            parser.error(
                "missing dependency 'openai-whisper'. Install with: pip install openai-whisper"
            )
        raise

    async def process_one(recognizer, audio_path, out_path, mode):
        from .utils import format_time

        times, lines = recognizer.transcribe(audio_path)

        use_llm = False
        if mode == "online":
            use_llm = True
        elif mode == "auto":
            from .corrector import needs_llm_fix

            use_llm = needs_llm_fix(lines)

        if use_llm:
            from .corrector import llm_fix

            print(f"[lrcgen] LLM correcting: {os.path.basename(audio_path)}", file=sys.stderr)
            lines = await llm_fix(lines)
            print(f"[lrcgen] LLM correction done: {os.path.basename(audio_path)}", file=sys.stderr)

        title = os.path.splitext(os.path.basename(audio_path))[0]

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"[ti:{title}]\n[ar:Unknown]\n[al:Unknown]\n\n")
            for t, l in zip(times, lines):
                f.write(f"{format_time(t)}{l}\n")

    recognizer = WhisperRecognizer()

    async def runner():
        if is_input_dir:
            for f in os.listdir(input_path):
                if f.lower().endswith(AUDIO_EXTS):
                    in_path = os.path.join(input_path, f)
                    out_path = os.path.join(
                        output_path,
                        os.path.splitext(f)[0] + ".lrc",
                    )
                    await process_one(recognizer, in_path, out_path, mode)
            return

        # Single file mode
        if not input_path.lower().endswith(AUDIO_EXTS):
            parser.error(f"unsupported audio extension: {input_path}")

        # If output is a directory, write <basename>.lrc into it
        if os.path.isdir(output_path) or output_path.endswith(os.sep):
            os.makedirs(output_path, exist_ok=True)
            out_path = os.path.join(
                output_path,
                os.path.splitext(os.path.basename(input_path))[0] + ".lrc",
            )
        else:
            out_path = output_path
            if not out_path.lower().endswith(".lrc"):
                out_path = out_path + ".lrc"

        await process_one(recognizer, input_path, out_path, mode)
        print(f"[lrcgen] wrote: {out_path}", file=sys.stderr)

    asyncio.run(runner())


if __name__ == "__main__":
    main()
