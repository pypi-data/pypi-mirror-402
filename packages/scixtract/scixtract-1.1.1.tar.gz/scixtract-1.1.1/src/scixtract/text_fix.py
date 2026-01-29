from __future__ import annotations

import re


def fix_paragraph_hyphenation(text: str, *, infer_paragraphs: bool = True) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"([A-Za-z0-9])-\n([A-Za-z0-9])", r"\1\2", text)

    if infer_paragraphs and "\n\n" not in text:
        text = re.sub(r"([.!?][\"'\)\]]*)\n(?=[A-Z])", r"\1\n\n", text)

    paragraphs = re.split(r"\n\s*\n", text.strip())
    fixed: list[str] = []
    for p in paragraphs:
        p = re.sub(r"\s*\n\s*", " ", p).strip()
        p = re.sub(r"[ \t]+", " ", p)
        fixed.append(p)
    return "\n\n".join(fixed) + "\n"
