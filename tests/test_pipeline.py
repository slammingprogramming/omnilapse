from pathlib import Path

import pytest

from omnilapse import ffmpeg_utils
from omnilapse.config import EncodingConfig
from omnilapse.pipeline import Job
from omnilapse.sources.base import BuildContext, Source


class StubSource(Source):
    def __init__(self, tag: str):
        self.tag = tag

    def build(self, ctx: BuildContext) -> Path:
        path = ctx.segment_path()
        path.write_bytes(f"clip-{self.tag}".encode())
        return path

    def describe(self) -> str:
        return f"StubSource({self.tag})"


@pytest.fixture(autouse=True)
def fake_ffmpeg(monkeypatch):
    monkeypatch.setattr(ffmpeg_utils, "find_ffmpeg", lambda: "ffmpeg")


def test_job_requires_sources(tmp_path: Path):
    with pytest.raises(ValueError):
        Job(sources=[], output=tmp_path / "out.mp4")


def test_single_source_job_copies_clip_to_output(tmp_path: Path):
    job = Job(sources=[StubSource("a")], output=tmp_path / "out.mp4")
    result = job.run()
    assert result == tmp_path / "out.mp4"
    assert result.read_bytes() == b"clip-a"


def test_multi_source_job_concatenates(tmp_path: Path, monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        Path(cmd[-1]).write_bytes(b"concatenated")
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(ffmpeg_utils, "run", fake_run)

    job = Job(sources=[StubSource("a"), StubSource("b")], output=tmp_path / "out.mp4")
    result = job.run()

    assert result.read_bytes() == b"concatenated"
    cmd = captured["cmd"]
    assert "-c" in cmd and "copy" in cmd
    assert "concat" in cmd


def test_temp_work_dir_is_cleaned_up_by_default(tmp_path: Path):
    seen_work_dir = {}

    class RecordingSource(StubSource):
        def build(self, ctx: BuildContext) -> Path:
            seen_work_dir["dir"] = ctx.work_dir
            return super().build(ctx)

    job = Job(sources=[RecordingSource("a")], output=tmp_path / "out.mp4")
    job.run()

    assert not seen_work_dir["dir"].exists()


def test_explicit_work_dir_is_not_deleted(tmp_path: Path):
    work_dir = tmp_path / "work"
    job = Job(sources=[StubSource("a")], output=tmp_path / "out.mp4", work_dir=work_dir)
    job.run()

    assert work_dir.exists()


def test_keep_intermediate_preserves_auto_created_work_dir(tmp_path: Path):
    seen_work_dir = {}

    class RecordingSource(StubSource):
        def build(self, ctx: BuildContext) -> Path:
            seen_work_dir["dir"] = ctx.work_dir
            return super().build(ctx)

    job = Job(sources=[RecordingSource("a")], output=tmp_path / "out.mp4", keep_intermediate=True)
    job.run()

    assert seen_work_dir["dir"].exists()
