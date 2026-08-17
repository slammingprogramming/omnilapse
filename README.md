# timelapse-generator

A single tool for turning things into timelapses: folders of photos, existing
videos (sped up), live streams (RTSP/HTTP/...), or any mix of those stitched
into one output clip.

Under the hood it's a thin, uniform layer over `ffmpeg`. Every input is
normalized to a shared resolution/fps/codec and, when there's more than one,
concatenated with a fast stream-copy at the end.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/download.html) (and `ffprobe`, which ships with it) on your `PATH`

## Install

```bash
pip install -e ".[dev]"
```

This installs the `timelapse-gen` CLI.

## Usage

### From a folder of photos

```bash
timelapse-gen photos ./my_photos -o timelapse.mp4 --fps 30
```

Photos are sorted automatically: if filenames contain a
`YYYYMMDD_HH_MM_SS`-style timestamp it sorts by that, otherwise by filename.
Override with `--sort-by {auto,name,mtime,pattern}` and `--pattern <regex>`.

### From an existing video (speed it up)

```bash
timelapse-gen video long_recording.mp4 -o timelapse.mp4 --speed-factor 20
# or target a specific output length instead of a fixed speed:
timelapse-gen video long_recording.mp4 -o timelapse.mp4 --target-duration 30
```

### From a live stream (RTSP/HTTP/...)

Samples one frame every `--interval` seconds until `--duration` or
`--max-frames` is hit, then encodes them into a clip.

```bash
timelapse-gen stream rtsp://user:pass@camera.local/stream \
  --interval 10 --duration 3600 -o timelapse.mp4
```

### Mixed sources (photos + video + stream, in one output)

Describe the sources in a JSON job file and run it — see
[`examples/job.example.json`](examples/job.example.json):

```bash
timelapse-gen job my_job.json
```

```json
{
  "output": "out/mixed_timelapse.mp4",
  "encoding": { "fps": 30, "width": 1920, "crf": 18 },
  "sources": [
    { "type": "photos", "directory": "morning_photos" },
    { "type": "video", "path": "afternoon_clip.mp4", "speed_factor": 8 },
    { "type": "stream", "url": "rtsp://camera.local/stream", "interval_seconds": 10, "duration_seconds": 3600 }
  ]
}
```

### Common options

All subcommands accept `--fps`, `--width`/`--height`, `--codec`, `--pix-fmt`,
`--crf`, `--preset`, `--work-dir` (reuse a directory for intermediate files),
and `--keep-intermediate` (don't delete auto-created temp files — useful for
debugging).

## Project layout

See [AGENTS.md](AGENTS.md) for architecture notes, conventions, and the
current roadmap.

## Tests

```bash
pytest
```

Most tests mock ffmpeg calls and run without it installed; a handful in
`tests/test_integration.py` invoke real ffmpeg and are skipped automatically
if it isn't on `PATH`.

## History

The original prototype — a single script for turning a dated-filename photo
folder into a timelapse — lives in
[`Pictures to Timelapse Converter/timelapsegen.py`](Pictures%20to%20Timelapse%20Converter/timelapsegen.py).
Its logic was generalized into `timelapse_generator.sources.photos` as part
of building this into a full multi-source tool.
