import argparse
import asyncio
import os
import sys

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


def main():
    parser = argparse.ArgumentParser("lrcgen")
    from . import __version__

    parser.add_argument("--version", action="version", version=f"lrcgen {__version__}")
    # Back-compat positional args (older usage: lrcgen input_dir output_dir)
    parser.add_argument("input", nargs="?", help="音频文件或目录（兼容旧版：目录）")
    parser.add_argument("output", nargs="?", help="输出文件或目录（兼容旧版：目录）")
    # Flag-style args (new usage: --audio <file/dir> --output <file/dir>)
    parser.add_argument("--audio", dest="audio", help="音频文件或目录")
    parser.add_argument("--output", dest="out", help="输出文件或目录")
    parser.add_argument("--offline", action="store_true", help="完全离线")
    parser.add_argument("--online", action="store_true", help="强制联网纠错")
    parser.add_argument("--model", default="medium", help="Whisper model (e.g. tiny/base/small/medium/large)")
    parser.add_argument("--language", default="zh", help="Whisper language code (default: zh)")
    parser.add_argument(
        "--lyrics-file",
        help="完整歌词文件（txt 或 lrc 均可；顺序可乱）。启用后将从歌词中选取/截选每行内容。",
    )
    parser.add_argument(
        "--lyrics",
        help="直接传入完整歌词文本（不方便写文件时使用）。",
    )
    args = parser.parse_args()

    input_path = args.audio or args.input
    output_path = args.out or args.output

    if not input_path or not output_path:
        parser.error("missing input/output: use positional 'input output' or flags '--audio/--output'")

    if not os.path.exists(input_path):
        parser.error(f"input not found: {input_path}")

    if args.offline and args.online:
        parser.error("--offline and --online are mutually exclusive")

    if args.lyrics and args.lyrics_file:
        parser.error("--lyrics and --lyrics-file are mutually exclusive")

    if args.offline:
        mode = "offline"
    elif args.online:
        mode = "online"
    else:
        mode = "auto"

    if mode == "online":
        from .config import OPENAI_API_KEY

        try:
            import openai  # noqa: F401
        except ModuleNotFoundError:
            parser.error("--online requires extra 'online'. Install with: pip install \"lrcgen[online]\"")

        if not OPENAI_API_KEY:
            parser.error(
                "--online requires OPENAI_API_KEY. Set it in .env or environment variables."
            )

    is_input_dir = os.path.isdir(input_path)

    if is_input_dir and (args.lyrics or args.lyrics_file):
        parser.error("--lyrics/--lyrics-file currently supports single-file mode only")
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

    recognizer = WhisperRecognizer(model_name=args.model, language=args.language)

    from .api import generate_lrc, generate_lrc_batch

    lyrics_text = None
    if args.lyrics_file:
        try:
            with open(args.lyrics_file, "r", encoding="utf-8") as f:
                lyrics_text = f.read()
        except FileNotFoundError:
            parser.error(f"lyrics file not found: {args.lyrics_file}")
    elif args.lyrics:
        lyrics_text = args.lyrics

    if lyrics_text and mode == "online":
        print("[lrcgen] note: lyrics mode enabled; skipping LLM correction", file=sys.stderr)

    async def runner():
        if is_input_dir:
            results = await generate_lrc_batch(
                input_path,
                output_path,
                mode=mode,
                recognizer=recognizer,
            )
            for r in results:
                if r.used_llm:
                    print(
                        f"[lrcgen] LLM corrected: {os.path.basename(r.audio_path)}",
                        file=sys.stderr,
                    )
                print(f"[lrcgen] wrote: {r.out_path}", file=sys.stderr)
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

        r = await generate_lrc(
            input_path,
            out_path,
            mode=mode,
            lyrics_text=lyrics_text,
            recognizer=recognizer,
            model_name=args.model,
            language=args.language,
        )
        if getattr(r, "used_lyrics", False):
            print(
                f"[lrcgen] lyrics aligned: {getattr(r, 'lyrics_matched', 0)}/{r.line_count}",
                file=sys.stderr,
            )
        if r.used_llm:
            print(f"[lrcgen] LLM corrected: {os.path.basename(r.audio_path)}", file=sys.stderr)
        print(f"[lrcgen] wrote: {r.out_path}", file=sys.stderr)

    asyncio.run(runner())


if __name__ == "__main__":
    main()
