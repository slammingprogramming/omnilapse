import shutil
import subprocess
from pathlib import Path

import pytest

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None

requires_ffmpeg = pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg not found on PATH")


def make_test_image(path: Path, color: str = "red", size: str = "64x64") -> Path:
    """Generate a tiny synthetic JPEG at `path` using ffmpeg's lavfi source (no
    external image needed, and it exercises the same ffmpeg binary the tool uses).
    """
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s={size}",
            "-frames:v", "1", str(path),
        ],
        check=True, capture_output=True,
    )
    return path


def make_test_video(path: Path, duration: float = 2.0, size: str = "64x64", fps: int = 10) -> Path:
    """Generate a tiny synthetic mp4 at `path` using ffmpeg's lavfi testsrc."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=size={size}:rate={fps}:duration={duration}",
            "-pix_fmt", "yuv420p", str(path),
        ],
        check=True, capture_output=True,
    )
    return path
