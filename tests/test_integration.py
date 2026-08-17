"""End-to-end tests that actually invoke ffmpeg. Skipped if ffmpeg isn't on PATH."""

from pathlib import Path

from timelapse_generator.config import EncodingConfig
from timelapse_generator.pipeline import Job
from timelapse_generator.sources import PhotoSource, StreamSource, VideoSource

from .conftest import make_test_image, make_test_video, requires_ffmpeg


@requires_ffmpeg
def test_photos_to_timelapse(tmp_path: Path):
    photo_dir = tmp_path / "photos"
    photo_dir.mkdir()
    for i in range(5):
        make_test_image(photo_dir / f"img_{i:02d}.jpg", color="red" if i % 2 else "blue")

    output = tmp_path / "out.mp4"
    job = Job(sources=[PhotoSource(directory=photo_dir)], output=output, encoding=EncodingConfig(fps=10))
    result = job.run()

    assert result == output
    assert result.exists()
    assert result.stat().st_size > 0


@requires_ffmpeg
def test_video_to_timelapse(tmp_path: Path):
    source_video = tmp_path / "source.mp4"
    make_test_video(source_video, duration=2, fps=10)

    output = tmp_path / "out.mp4"
    job = Job(sources=[VideoSource(path=source_video, speed_factor=4.0)], output=output)
    result = job.run()

    assert result.exists()
    assert result.stat().st_size > 0


@requires_ffmpeg
def test_stream_capture_from_local_file(tmp_path: Path):
    # ffmpeg treats a local file path the same as a network URL for -i, so this
    # exercises the real capture command without needing a live RTSP/HTTP feed.
    source_video = tmp_path / "source.mp4"
    make_test_video(source_video, duration=3, fps=10)

    output = tmp_path / "out.mp4"
    job = Job(
        sources=[StreamSource(url=str(source_video), interval_seconds=1, max_frames=2, rtsp_transport=None)],
        output=output,
    )
    result = job.run()

    assert result.exists()
    assert result.stat().st_size > 0


@requires_ffmpeg
def test_mixed_sources_concatenate(tmp_path: Path):
    photo_dir = tmp_path / "photos"
    photo_dir.mkdir()
    for i in range(3):
        make_test_image(photo_dir / f"img_{i:02d}.jpg")

    source_video = tmp_path / "source.mp4"
    make_test_video(source_video, duration=1, fps=10)

    output = tmp_path / "out.mp4"
    job = Job(
        sources=[
            PhotoSource(directory=photo_dir),
            VideoSource(path=source_video, speed_factor=4.0),
        ],
        output=output,
        encoding=EncodingConfig(fps=10),
    )
    result = job.run()

    assert result.exists()
    assert result.stat().st_size > 0
