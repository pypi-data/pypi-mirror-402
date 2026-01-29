import re
from opencc import OpenCC

cc = OpenCC("t2s")


def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"[{minutes:02d}:{seconds:05.2f}]"


def basic_clean(text: str) -> str:
    """
    繁转简 + 基础清洗
    """
    text = cc.convert(text)
    text = re.sub(r"[，。！？、；：]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
