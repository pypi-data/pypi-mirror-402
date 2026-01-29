import whisper
from .utils import basic_clean


class WhisperRecognizer:
    def __init__(self, model_name="medium", language="zh"):
        self.model = whisper.load_model(model_name)
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
