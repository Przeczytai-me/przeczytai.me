import pytest

from app import normalization


def apply_readings(text: str, pairs: list[dict[str, str]] | None) -> str:
    return normalization.apply_abbreviation_readings(text, pairs)


def test_apply_abbreviation_at_sentence_start() -> None:
    """Replace a dotted abbreviation at the start of a sentence."""
    pairs = [{"abbreviation": "Np.", "read_as": "Na przykład"}]

    assert apply_readings("Np. Ala ma kota.", pairs) == "Na przykład Ala ma kota."


def test_apply_abbreviation_in_mid_text() -> None:
    """Replace a bounded abbreviation in the middle of text."""
    pairs = [{"abbreviation": "PKP", "read_as": "Pe Ka Pe"}]

    assert apply_readings("Podróżuję przez PKP, codziennie.", pairs) == (
        "Podróżuję przez Pe Ka Pe, codziennie."
    )


@pytest.mark.parametrize(
    ("source", "pairs", "expected"),
    [
        (
            "ANp. Np.ala Np. Ala",
            [{"abbreviation": "Np.", "read_as": "Na przykład"}],
            "ANp. Np.ala Na przykład Ala",
        ),
        (
            "ANp NpA Np.",
            [{"abbreviation": "Np", "read_as": "en pe"}],
            "ANp NpA en pe.",
        ),
    ],
)
def test_apply_abbreviation_does_not_replace_inside_words(
    source: str,
    pairs: list[dict[str, str]],
    expected: str,
) -> None:
    """Require non-word boundaries on both sides of each abbreviation."""
    assert apply_readings(source, pairs) == expected


def test_apply_abbreviation_replaces_all_occurrences() -> None:
    """Replace every bounded occurrence of an abbreviation."""
    pairs = [{"abbreviation": "PKP", "read_as": "Pe Ka Pe"}]

    assert apply_readings("PKP oraz PKP, potem PKP.", pairs) == (
        "Pe Ka Pe oraz Pe Ka Pe, potem Pe Ka Pe."
    )


def test_apply_abbreviation_is_case_sensitive() -> None:
    """Leave differently cased spellings unchanged."""
    pairs = [{"abbreviation": "PKP", "read_as": "Pe Ka Pe"}]

    assert apply_readings("PKP pkp Pkp", pairs) == "Pe Ka Pe pkp Pkp"


def test_apply_abbreviation_trims_pair_values() -> None:
    """Trim the abbreviation and spoken replacement before applying a pair."""
    pairs = [{"abbreviation": "  PKP\t", "read_as": "  Pe Ka Pe  "}]

    assert apply_readings("PKP.", pairs) == "Pe Ka Pe."


def test_apply_abbreviation_processes_pairs_in_order() -> None:
    """Apply later pairs to the output produced by earlier pairs."""
    pairs = [
        {"abbreviation": "ABC", "read_as": "XYZ"},
        {"abbreviation": "XYZ", "read_as": "iks igrek zet"},
    ]

    assert apply_readings("ABC.", pairs) == "iks igrek zet."


@pytest.mark.parametrize("pairs", [None, []], ids=["none", "empty-list"])
def test_apply_abbreviation_with_no_pairs_returns_text_unchanged(
    pairs: list[dict[str, str]] | None,
) -> None:
    """Return the exact input text when no abbreviation pairs are supplied."""
    text = "PKP i Np. pozostają bez zmian."

    assert apply_readings(text, pairs) == text
