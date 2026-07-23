import httpx


def test_tts_options_endpoint(
    api_client: httpx.Client,
    public_api_client: httpx.Client,
) -> None:
    unauthorized = public_api_client.get("/api/v1/tts-options")
    assert unauthorized.status_code == 401, unauthorized.text

    response = api_client.get("/api/v1/tts-options")
    assert response.status_code == 200, response.text
    options = response.json()
    assert options["vendors"]
    assert options["models"]
    assert options["voices"]
    assert options["defaults"]["model"]
    assert options["defaults"]["voice"]
