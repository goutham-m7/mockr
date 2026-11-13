# Human calibration protocol

The 12 samples are original synthetic answers, four per round, with intended weak-to-strong variation. They are NOT human-scored yet. DSA execution counts describe the original bank cases, not a human rating. Verify any edited source again before rating it.

Read each sample independently with the targets and common 1–5 anchors in `src/mockr_coach/judge.py`. Fill the `score` and `rater` cells in `human_labels.csv`. Use an actual human rater identifier; do not call generated scores human labels. Leave unrated cells empty. Do not inspect judge output first; label blind. Keep the question, transcript, and labels together when creating a custom directory.

Run `uv run mockr calibrate --provider openai` to compare with a real judge after configuring the provider. `--provider mock` exercises the harness only; its simple length heuristic is not an LLM evaluation. Output includes matched criterion count, exact agreement, within-one agreement and mean absolute error; partial labels are explicitly counted. The tiny single-author sample set cannot establish general validity. Use more raters and a held-out set for serious comparisons.

Arithmetic unit tests contain explicitly synthetic reference numbers. They are test fixtures, never evidence of human agreement.
