import base64
import json
from dataclasses import asdict
from datetime import UTC, datetime

import boto3
import ulid
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

from app.costs import CostBreakdown
from app.models import ReadingStatus

COST_COUNTERS = (
    "total_usd_micros",
    "tts_usd_micros",
    "llm_usd_micros",
    "compute_usd_micros",
    "storage_usd_micros",
    "platform_usd_micros",
    "chars",
    "audio_ms",
    "runs",
)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _encode_cursor(key: dict | None) -> str | None:
    if not key:
        return None
    return base64.urlsafe_b64encode(json.dumps(key).encode()).decode()


def _decode_cursor(cursor: str | None) -> dict | None:
    if not cursor:
        return None
    return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())


class ReadingRepository:
    def __init__(self, table_name: str, processor_function_name: str | None) -> None:
        self.table = boto3.resource("dynamodb").Table(table_name)
        self.processor_function_name = processor_function_name
        self.lambda_client = boto3.client("lambda") if processor_function_name else None

    def create(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        char_count: int,
        vendor: str,
        voice: str,
        abbreviation_readings: list[dict] | None = None,
    ) -> dict:
        now = _now()
        item = {
            "pk": f"USER#{owner_user_id}",
            "sk": f"READING#{reading_id}",
            "reading_id": reading_id,
            "owner_user_id": owner_user_id,
            "original_text_key": original_text_key,
            "corrected_text_key": None,
            "recording_key": None,
            "vendor": vendor,
            "voice": voice,
            "abbreviation_readings": abbreviation_readings,
            "status": ReadingStatus.UPLOADED,
            "attempts": 1,
            "metadata": {},
            "char_count": char_count,
            "created_at": now,
            "updated_at": now,
        }

        self.table.put_item(Item=item)
        return item

    def begin_retry(self, owner_user_id: str, reading_id: str) -> int:
        try:
            response = self.table.update_item(
                Key={"pk": f"USER#{owner_user_id}", "sk": f"READING#{reading_id}"},
                UpdateExpression=(
                    "SET #status = :uploaded, "
                    "attempts = if_not_exists(attempts, :one) + :one, "
                    "updated_at = :updated_at"
                ),
                ConditionExpression=(
                    "attribute_exists(reading_id) AND "
                    "#status IN (:completed, :failed, :failed_to_start)"
                ),
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":uploaded": ReadingStatus.UPLOADED.value,
                    ":one": 1,
                    ":updated_at": _now(),
                    ":completed": ReadingStatus.COMPLETED.value,
                    ":failed": ReadingStatus.FAILED.value,
                    ":failed_to_start": ReadingStatus.FAILED_TO_START.value,
                },
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise RetryConflictError from exc
            raise
        return int(response["Attributes"]["attempts"])

    def next_id(self) -> str:
        return str(ulid.new())

    def start_processing(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        vendor: str,
        voice: str,
        job_id: str,
        abbreviation_readings: list[dict] | None = None,
    ) -> None:
        if not self.lambda_client or not self.processor_function_name:
            raise ProcessingStartError

        try:
            response = self.lambda_client.invoke(
                FunctionName=self.processor_function_name,
                InvocationType="Event",
                Payload=json.dumps(
                    {
                        "reading_id": reading_id,
                        "job_id": job_id,
                        "owner_user_id": owner_user_id,
                        "original_text_key": original_text_key,
                        "vendor": vendor,
                        "voice": voice,
                        "abbreviation_readings": abbreviation_readings,
                    }
                ).encode(),
            )
        except (BotoCoreError, ClientError) as exc:
            raise ProcessingStartError from exc

        if response.get("StatusCode") != 202:
            raise ProcessingStartError

    def create_job(self, owner_user_id: str, reading_id: str, attempt: int) -> dict:
        job_id = self.next_id()
        now = _now()
        item = {
            "pk": f"USER#{owner_user_id}",
            "sk": f"JOB#{job_id}",
            "job_id": job_id,
            "reading_id": reading_id,
            "owner_user_id": owner_user_id,
            "attempt": attempt,
            "status": ReadingStatus.UPLOADED.value,
            "error": None,
            "failed_step": None,
            "created_at": now,
            "updated_at": now,
        }
        self.table.put_item(Item=item)
        return item

    def get_job(self, owner_user_id: str, job_id: str) -> dict | None:
        return self._get_item(owner_user_id, job_id, item_type="JOB")

    def set_job_status(
        self,
        owner_user_id: str,
        job_id: str,
        status: ReadingStatus | str,
        error: str | None = None,
        failed_step: str | None = None,
    ) -> None:
        values: dict[str, object] = {":status": str(status), ":updated_at": _now()}
        updates = ["#status = :status", "updated_at = :updated_at"]
        if error is not None:
            values[":error"] = error
            updates.append("error = :error")
        if failed_step is not None:
            values[":failed_step"] = failed_step
            updates.append("failed_step = :failed_step")
        self._update_existing(
            owner_user_id,
            job_id,
            "SET " + ", ".join(updates),
            {"#status": "status"},
            values,
            item_type="JOB",
            identity_field="job_id",
        )

    def list_jobs(
        self, owner_user_id: str, limit: int, cursor: str | None
    ) -> tuple[list[dict], str | None]:
        query = {
            "KeyConditionExpression": Key("pk").eq(f"USER#{owner_user_id}")
            & Key("sk").begins_with("JOB#"),
            "Limit": limit,
            "ScanIndexForward": False,
        }
        if start_key := _decode_cursor(cursor):
            query["ExclusiveStartKey"] = start_key
        response = self.table.query(**query)
        return response.get("Items", []), _encode_cursor(response.get("LastEvaluatedKey"))

    def mark_processing_start_failed(self, owner_user_id: str, reading_id: str) -> None:
        self.set_status(
            owner_user_id,
            reading_id,
            ReadingStatus.FAILED_TO_START,
            {"processing_start_error": "lambda_invoke_failed"},
        )

    def set_status(
        self,
        owner_user_id: str,
        reading_id: str,
        status: ReadingStatus | str,
        metadata_patch: dict[str, object] | None = None,
    ) -> None:
        if metadata_patch and not self._update_existing(
            owner_user_id,
            reading_id,
            "SET metadata = if_not_exists(metadata, :empty_metadata)",
            {},
            {":empty_metadata": {}},
        ):
            return

        names = {"#status": "status"}
        values: dict[str, object] = {
            ":status": status,
            ":updated_at": _now(),
        }
        updates = ["#status = :status", "updated_at = :updated_at"]
        for index, (key, value) in enumerate((metadata_patch or {}).items()):
            name = f"#metadata_key_{index}"
            placeholder = f":metadata_value_{index}"
            names[name] = key
            values[placeholder] = value
            updates.append(f"metadata.{name} = {placeholder}")

        self._update_existing(
            owner_user_id,
            reading_id,
            "SET " + ", ".join(updates),
            names,
            values,
        )

    def mark_completed(
        self,
        owner_user_id: str,
        reading_id: str,
        corrected_text_key: str,
        recording_key: str,
        metadata: dict[str, object],
        timing_map_key: str,
        *,
        cost: CostBreakdown | None = None,
    ) -> None:
        updates = [
            "#status = :status",
            "corrected_text_key = :corrected_text_key",
            "recording_key = :recording_key",
            "timing_map_key = :timing_map_key",
            "metadata = :metadata",
            "updated_at = :updated_at",
        ]
        values: dict[str, object] = {
            ":status": ReadingStatus.COMPLETED,
            ":corrected_text_key": corrected_text_key,
            ":recording_key": recording_key,
            ":timing_map_key": timing_map_key,
            ":metadata": metadata,
            ":updated_at": _now(),
        }
        if cost is not None:
            updates.extend(
                [
                    "cost_usd_micros = :cost_usd_micros",
                    "cost_components = :cost_components",
                    "cost_usage = :cost_usage",
                    "price_book_version = :price_book_version",
                ]
            )
            values.update(
                {
                    ":cost_usd_micros": cost.total_usd_micros,
                    ":cost_components": {
                        "tts_usd_micros": cost.tts_usd_micros,
                        "llm_usd_micros": cost.llm_usd_micros,
                        "compute_usd_micros": cost.compute_usd_micros,
                        "storage_usd_micros": cost.storage_usd_micros,
                        "platform_usd_micros": cost.platform_usd_micros,
                    },
                    ":cost_usage": asdict(cost.usage),
                    ":price_book_version": cost.price_book_version,
                }
            )
        self._update_existing(
            owner_user_id,
            reading_id,
            "SET " + ", ".join(updates),
            {"#status": "status"},
            values,
        )

    def add_cost_rollup(
        self,
        owner_user_id: str,
        month: str,
        cost: CostBreakdown,
        *,
        reading_id: str,
        voice: str,
        run_key: str,
    ) -> None:
        now = _now()
        usage = cost.usage
        counters = {
            "total_usd_micros": cost.total_usd_micros,
            "tts_usd_micros": cost.tts_usd_micros,
            "llm_usd_micros": cost.llm_usd_micros,
            "compute_usd_micros": cost.compute_usd_micros,
            "storage_usd_micros": cost.storage_usd_micros,
            "platform_usd_micros": cost.platform_usd_micros,
            "chars": usage.chars_synthesized,
            "audio_ms": usage.audio_ms,
            "runs": 1,
        }
        try:
            self.table.put_item(
                Item={
                    "pk": "SYSTEM",
                    "sk": f"COSTRUN#{month}#{run_key}",
                    "reading_id": reading_id,
                    "owner_user_id": owner_user_id,
                    "vendor": str(usage.vendor),
                    "voice": voice,
                    "total_usd_micros": cost.total_usd_micros,
                    "tts_usd_micros": cost.tts_usd_micros,
                    "llm_usd_micros": cost.llm_usd_micros,
                    "compute_usd_micros": cost.compute_usd_micros,
                    "storage_usd_micros": cost.storage_usd_micros,
                    "platform_usd_micros": cost.platform_usd_micros,
                    "chars": usage.chars_synthesized,
                    "audio_ms": usage.audio_ms,
                    "chunks": usage.chunks,
                    "stored_bytes": usage.stored_bytes,
                    "lambda_memory_mb": usage.lambda_memory_mb,
                    "compute_ms_by_stage": usage.compute_ms_by_stage,
                    "llm_input_tokens": usage.llm_input_tokens,
                    "llm_output_tokens": usage.llm_output_tokens,
                    "price_book_version": cost.price_book_version,
                    "created_at": now,
                },
                ConditionExpression="attribute_not_exists(sk)",
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return
            raise

        update_expression = "SET updated_at = :updated_at ADD " + ", ".join(
            f"{field} :{field}" for field in COST_COUNTERS
        )
        values = {":updated_at": now} | {f":{field}": value for field, value in counters.items()}
        for sort_key in (f"COST#{month}", f"COSTUSER#{month}#{owner_user_id}"):
            self.table.update_item(
                Key={"pk": "SYSTEM", "sk": sort_key},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=values,
            )

    def get_system_month_costs(self, months: int) -> list[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("pk").eq("SYSTEM") & Key("sk").begins_with("COST#"),
            Limit=months,
            ScanIndexForward=False,
        )
        return response.get("Items", [])

    def list_user_month_costs(self, month: str) -> list[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("pk").eq("SYSTEM")
            & Key("sk").begins_with(f"COSTUSER#{month}#"),
        )
        return response.get("Items", [])

    def list_run_costs(self, limit: int) -> list[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("pk").eq("SYSTEM") & Key("sk").begins_with("COSTRUN#"),
            Limit=limit,
            ScanIndexForward=False,
        )
        return response.get("Items", [])

    def list(
        self, owner_user_id: str, limit: int, cursor: str | None
    ) -> tuple[list[dict], str | None]:
        query = {
            "KeyConditionExpression": Key("pk").eq(f"USER#{owner_user_id}")
            & Key("sk").begins_with("READING#"),
            "Limit": limit,
            "ScanIndexForward": False,
        }
        if start_key := _decode_cursor(cursor):
            query["ExclusiveStartKey"] = start_key
        response = self.table.query(**query)
        return response.get("Items", []), _encode_cursor(response.get("LastEvaluatedKey"))

    def get(self, owner_user_id: str, reading_id: str) -> dict | None:
        return self._get_item(owner_user_id, reading_id)

    def delete(self, owner_user_id: str, reading_id: str) -> None:
        item = self._get_item(owner_user_id, reading_id)
        if not item:
            return
        self.table.delete_item(Key={"pk": f"USER#{owner_user_id}", "sk": f"READING#{reading_id}"})

    def _get_item(
        self, owner_user_id: str, item_id: str, item_type: str = "READING"
    ) -> dict | None:
        response = self.table.get_item(
            Key={"pk": f"USER#{owner_user_id}", "sk": f"{item_type}#{item_id}"}
        )
        return response.get("Item")

    def _update_existing(
        self,
        owner_user_id: str,
        reading_id: str,
        update_expression: str,
        names: dict[str, str],
        values: dict[str, object],
        item_type: str = "READING",
        identity_field: str = "reading_id",
    ) -> bool:
        request = {
            "Key": {"pk": f"USER#{owner_user_id}", "sk": f"{item_type}#{reading_id}"},
            "UpdateExpression": update_expression,
            "ConditionExpression": f"attribute_exists({identity_field})",
            "ExpressionAttributeValues": values,
        }
        if names:
            request["ExpressionAttributeNames"] = names
        try:
            self.table.update_item(**request)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return False
            raise
        return True


class ProcessingStartError(Exception):
    pass


class RetryConflictError(Exception):
    pass
