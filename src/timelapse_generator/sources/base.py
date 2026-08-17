"""Base types shared by every timelapse source."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from ..config import EncodingConfig


@dataclass
class BuildContext:
    """Everything a Source needs to produce a normalized intermediate clip."""

    work_dir: Path
    encoding: EncodingConfig
    ffmpeg_path: str
    segment_index: int = 0

    def segment_path(self, suffix: str = ".mp4") -> Path:
        return self.work_dir / f"segment_{self.segment_index:03d}{suffix}"


class Source(ABC):
    """A single input (a photo folder, a video, a live stream, ...) that can be
    normalized into one intermediate clip encoded with a shared EncodingConfig.
    A Job strings several Sources together and concatenates their clips.
    """

    @abstractmethod
    def build(self, ctx: BuildContext) -> Path:
        """Produce a clip at ctx.segment_path() (or return an existing path to it)
        encoded with ctx.encoding, and return that path.
        """
        raise NotImplementedError

    def describe(self) -> str:
        return self.__class__.__name__
