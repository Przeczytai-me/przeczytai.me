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


def _normalize_year_abbreviation(text: str) -> str:
    return _YEAR_ABBREVIATION_RE.sub(r"\1 roku", text)


_RULES = (
    _normalize_whitespace,
    _normalize_punctuation,
    _normalize_links,
    _normalize_year_abbreviation,
)


def normalize(text: str) -> str:
    for rule in _RULES:
        text = rule(text)
    return text


def apply_abbreviation_readings(text: str, pairs: list[dict] | None) -> str:
    if not pairs:
        return text
    for pair in pairs:
        abbreviation = pair["abbreviation"].strip()
        read_as = pair["read_as"].strip()
        pattern = re.compile(rf"(?<!\w){re.escape(abbreviation)}(?!\w)")
        text = pattern.sub(lambda _, replacement=read_as: replacement, text)
    return text
