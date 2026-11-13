import json
import sqlite3

import pytest

from mockr_coach.bank import Case, load_bank, parse_question
from mockr_coach.calibration import default_directory
from mockr_coach.history import History
from mockr_coach.judge import validate_scorecard
from mockr_coach.providers import MockProvider
from mockr_coach.sandbox import Sandbox, SandboxUnavailable
from mockr_coach.session import Round


def test_sandbox_preflight_detects_infrastructure_failure(monkeypatch):
    # OS subprocess boundary, not a fake of our runner logic.
    monkeypatch.setattr("mockr_coach.sandbox.shutil.which", lambda name: None)
    monkeypatch.setattr("mockr_coach.sandbox.platform.system", lambda: "Unsupported")
    with pytest.raises(SandboxUnavailable):
        Sandbox().run("def solve(): return 1", (Case([], 1),))


@pytest.mark.parametrize(
    "value",
    ["not fenced", "```json\n{broken}\n```\nPrompt", "```json\n[]\n```\nPrompt"],
)
def test_malformed_question_documents(value):
    with pytest.raises(ValueError):
        parse_question(value)


def test_bad_case_shape():
    meta = {
        "id": "x",
        "kind": "dsa",
        "title": "X",
        "topic": "x",
        "tests": [{"args": "not-list", "expected": 0}],
    }
    with pytest.raises(ValueError):
        parse_question("```json\n" + json.dumps(meta) + "\n```\nPrompt")


def test_reject_newer_history_schema(tmp_path):
    path = tmp_path / "future.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError, match="schema"):
        History(path)


def test_incomplete_session_cannot_be_saved():
    with pytest.raises(ValueError, match="unfinished"):
        Round(load_bank()[0], MockProvider()).record("mock")


def test_bad_criterion_shape():
    with pytest.raises(ValueError):
        validate_scorecard({"criteria": [{}] * 4}, "dsa", [{"answer": "a"}])


@pytest.mark.parametrize(
    "sample",
    sorted((default_directory() / "samples").glob("dsa-*.json")),
    ids=lambda p: p.stem,
)
def test_calibration_execution_counts_are_real(sample):
    data = json.loads(sample.read_text())
    code = next(t["answer"] for t in data["transcript"] if t["stage"] == "code")
    question = next(q for q in load_bank() if q.id == "dsa-parcel-pair")
    result = Sandbox().run(code, question.tests)
    assert result.passed == data["execution"]["passed"]
    assert result.status == data["execution"]["status"]
