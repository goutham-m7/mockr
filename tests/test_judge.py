import copy

import pytest

from mockr_coach.judge import RUBRICS, judge, validate_scorecard
from mockr_coach.providers import MockProvider


@pytest.mark.parametrize("kind", ["dsa", "design", "behavioural"])
def test_evidence_scorecards(kind):
    transcript = [
        {
            "stage": "approach",
            "answer": "I compared alternatives and measured the outcome with a clear baseline.",
        }
    ]
    card = judge(MockProvider(), kind, "An original prompt", transcript, None)
    assert len(card["criteria"]) == len(RUBRICS[kind])
    assert all(c["quote"] in transcript[0]["answer"] for c in card["criteria"])
    assert 1 <= card["overall"] <= 5


def test_correctness_uses_execution():
    transcript = [{"stage": "code", "answer": "def solve(x): return 1"}]
    card = judge(
        MockProvider(),
        "dsa",
        "A prompt",
        transcript,
        {"passed": 0, "total": 5, "status": "wrong-answer"},
    )
    assert next(c for c in card["criteria"] if c["id"] == "correctness")["score"] == 1


@pytest.mark.parametrize(
    "mutation", ["quote", "missing", "extra", "range", "bool", "duplicate", "feedback"]
)
def test_invalid_judge_output(mutation):
    transcript = [
        {"stage": "action", "answer": "I wrote a test and resolved the incident."}
    ]
    card = judge(MockProvider(), "behavioural", "A prompt", transcript, None)
    raw = copy.deepcopy(card)
    if mutation == "quote":
        raw["criteria"][0]["quote"] = "A fabricated statement"
    if mutation == "missing":
        raw["criteria"].pop()
    if mutation == "extra":
        raw["criteria"].append(
            {"id": "made-up", "score": 3, "quote": "I", "feedback": "More detail"}
        )
    if mutation == "range":
        raw["criteria"][0]["score"] = 6
    if mutation == "bool":
        raw["criteria"][0]["score"] = True
    if mutation == "duplicate":
        raw["criteria"][1]["id"] = raw["criteria"][0]["id"]
    if mutation == "feedback":
        raw["criteria"][0]["feedback"] = ""
    with pytest.raises(ValueError):
        validate_scorecard(raw, "behavioural", transcript)


def test_provider_boundary_receives_rubric_and_execution():
    class Capture:
        def complete(self, system, payload):
            assert "untrusted" in system
            assert payload["rubric"] == RUBRICS["dsa"]
            assert payload["execution"]["passed"] == 5
            return MockProvider().complete(system, payload)

    judge(
        Capture(),
        "dsa",
        "Prompt",
        [{"stage": "code", "answer": "def solve(x): return x"}],
        {"passed": 5, "total": 5, "status": "passed"},
    )


def test_empty_transcript_rejected():
    with pytest.raises(ValueError):
        judge(MockProvider(), "dsa", "Prompt", [], None)
