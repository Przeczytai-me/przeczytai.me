from dataclasses import replace

from app import costs
from app.costs import CostBreakdown, RunUsage, estimate_cost, usage_from_text
from app.pricing import DEFAULT_PRICES, PRICE_BOOK_VERSION
from app.splitting import split_text

BASE_USAGE = RunUsage(
    chars_synthesized=1_000_000,
    chunks=1,
    audio_ms=60_000,
    stored_bytes=360_000,
    compute_ms_by_stage={"synthesize": 1_000},
    lambda_memory_mb=1024,
    vendor="openai",
)


def test_estimate_cost_components_match_hand_calculation() -> None:
    usage = RunUsage(
        chars_synthesized=2_000_000,
        chunks=996,
        audio_ms=120_000,
        stored_bytes=1_000_000_000,
        compute_ms_by_stage={"normalize": 10_000, "synthesize": 20_000, "merge": 30_000},
        lambda_memory_mb=1024,
        vendor="openai",
        llm_input_tokens=1_000_000,
        llm_output_tokens=2_000_000,
    )

    result = estimate_cost(usage)

    # 2M chars * $15/M = $30.
    assert result.tts_usd_micros == 30_000_000
    # 1M input * $3/M + 2M output * $15/M = $33.
    assert result.llm_usd_micros == 33_000_000
    # 1 GB * 60 s * $0.0000166667 + $0.0000002 = $0.001000202.
    assert result.compute_usd_micros == 1_000
    # 1 GB-month * $0.023 + 4 PUTs * $0.005/1000 = $0.02302.
    assert result.storage_usd_micros == 23_020
    # $0.00001 per run.
    assert result.platform_usd_micros == 10
    assert result.total_usd_micros == 63_024_030
    assert result.total_usd_micros == sum(
        (
            result.tts_usd_micros,
            result.llm_usd_micros,
            result.compute_usd_micros,
            result.storage_usd_micros,
            result.platform_usd_micros,
        )
    )


def test_edge_tts_is_free_but_total_cost_is_not_zero() -> None:
    result = estimate_cost(replace(BASE_USAGE, vendor="edge-tts"))

    assert result.tts_usd_micros == 0
    assert result.total_usd_micros > 0


def test_unknown_vendor_uses_default_tts_price() -> None:
    result = estimate_cost(replace(BASE_USAGE, vendor="unknown"))

    assert result.tts_usd_micros == 15_000_000


def test_run_usage_sums_compute_stages() -> None:
    usage = replace(BASE_USAGE, compute_ms_by_stage={"normalize": 41, "synthesize": 38_902, "merge": 610})

    assert usage.compute_ms == 39_553


def test_explicit_prices_override_defaults() -> None:
    prices = DEFAULT_PRICES | {"tts.openai": 2.0}

    result = estimate_cost(BASE_USAGE, prices=prices)

    assert result.tts_usd_micros == 2_000_000


def test_estimate_cost_carries_price_book_version() -> None:
    result = estimate_cost(BASE_USAGE)

    assert isinstance(result, CostBreakdown)
    assert result.price_book_version == PRICE_BOOK_VERSION


def test_usage_from_text_uses_real_chunks_and_full_timeout() -> None:
    text = "Ala ma kota. Ela ma psa."

    usage = usage_from_text(
        text,
        "openai",
        max_chunk_chars=12,
        lambda_memory_mb=1536,
        lambda_timeout_ms=123_456,
    )

    assert usage.chars_synthesized == 24
    assert usage.chunks == len(split_text(text, 12)) == 2
    assert usage.audio_ms == 1_600
    assert usage.stored_bytes == 9_648
    assert usage.compute_ms_by_stage == {"estimated": 123_456}
    assert usage.lambda_memory_mb == 1536
    assert usage.vendor == "openai"
    assert usage.llm_input_tokens == usage.llm_output_tokens == 0


def test_usage_from_empty_text_is_usable() -> None:
    usage = usage_from_text(
        "",
        "edge-tts",
        max_chunk_chars=100,
        lambda_memory_mb=1024,
        lambda_timeout_ms=1_000,
    )

    assert usage.chars_synthesized == usage.chunks == usage.audio_ms == usage.stored_bytes == 0
    assert usage.compute_ms_by_stage == {"estimated": 1_000}
    assert estimate_cost(usage).total_usd_micros > 0


def test_paid_vendor_estimate_is_not_driven_by_speech_rate(monkeypatch) -> None:
    text = "Ala ma kota. " * 5_000
    arguments = {
        "vendor": "openai",
        "max_chunk_chars": 3_000,
        "lambda_memory_mb": 1024,
        "lambda_timeout_ms": 900_000,
    }
    baseline = estimate_cost(usage_from_text(text, **arguments)).total_usd_micros

    monkeypatch.setattr(costs, "CHARS_PER_MINUTE", 450)
    halved = estimate_cost(usage_from_text(text, **arguments)).total_usd_micros
    monkeypatch.setattr(costs, "CHARS_PER_MINUTE", 1_800)
    doubled = estimate_cost(usage_from_text(text, **arguments)).total_usd_micros

    assert abs(halved - baseline) < baseline * 0.1
    assert abs(doubled - baseline) < baseline * 0.1


def test_storage_puts_do_not_scale_with_chunk_count() -> None:
    """Chunk MP3s never leave /tmp.

    Only four objects are ever PUT - original text, corrected text, timing map
    and the merged recording - so charging one PUT per chunk overstates a run
    with many chunks.
    """
    few = estimate_cost(replace(BASE_USAGE, chunks=1))
    many = estimate_cost(replace(BASE_USAGE, chunks=500))

    assert few.storage_usd_micros == many.storage_usd_micros
