"""Strict, portable Markdown question bank. No model-generated hidden cases."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

KINDS = ("dsa", "design", "behavioural")


@dataclass(frozen=True)
class Case:
    args: list
    expected: object


@dataclass(frozen=True)
class Question:
    id: str
    kind: str
    title: str
    topic: str
    prompt: str
    tests: tuple[Case, ...] = ()
    reference: str = ""


def parse_question(text: str) -> Question:
    match = re.fullmatch(r"```json\s*\n(.*?)\n```\s*\n(.+)", text.strip(), re.S)
    if not match:
        raise ValueError("Question needs a JSON metadata fence followed by a prompt")
    try:
        meta = json.loads(match[1])
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid question JSON") from exc
    allowed = {"id", "kind", "title", "topic", "tests", "reference"}
    if not isinstance(meta, dict) or set(meta) - allowed:
        raise ValueError("Unknown question metadata")
    for key in ("id", "kind", "title", "topic"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            raise ValueError(f"Missing or invalid {key}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", meta["id"]):
        raise ValueError("Question id must be a lowercase slug")
    if meta["kind"] not in KINDS:
        raise ValueError("Invalid round kind")
    tests = meta.get("tests", [])
    if not isinstance(tests, list):
        raise ValueError("Invalid tests")
    cases = []
    for case in tests:
        if not isinstance(case, dict) or set(case) != {"args", "expected"} or not isinstance(case["args"], list):
            raise ValueError("Each test needs args array and expected JSON value")
        cases.append(Case(case["args"], case["expected"]))
    reference = meta.get("reference", "")
    if not isinstance(reference, str):
        raise ValueError("Invalid reference solution")
    if meta["kind"] == "dsa" and not cases:
        raise ValueError("DSA questions require hidden tests")
    if meta["kind"] != "dsa" and (cases or reference):
        raise ValueError("Only DSA questions can contain code/tests")
    return Question(meta["id"], meta["kind"], meta["title"], meta["topic"], match[2].strip(), tuple(cases), reference)


def load_bank(directory: Path | None = None) -> list[Question]:
    directory = directory or Path(__file__).parent / "questions"
    questions = []
    seen = set()
    for path in sorted(directory.rglob("*.md")):
        try:
            question = parse_question(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ValueError(f"{path.name}: {exc}") from exc
        if question.id in seen:
            raise ValueError(f"Duplicate question id: {question.id}")
        seen.add(question.id)
        questions.append(question)
    if not questions:
        raise ValueError(f"No questions in {directory}")
    return questions
