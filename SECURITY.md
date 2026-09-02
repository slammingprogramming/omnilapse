# Security Policy

## Supported Versions

This project is pre-1.0 and does not yet maintain parallel release branches.
Security fixes are made against the latest release on `main`.

| Version | Supported |
| ------- | --------- |
| latest  | ✅ |
| older   | ❌ |

## Reporting a Vulnerability

Please report security issues privately rather than opening a public issue
with details in it. Two ways to reach the maintainer, either is fine:

### Option A: GitHub private vulnerability reporting

Use this repository's **Security** tab → **Report a vulnerability**, if it
has been enabled. Simplest option, no extra setup required.

### Option B: Direct contact over SimpleX (verified)

For direct, ongoing private contact, reach the maintainer over
[SimpleX](https://simplex.chat) at:

`https://smp14.simplex.im/a#3gZ-zeHs4QrFZKLAN0o3SC_XQJXhj1eYBVTO_c0FAtg`

First contact goes through a lightweight identity verification so reports
can be attributed to a real GitHub identity without exposing details
publicly:

1. Open a minimal GitHub issue that only states you're reaching out
   privately about a security-sensitive issue — no technical details yet.
2. Connect to the SimpleX address above and reference that issue.
3. Both sides exchange a public-key signature over the issue to mutually
   verify identity (your GitHub account ↔ your SimpleX profile, and the
   maintainer's identity in turn) before any details are shared.
4. Once verified, discuss the actual issue over SimpleX. Later reports
   from the same, already-verified SimpleX profile skip re-verification.

Whichever option you use, please include:

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
