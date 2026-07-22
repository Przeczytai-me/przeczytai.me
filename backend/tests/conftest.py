import pytest


@pytest.fixture(autouse=True)
def stub_processing_mp3_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.processing.mp3_duration_seconds", lambda _path: 1.0)
