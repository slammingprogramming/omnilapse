# Security Policy

## Supported Versions

This project is pre-1.0 and does not yet maintain parallel release branches.
Security fixes are made against the latest release on `master`.

| Version | Supported |
| ------- | --------- |
| latest  | ✅ |
| older   | ❌ |

## Reporting a Vulnerability

Please report security issues privately rather than opening a public issue.

Preferred: use GitHub's private vulnerability reporting for this repository
(**Security** tab → **Report a vulnerability**), if it has been enabled.

If that isn't available, contact the maintainer directly at
`[MAINTAINER CONTACT — TODO before publishing]`.

Please include:

- A description of the issue and its potential impact
- Steps to reproduce (a minimal example is ideal)
- The version/commit you tested against

We'll acknowledge reports as promptly as we can and work with you on a fix
and coordinated disclosure timeline before any public write-up.

## Scope notes

`omnilapse` shells out to `ffmpeg`/`ffprobe` with paths and URLs you give
it — it does not fetch or execute anything on its own. Reports related to how
untrusted input (e.g. a job file or stream URL from someone else) is passed
to those subprocesses are in scope; issues purely within `ffmpeg` itself
should also be reported upstream to the [FFmpeg project](https://ffmpeg.org/security.html).
