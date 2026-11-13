# mockr design

## Problem and scope
Practice interviews need reproducible questions, executable feedback, and evidence for subjective scores. mockr is a local-first text interview coach with optional browser speech, not an autonomous hiring decision tool. All question content and fixtures are original synthetic material.

## Decisions and alternatives
Python 3.12 fits submitted Python solutions, SQLite, and a dependency-free HTTP server. A TypeScript frontend plus Python runner would add a second runtime without improving the core. SQLite avoids server setup; a local single-user UI avoids authentication and cloud storage. Markdown files contain a JSON metadata fence and a readable prompt, making the bank inspectable and portable without a YAML dependency.

Native macOS Seatbelt isolates a fresh Python subprocess for every hidden case; Linux uses bubblewrap with unshared namespaces and a read-only runtime. Both deny network, protect host files, limit CPU/memory/file sizes/processes, and enforce wall time. Unsupported hosts fail closed. Resource limits alone are not a sandbox. This is defense in depth for local practice, not a hostile multi-tenant execution service; kernel/interpreter vulnerabilities remain out of scope.

## Components and data flow
CLI/browser → round state machine → provider (mock or OpenAI-compatible HTTP).
DSA code → sandbox supervisor → one isolated worker per hidden case → aggregate result.
Transcript + explicit round rubric + execution summary → judge → validated evidence scorecard → SQLite.
SQLite → progress aggregation → loopback dashboard.
Calibration samples + human reference scores → same judge → exact/within-one agreement and MAE.

## Contracts
DSA follows approach → code → complexity. System design follows requirements → estimates → API → data model → scaling → trade-offs. Behavioural follows situation → task → action → result → reflection. The provider produces answer-aware probes after each answer; fixed stage ordering cannot be changed by model output.
Every rubric criterion has integer score 1–5, a verbatim nonempty candidate quote and concrete feedback. Validate every quote against candidate answers, exact criterion coverage, and bounds before storage. Mock scoring is deterministic and transparent, not an LLM-quality claim. Real judging is a JSON-only OpenAI chat-completions request with bounded response size and timeout, no automatic retry.

## Failure behavior and security
Malformed question files fail before a session starts. Candidate input is untrusted, including instructions to the judge. Code/test data are passed over stdin, not shell interpolation. Hidden cases stay server-side and reports expose only counts/status, not expected values. Invalid judge JSON/quotes fail visibly; unfinished sessions remain in memory and are not represented as completed. SQLite stores full plaintext transcripts locally; browser routes expose only loopback, check Host/Origin, and use a per-server CSRF token for writes. No CORS or remote binding. Voice requires an explicit click; browser vendors may process speech remotely even though mockr uses no paid voice API.

## Rollout and storage
Fresh local repository and schema version 1; create tables on first use. Default history is ~/.local/share/mockr/history.sqlite3; demo uses memory unless --db is supplied. No cloud migration, telemetry, package publication, remote, or credentials in the repository.

## Verification contract
- Question loader: 30 unique originals (10 per type), validated metadata, DSA edge cases and reference solutions executed in isolation.
- Rounds: all stage sequences, answer-aware follow-ups, rejection of blank/oversized input and duplicate completion.
- Runner: correct/wrong code, syntax/runtime errors, timeout, network/filesystem/subprocess denial.
- Judge: each rubric, quote provenance, missing/extra criteria, invalid scores, HTTP failure and malformed response.
- Storage/dashboard: real SQLite round trip, weak-topic means/trends, empty state, escaped hostile text.
- Browser: text session and optional speech controls; real HTTP integration covers API, origin/CSRF and error behavior. Native microphone permission and speech accuracy require manual browser checks.
- Calibration: human reference fixture provenance, exact/within-one/MAE calculations, offline and remote provider path.
- CLI/demo: run tests, lint, demo, calibration and capture actual output in README.

## Limitations and roadmap
No resume upload, video, editor integration, distributed execution, anti-cheat, or hiring recommendations. Expand independently human-labeled calibration, add a stronger container/VM execution backend for hostile code, and conduct cross-browser microphone accessibility testing. The bundled small calibration set is author-scored synthetic data, not a representative validity study.
