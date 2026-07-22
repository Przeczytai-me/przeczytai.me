import pytest

from test_api import FakeRepo, client


class AbbreviationRepo(FakeRepo):
    def __init__(self) -> None:
        super().__init__()
        self.created_abbreviation_readings: list[list[dict[str, str]] | None] = []
        self.started_abbreviation_readings: list[list[dict[str, str]] | None] = []

    def create(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        char_count: int,
        vendor: str | None,
        voice: str | None,
        abbreviation_readings: list[dict[str, str]] | None = None,
    ) -> dict:
        self.created_abbreviation_readings.append(abbreviation_readings)
        return super().create(
            owner_user_id,
            reading_id,
            original_text_key,
            char_count,
            vendor,
            voice,
        )

    def start_processing(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        vendor: str | None,
        voice: str | None,
        job_id: str,
        abbreviation_readings: list[dict[str, str]] | None = None,
    ) -> None:
        self.started_abbreviation_readings.append(abbreviation_readings)
        super().start_processing(
            owner_user_id,
            reading_id,
            original_text_key,
            vendor,
            voice,
            job_id,
        )


def test_create_passes_trimmed_abbreviation_readings_to_repository_and_processor() -> None:
    """Pass trimmed document abbreviation readings through both creation stages."""
    repo = AbbreviationRepo()
    test_client, _ = client(repo)
    pairs = [
        {"abbreviation": "  Np.  ", "read_as": "  Na przykład  "},
        {"abbreviation": " PKP\t", "read_as": " Pe Ka Pe "},
    ]

    response = test_client.post(
        "/api/v1/readings",
        json={"original_text": "tekst", "abbreviation_readings": pairs},
    )

    expected = [
        {"abbreviation": "Np.", "read_as": "Na przykład"},
        {"abbreviation": "PKP", "read_as": "Pe Ka Pe"},
    ]
    assert response.status_code == 202
    assert response.json()["status"] == "uploaded"
    assert "abbreviation_readings" not in response.json()
    assert repo.created_abbreviation_readings == [expected]
    assert repo.started_abbreviation_readings == [expected]


@pytest.mark.parametrize(
    "request_extra",
    [{}, {"abbreviation_readings": []}],
    ids=["omitted", "empty-list"],
)
def test_create_treats_absent_abbreviation_readings_as_none(
    request_extra: dict[str, object],
) -> None:
    """Preserve existing creation behavior when no abbreviation pairs are supplied."""
    repo = AbbreviationRepo()
    test_client, _ = client(repo)

    response = test_client.post(
        "/api/v1/readings",
        json={"original_text": "tekst", **request_extra},
    )

    assert response.status_code == 202
    assert repo.created_abbreviation_readings == [None]
    assert repo.started_abbreviation_readings == [None]


@pytest.mark.parametrize(
    "pairs",
    [
        [{"abbreviation": "   ", "read_as": "wartość"}],
        [{"abbreviation": "skrót", "read_as": "\t  "}],
        [{"abbreviation": "x" * 51, "read_as": "wartość"}],
        [{"abbreviation": "skrót", "read_as": "x" * 201}],
        [{"abbreviation": f"Skrót {index}", "read_as": "wartość"} for index in range(101)],
        [
            {"abbreviation": "  Np. ", "read_as": "pierwszy"},
            {"abbreviation": "np.", "read_as": "drugi"},
        ],
    ],
    ids=[
        "empty-abbreviation",
        "empty-read-as",
        "abbreviation-too-long",
        "read-as-too-long",
        "too-many-pairs",
        "duplicate-casefolded-abbreviation",
    ],
)
def test_create_rejects_invalid_abbreviation_readings(
    pairs: list[dict[str, str]],
) -> None:
    """Reject invalid document abbreviation readings before creating a reading."""
    repo = AbbreviationRepo()
    test_client, _ = client(repo)

    response = test_client.post(
        "/api/v1/readings",
        json={"original_text": "tekst", "abbreviation_readings": pairs},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert repo.created_abbreviation_readings == []
    assert repo.items == {}


def test_create_rejects_abbreviation_reading_with_missing_key() -> None:
    """Return the structured validation error when an entry is missing a required key."""
    repo = AbbreviationRepo()
    test_client, _ = client(repo)

    response = test_client.post(
        "/api/v1/readings",
        json={
            "original_text": "tekst",
            "abbreviation_readings": [{"abbreviation": "PKP"}],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert repo.created_abbreviation_readings == []
    assert repo.items == {}


def test_reading_create_schema_exposes_abbreviation_readings() -> None:
    """Publish abbreviation readings in the reading creation OpenAPI schema."""
    test_client, _ = client()

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()["components"]["schemas"]["ReadingCreateRequest"]
    assert "abbreviation_readings" in schema["properties"]
