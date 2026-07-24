# Àgbẹ̀ — Offline Agricultural Advisor
ADTC 2026 · Agriculture track

Full design rationale lives in `report/Agbe_ADTC_Proposal.pdf` (the proposal). This repo is where the proposal becomes code.

## Repo map

```
agbe/
├── metadata.json          # REQUIRED by ADTC template — team/model/test_prompts, root level
├── download_model.sh      # REQUIRED — downloads the .gguf to model/, must be idempotent
├── REPORT.md              # REQUIRED — technical writeup judges + LLM audit read
├── model/                 # .gguf lands here (gitignored, populated by download_model.sh)
├── .gitignore
│
├── eval/                  # OUR OWN dev tooling — not part of the official template
│   ├── questions.jsonl    # ~150-question internal tuning set (all 3 teammates contribute)
│   └── harness.py         # fast local iteration loop — see "Two harnesses" below
├── src/
│   ├── retrieval/         # Track A — BM25 + embeddings + rank fusion
│   ├── kb/                # Track A — SQLite schema + loaders for the 6 tables
│   ├── engine/            # Track B — llama.cpp server wrapper, quantisation, lookup decoding
│   ├── router/            # Track C — intent classification, tier routing, SQL templates
│   └── tools/             # Track C — Tier C calculator, citation/grammar validation
├── data/
│   ├── raw/               # Source PDFs/bulletins (gitignored — check licences before committing)
│   └── processed/         # Chunked passages, provenance file
└── scripts/                # bake-off, quantisation sweep, roofline calc, thread sweep
```

## Repo structure vs. the official template

This repo root now matches the required submission layout exactly:
`metadata.json`, `download_model.sh`, `REPORT.md`, `model/` (gitignored `.gguf`), `.gitignore`.
Everything else (`eval/`, `src/`, `data/`, `scripts/`) is internal dev scaffolding — the template
doesn't require it and doesn't forbid it. `eval/harness.py` is our own iteration tool for tuning
*before* a run; `adtc-profiler` is the tool that actually produces the numbers that get scored.
Don't confuse the two — see "Two harnesses" below.

## The rubric ambiguities are resolved — read this before optimising anything

The proposal (Section 1.3) flagged two open questions and planned to email organisers. **Both are
answered by the actual profiler README, so that email is no longer needed:**

- **Peak RAM = process-level `peak_rss_mb`**, measured by the profiler itself, not system-wide.
- **Speed score uses a fixed reference, not max-observed**: `S_perf = min(TPS / 15.0, 1.0) * 100`.
  It is capped at 100. A team shipping a blazing-fast useless model does **not** compress anyone else's
  score — that risk in the proposal's Observation 2 doesn't exist.

Full formula:

```
S_total = 0.50·S_acc + 0.30·S_perf + 0.20·S_eff − P_thermal

S_perf = min(TPS / 15.0, 1.0) × 100
S_eff  = max(0, (7.0 − peak_rss_gb) / 7.0) × 100
P_thermal = −10 flat, if throttled or core temp > 85°C
```

**This changes the strategy in one important way.** Because `S_perf` is capped once TPS ≥ 15, chasing
speed past that point buys zero rubric points (it still matters for demo feel and audit-variance
margin — see below — but not for score). Re-running the proposal's own worked example with the real
formula:

| Move | Δ component score | Weight | Δ total score |
|---|---|---|---|
| Peak RSS 3.0GB → 1.5GB | ΔS_eff = 21.4 | ×0.20 | **+4.3 pts** |
| TPS 8 → 15 (reaching the cap) | ΔS_perf = 46.7 | ×0.30 | **+14.0 pts** |
| TPS 15 → 22 (past the cap) | ΔS_perf = 0 | ×0.30 | **+0.0 pts** |

The proposal's directional call — spend memory to buy speed — still holds (14.0 pts >> 4.3 pts). But
the target is now concrete: **get comfortably past 15 TPS, not "as fast as possible."** Aim for headroom
— maybe 18–20 TPS sustained — because the audit re-measures on different hardware and the comparator
tolerates only ±25% variance on throughput before flagging, and >50% before failing outright. Undershoot
on audit day and you lose points you thought you'd banked; overshoot costs you nothing extra.

## Two harnesses — don't conflate them

1. **`eval/harness.py`** (ours) — fast internal iteration loop for tuning quantisation, lookup decoding,
   thread count, etc. during Phases 1–4. Not what gets scored.
2. **`adtc-profiler`** (official, `pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"`)
   — the actual scoring tool. Requires `llama-bench` on PATH (part of llama.cpp). Run
   `adtc-profiler run --submission . --mode participant --output submission.json --skip-accuracy`
   as a smoke test before every submission. Also run `adtc-profiler compare` against a prior run to
   catch variance before the real audit does.

## Accuracy scoring is different from what the proposal assumed

The proposal planned a large hidden validation set. The actual mechanism: `metadata.json` requires
**exactly 2** `test_prompts` you write yourself, and organisers add 2 hidden prompts in-domain — all 4
score `S_acc`. Our internal 150-question eval set (Phase 0) is still the right move for *tuning*, but
the 2 submitted prompts should be chosen deliberately: ones that showcase the structured-lookup
+ citation behaviour (a Tier A fact + a Tier B diagnosis are good picks) since judges and the hidden
prompts will likely probe similar territory. Current placeholders in `metadata.json` do exactly this —
replace only if you find stronger examples.

## Day 1 checklist (do these first, in order)

- [ ] Register team on DevPost, get your real `team_id`, fill it into `metadata.json`
- [ ] `pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"`,
      confirm `llama-bench` is on PATH (build llama.cpp from source per the proposal's Track B plan —
      that gives you the binary and the profiler both need)
- [ ] Pull the provided Agriculture validation/domain prompts if published — write our own eval
      questions to cover gaps, not duplicate them
- [ ] Apply for Udutech GPU credits (5 hrs) — reserve for a possible QLoRA fine-tune pass in week 3
- [ ] Fill in every placeholder in `metadata.json` (team_id, submitter info, model block once bake-off picks a winner)
- [ ] All 3 teammates: write 50 eval questions each into `eval/questions.jsonl` (schema below), covering
      Tier A/B/C/D per the proposal's taxonomy — this is for tuning, separate from the 2 official `test_prompts`

## Frozen interfaces (do not change after day 2)

```python
Retriever.search(query, k) -> List[Passage(text, source_id, doc, page, score)]
KB.query(intent, slots)    -> List[Row(..., source_id)]
Engine.generate(prompt, grammar) -> dict(text, tokens, timings)
```

See `src/retrieval/interfaces.py`, `src/kb/interfaces.py`, `src/engine/interfaces.py` — stub implementations
are in place so all three tracks can build against these from day one without waiting on each other.
