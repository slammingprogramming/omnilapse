# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SlammingProgramming and contributors
"""Build a timelapse segment from an existing video by speeding it up."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .. import ffmpeg_utils
from .base import BuildContext, Source

DEFAULT_SPEED_FACTOR = 8.0


@dataclass
class VideoSource(Source):
    path: Path
    speed_factor: Optional[float] = None
    target_duration: Optional[float] = None

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        if self.speed_factor is not None and self.target_duration is not None:
            raise ValueError("Set only one of speed_factor or target_duration, not both.")
        if not self.path.is_file():
            raise FileNotFoundError(f"Video source file not found: {self.path}")

    def resolve_speed_factor(self) -> float:
        if self.speed_factor is not None:
            if self.speed_factor <= 0:
                raise ValueError("speed_factor must be > 0")
            return self.speed_factor
        if self.target_duration is not None:
            if self.target_duration <= 0:
                raise ValueError("target_duration must be > 0")
            source_duration = ffmpeg_utils.probe_duration_seconds(self.path)
            return source_duration / self.target_duration
        return DEFAULT_SPEED_FACTOR

    def build(self, ctx: BuildContext) -> Path:
        factor = self.resolve_speed_factor()

        vf_parts = [f"setpts=PTS/{factor}", "format=" + ctx.encoding.pix_fmt]
        scale = ctx.encoding.scale_filter()
        if scale:
            vf_parts.append(scale)
        vf_parts.append(f"fps={ctx.encoding.fps}")

        output = ctx.segment_path()
        cmd = [
            ctx.ffmpeg_path,
            "-y",
            "-i", str(self.path),
            "-vf", ",".join(vf_parts),
            "-an",
            "-c:v", ctx.encoding.codec,
            "-pix_fmt", ctx.encoding.pix_fmt,
            "-crf", str(ctx.encoding.crf),
            "-preset", ctx.encoding.preset,
            str(output),
        ]
        ffmpeg_utils.run(cmd)
        return output

    def describe(self) -> str:
        return f"VideoSource({self.path})"
