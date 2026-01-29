# lrcgen

AI-powered LRC generator using Whisper + optional LLM correction.

## Install
```bash
pip install lrcgen
```

## Requirements

- Offline transcription uses Whisper models (first run may download model files).
- Online correction requires `OPENAI_API_KEY` (or a compatible API via `OPENAI_BASE_URL`).

## Usage

```bash
# batch
lrcgen input/ output/
lrcgen input/ output/ --offline
lrcgen input/ output/ --online

# single file
lrcgen --audio input/song.mp3 --output out.lrc --offline

# choose whisper model/language
lrcgen --audio input/song.mp3 --output out.lrc --offline --model small --language zh

# module entrypoint (same as lrcgen command)
python -m lrcgen --audio input/song.mp3 --output out.lrc --offline

# version
python -m lrcgen --version
```

### Online config

Set env vars (e.g. via `.env`):

- `OPENAI_API_KEY=...`
- `OPENAI_BASE_URL=https://api.openai.com/v1` (optional)
- `OPENAI_MODEL=gpt-4o-mini` (optional)

## Library usage

```python
from lrcgen.api import generate_lrc_sync

generate_lrc_sync("input/song.mp3", "out.lrc", mode="offline")
```

## Project structure

```text
genlrc/
	README.md
	pyproject.toml
	music_to_lrc_batch.py
	lrcgen/
		__init__.py        # package version
		__main__.py        # enables: python -m lrcgen
		cli.py             # argparse CLI entrypoint
		api.py             # stable library API (sync + async)
		whisperer.py       # Whisper transcription wrapper
		corrector.py       # optional LLM correction + guardrails
		utils.py           # time formatting + basic text cleaning
		config.py          # env/.env config (OPENAI_*, etc.)
		input/             # optional local test inputs (not packaged)
		output/            # optional local outputs (not packaged)
	test/
		test.py            # small unittest suite
	tools/
		clean.py           # removes dist/build/cache artifacts
	.github/workflows/
		ci.yml             # CI build + checks
		publish.yml        # tag-based publish via PyPI Trusted Publishing (OIDC)
```

How it fits together:

- CLI: `lrcgen/cli.py` parses args and calls `lrcgen/api.py`.
- Core pipeline: `whisperer.py` transcribes audio → `utils.py` cleans → `corrector.py` optionally fixes lines → writes `.lrc`.
- Configuration: `config.py` loads environment variables (and `.env` if present).

## Features

* Offline Whisper transcription
* Optional LLM correction
* Simplified Chinese output
* Batch processing