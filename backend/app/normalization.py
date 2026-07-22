import re


# Identifier stored in reading metadata for the current normalization rule set.
RULE_BASED_NORMALIZATION_VERSION = "regex-v1"


_MARKDOWN_LINK_RE = re.compile(
    r"(?<!!)\[([^\]\n]+)\]\(\s*(?:[^()\s]+|\([^()\s]*\))+"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
_YEAR_ABBREVIATION_RE = re.compile(r"(?<!\w)(\d+)[ \t]*r\.(?!\w)", re.IGNORECASE)
_PUNCTUATION_TRANSLATION = str.maketrans(
    {
        "„": '"',
        "”": '"',
        "“": '"',
        "«": '"',
        "»": '"',
        "‚": "'",
        "‘": "'",
        "’": "'",
        "–": "-",
        "—": "-",
        "―": "-",
    }
)
_ABBREVIATIONS = (
    (re.compile(r"(?<!\w)np\.(?!\w)", re.IGNORECASE), "na przykład"),
    (re.compile(r"(?<!\w)tzn\.(?!\w)", re.IGNORECASE), "to znaczy"),
    (re.compile(r"(?<!\w)m\.in\.(?!\w)", re.IGNORECASE), "między innymi"),
    (re.compile(r"(?<!\w)itd\.(?!\w)", re.IGNORECASE), "i tak dalej"),
    (re.compile(r"(?<!\w)itp\.(?!\w)", re.IGNORECASE), "i tym podobne"),
    (re.compile(r"(?<!\w)tj\.(?!\w)", re.IGNORECASE), "to jest"),
    (re.compile(r"(?<!\w)ok\.(?!\w)", re.IGNORECASE), "około"),
    (re.compile(r"(?<!\w)zł(?!\w)", re.IGNORECASE), "złotych"),
)


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_punctuation(text: str) -> str:
    text = re.sub(r"!+", "!", text)
    text = re.sub(r"\?+", "?", text)
    text = re.sub(r"\.{4,}", "…", text)
    return text.translate(_PUNCTUATION_TRANSLATION)


def _normalize_links(text: str) -> str:
    return _MARKDOWN_LINK_RE.sub(r"\1", text)


def _expand_abbreviation(match: re.Match[str], replacement: str) -> str:
    if match.group()[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _normalize_abbreviations(text: str) -> str:
    text = _YEAR_ABBREVIATION_RE.sub(r"\1 roku", text)
    for pattern, replacement in _ABBREVIATIONS:
        text = pattern.sub(lambda match, value=replacement: _expand_abbreviation(match, value), text)
    return text


_RULES = (
    _normalize_whitespace,
    _normalize_punctuation,
    _normalize_links,
    _normalize_abbreviations,
)


def normalize(text: str) -> str:
    for rule in _RULES:
        text = rule(text)
    return text


async def ai_normalize(text: str) -> str:
    """Placeholder for the future Claude API (anthropic SDK) normalization pass.

    Runs after the regex rule pipeline (normalize()). Any failure in the real
    implementation must fall back to the regex-normalized result. Currently a
    no-op stub returning the input unchanged.
    """
    return text
