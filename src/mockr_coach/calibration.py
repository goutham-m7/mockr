"""Agreement against explicit human labels; empty labels never imply success."""

import csv
import json
from pathlib import Path

from .judge import RUBRICS, judge
from .providers import Provider


def default_directory() -> Path:
    return Path(__file__).with_name("calibration_data")


def calibrate(provider: Provider, directory: Path | None = None) -> dict:
    directory = directory or default_directory()
    samples = {}
    for path in sorted((directory / "samples").glob("*.json")):
        sample = json.loads(path.read_text())
        if sample["kind"] not in RUBRICS or sample["id"] in samples or not sample["transcript"]:
            raise ValueError("Invalid or duplicate calibration sample")
        samples[sample["id"]] = sample
    if not samples:
        raise ValueError("No calibration samples")
    labeled = []
    seen = set()
    with (directory / "human_labels.csv").open(newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != ["sample_id", "criterion", "score", "rater"]:
            raise ValueError("Labels need sample_id,criterion,score,rater columns")
        for row in reader:
            key = (row["sample_id"], row["criterion"])
            if key in seen or key[0] not in samples or key[1] not in {c["id"] for c in RUBRICS[samples[key[0]]["kind"]]}:
                raise ValueError("Unknown or duplicate calibration label")
            seen.add(key)
            if not row["score"].strip():
                continue
            try:
                score = int(row["score"])
            except ValueError as exc:
                raise ValueError("Human scores must be integers 1–5") from exc
            if not 1 <= score <= 5 or not row["rater"].strip():
                raise ValueError("Every human score needs 1–5 and a named rater")
            labeled.append((key,score))
    total = sum(len(RUBRICS[s["kind"]]) for s in samples.values())
    if not labeled:
        return dict(status="no human labels yet: fill calibration/human_labels.csv", labeled_criteria=0, total_criteria=total, samples=len(samples))
    predictions = {}
    for sample_id in sorted({key[0] for key,_ in labeled}):
        sample = samples[sample_id]
        card = judge(provider,sample["kind"],sample["prompt"],sample["transcript"],sample.get("execution"))
        predictions.update({(sample_id,c["id"]):c["score"] for c in card["criteria"]})
    errors = [abs(predictions[key]-score) for key,score in labeled]
    return dict(status="scored", labeled_criteria=len(errors), total_criteria=total, labeled_samples=len({key[0] for key,_ in labeled}), exact_agreement=sum(e==0 for e in errors)/len(errors), within_one=sum(e<=1 for e in errors)/len(errors), mae=sum(errors)/len(errors), comparisons=[dict(sample_id=key[0],criterion=key[1],reference=score,predicted=predictions[key]) for key,score in labeled])
