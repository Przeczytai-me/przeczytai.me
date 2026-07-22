import asyncio
import inspect

import pytest

from app.normalization import ai_normalize, normalize


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("  Ala\t\tma   kota.  ", "Ala ma kota."),
        ("\n\t  Ala ma kota. \n", "Ala ma kota."),
        ("a\n\n\nb", "a\n\nb"),
        ("a\n\n\n\nb", "a\n\nb"),
        ("Ala ma kota.\nKot śpi.", "Ala ma kota.\nKot śpi."),
    ],
)
def test_normalize_whitespace(source: str, expected: str) -> None:
    assert normalize(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Wow!!!", "Wow!"),
        ("Really??", "Really?"),
        ("Poczekaj.....", "Poczekaj…"),
        ("Koniec. Tak! Serio?", "Koniec. Tak! Serio?"),
        ("Poczekaj...", "Poczekaj..."),
    ],
)
def test_normalize_punctuation(source: str, expected: str) -> None:
    assert normalize(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Odwiedź https://example.com teraz", "Odwiedź https://example.com teraz"),
        ("Odwiedź www.example.com teraz", "Odwiedź www.example.com teraz"),
        ("Napisz do user@example.com dzisiaj", "Napisz do user@example.com dzisiaj"),
    ],
)
def test_normalize_preserves_links_embedded_in_plain_text(source: str, expected: str) -> None:
    assert normalize(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Przeczytaj [dokumentację](https://example.com/docs).", "Przeczytaj dokumentację."),
        ("Sprawdź [nasz serwis](www.example.com).", "Sprawdź nasz serwis."),
        (
            '[opis wersji](https://example.com/releases/v2 "Wydanie drugie")',
            "opis wersji",
        ),
        ("Zobacz [sekcję](../docs/start.md).", "Zobacz sekcję."),
    ],
)
def test_normalize_markdown_links_keeps_only_visible_text(source: str, expected: str) -> None:
    assert normalize(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Np. to działa.", "Na przykład to działa."),
        ("To np. działa.", "To na przykład działa."),
        ("Tzn. to działa.", "To znaczy to działa."),
        ("To tzn. działa.", "To to znaczy działa."),
        ("M.in. to działa.", "Między innymi to działa."),
        ("To m.in. działa.", "To między innymi działa."),
        ("Itd. omówimy później.", "I tak dalej omówimy później."),
        ("Wymieniamy itd. elementy.", "Wymieniamy i tak dalej elementy."),
        ("Itp. można wymieniać.", "I tym podobne można wymieniać."),
        ("Dodaj owoce itp. produkty.", "Dodaj owoce i tym podobne produkty."),
        ("Tj. właściwy wynik.", "To jest właściwy wynik."),
        ("Wynik, tj. odpowiedź.", "Wynik, to jest odpowiedź."),
        ("Ok. stu osób przyszło.", "Około stu osób przyszło."),
        ("Było ok. stu osób.", "Było około stu osób."),
        ("Zł to polska waluta.", "Złotych to polska waluta."),
        ("Cena w zł wzrosła.", "Cena w złotych wzrosła."),
    ],
)
def test_normalize_polish_abbreviations(source: str, expected: str) -> None:
    assert normalize(source) == expected


@pytest.mark.parametrize(
    "text",
    [
        "Rozdział pozostaje bez zmian.",
    ],
)
def test_normalize_does_not_expand_abbreviation_lookalikes(text: str) -> None:
    assert normalize(text) == text


@pytest.mark.parametrize(
    "text",
    [
        "  Np.  sprawdź [stronę](https://example.com)!!!\n\n\nPotem napisz do user@example.com??  ",
        "Koszt to 20 zł..... Tzn.  dużo.",
        "Czysty tekst.\nDrugi wiersz?",
    ],
)
def test_normalize_is_idempotent(text: str) -> None:
    normalized = normalize(text)

    assert normalize(normalized) == normalized


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "\nNp.  Jan\tma konto!!!\n\n\n\nNapisz do user@example.com??  To itd. działa.\n",
            "Na przykład Jan ma konto!\n\nNapisz do user@example.com? To i tak dalej działa.",
        ),
        (
            "Koszt to  20 zł.... Sprawdź [cennik](www.example.com)\nTzn.  zapłać ok.  jutra!!!",
            "Koszt to 20 złotych… Sprawdź cennik\nTo znaczy zapłać około jutra!",
        ),
    ],
)
def test_normalize_realistic_polish_paragraphs(source: str, expected: str) -> None:
    assert normalize(source) == expected


def test_normalize_clean_text_passes_through_unchanged() -> None:
    text = "Ala ma kota.\nKot śpi spokojnie."

    assert normalize(text) == text


def test_ai_normalize_is_async_noop() -> None:
    text = "Tekst pozostaje bez zmian."

    assert inspect.iscoroutinefunction(ai_normalize)
    assert asyncio.run(ai_normalize(text)) == text


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("„Ala” powiedziała “cześć”.", '"Ala" powiedziała "cześć".'),
        ("«Zdanie» w cudzysłowie.", '"Zdanie" w cudzysłowie.'),
        ("To ‚jest' ‘przykład’.", "To 'jest' 'przykład'."),
        ("Zakres 2020–2024 i pauza — tak, myślnik ― też.", "Zakres 2020-2024 i pauza - tak, myślnik - też."),
        ('Zwykłe "cudzysłowy" i \'apostrofy\' bez zmian.', 'Zwykłe "cudzysłowy" i \'apostrofy\' bez zmian.'),
    ],
)
def test_normalize_quotes_and_dashes(source: str, expected: str) -> None:
    assert normalize(source) == expected


@pytest.mark.parametrize(
    "text",
    [
        "„Ala” powiedziała “cześć”.",
        "Zakres 2020–2024 i pauza — tak, myślnik ― też.",
    ],
)
def test_normalize_quotes_and_dashes_is_idempotent(text: str) -> None:
    normalized = normalize(text)

    assert normalize(normalized) == normalized


def test_normalize_plain_url_preserves_trailing_polish_closing_quote() -> None:
    assert normalize("„Zobacz https://example.com”") == '"Zobacz https://example.com"'


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("W 2024 r. wydano książkę.", "W 2024 roku wydano książkę."),
        ("W 1999 r. urodził się.", "W 1999 roku urodził się."),
    ],
)
def test_normalize_year_abbreviation(source: str, expected: str) -> None:
    assert normalize(source) == expected


@pytest.mark.parametrize(
    "text",
    [
        "Proszę o r. wydania dokumentu.",
        "Litera r. nie jest rokiem.",
    ],
)
def test_normalize_year_abbreviation_requires_preceding_number(text: str) -> None:
    assert normalize(text) == text
