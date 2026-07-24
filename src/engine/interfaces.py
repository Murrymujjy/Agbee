"""Track B owns this file's implementation, backed by llama.cpp's local
HTTP server. Frozen signature as of day 2."""
from typing import Protocol, TypedDict


class GenerateResult(TypedDict):
    text: str
    tokens: int
    timings: dict  # {"prefill_s": float, "decode_s": float}


class Engine(Protocol):
    def generate(self, prompt: str, grammar: str | None = None) -> GenerateResult:
        """grammar is a GBNF string forcing parseable/cited output.
        Must call the shared llama.cpp server endpoint, not spawn a new process."""
        ...


class StubEngine:
    def generate(self, prompt: str, grammar: str | None = None) -> GenerateResult:
        return {
            "text": "[stub] Apply NPK 15-15-15 at 200kg/ha in two split applications. [source: stub-001]",
            "tokens": 20,
            "timings": {"prefill_s": 0.01, "decode_s": 0.05},
        }
