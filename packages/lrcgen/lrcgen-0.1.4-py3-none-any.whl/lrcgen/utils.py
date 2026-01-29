import re

try:
    from opencc import OpenCC

    _cc = OpenCC("t2s")
except ModuleNotFoundError:  # optional dependency
    _cc = None


def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"[{minutes:02d}:{seconds:05.2f}]"


def basic_clean(text: str) -> str:
    """
    繁转简 + 基础清洗
    """
    if _cc:
        text = _cc.convert(text)
    text = re.sub(r"[，。！？、；：]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
