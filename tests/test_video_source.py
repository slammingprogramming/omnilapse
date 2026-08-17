from pathlib import Path

import pytest

from timelapse_generator import ffmpeg_utils
from timelapse_generator.config import EncodingConfig
from timelapse_generator.sources.base import BuildContext
from timelapse_generator.sources.video import DEFAULT_SPEED_FACTOR, VideoSource


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        VideoSource(path=tmp_path / "missing.mp4")


def test_both_speed_and_duration_raises(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    with pytest.raises(ValueError):
        VideoSource(path=video, speed_factor=2.0, target_duration=10.0)


def test_resolve_speed_factor_default(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    source = VideoSource(path=video)
    assert source.resolve_speed_factor() == DEFAULT_SPEED_FACTOR


def test_resolve_speed_factor_explicit(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    source = VideoSource(path=video, speed_factor=4.0)
    assert source.resolve_speed_factor() == 4.0


def test_resolve_speed_factor_invalid(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    source = VideoSource(path=video, speed_factor=-1)
    with pytest.raises(ValueError):
        source.resolve_speed_factor()


def test_resolve_speed_factor_from_target_duration(tmp_path: Path, monkeypatch):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    monkeypatch.setattr(ffmpeg_utils, "probe_duration_seconds", lambda p: 100.0)
    source = VideoSource(path=video, target_duration=10.0)
    assert source.resolve_speed_factor() == 10.0


def test_build_invokes_ffmpeg_with_expected_command(tmp_path: Path, monkeypatch):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        Path(cmd[-1]).write_bytes(b"fake-video")
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(ffmpeg_utils, "run", fake_run)

    work_dir = tmp_path / "work"
    work_dir.mkdir()
    ctx = BuildContext(
        work_dir=work_dir,
        encoding=EncodingConfig(fps=30),
        ffmpeg_path="ffmpeg",
        segment_index=0,
    )
    source = VideoSource(path=video, speed_factor=8.0)
    output = source.build(ctx)

    assert output.exists()
    cmd = captured["cmd"]
    assert "setpts=PTS/8.0" in ",".join(cmd)
    assert "-an" in cmd
