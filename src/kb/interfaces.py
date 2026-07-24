"""Track A owns this file's implementation. Frozen signature as of day 2."""
from dataclasses import dataclass
from typing import Any, List, Protocol


@dataclass
class Row:
    data: dict[str, Any]
    source_id: str


class KB(Protocol):
    def query(self, intent: str, slots: dict) -> List[Row]:
        """intent e.g. 'fertilizer_rate', slots e.g. {'crop': 'maize', 'state': 'Oyo'}.
        Returns matching rows from the six structured tables, each carrying
        its source_id for citation."""
        ...


class StubKB:
    def query(self, intent: str, slots: dict) -> List[Row]:
        return [Row(data={"note": "stub row", "intent": intent, "slots": slots}, source_id="stub-kb-001")]
