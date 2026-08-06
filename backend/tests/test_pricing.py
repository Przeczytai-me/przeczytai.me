import pytest

from app.pricing import DEFAULT_PRICES, PRICE_BOOK_VERSION, get_prices


def test_get_prices_returns_documented_defaults() -> None:
    assert get_prices() == {
        "tts.edge-tts": 0.0,
        "tts.openai": 15.0,
        "tts.default": 15.0,
        "llm.input": 3.0,
        "llm.output": 15.0,
        "lambda.gb_second": 0.0000166667,
        "lambda.request": 0.0000002,
        "s3.gb_month": 0.023,
        "s3.per_1k_put": 0.005,
        "platform.per_run": 0.00001,
    }


def test_get_prices_overrides_only_named_key() -> None:
    assert get_prices('{"tts.openai": 42}') == DEFAULT_PRICES | {"tts.openai": 42.0}


@pytest.mark.parametrize("value", ["not json", "[]", None])
def test_get_prices_ignores_invalid_overrides(value: str | None) -> None:
    assert get_prices(value) == DEFAULT_PRICES


def test_price_book_version_is_non_empty() -> None:
    assert isinstance(PRICE_BOOK_VERSION, str)
    assert PRICE_BOOK_VERSION
