"""Track C owns the real implementation (embedding-similarity intent
classification per proposal Section 4.3, step 2). This stub is a crude
keyword classifier so the demo app has *something* to route on before
that's built. Replace RouterStub with the real thing without changing
the Router protocol below.
"""
from dataclasses import dataclass
from typing import Literal, Protocol

Tier = Literal["A", "B", "C", "D"]


@dataclass
class RouteResult:
    tier: Tier
    intent: str          # e.g. "fertilizer_rate", "pest_diagnosis", "calculation"
    slots: dict           # e.g. {"crop": "maize", "state": "Oyo"}
    confidence: float


class Router(Protocol):
    def classify(self, question: str) -> RouteResult: ...


_TIER_A_HINTS = ["when should i plant", "spacing", "how much npk", "rate of", "which variety",
                 "kg of seed", "fertiliser rate", "fertilizer rate"]
_TIER_C_HINTS = ["hectares", "how many bags", "cost", "schedule from planting"]
_TIER_D_HINTS = ["loan", "credit", "price of", "market price", "land tenure", "livestock", "vaccine"]


class RouterStub:
    """Naive substring matching — good enough to route the demo, not good
    enough to ship. Real version uses embedding similarity against a
    labelled example set (proposal Section 4.3)."""

    def classify(self, question: str) -> RouteResult:
        q = question.lower()

        if any(h in q for h in _TIER_D_HINTS):
            return RouteResult(tier="D", intent="out_of_scope", slots={}, confidence=0.6)

        if any(h in q for h in _TIER_C_HINTS):
            return RouteResult(tier="C", intent="calculation", slots=self._extract_slots(q), confidence=0.5)

        if any(h in q for h in _TIER_A_HINTS):
            return RouteResult(tier="A", intent="lookup", slots=self._extract_slots(q), confidence=0.5)

        return RouteResult(tier="B", intent="diagnosis_or_explanation", slots=self._extract_slots(q), confidence=0.4)

    @staticmethod
    def _extract_slots(q: str) -> dict:
        crops = ["maize", "cassava", "rice", "yam", "cowpea", "sorghum", "tomato", "pepper", "soybean", "cocoa"]
        states = ["oyo", "kano", "kaduna", "kwara", "ogun", "benue", "niger", "plateau"]
        slots = {}
        for c in crops:
            if c in q:
                slots["crop"] = c
                break
        for s in states:
            if s in q:
                slots["state"] = s.title()
                break
        return slots
