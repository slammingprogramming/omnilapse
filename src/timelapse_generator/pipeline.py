"""Job orchestration: run one or more Sources and stitch them into one output file."""

from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import ffmpeg_utils
from .config import EncodingConfig
from .sources.base import BuildContext, Source

log = logging.getLogger("timelapse_generator")


@dataclass
class Job:
    sources: List[Source]
    output: Path
    encoding: EncodingConfig = field(default_factory=EncodingConfig)
    work_dir: Optional[Path] = None
    keep_intermediate: bool = False

    def __post_init__(self) -> None:
        self.output = Path(self.output)
        if self.work_dir is not None:
            self.work_dir = Path(self.work_dir)
        if not self.sources:
            raise ValueError("Job needs at least one source.")

    def run(self) -> Path:
        ffmpeg_path = ffmpeg_utils.find_ffmpeg()

        owns_work_dir = self.work_dir is None
        work_dir = self.work_dir or Path(tempfile.mkdtemp(prefix="timelapse_gen_"))
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            clips: List[Path] = []
            for index, source in enumerate(self.sources):
                log.info("[%d/%d] building %s", index + 1, len(self.sources), source.describe())
                ctx = BuildContext(
                    work_dir=work_dir,
                    encoding=self.encoding,
                    ffmpeg_path=ffmpeg_path,
                    segment_index=index,
                )
                clips.append(source.build(ctx))

            self.output.parent.mkdir(parents=True, exist_ok=True)

            if len(clips) == 1:
                shutil.copy2(clips[0], self.output)
            else:
                log.info("concatenating %d segments", len(clips))
                list_path = work_dir / "segments.txt"
                ffmpeg_utils.write_concat_list(clips, list_path)
                cmd = [
                    ffmpeg_path,
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(list_path),
                    "-c", "copy",
                    str(self.output),
                ]
                ffmpeg_utils.run(cmd)

            log.info("done: %s", self.output)
            return self.output
        finally:
            if owns_work_dir and not self.keep_intermediate:
                shutil.rmtree(work_dir, ignore_errors=True)
