# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SlammingProgramming and contributors
"""Load a Job from a JSON job-spec file, for mixed multi-source timelapses.

Example job file (see examples/job.example.json):

{
  "output": "out/timelapse.mp4",
  "encoding": {"fps": 30, "width": 1920, "crf": 18},
  "sources": [
    {"type": "photos", "directory": "morning_photos"},
    {"type": "video", "path": "afternoon_clip.mp4", "speed_factor": 8},
    {"type": "stream", "url": "rtsp://camera.local/stream", "interval_seconds": 10, "duration_seconds": 3600}
  ]
}
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict

from .config import EncodingConfig
from .pipeline import Job
from .sources import PhotoSource, StreamSource, VideoSource
from .sources.base import Source


def _build_photos(spec: Dict[str, Any]) -> Source:
    kwargs = dict(spec)
    kwargs.pop("type")
    if "pattern" in kwargs and kwargs["pattern"] is not None:
        kwargs["pattern"] = re.compile(kwargs["pattern"])
    return PhotoSource(**kwargs)


def _build_video(spec: Dict[str, Any]) -> Source:
    kwargs = dict(spec)
    kwargs.pop("type")
    return VideoSource(**kwargs)


def _build_stream(spec: Dict[str, Any]) -> Source:
    kwargs = dict(spec)
    kwargs.pop("type")
    return StreamSource(**kwargs)


SOURCE_BUILDERS: Dict[str, Callable[[Dict[str, Any]], Source]] = {
    "photos": _build_photos,
    "video": _build_video,
    "stream": _build_stream,
}


def build_source(spec: Dict[str, Any]) -> Source:
    source_type = spec.get("type")
    builder = SOURCE_BUILDERS.get(source_type)
    if builder is None:
        raise ValueError(
            f"Unknown source type {source_type!r}; expected one of {sorted(SOURCE_BUILDERS)}"
        )
    return builder(spec)


def load_job(path: Path) -> Job:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    if "output" not in data:
        raise ValueError(f"Job file {path} is missing required field 'output'")
    if not data.get("sources"):
        raise ValueError(f"Job file {path} needs at least one entry in 'sources'")

    encoding = EncodingConfig(**data.get("encoding", {}))
    sources = [build_source(spec) for spec in data["sources"]]

    return Job(
        sources=sources,
        output=Path(data["output"]),
        encoding=encoding,
        work_dir=Path(data["work_dir"]) if data.get("work_dir") else None,
        keep_intermediate=bool(data.get("keep_intermediate", False)),
    )
