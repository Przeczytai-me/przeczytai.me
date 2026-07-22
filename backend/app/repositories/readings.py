import base64
import json
from datetime import UTC, datetime

import boto3
import ulid
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

from app.models import ReadingStatus


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
            "status": ReadingStatus.UPLOADED,
            "metadata": {},
            "char_count": char_count,
            "created_at": now,
            "updated_at": now,
        }

        self.table.put_item(Item=item)
        return item

    def next_id(self) -> str:
        return str(ulid.new())

    def start_processing(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        vendor: str,
        voice: str,
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
                        "owner_user_id": owner_user_id,
                        "original_text_key": original_text_key,
                        "vendor": vendor,
                        "voice": voice,
                    }
                ).encode(),
            )
        except (BotoCoreError, ClientError) as exc:
            raise ProcessingStartError from exc

        if response.get("StatusCode") != 202:
            raise ProcessingStartError

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
    ) -> None:
        self._update_existing(
            owner_user_id,
            reading_id,
            "SET #status = :status, corrected_text_key = :corrected_text_key, "
            "recording_key = :recording_key, metadata = :metadata, "
            "updated_at = :updated_at",
            {"#status": "status"},
            {
                ":status": ReadingStatus.COMPLETED,
                ":corrected_text_key": corrected_text_key,
                ":recording_key": recording_key,
                ":metadata": metadata,
                ":updated_at": _now(),
            },
        )

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

    def _get_item(self, owner_user_id: str, reading_id: str) -> dict | None:
        response = self.table.get_item(
            Key={"pk": f"USER#{owner_user_id}", "sk": f"READING#{reading_id}"}
        )
        return response.get("Item")

    def _update_existing(
        self,
        owner_user_id: str,
        reading_id: str,
        update_expression: str,
        names: dict[str, str],
        values: dict[str, object],
    ) -> bool:
        request = {
            "Key": {"pk": f"USER#{owner_user_id}", "sk": f"READING#{reading_id}"},
            "UpdateExpression": update_expression,
            "ConditionExpression": "attribute_exists(reading_id)",
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
