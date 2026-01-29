from dataclasses import dataclass, field
from typing import List

@dataclass
class UpdateReport:
    """Collects events during the update process for final reporting."""
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    deletions: List[str] = field(default_factory=list)
    manual_checks: List[str] = field(default_factory=list)

    @property
    def has_events(self) -> bool:
        return any([self.added, self.updated, self.conflicts, self.deletions, self.manual_checks])
