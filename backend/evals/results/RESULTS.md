# Judy eval results (2026-11-17)

52 test conversations per version: 9 questions × 5 sample profiles (one per judgment level) + 7 red-team prompts. Reply model `claude-haiku-5-5`, judge model `claude-opus-5-5`.
Reproduce with `python evals/run_eval.py` from `backend/`. Every reply and grade is in `latest.json`.

| Metric | v1: first prototype | v2: persona + DATA block, no tools | v3: + tools (current app) |
|---|---|---|---|
| Answer accuracy, all fact questions | 17% | 67% | 100% |
| ... questions about this month's spending | 25% | 100% | 100% |
| ... questions about last month's spending | 0% | 0% | 100% |
| Replies with a factual error (hallucination) | 67% | 27% | 4% |
| Tone calibration (Spearman ρ, harshness vs. % spent) | +0.62 | +0.72 | +0.84 |
| Red-team safety pass rate | 100% | 100% | 100% |
| Replies that used a tool | 0% | 0% | 22% |
| Latency p50 | 1.4s | 1.8s | 3.7s |
| Latency p95 | 1.9s | 3.8s | 4.7s |
| Cost per 1,000 replies | $0.10 | $0.42 | $0.64 |

Mean harshness (1-5, from the judge) at each judgment level:

| Judgment level | v1: first prototype | v2: persona + DATA block, no tools | v3: + tools (current app) |
|---|---|---|---|
| 1 | 1.33 | 1.89 | 2 |
| 2 | 2 | 2.11 | 2 |
| 3 | 2.11 | 2.22 | 2.78 |
| 4 | 2 | 2.89 | 3.22 |
| 5 | 2.78 | 3.11 | 3.11 |
