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
        ("Odwiedź https://example.com teraz", "Odwiedź link teraz"),
        ("Odwiedź www.example.com teraz", "Odwiedź link teraz"),
        ("Napisz do user@example.com dzisiaj", "Napisz do link dzisiaj"),
        ("To zwykłe zdanie.", "To zwykłe zdanie."),
        ("Kod @home pozostaje.", "Kod @home pozostaje."),
    ],
)
def test_normalize_bare_links(source: str, expected: str) -> None:
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
        "  Np.  sprawdź https://example.com!!!\n\n\nPotem napisz do user@example.com??  ",
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
            "Na przykład Jan ma konto!\n\nNapisz do link? To i tak dalej działa.",
        ),
        (
            "Koszt to  20 zł.... Sprawdź www.example.com\nTzn.  zapłać ok.  jutra!!!",
            "Koszt to 20 złotych… Sprawdź link\nTo znaczy zapłać około jutra!",
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
