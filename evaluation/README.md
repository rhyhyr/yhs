# Live translation evaluation

This evaluates the real FastAPI `/api/chat` path with actual Neo4j, LLM and translation calls. Production files are never changed. The fixed twenty questions/reference strings are imported from `experiments/translation_eval_en.py`.

Question score: BERTScore F1 * 100. Smoothed char BLEU is auxiliary.
Answer score: 0.4 * reference-free bilingual LLM semantic assessment + 0.6 * preserved source-critical-fact ratio. The preferred COMETKiwi model could not be accessed (401); the LLM score is explicitly an alternative estimate, not a COMET score.

Run from the repository root, after backend dependencies and `evaluation/requirements.txt` are installed:

```powershell
python evaluation/preflight_qe.py
python evaluation/run_translation_e2e.py --phase collect --neo4j-uri bolt://YOUR_SERVER:7687
python evaluation/run_translation_e2e.py --phase questions
python evaluation/run_translation_e2e.py --phase answers
python evaluation/build_translation_report.py
python evaluation/verify_translation_e2e.py
```

The `.env` is loaded into the process without editing it. A URI override affects only that process. All service retrieval/translation settings remain unchanged. Live service initialization may perform its usual idempotent schema setup and web retrieval may use the service's cache.

Results are stored in `evaluation/results/translation_e2e/` (ignored by Git). Keep `protocol.json` and raw judge responses with the report. `collect` resumes successful IDs without regenerating their answers. For a fresh experiment choose a new directory via `--output PATH` on all runner phases; reporting scripts currently use the default directory.

No-source direct English fallback answers are marked N/A, never assigned a fabricated Korean source. Uncertain facts count as not preserved; zero critical facts are N/A. Quotes are checked against exact source/translation substrings. The evaluator may still miss errors; expert review is needed for calibrated quality claims.
