import re
from .styles import ANSI


STYLE_RE = re.compile(r"\[([a-zA-Z0-9_+]+):(.*?)\]")
BOLD_RE = re.compile(r"\*\*(.*?)\*\*")
UNDERLINE_RE = re.compile(r"__(.*?)__")
STRIKE_RE = re.compile(r"~~(.*?)~~")

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def parse(text: str) -> str:
    return _parse_block(text, [])


def _parse_block(text: str, style_stack):
    # blocos [style: ...]
    def repl(match):
        styles = match.group(1).split("+")
        content = match.group(2)

        ansi_start = ""
        ansi_end = ANSI["reset"]

        new_stack = style_stack.copy()

        for s in styles:
            code = ANSI.get(s)
            if code:
                ansi_start += code
                new_stack.append(s)

        inner = _parse_block(content, new_stack)

        # restaura estilos anteriores após reset
        restore = "".join(ANSI.get(s, "") for s in style_stack)

        return f"{ansi_start}{inner}{ansi_end}{restore}"

    text = STYLE_RE.sub(repl, text)

    # estilos inline — herdam stack
    def inline(style_key):
        return lambda m: (
            f"{ANSI[style_key]}{m.group(1)}{ANSI['reset']}"
            + "".join(ANSI.get(s, "") for s in style_stack)
        )

    text = BOLD_RE.sub(inline("bold"), text)
    text = UNDERLINE_RE.sub(inline("underline"), text)
    text = STRIKE_RE.sub(inline("strike"), text)

    return text


def strip_tags(text: str) -> str:
    """
    Remove ANSI codes e sintaxe de estilos
    (usado para logs em arquivo / JSON)
    """
    # remove ANSI
    text = ANSI_RE.sub("", text)

    # remove blocos [style:...]
    text = STYLE_RE.sub(lambda m: m.group(2), text)

    # remove markdown
    text = BOLD_RE.sub(r"\1", text)
    text = UNDERLINE_RE.sub(r"\1", text)
    text = STRIKE_RE.sub(r"\1", text)

    return text
