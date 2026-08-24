# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Licensed under AGPL-3.0-or-later; added standard OSS project scaffolding
  (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, issue/PR templates).

## [0.1.0] - 2026-08-16

### Added

- Initial multi-source timelapse tool: `timelapse-gen` CLI with `photos`,
  `video`, `stream`, and `job` subcommands.
- `PhotoSource`, `VideoSource`, `StreamSource`, each normalizing to a shared
  `EncodingConfig` and producing an intermediate clip via ffmpeg.
- `Job`/`pipeline.py` to run one or more sources and concatenate them
  (stream-copy) into a single output.
- `jobfile.py` JSON job-spec format for mixed workflows (photos + video +
  stream in one output); see `examples/job.example.json`.
- Unit tests (mocked ffmpeg) and integration tests (real ffmpeg, auto-skipped
  if unavailable); GitHub Actions CI.
- `AGENTS.md` documenting architecture, conventions, and roadmap.

### Removed

- The original single-purpose prototype script
  (`Pictures to Timelapse Converter/timelapsegen.py`), superseded by
  `sources/photos.py`.

[Unreleased]: https://github.com/OWNER/timelapse-generator/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/OWNER/timelapse-generator/releases/tag/v0.1.0
