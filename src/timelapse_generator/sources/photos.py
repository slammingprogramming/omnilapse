# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SlammingProgramming and contributors
"""Build a timelapse segment from a folder of still photos."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .. import ffmpeg_utils
from .base import BuildContext, Source

DEFAULT_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")

# Matches the original project's filename convention, e.g. 20251102_00_13_14.jpg
DEFAULT_TIMESTAMP_PATTERN = re.compile(r"(\d{8})_(\d{2})_(\d{2})_(\d{2})")


@dataclass
class PhotoSource(Source):
    directory: Path
    extensions: Tuple[str, ...] = DEFAULT_EXTENSIONS
    recursive: bool = False
    sort_by: str = "auto"  # "auto" | "name" | "mtime" | "pattern"
    pattern: Optional[re.Pattern] = None

    def __post_init__(self) -> None:
        self.directory = Path(self.directory)
        if self.sort_by == "pattern" and self.pattern is None:
            self.pattern = DEFAULT_TIMESTAMP_PATTERN

    def list_images(self) -> List[Path]:
        if not self.directory.is_dir():
            raise NotADirectoryError(f"Photo source directory not found: {self.directory}")

        globber = self.directory.rglob if self.recursive else self.directory.glob
        files = [
            p for p in globber("*")
            if p.is_file() and p.suffix.lower() in self.extensions
        ]
        if not files:
            raise FileNotFoundError(
                f"No images with extensions {self.extensions} found in {self.directory}"
            )

        sort_by = self.sort_by
        if sort_by == "auto":
            sort_by = "pattern" if self.pattern or DEFAULT_TIMESTAMP_PATTERN.search(files[0].name) else "name"

        if sort_by == "mtime":
            files.sort(key=lambda p: p.stat().st_mtime)
        elif sort_by == "pattern":
            pattern = self.pattern or DEFAULT_TIMESTAMP_PATTERN
            matched = []
            unmatched = []
            for p in files:
                m = pattern.search(p.name)
                if m:
                    matched.append(("".join(m.groups()), p))
                else:
                    unmatched.append(p)
            matched.sort(key=lambda t: t[0])
            files = [p for _, p in matched] + sorted(unmatched, key=lambda p: p.name)
        else:  # "name"
            files.sort(key=lambda p: p.name)

        return files

    def build(self, ctx: BuildContext) -> Path:
        images = self.list_images()
        list_path = ctx.work_dir / f"photos_{ctx.segment_index:03d}.txt"
        ffmpeg_utils.write_concat_list(images, list_path)

        vf_parts = ["format=" + ctx.encoding.pix_fmt]
        scale = ctx.encoding.scale_filter()
        if scale:
            vf_parts.append(scale)

        output = ctx.segment_path()
        cmd = [
            ctx.ffmpeg_path,
            "-y",
            "-r", str(ctx.encoding.fps),
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_path),
            "-vf", ",".join(vf_parts),
            "-r", str(ctx.encoding.fps),
            "-c:v", ctx.encoding.codec,
            "-pix_fmt", ctx.encoding.pix_fmt,
            "-crf", str(ctx.encoding.crf),
            "-preset", ctx.encoding.preset,
            str(output),
        ]
        ffmpeg_utils.run(cmd)
        return output

    def describe(self) -> str:
        return f"PhotoSource({self.directory})"
