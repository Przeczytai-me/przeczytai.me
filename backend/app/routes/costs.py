import calendar
import hashlib
from collections import defaultdict
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query

from app.auth import CurrentUser, require_admin
from app.config import Settings, get_settings
from app.costs import USD_MICROS, estimate_cost, usage_from_text
from app.models import ReadingCreateRequest
from app.pricing import PRICE_BOOK_VERSION, get_prices
from app.repositories.readings import ReadingRepository
from app.routes.readings import get_reading_repository
from app.tts import TTS_PROVIDERS

router = APIRouter(prefix="/api/v1/costs", tags=["costs"])
RUN_RESULT_LIMIT = 1_000
COMPONENTS = ("tts", "llm", "compute", "storage", "platform")
BUDGET_THRESHOLDS = [50, 80, 95]


def _usd(micros: int | float | None) -> float:
    return float(micros or 0) / USD_MICROS


def _month_from_item(item: dict) -> str:
    return str(item.get("sk", "")).split("#", 1)[-1]


def _user_ref(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()[:8]


def _components(item: dict) -> dict[str, float]:
    return {name: _usd(item.get(f"{name}_usd_micros")) for name in COMPONENTS}


def _month_keys(count: int, now: datetime) -> set[str]:
    year, month = now.year, now.month
    result = set()
    for _ in range(count):
        result.add(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year -= 1
            month = 12
    return result


def _serialize_month(item: dict) -> dict:
    return {
        "month": _month_from_item(item),
        "total_usd": _usd(item.get("total_usd_micros")),
        "runs": int(item.get("runs", 0)),
        "chars": int(item.get("chars", 0)),
        "audio_ms": int(item.get("audio_ms", 0)),
        "components": _components(item),
    }


def _serialize_user(item: dict, month: str) -> dict:
    user_id = str(item.get("sk", "")).removeprefix(f"COSTUSER#{month}#")
    return {
        "user_ref": _user_ref(user_id),
        "total_usd": _usd(item.get("total_usd_micros")),
        "runs": int(item.get("runs", 0)),
    }


def _serialize_run(item: dict) -> dict:
    return {
        "reading_id": item.get("reading_id"),
        "created_at": item.get("created_at"),
        "vendor": item.get("vendor"),
        "char_count": int(item.get("chars", 0)),
        "total_usd": _usd(item.get("total_usd_micros")),
        "components": _components(item),
        "usage": {
            "chars_synthesized": int(item.get("chars", 0)),
            "chunks": int(item.get("chunks", 0)),
            "audio_ms": int(item.get("audio_ms", 0)),
            "stored_bytes": int(item.get("stored_bytes", 0)),
            "lambda_memory_mb": int(item.get("lambda_memory_mb", 0)),
            "compute_ms_by_stage": item.get("compute_ms_by_stage", {}),
        },
    }


@router.get("")
async def get_costs(
    months: int = Query(default=6, ge=1, le=24),
    _: CurrentUser = Depends(require_admin),
    repo: ReadingRepository = Depends(get_reading_repository),
    settings: Settings = Depends(get_settings),
) -> dict:
    now = datetime.now(UTC)
    current_month = now.strftime("%Y-%m")
    selected_months = _month_keys(months, now)
    month_items = repo.get_system_month_costs(months)
    user_items = repo.list_user_month_costs(current_month)
    run_items = repo.list_run_costs(RUN_RESULT_LIMIT)
    costed_runs = [
        item
        for item in run_items
        if item.get("total_usd_micros") is not None
        and str(item.get("sk", "")).split("#")[1] in selected_months
    ]

    by_month = {_month_from_item(item): item for item in month_items}
    current = by_month.get(current_month, {})
    previous_date = datetime(now.year - (now.month == 1), (now.month - 2) % 12 + 1, 1, tzinfo=UTC)
    previous = by_month.get(previous_date.strftime("%Y-%m"), {})
    total_micros = sum(int(item.get("total_usd_micros", 0)) for item in month_items)
    total_runs = sum(int(item.get("runs", 0)) for item in month_items)
    month_micros = int(current.get("total_usd_micros", 0))
    month_runs = int(current.get("runs", 0))
    month_chars = int(current.get("chars", 0))
    month_audio_ms = int(current.get("audio_ms", 0))

    days: dict[str, dict[str, int]] = defaultdict(lambda: {"total_usd_micros": 0, "runs": 0})
    vendors: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"total_usd_micros": 0, "runs": 0, "chars": 0}
    )
    for item in costed_runs:
        day = str(item.get("created_at", ""))[:10]
        vendor = str(item.get("vendor", "unknown"))
        voice = str(item.get("voice", "unknown"))
        days[day]["total_usd_micros"] += int(item["total_usd_micros"])
        days[day]["runs"] += 1
        vendors[(vendor, voice)]["total_usd_micros"] += int(item["total_usd_micros"])
        vendors[(vendor, voice)]["runs"] += 1
        vendors[(vendor, voice)]["chars"] += int(item.get("chars", 0))

    monthly_limit = settings.monthly_budget_usd
    month_spent = _usd(month_micros)
    projected = month_spent / now.day * calendar.monthrange(now.year, now.month)[1]
    component_totals = _components(current)
    return {
        "currency": "USD",
        "price_book_version": PRICE_BOOK_VERSION,
        "budget": {
            "month_spent_usd": month_spent,
            "projected_month_usd": projected,
            "monthly_limit_usd": monthly_limit,
            "utilization": (
                month_spent / monthly_limit * 100 if monthly_limit and monthly_limit > 0 else None
            ),
            "thresholds": BUDGET_THRESHOLDS,
        },
        "totals": {
            "all_time_usd": _usd(total_micros),
            "month_usd": month_spent,
            "previous_month_usd": _usd(previous.get("total_usd_micros")),
            "runs_all_time": total_runs,
            "runs_month": month_runs,
            "chars_month": month_chars,
            "audio_ms_month": month_audio_ms,
            "avg_run_usd": _usd(total_micros) / total_runs if total_runs else 0,
            "usd_per_1k_chars": month_spent / month_chars * 1000 if month_chars else 0,
            "usd_per_audio_minute": (
                month_spent / month_audio_ms * 60_000 if month_audio_ms else 0
            ),
            "retained_storage_usd_per_month": _usd(current.get("storage_usd_micros")),
            "active_users_month": len(user_items),
        },
        "months": [_serialize_month(item) for item in sorted(month_items, key=_month_from_item)],
        "days": [
            {
                "date": day,
                "total_usd": _usd(values["total_usd_micros"]),
                "runs": values["runs"],
            }
            for day, values in sorted(days.items())
        ],
        "components": component_totals,
        "vendors": [
            {
                "vendor": vendor,
                "voice": voice,
                "total_usd": _usd(values["total_usd_micros"]),
                "runs": values["runs"],
                "chars": values["chars"],
            }
            for (vendor, voice), values in sorted(vendors.items())
        ],
        "users": [
            _serialize_user(item, current_month)
            for item in sorted(
                user_items, key=lambda value: int(value.get("total_usd_micros", 0)), reverse=True
            )
            if item.get("total_usd_micros") is not None
        ],
        "runs": [
            _serialize_run(item)
            for item in sorted(
                costed_runs, key=lambda value: str(value.get("created_at", "")), reverse=True
            )
        ],
        "limits": {
            "max_text_chars": settings.max_text_chars,
            "max_run_cost_usd": settings.max_run_cost_usd,
            "monthly_budget_usd": settings.monthly_budget_usd,
        },
    }


