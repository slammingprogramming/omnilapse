# AGENTS.md

Notes for anyone (human or agent) picking up work on this repo.

## What this project is

A single tool, `omnilapse`, that builds timelapses from any of:
- a folder of photos
- an existing video (sped up)
- a live stream (RTSP/HTTP/...), sampled at an interval
- any mix of the above, concatenated into one output

Everything is a thin, uniform wrapper around `ffmpeg`/`ffprobe` invoked via
`subprocess`. There is no video processing done in Python itself — Python's
job is to build the right ffmpeg command lines and stitch results together.

## Architecture

```
src/omnilapse/
  config.py        EncodingConfig — the shared fps/resolution/codec every
                    source is normalized to, so final concatenation can be a
                    cheap stream-copy instead of a second re-encode.
  ffmpeg_utils.py   find ffmpeg/ffprobe on PATH, run subprocess with error
                    capture, ffprobe duration lookups, concat-list writing.
  sources/
    base.py         Source ABC. One method: build(ctx) -> Path to a clip
                     encoded with ctx.encoding. BuildContext carries the
                     work dir, encoding config, and ffmpeg path.
    photos.py       PhotoSource — sorts a folder of images (by filename
                     timestamp pattern, mtime, or name) and encodes via the
                     ffmpeg concat demuxer.
    video.py        VideoSource — speeds up an existing video via the
                     `setpts` filter, either by a fixed factor or to hit a
                     target output duration (via ffprobe).
    stream.py       StreamSource — captures frames from a URL at a fixed
                     interval (fps filter + -t/-frames:v), then hands off to
                     PhotoSource to encode the captured frames.
  pipeline.py       Job — runs a list of Sources, each into its own clip in a
                     work dir, then concatenates (stream-copy) if there's more
                     than one. Owns temp-dir lifecycle (auto-create + cleanup
                     unless keep_intermediate or an explicit work_dir is
                     given — explicit work dirs are never deleted).
  jobfile.py        Loads a JSON job spec (see examples/job.example.json)
                     describing a Job with mixed source types — this is the
                     "photos + video + stream in one output" entry point.
  cli.py            argparse CLI: `photos`, `video`, `stream`, `job`
                     subcommands, each building a single- or multi-source Job
                     and calling .run().
```

Adding a new source type (e.g. a screen-recording source, an image-sequence-
from-a-different-tool source): implement `Source.build()`, add a
`SOURCE_BUILDERS` entry in `jobfile.py`, and add a CLI subcommand in
`cli.py`. Nothing else needs to change — `pipeline.Job` is source-agnostic.

## Conventions

- No dependencies beyond the stdlib for the core package; `ffmpeg`/`ffprobe`
  are the only external requirements, and are invoked as subprocesses, never
  linked as a library. Keep it that way unless there's a strong reason not
  to — this is meant to be a "just works if you have ffmpeg" tool.
- `dev` extra (`pytest`) is the only optional dependency group.
- Every `Source` is a `@dataclass` with validation in `__post_init__`
  (fail fast on bad input — missing files, invalid ranges — before any
  ffmpeg process is spawned).
- `EncodingConfig` is the single source of truth for output format; sources
  should never hardcode fps/codec/pixel format themselves.
- Tests mock `ffmpeg_utils.run`/`find_ffmpeg` for unit tests (fast, no ffmpeg
  needed) and use real ffmpeg (via `tests/conftest.py` lavfi helpers) in
  `tests/test_integration.py` for end-to-end coverage — those are
  auto-skipped when ffmpeg isn't on PATH.

## Build / test

```bash
pip install -e ".[dev]"
pytest
omnilapse --help
```

## License

AGPL-3.0-or-later (see [LICENSE](LICENSE)). New source files should carry the
two-line SPDX header used throughout `src/`:

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) <year> SlammingProgramming and contributors
```

## Publishing safety

This repository's history is public (GitHub). Before pushing anything to a
public remote — not just once, but every time:

- [ ] Sweep tracked files and the *full* commit history (not just the diff)
      for names, personal emails, local filesystem paths, internal
      hostnames, or references to any private infrastructure.
      `git log --all --format="%an <%ae> / %cn <%ce>"` for authorship;
      `git grep` across tracked files for anything that looks personal.
- [ ] Never name or reference a private mirror/remote (host, path, org/team
      name) in any tracked file, commit message, or doc — including this
      one. If a workflow note needs that detail, keep it out of git
      entirely.
- [ ] Get the repo owner's explicit go-ahead for that specific push before
      pushing to a public remote — a prior push being fine doesn't imply
      the next one is.

Remaining one-time setup (needs the GitHub web UI, not git):

- [ ] Confirm GitHub's private vulnerability reporting is enabled
      (Settings → Security), since `SECURITY.md` offers it as Option A.
- [ ] Add a CI badge to `README.md` once Actions has run at least once.

## Roadmap / open items

Rough priority order for whoever picks this up next:

- [ ] YAML job files as an alternative to JSON (`jobfile.py` currently only
      parses JSON; the schema is simple enough that YAML support is just a
      loader swap plus a `pyyaml` optional dependency).
- [ ] EXIF-based timestamp sorting for `PhotoSource` (currently: filename
      pattern, mtime, or name only — no image metadata read). Should stay an
      optional path (extra dependency like `Pillow`) rather than a hard
      requirement.
- [ ] Auto-reconnect for `StreamSource` on a dropped RTSP connection during a
      long capture, instead of the whole job failing partway through.
- [ ] A "watch" mode: keep appending newly-arrived frames from a folder or a
      live stream into a growing timelapse (for long-running/unattended
      capture, as opposed to today's fixed-duration jobs).
- [ ] Hardware-accelerated encode presets (nvenc/qsv/videotoolbox) as
      alternates to the default `libx264`.
- [ ] Optional overlay/burn-in filter (timestamp, watermark) applied at the
      final concat stage.
- [ ] `--version` flag on the CLI.
- [ ] Progress reporting during long stream captures (ffmpeg's `-progress`
      pipe, surfaced as a simple progress bar).
- [ ] Package for PyPI (CI already exists: `.github/workflows/ci.yml`).
- [ ] Consider whether `VideoSource` should have an option to keep audio
      (sped up alongside video) instead of always dropping it with `-an`.

## History

This project grew from a single-script prototype (`Pictures to Timelapse
Converter/timelapsegen.py`, since removed) hardcoded to one photo-filename
convention and one ffmpeg command. Its logic (dated-filename sorting +
concat-demuxer encode) was generalized into `sources/photos.py`.
