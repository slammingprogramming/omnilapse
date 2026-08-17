"""Shared configuration types for building timelapses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EncodingConfig:
    """Output encoding settings applied uniformly across every source in a job.

    All sources in a job are normalized to this config before concatenation, so
    the final concat step can use stream copy instead of re-encoding twice.
    """

    fps: float = 30.0
    width: Optional[int] = None
    height: Optional[int] = None
    codec: str = "libx264"
    pix_fmt: str = "yuv420p"
    crf: int = 18
    preset: str = "medium"

    def __post_init__(self) -> None:
        object.__setattr__(self, "fps", float(self.fps))

    def scale_filter(self) -> Optional[str]:
        if self.width is None and self.height is None:
            return None
        w = self.width if self.width is not None else -2
        h = self.height if self.height is not None else -2
        return f"scale={w}:{h}"
