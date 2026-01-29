# lrcgen

AI-powered LRC generator using Whisper + optional LLM correction.

## Install
```bash
pip install lrcgen
```

## Usage

```bash
lrcgen input/ output/
lrcgen input/ output/ --offline
lrcgen input/ output/ --online

# single file
lrcgen --audio input/song.mp3 --output out.lrc --offline
```

## Features

* Offline Whisper transcription
* Optional LLM correction
* Simplified Chinese output
* Batch processing