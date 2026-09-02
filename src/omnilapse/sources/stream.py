# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SlammingProgramming and contributors
"""Build a timelapse segment by sampling frames from a live feed (RTSP/HTTP/etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .. import ffmpeg_utils
from .base import BuildContext, Source
from .photos import PhotoSource


@dataclass
class StreamSource(Source):
    url: str
    interval_seconds: float = 5.0
    duration_seconds: Optional[float] = None
    max_frames: Optional[int] = None
    capture_dir: Optional[Path] = None
    rtsp_transport: Optional[str] = "tcp"

    def __post_init__(self) -> None:
        if self.duration_seconds is None and self.max_frames is None:
            raise ValueError(
                "StreamSource needs duration_seconds and/or max_frames so capture "
                "has a defined end (a job must terminate). For an open-ended capture, "
                "use `omnilapse stream` directly and stop it with Ctrl+C."
            )
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        if self.capture_dir is not None:
            self.capture_dir = Path(self.capture_dir)

    def capture_frames(self, ctx: BuildContext) -> Path:
        capture_dir = self.capture_dir or (ctx.work_dir / f"stream_capture_{ctx.segment_index:03d}")
        capture_dir.mkdir(parents=True, exist_ok=True)

        cmd = [ctx.ffmpeg_path, "-y"]
        if self.url.lower().startswith("rtsp://") and self.rtsp_transport:
            cmd += ["-rtsp_transport", self.rtsp_transport]
        cmd += ["-i", self.url, "-vf", f"fps=1/{self.interval_seconds}"]
        if self.duration_seconds is not None:
            cmd += ["-t", str(self.duration_seconds)]
        if self.max_frames is not None:
            cmd += ["-frames:v", str(self.max_frames)]
        cmd += [str(capture_dir / "frame_%06d.jpg")]

        ffmpeg_utils.run(cmd)
        return capture_dir

    def build(self, ctx: BuildContext) -> Path:
        capture_dir = self.capture_frames(ctx)
        photos = PhotoSource(directory=capture_dir, sort_by="name")
        return photos.build(ctx)

    def describe(self) -> str:
        return f"StreamSource({self.url})"
