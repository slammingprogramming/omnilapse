from pathlib import Path

from omnilapse import cli, ffmpeg_utils
from omnilapse.pipeline import Job


def test_photos_command_parses_defaults(tmp_path: Path):
    parser = cli.build_parser()
    args = parser.parse_args(["photos", str(tmp_path)])
    assert args.output == Path("timelapse.mp4")
    assert args.fps == 30.0
    assert args.sort_by == "auto"


def test_stream_command_requires_duration_or_max_frames():
    parser = cli.build_parser()
    try:
        parser.parse_args(["stream", "rtsp://x/y"])
        assert False, "expected SystemExit"
    except SystemExit:
        pass


def test_main_runs_job_and_reports_output(tmp_path, monkeypatch, capsys):
    output = tmp_path / "out.mp4"

    def fake_run(self):
        output.write_bytes(b"video")
        return output

    monkeypatch.setattr(Job, "run", fake_run)

    photo_dir = tmp_path / "photos"
    photo_dir.mkdir()

    rc = cli.main(["photos", str(photo_dir), "-o", str(output)])

    assert rc == 0
    captured = capsys.readouterr()
    assert str(output) in captured.out


def test_main_handles_missing_directory_gracefully(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ffmpeg_utils, "find_ffmpeg", lambda: "ffmpeg")
    rc = cli.main(["photos", str(tmp_path / "nope")])
    assert rc == 1
