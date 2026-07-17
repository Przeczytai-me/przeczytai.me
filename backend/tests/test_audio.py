from pathlib import Path

import pytest

from app.audio import AudioMergeError, merge_mp3_files


def test_merge_mp3_files_concatenates_parts_in_order(tmp_path: Path) -> None:
    parts = [tmp_path / f"part-{index}.mp3" for index in range(3)]
    contents = [b"first-part", b"second-part", b"third-part"]
    for part, content in zip(parts, contents, strict=True):
        part.write_bytes(content)
    output = tmp_path / "merged.mp3"

    merge_mp3_files(parts, output)

    assert output.read_bytes() == b"".join(contents)


def test_merge_mp3_files_rejects_missing_part_before_writing(tmp_path: Path) -> None:
    parts = [tmp_path / f"part-{index}.mp3" for index in range(3)]
    for part in parts:
        part.write_bytes(b"audio")
    parts[1].unlink()
    output = tmp_path / "merged.mp3"

    with pytest.raises(AudioMergeError, match=r"\b1\b"):
        merge_mp3_files(parts, output)

    assert not output.exists()


def test_merge_mp3_files_rejects_empty_part_before_writing(tmp_path: Path) -> None:
    parts = [tmp_path / "part-0.mp3", tmp_path / "part-1.mp3"]
    parts[0].write_bytes(b"audio")
    parts[1].write_bytes(b"")
    output = tmp_path / "merged.mp3"

    with pytest.raises(AudioMergeError, match=r"\b1\b"):
        merge_mp3_files(parts, output)

    assert not output.exists()


def test_merge_mp3_files_copies_single_part(tmp_path: Path) -> None:
    part = tmp_path / "only.mp3"
    part.write_bytes(b"single-part-audio")
    output = tmp_path / "merged.mp3"

    merge_mp3_files([part], output)

    assert output.read_bytes() == part.read_bytes()
