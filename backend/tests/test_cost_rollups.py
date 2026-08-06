import re
from collections.abc import Callable
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

from app.repositories.readings import ReadingRepository


class FakeTable:
    def __init__(self, raise_conditional: bool = False) -> None:
        self.calls: list[dict[str, object]] = []
        self.raise_conditional = raise_conditional
        self.item: dict | None = None
        self.items: dict[tuple[object, object], dict] = {}
        self.query_items: list[dict] = []

    def update_item(self, **kwargs: object) -> None:
        self.calls.append(kwargs)
        if self.raise_conditional:
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "UpdateItem",
            )

        key = kwargs["Key"]
        assert isinstance(key, dict)
        stored = self.items.setdefault((key["pk"], key["sk"]), dict(key))
        values = kwargs["ExpressionAttributeValues"]
        assert isinstance(values, dict)
        for placeholder, value in values.items():
            field = str(placeholder).removeprefix(":")
            if field != "updated_at" and isinstance(value, int):
                stored[field] = int(stored.get(field, 0)) + value

    def put_item(self, **kwargs: object) -> None:
        self.calls.append(kwargs)
        item = kwargs["Item"]
        assert isinstance(item, dict)
        key = (item["pk"], item["sk"])
        if kwargs.get("ConditionExpression") is not None and key in self.items:
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "PutItem",
            )
        self.items[key] = dict(item)

    def get_item(self, **kwargs: object) -> dict:
        self.calls.append(kwargs)
        return {"Item": self.item} if self.item is not None else {}

    def query(self, **kwargs: object) -> dict:
        self.calls.append(kwargs)
        return {"Items": self.query_items}

    def scan(self, **kwargs: object) -> None:
        del kwargs
        pytest.fail("Cost rollups must be queried, not scanned")


def make_repository(table: FakeTable) -> ReadingRepository:
    repository = object.__new__(ReadingRepository)
    repository.table = table
    repository.processor_function_name = None
    return repository


EXPECTED_COUNTERS = {
    "total_usd_micros": 1234,
    "tts_usd_micros": 1000,
    "llm_usd_micros": 20,
    "compute_usd_micros": 101,
    "storage_usd_micros": 99,
    "platform_usd_micros": 14,
    "chars": 321,
    "audio_ms": 654,
    "runs": 1,
}
COUNTERS = tuple(EXPECTED_COUNTERS)
USAGE = SimpleNamespace(
    chars_synthesized=EXPECTED_COUNTERS["chars"],
    audio_ms=EXPECTED_COUNTERS["audio_ms"],
    chunks=7,
    stored_bytes=90_000,
    lambda_memory_mb=256,
    vendor="openai",
    compute_ms_by_stage={"normalize": 1, "synthesize": 90, "merge": 10},
    llm_input_tokens=0,
    llm_output_tokens=0,
)
COST = SimpleNamespace(
    total_usd_micros=EXPECTED_COUNTERS["total_usd_micros"],
    tts_usd_micros=EXPECTED_COUNTERS["tts_usd_micros"],
    llm_usd_micros=EXPECTED_COUNTERS["llm_usd_micros"],
    compute_usd_micros=EXPECTED_COUNTERS["compute_usd_micros"],
    storage_usd_micros=EXPECTED_COUNTERS["storage_usd_micros"],
    platform_usd_micros=EXPECTED_COUNTERS["platform_usd_micros"],
    price_book_version="2026-08-05",
    usage=USAGE,
)


def add_rollup(table: FakeTable, run_key: str = "job-1") -> None:
    make_repository(table).add_cost_rollup(
        "user-1",
        "2026-08",
        COST,
        reading_id="reading-1",
        voice="alloy",
        run_key=run_key,
    )


def test_add_cost_rollup_writes_month_user_and_run_records() -> None:
    table = FakeTable()

    add_rollup(table)

    assert len(table.calls) == 3
    update_keys = {tuple(call["Key"].values()) for call in table.calls if "Key" in call}
    assert update_keys == {
        ("SYSTEM", "COST#2026-08"),
        ("SYSTEM", "COSTUSER#2026-08#user-1"),
    }
    run_call = next(call for call in table.calls if "Item" in call)
    assert str(run_call["Item"]["sk"]).startswith("COSTRUN#2026-08#")


