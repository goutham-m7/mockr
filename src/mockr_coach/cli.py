"""Composition root for text interviews, scripted demo, calibration and local UI."""

import argparse
import json
import os
import sys
from pathlib import Path

from .bank import load_bank
from .calibration import calibrate, default_directory
from .history import History
from .providers import MockProvider, OpenAIProvider, ProviderError
from .sandbox import SandboxUnavailable
from .session import Round
from .web import create_server

DEFAULT_DB = Path.home() / ".local/share/mockr/history.sqlite3"


def scorecard_text(interview: Round) -> str:
    card = interview.scorecard
    lines = [f"Scorecard: {card['overall']:.2f}/5"]
    if interview.execution:
        result = interview.execution
        lines.append(
            f"{result['passed']}/{result['total']} hidden tests · {result['status']}"
        )
    for c in card["criteria"]:
        lines += [
            f"  {c['id']}: {c['score']}/5",
            f"    Evidence: {json.dumps(c['quote'], ensure_ascii=False)}",
            f"    Next: {c['feedback']}",
        ]
    return "\n".join(lines)


def demo(db_path: Path | str) -> None:
    bank = {q.id: q for q in load_bank()}
    print("mockr demo | OFFLINE MOCK · deterministic heuristic, not an LLM evaluation")
    names = [
        ("dsa", "dsa-parcel-pair", "DSA"),
        ("design", "design-neighbour-library", "SYSTEM DESIGN"),
        ("behavioural", "behavioural-unclear-goal", "BEHAVIOURAL"),
    ]
    for kind, question_id, label in names:
        sample = json.loads(
            (default_directory() / "samples" / f"{kind}-04.json").read_text()
        )
        interview = Round(bank[question_id], MockProvider())
        for turn in sample["transcript"]:
            interview.answer(turn["answer"])
        with History(db_path) as history:
            history.save(interview.record("mock"))
        print(f"\n{label} | {interview.question.title}")
        print(scorecard_text(interview))
    print("\n3 rounds completed · 15 evidence-backed rubric scores")
    if str(db_path) != ":memory:":
        print(f"Saved locally: {db_path}")


def interview_text(question, provider, provider_name, db_path) -> None:
    interview = Round(question, provider)
    print(f"mockr | {question.kind} | {provider_name}")
    if provider_name == "mock":
        print("OFFLINE MOCK: deterministic smoke-test heuristic, not a real LLM coach.")
    while not interview.done:
        print("\n" + interview.prompt)
        if interview.stage == "code":
            print("Paste Python; enter :end on its own line to submit.")
            lines = []
            while (line := input()) != ":end":
                lines.append(line)
            answer = "\n".join(lines)
        else:
            answer = input("\nYou: ")
        try:
            interview.answer(answer)
        except ValueError as exc:
            print(f"Answer not accepted: {exc}", file=sys.stderr)
    with History(db_path) as history:
        history.save(interview.record(provider_name))
    print("\n" + scorecard_text(interview))
    print(f"Saved locally: {db_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mockr",
        description="Local-first interview practice. Text mode by default; no account or API key needed.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="interview",
        choices=["interview", "demo", "serve", "questions", "history", "calibrate"],
    )
    parser.add_argument(
        "--kind", choices=["dsa", "design", "behavioural"], default="dsa"
    )
    parser.add_argument("--question", help="Question id; use questions to list")
    parser.add_argument(
        "--bank", type=Path, help="Directory of Markdown question files"
    )
    parser.add_argument("--db", help="SQLite history path; demo defaults to memory")
    parser.add_argument("--provider", choices=["mock", "openai"], default="mock")
    parser.add_argument(
        "--port", type=int, default=8765, help="Loopback dashboard port"
    )
    parser.add_argument(
        "--calibration-dir",
        type=Path,
        help="Directory containing samples/ and human_labels.csv",
    )
    args = parser.parse_args(argv)
    db_path = args.db or (":memory:" if args.command == "demo" else DEFAULT_DB)
    try:
        if args.command == "demo":
            demo(db_path)
            return 0
        if args.command == "history":
            with History(db_path) as history:
                print(json.dumps(history.summary(), indent=2))
            return 0
        if args.command == "questions":
            for q in load_bank(args.bank):
                print(f"{q.id} | {q.kind} | {q.topic} | {q.title}")
            return 0
        provider = (
            MockProvider()
            if args.provider == "mock"
            else OpenAIProvider(
                os.environ.get("MOCKR_BASE_URL", "https://api.openai.com/v1"),
                os.environ.get("MOCKR_API_KEY", ""),
                os.environ.get("MOCKR_MODEL", ""),
            )
        )
        if args.command == "calibrate":
            report = calibrate(provider, args.calibration_dir)
            print(f"Provider: {args.provider}")
            if report["status"] != "scored":
                print(report["status"])
            print(json.dumps(report, indent=2))
            return 0
        bank = load_bank(args.bank)
        if args.command == "serve":
            if not 0 <= args.port <= 65535:
                raise ValueError("Port must be 0–65535")
            server = create_server(db_path, bank, provider, args.provider, args.port)
            print(
                f"mockr dashboard: http://127.0.0.1:{server.server_port} | provider: {args.provider}",
                flush=True,
            )
            print(
                "Loopback only. Ctrl+C stops the server. Voice controls are in the browser.",
                flush=True,
            )
            try:
                server.serve_forever()
            finally:
                server.server_close()
            return 0
        question = (
            next((q for q in bank if q.id == args.question), None)
            if args.question
            else next((q for q in bank if q.kind == args.kind), None)
        )
        if question is None:
            raise ValueError("Unknown question or no questions for that round kind")
        interview_text(question, provider, args.provider, db_path)
        return 0
    except (ValueError, OSError, ProviderError, SandboxUnavailable) as exc:
        print(f"mockr: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nStopped. Unfinished answers were not saved.", file=sys.stderr)
        return 130
