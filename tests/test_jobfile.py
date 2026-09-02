import json
from pathlib import Path

import pytest

from omnilapse.jobfile import load_job
from omnilapse.sources import PhotoSource, StreamSource, VideoSource


def write_job(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "job.json"
    path.write_text(json.dumps(data))
    return path


def test_load_job_missing_output(tmp_path: Path):
    path = write_job(tmp_path, {"sources": [{"type": "photos", "directory": "x"}]})
    with pytest.raises(ValueError):
        load_job(path)


def test_load_job_missing_sources(tmp_path: Path):
    path = write_job(tmp_path, {"output": "out.mp4", "sources": []})
    with pytest.raises(ValueError):
        load_job(path)


def test_load_job_unknown_source_type(tmp_path: Path):
    path = write_job(tmp_path, {"output": "out.mp4", "sources": [{"type": "carrier-pigeon"}]})
    with pytest.raises(ValueError):
        load_job(path)


def test_load_job_builds_mixed_sources(tmp_path: Path):
    photos_dir = tmp_path / "photos_dir"
    photos_dir.mkdir()
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"x")

    data = {
        "output": "out/mixed.mp4",
        "encoding": {"fps": 24, "width": 1280},
        "sources": [
            {"type": "photos", "directory": str(photos_dir)},
            {"type": "video", "path": str(clip), "speed_factor": 6},
            {"type": "stream", "url": "rtsp://cam/stream", "duration_seconds": 120},
        ],
    }
    path = write_job(tmp_path, data)
    job = load_job(path)

    assert job.output == Path("out/mixed.mp4")
    assert job.encoding.fps == 24
    assert job.encoding.width == 1280
    assert len(job.sources) == 3
    assert isinstance(job.sources[0], PhotoSource)
    assert isinstance(job.sources[1], VideoSource)
    assert job.sources[1].speed_factor == 6
    assert isinstance(job.sources[2], StreamSource)
    assert job.sources[2].duration_seconds == 120


def test_load_job_photos_pattern_is_compiled(tmp_path: Path):
    data = {
        "output": "out.mp4",
        "sources": [{"type": "photos", "directory": "x", "pattern": r"(\d+)"}],
    }
    path = write_job(tmp_path, data)
    job = load_job(path)
    assert job.sources[0].pattern.pattern == r"(\d+)"
