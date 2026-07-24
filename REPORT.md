# Àgbẹ̀ — Technical Report

## Problem

Nigeria's agricultural extension system is severely understaffed relative to FAO-recommended ratios.
Practical agronomic knowledge — planting windows, fertiliser rates, pest control — sits with a small
number of extension agents and in ageing printed bulletins. Farmers get this advice late, second-hand,
or not at all; a planting window missed by three weeks can cost a season.

Cloud AI doesn't solve this: rural connectivity is unreliable exactly where need is greatest, mobile
data is a real cost few will spend on one agronomy question, and general-purpose models don't know
Nigeria-specific facts (zone-specific planting windows, NAFDAC-registered agrochemicals) — they answer
anyway, fluently and wrongly. A confident wrong fertiliser rate is more dangerous than no answer.

**Target user:** the extension agent, agrodealer, or cooperative officer — the operator standing between
a laptop and a farmer in the field — not the farmer directly. See proposal Section 2.3 for the full
persona breakdown.

## Design Decisions

TODO once Phase 0/1 bake-off is complete. Cover:
- Which model won the bake-off (Qwen3-1.7B-Instruct vs Llama 3.2 1B vs Gemma 3 1B) and why
- Quantisation level chosen and where the quality/speed knee was found
- Why structured-first routing (SQL lookup for Tier A facts) instead of pure RAG
- Why prompt lookup decoding + domain phrase bank, and its measured acceptance rate

## Constraints

- **Hardware:** ADTC Standard Laptop — 4 vCPU, 8GB DDR4, integrated graphics only, Ubuntu 22.04.
  RAM_LIMIT_GB=7.0 is the effective budget used in the efficiency score.
- **Connectivity:** zero network calls permitted once profiling starts. `download_model.sh` runs
  before profiling; the model and all retrieval assets must be fully local afterward.
- **Runtime:** llama.cpp only, GGUF weights only — no other inference runtime is accepted.
- **Data:** offline knowledge base built from NAERLS/ABU Zaria bulletins, IITA publications, NCRI/NIHORT/CRIN,
  state ADP crop calendars, FAO guides, CGIAR/CIMMYT catalogues, NAFDAC agrochemical listings.
  Licence/redistribution terms tracked per-source (see `data/processed/provenance.*`).

## Benchmarks

TODO — fill in after running `adtc-profiler run --mode participant` on the dev machine.

| Metric | Value | Notes |
|---|---|---|
| tokens_per_second_generation | TODO | scored via min(TPS/15.0, 1.0)*100 — target comfortably >15 for full S_perf, with margin for the ±25% audit variance tolerance |
| first_token_latency_ms | TODO | |
| peak_rss_mb | TODO | scored via max(0, (7.0 - peak_rss_gb)/7.0)*100 |
| steady_state_rss_mb | TODO | |
| thermal throttling observed? | TODO | flat -10 penalty if throttled or core temp >85°C — validate under a 10-min sustained load, not a short burst |

Predicted (analytical, from proposal Section 5.5): peak resident ~1.6–1.8 GB. To be verified against
measured `adtc-profiler` output and reconciled if the gap exceeds a few hundred MB.
