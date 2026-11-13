import pytest

from mockr_coach.bank import load_bank
from mockr_coach.providers import MockProvider
from mockr_coach.session import STAGES, Round


@pytest.mark.parametrize("kind", ["dsa", "design", "behavioural"])
def test_structured_round(kind):
    q = next(q for q in load_bank() if q.kind == kind)
    interview = Round(q, MockProvider())
    assert q.prompt in interview.prompt
    for stage, _ in STAGES[kind]:
        assert interview.stage == stage
        text = (
            q.reference
            if stage == "code"
            else "I chose an approach with explicit constraints and measured results."
        )
        interview.answer(text)
    assert interview.done
    assert interview.scorecard["overall"] >= 1
    assert [t["stage"] for t in interview.transcript] == [s for s, _ in STAGES[kind]]
    if kind == "dsa":
        assert interview.execution["passed"] == 5
    with pytest.raises(ValueError, match="complete"):
        interview.answer("again")


def test_probe_references_previous_answer():
    q = next(q for q in load_bank() if q.kind == "design")
    interview = Round(q, MockProvider())
    interview.answer("I need durable reservations.")
    assert "I need durable reservations." in interview.prompt
    assert "estimates" in interview.prompt.lower()


@pytest.mark.parametrize("text", ["", "   ", "x" * 70000])
def test_invalid_answer_leaves_state_unchanged(text):
    interview = Round(load_bank()[0], MockProvider())
    with pytest.raises(ValueError):
        interview.answer(text)
    assert interview.transcript == []


def test_failed_provider_does_not_advance():
    class Bad:
        def complete(self, system, payload):
            return {"probe": ""}

    interview = Round(load_bank()[0], Bad())
    with pytest.raises(ValueError):
        interview.answer("Answer")
    assert interview.transcript == []


def test_fenced_python_submission():
    q = next(q for q in load_bank() if q.kind == "dsa")
    interview = Round(q, MockProvider())
    interview.answer("Binary search over speed.")
    interview.answer("```python\n" + q.reference + "```")
    assert interview.execution["passed"] == 5
