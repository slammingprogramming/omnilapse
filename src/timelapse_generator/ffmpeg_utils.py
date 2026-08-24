# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SlammingProgramming and contributors
"""Helpers for locating and invoking ffmpeg/ffprobe."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Sequence


class FFmpegNotFoundError(RuntimeError):
    pass


class FFmpegError(RuntimeError):
    """Raised when an ffmpeg/ffprobe invocation exits non-zero."""

    def __init__(self, cmd: Sequence[str], returncode: int, stderr: str):
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"Command failed ({returncode}): {' '.join(self.cmd)}\n{stderr.strip()}"
        )


def find_binary(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise FFmpegNotFoundError(
            f"'{name}' was not found on PATH. Install ffmpeg "
            "(https://ffmpeg.org/download.html) and make sure it's on your PATH."
        )
    return path


def find_ffmpeg() -> str:
    return find_binary("ffmpeg")


def find_ffprobe() -> str:
    return find_binary("ffprobe")


def run(cmd: Sequence[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, raising FFmpegError with captured stderr on failure."""
    kwargs.setdefault("stdout", subprocess.PIPE)
    kwargs.setdefault("stderr", subprocess.PIPE)
    kwargs.setdefault("text", True)
    result = subprocess.run(list(cmd), **kwargs)
    if result.returncode != 0:
        raise FFmpegError(cmd, result.returncode, result.stderr or "")
    return result


def probe_duration_seconds(path: Path) -> float:
    """Return the duration of a media file in seconds via ffprobe."""
    ffprobe = find_ffprobe()
    cmd: List[str] = [
        ffprobe,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    result = run(cmd)
    data = json.loads(result.stdout)
    try:
        return float(data["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FFmpegError(cmd, 0, f"Could not parse duration from ffprobe output: {result.stdout}") from exc


def write_concat_list(entries: Sequence[Path], list_path: Path) -> None:
    """Write an ffmpeg concat-demuxer list file for the given files, in order."""
    with open(list_path, "w", encoding="utf-8") as f:
        for entry in entries:
            safe_path = str(entry.resolve()).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")
