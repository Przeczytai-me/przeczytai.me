import json
import math


PRICE_BOOK_VERSION = "2026-08-05"
DEFAULT_PRICES = {
    "tts.edge-tts": 0.0,  # unverified: Edge TTS is exposed without a usage price
    "tts.openai": 15.0,  # unverified estimate; $0.015/min at 900 chars/min implies ~16.7
    "tts.default": 15.0,  # unverified: fallback uses the OpenAI TTS estimate
    "llm.input": 3.0,  # unverified: representative OpenAI input price per 1M tokens
    "llm.output": 15.0,  # unverified: representative OpenAI output price per 1M tokens
    "lambda.gb_second": 0.0000166667,  # unverified: AWS Lambda public x86 rate
    "lambda.request": 0.0000002,  # unverified: AWS Lambda public request rate
    "s3.gb_month": 0.023,  # unverified: AWS S3 Standard public storage rate
    "s3.per_1k_put": 0.005,  # unverified: AWS S3 Standard public PUT rate
    "platform.per_run": 0.00001,  # unverified: internal platform allowance
}


def get_prices(overrides_json: str | None = None) -> dict[str, float]:
    if overrides_json is None:
        return DEFAULT_PRICES.copy()
    try:
        overrides = json.loads(overrides_json)
        if not isinstance(overrides, dict):
            return DEFAULT_PRICES.copy()
        prices = DEFAULT_PRICES.copy()
        for key, value in overrides.items():
            if key not in DEFAULT_PRICES:
                continue
            try:
                price = float(value)
            except (TypeError, ValueError, OverflowError):
                continue
            if math.isfinite(price) and price >= 0:
                prices[key] = price
        return prices
    except (TypeError, ValueError):
        return DEFAULT_PRICES.copy()
