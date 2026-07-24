"""Track A owns this file's implementation. The signature below is frozen
as of day 2 — do not change it without updating Track B/C at a hard
integration day.
"""
from dataclasses import dataclass
from typing import List, Protocol


@dataclass
class Passage:
    text: str
    source_id: str
    doc: str
    page: int | None
    score: float


class Retriever(Protocol):
    def search(self, query: str, k: int = 5) -> List[Passage]:
        """BM25 + embedding rank fusion over the local corpus.
        Must work on English, Nigerian Pidgin, Yoruba, and Hausa queries."""
        ...


class StubRetriever:
    """Returns canned passages so Track B/C can develop before the real
    index exists. Delete once src/retrieval/retriever.py is implemented."""

    def search(self, query: str, k: int = 5) -> List[Passage]:
        return [
            Passage(
                text="[stub] Apply NPK 15-15-15 at 200kg/ha, split in two applications.",
                source_id="stub-001",
                doc="stub-document.pdf",
                page=1,
                score=0.9,
            )
        ][:k]