@router.post("/estimate")
async def estimate_costs(
    request: ReadingCreateRequest,
    _: CurrentUser = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    original_text = request.original_text
    prices = get_prices(settings.cost_price_overrides)
    estimates = []
    chunk_count = 0
    for vendor, provider in TTS_PROVIDERS.items():
        usage = usage_from_text(
            original_text,
            vendor,
            max_chunk_chars=settings.max_chunk_chars,
            lambda_memory_mb=settings.lambda_memory_mb,
            lambda_timeout_ms=settings.lambda_timeout_ms,
        )
        cost = estimate_cost(usage, prices)
        chunk_count = usage.chunks
        rejection = None
        if len(original_text) > settings.max_text_chars:
            rejection = {
                "code": "payload_too_large",
                "message": f"Text must be {settings.max_text_chars} characters or fewer",
            }
        elif provider.max_input_chars is not None and len(original_text) > provider.max_input_chars:
            rejection = {
                "code": "payload_too_large",
                "message": f"{vendor} input must be {provider.max_input_chars} characters or fewer",
            }
        elif cost.total_usd_micros > settings.max_run_cost_usd * USD_MICROS:
            rejection = {
                "code": "cost_limit_exceeded",
                "message": "Estimated reading cost exceeds the per-run limit",
            }
        estimates.append(
            {
                "vendor": str(vendor),
                "voice": provider.default_voice,
                "estimated_audio_ms": usage.audio_ms,
                "allowed": rejection is None,
                "rejection": rejection,
                "cost": {
                    "total_usd": _usd(cost.total_usd_micros),
                    "components": _components(cost.__dict__),
                },
            }
        )

    return {
        "char_count": len(original_text),
        "chunk_count": chunk_count,
        "vendors": estimates,
        "limits": {
            "max_text_chars": settings.max_text_chars,
            "max_run_cost_usd": settings.max_run_cost_usd,
        },
        "price_book_version": PRICE_BOOK_VERSION,
    }
