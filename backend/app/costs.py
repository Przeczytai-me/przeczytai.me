from dataclasses import dataclass

from app.pricing import DEFAULT_PRICES, PRICE_BOOK_VERSION
from app.splitting import split_text


CHARS_PER_MINUTE = 900
ASSUMED_BITRATE_BPS = 48_000
USD_MICROS = 1_000_000


@dataclass(frozen=True)
class RunUsage:
    chars_synthesized: int
    chunks: int
    audio_ms: int
    stored_bytes: int
    compute_ms_by_stage: dict[str, int]
    lambda_memory_mb: int
    vendor: str
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0

    @property
    def compute_ms(self) -> int:
        return sum(self.compute_ms_by_stage.values())


@dataclass(frozen=True)
class CostBreakdown:
    usage: RunUsage
    price_book_version: str
    tts_usd_micros: int
    llm_usd_micros: int
    compute_usd_micros: int
    storage_usd_micros: int
    platform_usd_micros: int
    total_usd_micros: int


def _usd_micros(dollars: float) -> int:
    return round(dollars * USD_MICROS)


def estimate_cost(
    usage: RunUsage, prices: dict[str, float] | None = None
) -> CostBreakdown:
    prices = prices or DEFAULT_PRICES
    tts = _usd_micros(
        usage.chars_synthesized
        / 1_000_000
        * prices.get(f"tts.{usage.vendor}", prices["tts.default"])
    )
    llm = _usd_micros(
        usage.llm_input_tokens / 1_000_000 * prices["llm.input"]
        + usage.llm_output_tokens / 1_000_000 * prices["llm.output"]
    )
    compute = _usd_micros(
        usage.lambda_memory_mb
        / 1024
        * usage.compute_ms
        / 1000
        * prices["lambda.gb_second"]
        + prices["lambda.request"]
    )
    storage = _usd_micros(
        usage.stored_bytes / 1_000_000_000 * prices["s3.gb_month"]
        + (usage.chunks + 4) / 1000 * prices["s3.per_1k_put"]
    )
    platform = _usd_micros(prices["platform.per_run"])
    components = (tts, llm, compute, storage, platform)
    return CostBreakdown(
        usage=usage,
        price_book_version=PRICE_BOOK_VERSION,
        tts_usd_micros=tts,
        llm_usd_micros=llm,
        compute_usd_micros=compute,
        storage_usd_micros=storage,
        platform_usd_micros=platform,
        total_usd_micros=sum(components),
    )


def usage_from_text(
    text: str,
    vendor: str,
    *,
    max_chunk_chars: int,
    lambda_memory_mb: int,
    lambda_timeout_ms: int,
) -> RunUsage:
    chunks = split_text(text, max_chunk_chars)
    audio_ms = round(len(text) / CHARS_PER_MINUTE * 60_000)
    stored_bytes = len(text.encode()) * 2 + round(audio_ms / 1000 * ASSUMED_BITRATE_BPS / 8)
    return RunUsage(
        chars_synthesized=len(text),
        chunks=len(chunks),
        audio_ms=audio_ms,
        stored_bytes=stored_bytes,
        compute_ms_by_stage={"estimated": lambda_timeout_ms},
        lambda_memory_mb=lambda_memory_mb,
        vendor=vendor,
    )
