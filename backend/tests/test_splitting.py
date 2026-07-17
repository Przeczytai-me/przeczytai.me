import re
from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

from app.config import Settings
from app.splitting import Chunk, split_paragraphs, split_text


def assert_no_text_lost(original: str, chunks: list[Chunk | str]) -> None:
    """Assert that chunking preserves every non-whitespace character in order."""
    texts = [item.text if hasattr(item, "text") else item for item in chunks]
    assert re.sub(r"\s+", "", original) == re.sub(r"\s+", "", "".join(texts))


def test_chunk_is_a_frozen_dataclass() -> None:
    """Expose chunk metadata as immutable dataclass fields."""
    assert is_dataclass(Chunk)
    assert [field.name for field in fields(Chunk)] == ["index", "text", "char_count"]

    chunk = Chunk(index=0, text="abc", char_count=3)
    assert chunk.char_count == len(chunk.text)
    with pytest.raises(FrozenInstanceError):
        chunk.text = "changed"


def test_multi_paragraph_text_preserves_content_in_order() -> None:
    """Pack short paragraphs without losing or reordering their content."""
    text = "Pierwszy akapit.\n\nDrugi akapit.\n\nTrzeci akapit."

    chunks = split_text(text, max_chunk_chars=200)

    assert len(chunks) == 1
    assert_no_text_lost(text, chunks)


def test_polish_abbreviations_do_not_end_sentences() -> None:
    """Keep every supported Polish abbreviation attached to following text."""
    abbreviations = [
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
    ]

    for abbreviation in abbreviations:
        prefix = f"To {abbreviation} Kowalski"
        text = f"{prefix} omawiał niezwykle rozbudowany dokument"
        chunks = split_text(text, max_chunk_chars=len(prefix))

        assert "Kowalski" in chunks[0].text
        assert_no_text_lost(text, chunks)


def test_single_letter_initial_does_not_end_a_sentence() -> None:
    """Keep an uppercase initial attached to the following surname."""
    prefix = "Autor J. Kowalski"
    text = f"{prefix} przygotował niezwykle rozbudowany dokument"

    chunks = split_text(text, max_chunk_chars=len(prefix))

    assert "Kowalski" in chunks[0].text
    assert_no_text_lost(text, chunks)


def test_year_abbreviation_in_a_date_does_not_end_a_sentence() -> None:
    """Keep the year abbreviation in a date attached to following text."""
    prefix = "Spotkanie odbyło się 15 lipca 2026 r. Następnie"
    text = f"{prefix} omówiono niezwykle rozbudowany dokument"

    chunks = split_text(text, max_chunk_chars=len(prefix))

    assert "Następnie" in chunks[0].text
    assert_no_text_lost(text, chunks)


def test_decimal_number_does_not_end_a_sentence() -> None:
    """Keep a digit-dot-digit decimal number within one sentence."""
    prefix = "Wynik pomiaru to 3.5 Punktów"
    text = f"{prefix} w niezwykle rozbudowanym zestawieniu"

    chunks = split_text(text, max_chunk_chars=len(prefix))

    assert "Punktów" in chunks[0].text
    assert_no_text_lost(text, chunks)


def test_markdown_heading_is_a_separate_paragraph() -> None:
    """Keep a Markdown heading separate from surrounding paragraphs."""
    text = "Wprowadzenie.\n\n# Ważny nagłówek\n\nTreść rozdziału."

    assert split_paragraphs(text) == [
        "Wprowadzenie.",
        "# Ważny nagłówek",
        "Treść rozdziału.",
    ]


def test_markdown_list_items_stay_in_their_blocks() -> None:
    """Keep adjacent bullet and numbered items together by list block."""
    text = "- pierwszy\n* drugi\n\n1. jeden\n2. dwa"

    assert split_paragraphs(text) == ["- pierwszy\n* drugi", "1. jeden\n2. dwa"]


def test_paragraph_splitting_requires_a_blank_line() -> None:
    """Keep single-newline text together and split across multiple blank lines."""
    assert split_paragraphs("Pierwszy wiersz\nDrugi wiersz") == [
        "Pierwszy wiersz\nDrugi wiersz"
    ]
    assert split_paragraphs("Pierwszy akapit\n\n\nDrugi akapit") == [
        "Pierwszy akapit",
        "Drugi akapit",
    ]


