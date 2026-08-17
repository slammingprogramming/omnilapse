import sys
from pathlib import Path

import pytest

from timelapse_generator import ffmpeg_utils


def test_find_binary_raises_when_missing(monkeypatch):
    monkeypatch.setattr(ffmpeg_utils.shutil, "which", lambda name: None)
    with pytest.raises(ffmpeg_utils.FFmpegNotFoundError):
        ffmpeg_utils.find_binary("ffmpeg")


def test_find_binary_returns_path(monkeypatch):
    monkeypatch.setattr(ffmpeg_utils.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    assert ffmpeg_utils.find_binary("ffmpeg") == "/usr/bin/ffmpeg"


def test_run_raises_ffmpeg_error_on_failure():
    cmd = [sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(1)"]
    with pytest.raises(ffmpeg_utils.FFmpegError) as excinfo:
        ffmpeg_utils.run(cmd)
    assert "boom" in str(excinfo.value)
    assert excinfo.value.returncode == 1


def test_run_succeeds_and_returns_result():
    cmd = [sys.executable, "-c", "print('ok')"]
    result = ffmpeg_utils.run(cmd)
    assert result.returncode == 0
    assert "ok" in result.stdout


def test_write_concat_list(tmp_path: Path):
    a = tmp_path / "a.jpg"
    b = tmp_path / "b.jpg"
    a.write_bytes(b"1")
    b.write_bytes(b"2")
    list_path = tmp_path / "list.txt"

    ffmpeg_utils.write_concat_list([a, b], list_path)

    content = list_path.read_text()
    lines = content.strip().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("file '")
    assert "a.jpg" in lines[0]
    assert "b.jpg" in lines[1]
    assert "\\" not in content
