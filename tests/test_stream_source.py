from pathlib import Path

import pytest

from omnilapse import ffmpeg_utils
from omnilapse.config import EncodingConfig
from omnilapse.sources.base import BuildContext
from omnilapse.sources.stream import StreamSource


def test_requires_duration_or_max_frames():
    with pytest.raises(ValueError):
        StreamSource(url="rtsp://example/stream")


def test_invalid_interval():
    with pytest.raises(ValueError):
        StreamSource(url="rtsp://example/stream", duration_seconds=10, interval_seconds=0)


def test_accepts_duration_only():
    source = StreamSource(url="rtsp://example/stream", duration_seconds=60)
    assert source.duration_seconds == 60


def test_accepts_max_frames_only():
    source = StreamSource(url="rtsp://example/stream", max_frames=10)
    assert source.max_frames == 10


def test_capture_frames_command_for_rtsp(tmp_path: Path, monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(ffmpeg_utils, "run", fake_run)

    work_dir = tmp_path / "work"
    work_dir.mkdir()
    ctx = BuildContext(work_dir=work_dir, encoding=EncodingConfig(), ffmpeg_path="ffmpeg", segment_index=0)
    source = StreamSource(url="rtsp://example/stream", interval_seconds=5, duration_seconds=30)
    capture_dir = source.capture_frames(ctx)

    cmd = captured["cmd"]
    assert "-rtsp_transport" in cmd
    assert "fps=1/5" in ",".join(cmd)
    assert "-t" in cmd and "30" in cmd
    assert capture_dir.exists()


def test_capture_frames_command_for_http_omits_rtsp_transport(tmp_path: Path, monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(ffmpeg_utils, "run", fake_run)

    work_dir = tmp_path / "work"
    work_dir.mkdir()
    ctx = BuildContext(work_dir=work_dir, encoding=EncodingConfig(), ffmpeg_path="ffmpeg", segment_index=0)
    source = StreamSource(url="http://example/stream.m3u8", max_frames=5)
    source.capture_frames(ctx)

    cmd = captured["cmd"]
    assert "-rtsp_transport" not in cmd
    assert "-frames:v" in cmd and "5" in cmd
