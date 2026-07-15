import base64
import json
from datetime import UTC, datetime

import boto3
import ulid
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError


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
            "status": "processing",
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
        self.table.update_item(
            Key={"pk": f"USER#{owner_user_id}", "sk": f"READING#{reading_id}"},
            UpdateExpression=(
                "SET #status = :status, metadata = :metadata, updated_at = :updated_at"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "failed_to_start",
                ":metadata": {"processing_start_error": "lambda_invoke_failed"},
                ":updated_at": _now(),
            },
        )

    def mark_completed(
        self,
        owner_user_id: str,
        reading_id: str,
        corrected_text_key: str,
        recording_key: str,
        metadata: dict[str, object],
    ) -> None:
        try:
            self.table.update_item(
                Key={"pk": f"USER#{owner_user_id}", "sk": f"READING#{reading_id}"},
                UpdateExpression=(
                    "SET #status = :status, corrected_text_key = :corrected_text_key, "
                    "recording_key = :recording_key, metadata = :metadata, updated_at = :updated_at"
                ),
                ConditionExpression="attribute_exists(reading_id)",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "completed",
                    ":corrected_text_key": corrected_text_key,
                    ":recording_key": recording_key,
                    ":metadata": metadata,
                    ":updated_at": _now(),
                },
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return
            raise

    def mark_failed(
        self,
        owner_user_id: str,
        reading_id: str,
        metadata: dict[str, object],
    ) -> None:
        try:
            self.table.update_item(
                Key={"pk": f"USER#{owner_user_id}", "sk": f"READING#{reading_id}"},
                UpdateExpression=(
                    "SET #status = :status, metadata = :metadata, updated_at = :updated_at"
                ),
                ConditionExpression="attribute_exists(reading_id)",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "failed",
                    ":metadata": metadata,
                    ":updated_at": _now(),
                },
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return
            raise

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


class ProcessingStartError(Exception):
    pass
