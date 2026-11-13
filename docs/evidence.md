# Observed evidence

## Offline core

`uv run mockr demo` executed all three round state machines, the native macOS sandbox, quote validation and in-memory SQLite writes. Full stdout is in [demo.txt](demo.txt). Output repeats exactly across two runs; a regression test compares stdout. SQLite identifiers and server tokens remain cryptographically random and are not part of demo stdout.

`uv run pytest -q --cov=mockr_coach --cov-report=term-missing`: 108 passed; 88% statement coverage. `tests/test_sandbox.py` runs every DSA reference against the bank cases and exercises filesystem/network/process restrictions, timeouts and bounded output. `tests/test_hardening.py` verifies calibration execution counts by running their submitted code. HTTP tests exercise provider failures, error redaction and credential confinement across redirects. No paid service was called.

## Live browser

Started `uv run mockr demo --db demo.sqlite3`, then `uv run mockr serve --db demo.sqlite3 --port 8876`. In an isolated Chromium browser:

1. Opened the dashboard after the scripted demo: 3 completed rounds; topic means 3.50, 3.80 and 4.75. [Captured dashboard](assets/dashboard.webp).
2. Selected Behavioural / An unclear goal, clicked Start practice, and submitted the five answers from `calibration/samples/behavioural-04.json` through the actual textarea and Send answer control.
3. Observed “Round saved locally.”, a 3.80/5 card with five evidence quotes, and saved count 4.
4. Resized the real viewport to 390 × 844: document scroll width 390; no horizontal overflow. Browser error log was empty.
5. Inspected browser APIs: speech recognition and synthesis both present. Did not request microphone permission or claim recognition accuracy.

The browser's first cmux surface disappeared between operations; verification continued in a separate managed Chromium. No app change was made to conceal that tooling error.

## Calibration

`uv run mockr calibrate` reported `no human labels yet: fill calibration/human_labels.csv`, 12 samples and 60 unfilled human score cells. Agreement is pending actual human labels; synthetic arithmetic fixtures are not human ratings.

## Unverified boundaries

Live LLM quality and native microphone accuracy are not locally verified. Initial verification could not use Docker because its daemon was unavailable; the later Linux filesystem fix was verified in Docker as described below. Remote CI status is separate and is not claimed green here. macOS worker line coverage is not measured inside isolated interpreters; behavior is checked through integration results.

## Clean-clone and distribution check

Cloned the committed repository into a new temporary directory using local Git transport, removed its generated local origin, and ran `uv sync --locked --python 3.12`, `uv run pytest -q`, and `uv run mockr demo` in the fresh checkout. Install exited 0; all 108 tests passed; demo stdout matched `docs/demo.txt` byte-for-byte. No external remote was created or contacted.

`uv build` produced a source distribution and wheel locally. Installed that wheel into an isolated uv environment outside the source tree and ran `mockr demo` and `mockr calibrate`: the demo matched its captured output, and calibration found the packaged samples and correctly reported no human labels. Nothing was published.

Reproduce the clean-checkout test from the repository root:

```sh
work=$(mktemp -d)
git clone --no-local . "$work/mockr"
git -C "$work/mockr" remote remove origin
(
  cd "$work/mockr"
  uv sync --locked --python 3.12
  uv run pytest -q
  uv run mockr demo
)
```

## Linux filesystem regression

Linux CI reported that `open('/tmp/mockr-escape', 'w')` succeeded. The old bubblewrap setup mounted a private but writable `/tmp`; privacy was not the same as write denial. The original regression test is unchanged.

The fix remounts the synthetic root and `/tmp` read-only, keeps `/work` and runtime binds read-only, and replaces writable `/dev` plus procfs with a bind of the single `/dev/null` device. The optional dynamic-loader cache is read-only so shared-library Python installations can start. Kernel mounts enforce this even for native Python extensions; there is no Python-level audit-filter claim.

Local Linux Docker verification ran the full suite as UID/GID 65534: **118 passed in 16.49s**. This includes the original `/tmp/mockr-escape` failure and 10 added Linux-only checks for writes under `/tmp`, `/work`, `/`, `/dev`, `/usr`, mutation operations, and permitted `/dev/null` output. The container needs `--privileged` to permit nested user namespaces; mockr itself runs unprivileged and drops sandbox capabilities.

Command, from the repository root:

```sh
docker run --rm --privileged \
  --mount "type=bind,source=$(pwd),target=/source,readonly" \
  --env PYTHONPATH=/source/src --env PYTHONDONTWRITEBYTECODE=1 \
  --workdir /tmp python:3.12-slim sh -c '
    apt-get update -qq &&
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq bubblewrap >/dev/null &&
    pip install --quiet --root-user-action=ignore pytest pytest-cov &&
    python -c '"'"'import os; os.setgid(65534); os.setuid(65534); os.execvp("python",["python","-m","pytest","-q","--tb=short","--maxfail=1","-p","no:cacheprovider","/source/tests"])'"'"'
  '
```

The verification image resolved to `python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`. No image or package was published.

After the Linux fix, native macOS verification ran `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest -q --cov=mockr_coach --cov-report=term-missing` and `uv run mockr demo`: lint/format passed; 108 tests passed with 10 Linux-only skips and 88% coverage; the demo retained its three rounds, 15 evidence scores and 5/5 DSA result.
