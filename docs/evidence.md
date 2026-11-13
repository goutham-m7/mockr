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

Live LLM quality, native microphone accuracy and Linux kernel isolation are not locally verified. CI contains a Linux bubblewrap job but has not been pushed or run. Docker CLI was present, but the local daemon was unavailable. macOS worker line coverage is not measured inside isolated interpreters; behavior is checked through integration results.

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
