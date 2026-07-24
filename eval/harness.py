"""
Phase 0 measurement harness — "nothing gets built until we can measure it."

Design rules from the proposal (Section 6, Phase 0):
- 5 runs per test, discard the first (cold disk cache lies)
- report median and p95, not the average
- time prefill (reading prompt+context) and decode (generating answer) separately
- sample memory (RSS) every 100ms during the run
- read CPU temperature throughout, flag any run that shows thermal throttling

Usage:
    python harness.py --questions questions.jsonl --out results.json

This is a skeleton: engine_call() is a stub until Track B's Engine.generate()
is wired up. Everyone can develop against this file from day one.
"""
from __future__ import annotations

import argparse
import json
import statistics
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional

try:
    import psutil
except ImportError:
    psutil = None  # pip install psutil


# ---------------------------------------------------------------------------
# Memory + thermal sampling
# ---------------------------------------------------------------------------

@dataclass
class SampleTrace:
    rss_mb: list = field(default_factory=list)
    cpu_temp_c: list = field(default_factory=list)
    timestamps: list = field(default_factory=list)

    def peak_rss_mb(self) -> float:
        return max(self.rss_mb) if self.rss_mb else 0.0

    def max_temp_c(self) -> Optional[float]:
        vals = [t for t in self.cpu_temp_c if t is not None]
        return max(vals) if vals else None


def _read_cpu_temp_c() -> Optional[float]:
    """Best-effort CPU temp read on Linux. Returns None if unavailable
    (e.g. on the dev machine vs the actual target laptop)."""
    if psutil is None:
        return None
    try:
        temps = psutil.sensors_temperatures()
        for _, entries in temps.items():
            for e in entries:
                if e.current:
                    return float(e.current)
    except Exception:
        return None
    return None


class Sampler:
    """Background thread sampling RSS + CPU temp every `interval_ms` ms
    while the wrapped call runs."""

    def __init__(self, pid: Optional[int] = None, interval_ms: int = 100):
        self.pid = pid
        self.interval_s = interval_ms / 1000.0
        self.trace = SampleTrace()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._proc = psutil.Process(pid) if (psutil and pid) else (psutil.Process() if psutil else None)

    def _run(self):
        start = time.time()
        while not self._stop.is_set():
            if self._proc is not None:
                try:
                    rss = self._proc.memory_info().rss / (1024 * 1024)
                    self.trace.rss_mb.append(rss)
                except Exception:
                    pass
            self.trace.cpu_temp_c.append(_read_cpu_temp_c())
            self.trace.timestamps.append(time.time() - start)
            self._stop.wait(self.interval_s)

    def __enter__(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

@dataclass
class RunResult:
    prefill_s: float
    decode_s: float
    tokens_generated: int
    peak_rss_mb: float
    max_temp_c: Optional[float]

    @property
    def tokens_per_sec(self) -> float:
        return self.tokens_generated / self.decode_s if self.decode_s > 0 else 0.0


def timed_run(engine_call: Callable[[str], dict], prompt: str) -> RunResult:
    """engine_call must return dict with keys: text, tokens, timings
    where timings = {"prefill_s": float, "decode_s": float}.
    This is the shape of Engine.generate() — see src/engine/interfaces.py."""
    with Sampler() as sampler:
        result = engine_call(prompt)
    timings = result.get("timings", {})
    return RunResult(
        prefill_s=timings.get("prefill_s", 0.0),
        decode_s=timings.get("decode_s", 0.0),
        tokens_generated=result.get("tokens", 0),
        peak_rss_mb=sampler.trace.peak_rss_mb(),
        max_temp_c=sampler.trace.max_temp_c(),
    )


def median_p95(values: list[float]) -> tuple[float, float]:
    s = sorted(values)
    median = statistics.median(s)
    p95_idx = min(len(s) - 1, int(round(0.95 * (len(s) - 1))))
    return median, s[p95_idx]


# ---------------------------------------------------------------------------
# Question set + batch evaluation
# ---------------------------------------------------------------------------

def load_questions(path: Path) -> list[dict]:
    qs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                qs.append(json.loads(line))
    return qs


def evaluate(engine_call: Callable[[str], dict], questions: list[dict], runs_per_q: int = 5) -> dict:
    per_question = []
    for q in questions:
        run_results = []
        for i in range(runs_per_q):
            rr = timed_run(engine_call, q["question"])
            if i == 0:
                continue  # discard cold-cache first run
            run_results.append(rr)

        tps_vals = [r.tokens_per_sec for r in run_results]
        rss_vals = [r.peak_rss_mb for r in run_results]
        median_tps, p95_tps = median_p95(tps_vals)
        median_rss, p95_rss = median_p95(rss_vals)
        throttled = any((r.max_temp_c or 0) > 95 for r in run_results)  # placeholder threshold

        per_question.append({
            "id": q.get("id"),
            "tier": q.get("tier"),
            "median_tps": median_tps,
            "p95_tps": p95_tps,
            "median_peak_rss_mb": median_rss,
            "p95_peak_rss_mb": p95_rss,
            "possible_throttling": throttled,
        })

    return {"n_questions": len(questions), "results": per_question}


# ---------------------------------------------------------------------------
# Stub engine call — replace once Track B's Engine.generate() exists
# ---------------------------------------------------------------------------

def stub_engine_call(prompt: str) -> dict:
    """Placeholder so the harness is runnable end-to-end from day one.
    Replace with a call to src/engine/interfaces.py Engine.generate()."""
    time.sleep(0.05)
    return {"text": "stub answer", "tokens": 20, "timings": {"prefill_s": 0.01, "decode_s": 0.05}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", type=Path, default=Path(__file__).parent / "questions.jsonl")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results.json")
    ap.add_argument("--runs", type=int, default=5)
    args = ap.parse_args()

    questions = load_questions(args.questions)
    results = evaluate(stub_engine_call, questions, runs_per_q=args.runs)
    args.out.write_text(json.dumps(results, indent=2))
    print(f"Wrote {args.out} — {results['n_questions']} questions evaluated.")


if __name__ == "__main__":
    main()
