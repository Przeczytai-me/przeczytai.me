import httpx

from helpers import create_reading


def test_create_reading_endpoint(api_client: httpx.Client) -> None:
    created = create_reading(api_client, "Ala ma kota.")

    assert created["id"]
    assert created["status"] == "uploaded"
    assert created["vendor"] == "edge-tts"
    assert created["voice"] == "pl-PL-ZofiaNeural"
    assert created["char_count"] == len("Ala ma kota.")
    assert created["original_text_key"].endswith("/original.txt")
    assert created["corrected_text_key"] is None
    assert created["recording_key"] is None
