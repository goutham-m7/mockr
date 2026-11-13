import json

import pytest

from mockr_coach.bank import load_bank, parse_question


def document(meta, prompt="An original problem."):
    return "```json\n" + json.dumps(meta) + "\n```\n\n" + prompt


def test_parse_design():
    q = parse_question(
        document(
            {
                "id": "design-cache",
                "kind": "design",
                "title": "Cache",
                "topic": "storage",
            }
        )
    )
    assert q.prompt == "An original problem."
    assert q.kind == "design"


@pytest.mark.parametrize(
    "change", [{"kind": "unknown"}, {"id": "../bad"}, {"title": ""}, {"extra": 1}]
)
def test_invalid_metadata(change):
    meta = {
        "id": "design-cache",
        "kind": "design",
        "title": "Cache",
        "topic": "storage",
    }
    meta.update(change)
    with pytest.raises(ValueError):
        parse_question(document(meta))


def test_dsa_requires_tests():
    with pytest.raises(ValueError, match="tests"):
        parse_question(
            document({"id": "sum", "kind": "dsa", "title": "Sum", "topic": "arrays"})
        )


def test_duplicate_bank(tmp_path):
    text = document(
        {"id": "cache", "kind": "design", "title": "Cache", "topic": "storage"}
    )
    (tmp_path / "a.md").write_text(text)
    (tmp_path / "b.md").write_text(text)
    with pytest.raises(ValueError, match="Duplicate"):
        load_bank(tmp_path)


def test_empty_bank(tmp_path):
    with pytest.raises(ValueError, match="No questions"):
        load_bank(tmp_path)


def test_bundled_bank():
    bank = load_bank()
    assert len(bank) == 30
    assert {
        kind: sum(q.kind == kind for q in bank)
        for kind in ("dsa", "design", "behavioural")
    } == {"dsa": 10, "design": 10, "behavioural": 10}
    assert all(len(q.tests) >= 4 and q.reference for q in bank if q.kind == "dsa")
