import re
from dataclasses import dataclass


NO_BREAK_ABBREVIATIONS = frozenset(
    {
        "np.",
        "itd.",
        "itp.",
        "tzn.",
        "tj.",
        "m.in.",
        "prof.",
        "dr.",
        "mgr.",
        "inż.",
        "ul.",
        "św.",
        "r.",
        "ok.",
        "nr.",
        "godz.",
    }
)

_BLANK_LINES = re.compile(r"(?:\r?\n[^\S\r\n]*){2,}")
_LIST_ITEM = re.compile(r"(?:[-*]|\d+\.)\s+")
_INITIAL = re.compile(r"[A-ZĄĆĘŁŃÓŚŹŻ]\.")
_WHITESPACE = re.compile(r"\s+")
_OPENING_QUOTES = frozenset('"\'„“«‘')
_TOKEN_OPENERS = '"\'„“«‘([{'
_TOKEN_LOOKBEHIND = 32


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str
    char_count: int


def split_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    for block in _BLANK_LINES.split(text):
        lines = block.strip().splitlines()
        normal_lines: list[str] = []
        list_lines: list[str] = []

        def flush_normal() -> None:
            if normal_lines:
                paragraphs.append("\n".join(normal_lines).strip())
                normal_lines.clear()

        def flush_list() -> None:
            if list_lines:
                paragraphs.append("\n".join(list_lines).strip())
                list_lines.clear()

        for line in lines:
            if line.startswith("#"):
                flush_normal()
                flush_list()
                paragraphs.append(line.strip())
            elif _LIST_ITEM.match(line):
                flush_normal()
                list_lines.append(line)
            else:
                flush_list()
                normal_lines.append(line)

        flush_normal()
        flush_list()

    return [paragraph for paragraph in paragraphs if paragraph]


def _is_sentence_boundary(text: str, punctuation_index: int) -> bool:
    following = _WHITESPACE.match(text, punctuation_index + 1)
    if not following:
        return False
    next_index = following.end()
    if next_index >= len(text):
        return False
    next_character = text[next_index]
    if not (
        next_character.isupper()
        or next_character.isdigit()
        or next_character in _OPENING_QUOTES
    ):
        return False

    if text[punctuation_index] == ".":
        window_start = max(0, punctuation_index + 1 - _TOKEN_LOOKBEHIND)
        token_start = punctuation_index
        while token_start > window_start and not text[token_start - 1].isspace():
            token_start -= 1
        token = text[token_start : punctuation_index + 1].lstrip(_TOKEN_OPENERS)
        if token.casefold() in NO_BREAK_ABBREVIATIONS or _INITIAL.fullmatch(token):
            return False

    return True


def _split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    start = 0
    for punctuation in re.finditer(r"[.!?…]", text):
        end = punctuation.end()
        if _is_sentence_boundary(text, punctuation.start()):
            sentences.append(text[start:end].strip())
            start = end
    sentences.append(text[start:].strip())
    return [sentence for sentence in sentences if sentence]


def _hard_split(text: str, max_chunk_chars: int) -> list[str]:
    pieces: list[str] = []
    remaining = text.strip()
    while len(remaining) > max_chunk_chars:
        boundaries = list(re.finditer(r"\s+", remaining[: max_chunk_chars + 1]))
        if not boundaries:
            pieces.append(remaining[:max_chunk_chars])
            remaining = remaining[max_chunk_chars:].lstrip()
            continue
        boundary = boundaries[-1]
        if boundary.start() == 0:
            remaining = remaining[boundary.end() :]
            continue
        pieces.append(remaining[: boundary.start()].rstrip())
        remaining = remaining[boundary.end() :].lstrip()
    if remaining:
        pieces.append(remaining)
    return pieces


def split_text(text: str, max_chunk_chars: int) -> list[Chunk]:
    if max_chunk_chars <= 0:
        raise ValueError("max_chunk_chars must be positive")

    chunks: list[str] = []
    current = ""

    def add(piece: str, separator: str) -> None:
        nonlocal current
        candidate = f"{current}{separator}{piece}" if current else piece
        if current and len(candidate) > max_chunk_chars:
            chunks.append(current)
            current = piece
        else:
            current = candidate

    for paragraph in split_paragraphs(text):
        if len(paragraph) <= max_chunk_chars:
            add(paragraph, "\n\n")
            continue

        first_piece = True
        for sentence in _split_sentences(paragraph):
            pieces = (
                [sentence]
                if len(sentence) <= max_chunk_chars
                else _hard_split(sentence, max_chunk_chars)
            )
            for piece in pieces:
                add(piece, "\n\n" if first_piece else " ")
                first_piece = False

    if current:
        chunks.append(current)

    return [Chunk(index, chunk, len(chunk)) for index, chunk in enumerate(chunks)]
