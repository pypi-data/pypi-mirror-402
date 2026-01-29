import whisper
from typing import Optional

from .utils import basic_clean


class WhisperRecognizer:
    def __init__(self, model_name="medium", language="zh", device: Optional[str] = None):
        # device:
        # - None: let whisper/torch decide (usually uses GPU if available)
        # - "cpu"
        # - "cuda" or "cuda:0" / "cuda:1" ...
        self.model = whisper.load_model(model_name, device=device) if device else whisper.load_model(model_name)
        self.language = language

    def transcribe(self, audio_path: str):
        """
        返回：
        times: [float]
        lines: [str]
        """
        result = self.model.transcribe(
            audio_path,
            language=self.language,
            verbose=False
        )

        times, lines = [], []
        for seg in result["segments"]:
            text = basic_clean(seg["text"])
            if not text:
                continue
            times.append(seg["start"])
            lines.append(text)

        return times, lines
