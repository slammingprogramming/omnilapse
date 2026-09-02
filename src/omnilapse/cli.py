# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SlammingProgramming and contributors
"""Command-line interface for omnilapse.

Subcommands:
  photos  - build a timelapse from a folder of still images
  video   - speed up an existing video into a timelapse
  stream  - sample frames from a live feed (RTSP/HTTP/...) into a timelapse
  job     - run a JSON job file describing one or more mixed sources
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

from . import ffmpeg_utils
from .config import EncodingConfig
from .jobfile import load_job
from .pipeline import Job
from .sources import PhotoSource, StreamSource, VideoSource

log = logging.getLogger("omnilapse")


def _add_encoding_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("encoding")
    group.add_argument("--fps", type=float, default=30.0, help="output frames per second (default: 30)")
    group.add_argument("--width", type=int, default=None, help="output width in px (height auto-scaled)")
    group.add_argument("--height", type=int, default=None, help="output height in px (width auto-scaled)")
    group.add_argument("--codec", default="libx264", help="ffmpeg video codec (default: libx264)")
    group.add_argument("--pix-fmt", dest="pix_fmt", default="yuv420p", help="pixel format (default: yuv420p)")
    group.add_argument("--crf", type=int, default=18, help="constant rate factor, lower = higher quality (default: 18)")
    group.add_argument("--preset", default="medium", help="encoder preset (default: medium)")


def _encoding_from_args(args: argparse.Namespace) -> EncodingConfig:
    return EncodingConfig(
        fps=args.fps,
        width=args.width,
        height=args.height,
        codec=args.codec,
        pix_fmt=args.pix_fmt,
        crf=args.crf,
        preset=args.preset,
    )


def _add_job_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--work-dir", type=Path, default=None, help="reuse this directory for intermediate files instead of a temp dir")
    parser.add_argument("--keep-intermediate", action="store_true", help="don't delete auto-created intermediate files")


def cmd_photos(args: argparse.Namespace) -> Path:
    source = PhotoSource(
        directory=args.directory,
        recursive=args.recursive,
        sort_by=args.sort_by,
        pattern=re.compile(args.pattern) if args.pattern else None,
    )
    job = Job(
        sources=[source],
        output=args.output,
        encoding=_encoding_from_args(args),
        work_dir=args.work_dir,
        keep_intermediate=args.keep_intermediate,
    )
    return job.run()


def cmd_video(args: argparse.Namespace) -> Path:
    source = VideoSource(
        path=args.input,
        speed_factor=args.speed_factor,
        target_duration=args.target_duration,
    )
    job = Job(
        sources=[source],
        output=args.output,
        encoding=_encoding_from_args(args),
        work_dir=args.work_dir,
        keep_intermediate=args.keep_intermediate,
    )
    return job.run()


def cmd_stream(args: argparse.Namespace) -> Path:
    source = StreamSource(
        url=args.url,
        interval_seconds=args.interval,
        duration_seconds=args.duration,
        max_frames=args.max_frames,
        capture_dir=args.capture_dir,
        rtsp_transport=args.rtsp_transport,
    )
    job = Job(
        sources=[source],
        output=args.output,
        encoding=_encoding_from_args(args),
        work_dir=args.work_dir,
        keep_intermediate=args.keep_intermediate,
    )
    return job.run()


def cmd_job(args: argparse.Namespace) -> Path:
    job = load_job(args.job_file)
    if args.output is not None:
        job.output = args.output
    if args.work_dir is not None:
        job.work_dir = args.work_dir
    if args.keep_intermediate:
        job.keep_intermediate = True
    return job.run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omnilapse", description=__doc__.splitlines()[0])
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_photos = subparsers.add_parser("photos", help="build a timelapse from a folder of still images")
    p_photos.add_argument("directory", type=Path, help="folder containing photos")
    p_photos.add_argument("-o", "--output", type=Path, default=Path("timelapse.mp4"))
    p_photos.add_argument("--sort-by", choices=["auto", "name", "mtime", "pattern"], default="auto")
    p_photos.add_argument("--pattern", default=None, help="regex used to extract a sortable timestamp from filenames (with --sort-by pattern/auto)")
    p_photos.add_argument("--recursive", action="store_true", help="also search subfolders")
    _add_encoding_args(p_photos)
    _add_job_run_args(p_photos)
    p_photos.set_defaults(func=cmd_photos)

    p_video = subparsers.add_parser("video", help="speed up an existing video into a timelapse")
    p_video.add_argument("input", type=Path, help="source video file")
    p_video.add_argument("-o", "--output", type=Path, default=Path("timelapse.mp4"))
    speed_group = p_video.add_mutually_exclusive_group()
    speed_group.add_argument("--speed-factor", type=float, default=None, help="play this many times faster than the source (default: 8x if neither option is given)")
    speed_group.add_argument("--target-duration", type=float, default=None, help="stretch/compress output to this many seconds instead of a fixed speed factor")
    _add_encoding_args(p_video)
    _add_job_run_args(p_video)
    p_video.set_defaults(func=cmd_video)

    p_stream = subparsers.add_parser("stream", help="sample frames from a live feed (RTSP/HTTP/...) into a timelapse")
    p_stream.add_argument("url", help="stream URL, e.g. rtsp://user:pass@host/stream")
    p_stream.add_argument("-o", "--output", type=Path, default=Path("timelapse.mp4"))
    p_stream.add_argument("--interval", type=float, default=5.0, help="seconds between captured frames (default: 5)")
    duration_group = p_stream.add_mutually_exclusive_group(required=True)
    duration_group.add_argument("--duration", type=float, default=None, help="stop capturing after this many seconds")
    duration_group.add_argument("--max-frames", type=int, default=None, help="stop capturing after this many frames")
    p_stream.add_argument("--capture-dir", type=Path, default=None, help="save captured frames here instead of a temp dir")
    p_stream.add_argument("--rtsp-transport", default="tcp", help="rtsp transport protocol (default: tcp)")
    _add_encoding_args(p_stream)
    _add_job_run_args(p_stream)
    p_stream.set_defaults(func=cmd_stream)

    p_job = subparsers.add_parser("job", help="run a JSON job file describing one or more mixed sources (photos + video + stream)")
    p_job.add_argument("job_file", type=Path, help="path to a job JSON file (see examples/job.example.json)")
    p_job.add_argument("-o", "--output", type=Path, default=None, help="override the job file's output path")
    _add_job_run_args(p_job)
    p_job.set_defaults(func=cmd_job)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        output = args.func(args)
    except ffmpeg_utils.FFmpegNotFoundError as exc:
        log.error("%s", exc)
        return 2
    except ffmpeg_utils.FFmpegError as exc:
        log.error("ffmpeg failed: %s", exc)
        return 1
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        log.error("%s", exc)
        return 1

    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
