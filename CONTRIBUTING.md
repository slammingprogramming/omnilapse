# Contributing

Thanks for considering a contribution. This is a small project, so the
process is intentionally light.

## Ground rules

- By submitting a contribution, you agree to license it under this project's
  license, the GNU Affero General Public License v3.0 or later (see
  [LICENSE](LICENSE)). There's no separate CLA.
- Be kind — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Getting set up

Requirements: Python 3.9+, and [ffmpeg](https://ffmpeg.org/download.html)
(with `ffprobe`) on your `PATH`.

```bash
git clone <this repo>
cd omnilapse
pip install -e ".[dev]"
```

Run the CLI locally:

```bash
omnilapse --help
```

Run the tests:

```bash
pytest
```

Most tests mock ffmpeg calls and need nothing installed; a few in
`tests/test_integration.py` invoke real ffmpeg and are skipped automatically
if it's missing from `PATH`. If you're touching anything that builds an
ffmpeg command line, make sure ffmpeg is installed and those tests run too —
that's where wrong flags actually get caught.

## Before you open a PR

- Read [AGENTS.md](AGENTS.md) — it documents the architecture, conventions,
  and the current roadmap. Following the existing patterns (dataclass
  `Source`s validating in `__post_init__`, no dependencies beyond the
  stdlib, `EncodingConfig` as the single source of truth for output format)
  keeps the codebase consistent.
- Add or update tests for any behavior change.
- Run `pytest` locally and make sure it's green.
- Keep PRs focused — one change per PR is easier to review than several
  bundled together.

## Adding a new source type

If you're adding a new way to feed frames in (e.g. a screen-recording
source), see the "Adding a new source type" note in
[AGENTS.md](AGENTS.md#architecture) — it's a short, well-defined interface
(`Source.build()`), plus a `jobfile.py` entry and a CLI subcommand.

## Reporting bugs / requesting features

Use the GitHub issue templates. For security issues, see
[SECURITY.md](SECURITY.md) instead of opening a public issue.

## Commit messages / PR descriptions

Explain *why*, not just *what* — the diff already shows what changed. A
sentence or two on the motivation is enough for most changes.
