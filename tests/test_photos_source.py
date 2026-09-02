import time
from pathlib import Path

import pytest

from omnilapse import ffmpeg_utils
from omnilapse.config import EncodingConfig
from omnilapse.sources.base import BuildContext
from omnilapse.sources.photos import PhotoSource


def test_list_images_missing_directory(tmp_path: Path):
    source = PhotoSource(directory=tmp_path / "does-not-exist")
    with pytest.raises(NotADirectoryError):
        source.list_images()


def test_list_images_empty_directory(tmp_path: Path):
    source = PhotoSource(directory=tmp_path)
    with pytest.raises(FileNotFoundError):
        source.list_images()


def test_list_images_sort_by_name(tmp_path: Path):
    for name in ["c.jpg", "a.jpg", "b.jpg"]:
        (tmp_path / name).write_bytes(b"x")
    source = PhotoSource(directory=tmp_path, sort_by="name")
    result = [p.name for p in source.list_images()]
    assert result == ["a.jpg", "b.jpg", "c.jpg"]


def test_list_images_sort_by_pattern(tmp_path: Path):
    names = ["20251102_00_13_14.jpg", "20251101_23_59_59.jpg", "20251102_01_00_00.jpg"]
    for name in names:
        (tmp_path / name).write_bytes(b"x")
    source = PhotoSource(directory=tmp_path, sort_by="pattern")
    result = [p.name for p in source.list_images()]
    assert result == [
        "20251101_23_59_59.jpg",
        "20251102_00_13_14.jpg",
        "20251102_01_00_00.jpg",
    ]


def test_list_images_auto_falls_back_to_name_without_timestamp(tmp_path: Path):
    for name in ["img_3.jpg", "img_1.jpg", "img_2.jpg"]:
        (tmp_path / name).write_bytes(b"x")
    source = PhotoSource(directory=tmp_path, sort_by="auto")
    result = [p.name for p in source.list_images()]
    assert result == ["img_1.jpg", "img_2.jpg", "img_3.jpg"]


def test_list_images_sort_by_mtime(tmp_path: Path):
    old = tmp_path / "z_first.jpg"
    old.write_bytes(b"x")
    time.sleep(0.05)
    new = tmp_path / "a_second.jpg"
    new.write_bytes(b"x")

    source = PhotoSource(directory=tmp_path, sort_by="mtime")
    result = [p.name for p in source.list_images()]
    assert result == ["z_first.jpg", "a_second.jpg"]


def test_list_images_filters_by_extension(tmp_path: Path):
    (tmp_path / "photo.jpg").write_bytes(b"x")
    (tmp_path / "notes.txt").write_bytes(b"x")
    source = PhotoSource(directory=tmp_path)
    result = [p.name for p in source.list_images()]
    assert result == ["photo.jpg"]


def test_list_images_recursive(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.jpg").write_bytes(b"x")
    (tmp_path / "a.jpg").write_bytes(b"x")

    non_recursive = PhotoSource(directory=tmp_path, recursive=False)
    assert [p.name for p in non_recursive.list_images()] == ["a.jpg"]

    recursive = PhotoSource(directory=tmp_path, recursive=True)
    assert sorted(p.name for p in recursive.list_images()) == ["a.jpg", "b.jpg"]


def test_build_invokes_ffmpeg_with_expected_command(tmp_path: Path, monkeypatch):
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "b.jpg").write_bytes(b"x")

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
        encoding=EncodingConfig(fps=24, width=640),
        ffmpeg_path="ffmpeg",
        segment_index=0,
    )
    source = PhotoSource(directory=tmp_path, sort_by="name")
    output = source.build(ctx)

    assert output.exists()
    cmd = captured["cmd"]
    assert cmd[0] == "ffmpeg"
    assert "-r" in cmd and "24.0" in cmd
    assert "scale=640:-2" in ",".join(cmd)
