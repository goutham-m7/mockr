import csv
import json

import pytest

from mockr_coach.calibration import calibrate, default_directory
from mockr_coach.providers import MockProvider


def test_bundled_samples_have_no_human_claims():
    directory = default_directory()
    samples = [
        json.loads(p.read_text()) for p in (directory / "samples").glob("*.json")
    ]
    assert len(samples) == 12
    assert {
        kind: sum(s["kind"] == kind for s in samples)
        for kind in ("dsa", "design", "behavioural")
    } == {"dsa": 4, "design": 4, "behavioural": 4}
    report = calibrate(MockProvider(), directory)
    assert report["status"] == "no human labels yet: fill calibration/human_labels.csv"
    assert report["labeled_criteria"] == 0
    assert "mae" not in report


def fixtures(tmp_path, rows):
    (tmp_path / "samples").mkdir()
    sample = {
        "id": "s",
        "kind": "dsa",
        "prompt": "Add one",
        "transcript": [{"stage": "approach", "answer": "I add one."}],
        "execution": None,
        "provenance": "synthetic test fixture",
    }
    (tmp_path / "samples" / "s.json").write_text(json.dumps(sample))
    with (tmp_path / "human_labels.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "criterion", "score", "rater"])
        writer.writerows(rows)


def test_agreement_arithmetic_with_explicit_test_labels(tmp_path):
    # Synthetic unit-test numbers, NOT a human-validation claim.
    fixtures(
        tmp_path,
        [
            ["s", "approach", 1, "test-fixture"],
            ["s", "correctness", 2, "test-fixture"],
            ["s", "complexity", 3, "test-fixture"],
        ],
    )
    report = calibrate(MockProvider(), tmp_path)
    assert report["labeled_criteria"] == 3
    assert report["exact_agreement"] == pytest.approx(1 / 3)
    assert report["within_one"] == pytest.approx(2 / 3)
    assert report["mae"] == 1
    assert report["labeled_samples"] == 1


@pytest.mark.parametrize(
    "rows",
    [
        [["s", "approach", 6, "test"]],
        [["s", "approach", 2, ""]],
        [["unknown", "approach", 2, "test"]],
        [["s", "bogus", 2, "test"]],
        [["s", "approach", 2, "test"], ["s", "approach", 2, "test"]],
    ],
)
def test_invalid_labels_rejected(tmp_path, rows):
    fixtures(tmp_path, rows)
    with pytest.raises(ValueError):
        calibrate(MockProvider(), tmp_path)
