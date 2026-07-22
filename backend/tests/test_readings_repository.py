from collections.abc import Callable

import pytest
from botocore.exceptions import ClientError

from app.repositories.readings import ReadingRepository


class FakeTable:
    def __init__(self, raise_conditional: bool = False) -> None:
        self.calls: list[dict[str, object]] = []
        self.raise_conditional = raise_conditional

    def update_item(self, **kwargs: object) -> None:
        self.calls.append(kwargs)
        if self.raise_conditional:
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "UpdateItem",
            )


def make_repository(table: FakeTable) -> ReadingRepository:
    repository = object.__new__(ReadingRepository)
    repository.table = table
    repository.processor_function_name = None
    return repository


def test_mark_completed_updates_all_fields_atomically() -> None:
    table = FakeTable()
    repository = make_repository(table)
    metadata = {"chunks": 2, "processor": "edge-tts"}

    repository.mark_completed(
        "owner-1", "reading-1", "corrected.md", "recording.mp3", metadata, "timing.json"
    )

    assert len(table.calls) == 1
    request = table.calls[0]
    assert request["Key"] == {"pk": "USER#owner-1", "sk": "READING#reading-1"}
    assert request["ConditionExpression"] == "attribute_exists(reading_id)"
    expression = str(request["UpdateExpression"])
    names = request.get("ExpressionAttributeNames", {})
    assignments = {
        names.get(left.strip(), left.strip())
        for assignment in expression.removeprefix("SET ").split(",")
        for left in [assignment.split("=", 1)[0]]
    }
    assert assignments == {
        "status",
        "corrected_text_key",
        "recording_key",
        "timing_map_key",
        "metadata",
        "updated_at",
    }
    values = request["ExpressionAttributeValues"]
    assert "completed" in values.values()
    assert "corrected.md" in values.values()
    assert "recording.mp3" in values.values()
    assert "timing.json" in values.values()
    assert metadata in values.values()


def test_set_status_initializes_metadata_before_applying_patch() -> None:
    table = FakeTable()
    repository = make_repository(table)
    patch = {"error-code": "provider_failed", "retry count": 2}

    repository.set_status("owner-1", "reading-1", "failed", patch)

    assert len(table.calls) == 2
    initialize, update = table.calls
    assert "if_not_exists(metadata" in str(initialize["UpdateExpression"])
    assert initialize["ConditionExpression"] == "attribute_exists(reading_id)"
    assert update["ConditionExpression"] == "attribute_exists(reading_id)"

    expression = str(update["UpdateExpression"])
    names = update["ExpressionAttributeNames"]
    nested_aliases = {
        assignment.split("=", 1)[0].strip().removeprefix("metadata.")
        for assignment in expression.removeprefix("SET ").split(",")
        if assignment.split("=", 1)[0].strip().startswith("metadata.")
    }
    assert nested_aliases
    assert all(alias.startswith("#") for alias in nested_aliases)
    assert {names[alias] for alias in nested_aliases} == set(patch)


def test_set_status_without_patch_updates_only_status_and_timestamp() -> None:
    table = FakeTable()
    repository = make_repository(table)

    repository.set_status("owner-1", "reading-1", "processing")

    assert len(table.calls) == 1
    request = table.calls[0]
    assert request["UpdateExpression"] == "SET #status = :status, updated_at = :updated_at"
    assert request["ExpressionAttributeNames"] == {"#status": "status"}
    assert set(request["ExpressionAttributeValues"]) == {":status", ":updated_at"}
    assert request["ConditionExpression"] == "attribute_exists(reading_id)"


@pytest.mark.parametrize(
    "operation",
    [
        lambda repository: repository.mark_completed(
            "owner-1",
            "reading-1",
            "corrected.md",
            "recording.mp3",
            {"chunks": 1},
            "timing.json",
        ),
        lambda repository: repository.set_status(
            "owner-1", "reading-1", "failed", {"error": "provider_failed"}
        ),
        lambda repository: repository.set_status("owner-1", "reading-1", "processing"),
    ],
)
def test_conditional_check_failure_is_swallowed(
    operation: Callable[[ReadingRepository], None],
) -> None:
    operation(make_repository(FakeTable(raise_conditional=True)))