def test_paragraph_just_under_limit_stays_in_one_chunk() -> None:
    """Keep a paragraph shorter than the character limit in one chunk."""
    text = "a" * 49

    chunks = split_text(text, max_chunk_chars=50)

    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].char_count == len(text)


def test_paragraph_just_over_limit_is_split() -> None:
    """Split an oversized paragraph into chunks within the character limit."""
    text = "krótkie słowa mieszczą się w kilku bezpiecznych częściach"
    max_chunk_chars = len(text) - 1

    chunks = split_text(text, max_chunk_chars=max_chunk_chars)

    assert len(chunks) > 1
    assert all(chunk.char_count == len(chunk.text) for chunk in chunks)
    assert all(chunk.char_count <= max_chunk_chars for chunk in chunks)
    assert_no_text_lost(text, chunks)


def test_sentence_boundaries_support_all_required_punctuation() -> None:
    """Split oversized paragraphs at each supported sentence punctuation mark."""
    text = "Pierwsza. Druga! Trzecia? Czwarta… Piąta."

    chunks = split_text(text, max_chunk_chars=10)

    assert [chunk.text.strip() for chunk in chunks] == [
        "Pierwsza.",
        "Druga!",
        "Trzecia?",
        "Czwarta…",
        "Piąta.",
    ]


def test_giant_sentence_is_hard_split_only_between_words() -> None:
    """Hard-split a giant sentence without cutting words or losing text."""
    text = " ".join(f"wyraz{index}" for index in range(20))
    max_chunk_chars = 30

    chunks = split_text(text, max_chunk_chars=max_chunk_chars)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= max_chunk_chars for chunk in chunks)
    assert " ".join(chunk.text.strip() for chunk in chunks).split() == text.split()
    assert_no_text_lost(text, chunks)


def test_chunk_indices_are_gapless_and_zero_based() -> None:
    """Number every produced chunk sequentially starting from zero."""
    text = " ".join(f"element{index}" for index in range(20))

    chunks = split_text(text, max_chunk_chars=25)

    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_default_max_chunk_chars_is_3000() -> None:
    """Default the maximum chunk length to 3000 characters."""
    assert Settings(_env_file=None).max_chunk_chars == 3000


def test_oversized_word_is_split_exactly_at_the_limit() -> None:
    """Hard-split a single word at the character limit when no whitespace exists."""
    chunks = split_text("abcdef", max_chunk_chars=3)

    assert [chunk.text for chunk in chunks] == ["abc", "def"]


def test_oversized_word_within_text_stays_within_the_limit() -> None:
    """Keep every chunk within the limit even when a word alone exceeds it."""
    text = "abcdef ghij"

    chunks = split_text(text, max_chunk_chars=3)

    assert all(chunk.char_count <= 3 for chunk in chunks)
    assert_no_text_lost(text, chunks)


def test_giant_unbroken_word_stays_within_the_limit() -> None:
    """Hard-split a very long unbroken word into chunks within the limit."""
    text = "a" * 10_000

    chunks = split_text(text, max_chunk_chars=3000)

    assert all(chunk.char_count <= 3000 for chunk in chunks)
    assert_no_text_lost(text, chunks)


def test_minimal_limit_of_one_does_not_loop_forever() -> None:
    """Produce single-character chunks without hanging when the limit is 1."""
    chunks = split_text("abc def", max_chunk_chars=1)

    assert all(chunk.char_count == 1 for chunk in chunks)


def test_sentence_initial_capitalized_abbreviation_does_not_end_a_sentence() -> None:
    """Keep a capitalized sentence-initial abbreviation attached to its sentence."""
    text = "Np. Aa bbb cc dd ee ff"

    chunks = split_text(text, max_chunk_chars=10)

    assert all(chunk.text.strip() != "Np." for chunk in chunks)


def test_parenthesized_abbreviation_does_not_end_a_sentence() -> None:
    """Keep a parenthesized abbreviation from causing a mid-paragraph split."""
    prefix = "Zdanie (np. tak) dalej"
    text = f"{prefix} ciągnie się przez niezwykle rozbudowany dokument"

    chunks = split_text(text, max_chunk_chars=len(prefix))

    assert "dalej" in chunks[0].text
    assert_no_text_lost(text, chunks)


def test_splitting_a_long_run_of_sentence_punctuation_is_fast() -> None:
    """Scan long paragraphs in roughly linear time."""
    import time

    text = "." * 32_000 + " A"

    start = time.perf_counter()
    split_text(text, max_chunk_chars=100)
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