def test_month_and_user_rollups_use_atomic_counters() -> None:
    table = FakeTable()

    add_rollup(table)

    for call in (call for call in table.calls if "UpdateExpression" in call):
        expression = str(call["UpdateExpression"])
        values = call["ExpressionAttributeValues"]
        assert expression.startswith("SET ")
        assert "updated_at" in expression
        assert "ADD" in expression
        assert "ConditionExpression" not in call
        for field, amount in EXPECTED_COUNTERS.items():
            placeholder = re.search(rf"\b{field}\s+(:\w+)", expression)
            assert placeholder is not None
            assert values[placeholder.group(1)] == amount


def test_run_record_carries_everything_the_dashboard_needs() -> None:
    table = FakeTable()

    add_rollup(table)
    item = next(call["Item"] for call in table.calls if "Item" in call)

    assert item["pk"] == "SYSTEM"
    assert item["reading_id"] == "reading-1"
    assert item["owner_user_id"] == "user-1"
    assert item["vendor"] == "openai"
    assert item["voice"] == "alloy"
    assert item["total_usd_micros"] == EXPECTED_COUNTERS["total_usd_micros"]
    assert item["chars"] == EXPECTED_COUNTERS["chars"]
    assert item["audio_ms"] == EXPECTED_COUNTERS["audio_ms"]
    assert item["chunks"] == USAGE.chunks
    assert item["stored_bytes"] == USAGE.stored_bytes
    assert item["compute_ms_by_stage"] == USAGE.compute_ms_by_stage
    assert item["price_book_version"] == COST.price_book_version
    assert item["created_at"]


def test_each_run_key_gets_its_own_record_so_retries_are_not_lost() -> None:
    table = FakeTable()

    add_rollup(table, run_key="job-1")
    add_rollup(table, run_key="job-2")

    run_keys = [call["Item"]["sk"] for call in table.calls if "Item" in call]
    assert len(run_keys) == 2
    assert run_keys[0] != run_keys[1]


def test_add_cost_rollup_is_idempotent_for_the_same_run_key() -> None:
    table = FakeTable()

    add_rollup(table, run_key="job-1")
    add_rollup(table, run_key="job-1")

    month_item = table.items[("SYSTEM", "COST#2026-08")]
    user_item = table.items[("SYSTEM", "COSTUSER#2026-08#user-1")]
    month_counters = {field: month_item[field] for field in COUNTERS}
    user_counters = {field: user_item[field] for field in COUNTERS}
    run_records = [
        item for item in table.items.values() if str(item.get("sk", "")).startswith("COSTRUN#")
    ]
    assert (month_counters, user_counters, len(run_records)) == (
        EXPECTED_COUNTERS,
        EXPECTED_COUNTERS,
        1,
    )


@pytest.mark.parametrize(
    ("method", "prefix"),
    [
        (lambda repository: repository.get_system_month_costs(6), "COST#"),
        (lambda repository: repository.list_user_month_costs("2026-08"), "COSTUSER#2026-08#"),
        (lambda repository: repository.list_run_costs(6), "COSTRUN#"),
    ],
)
def test_cost_lists_query_by_sort_key_prefix(
    method: Callable[[ReadingRepository], list[dict]], prefix: str
) -> None:
    table = FakeTable()
    table.query_items = [{"total_usd_micros": 12}]

    assert method(make_repository(table)) == table.query_items

    assert len(table.calls) == 1
    condition = table.calls[0]["KeyConditionExpression"].get_expression()
    parts = [part.get_expression() for part in condition["values"]]
    assert any(part["operator"] == "=" and part["values"][1] == "SYSTEM" for part in parts)
    assert any(part["operator"] == "begins_with" and part["values"][1] == prefix for part in parts)
