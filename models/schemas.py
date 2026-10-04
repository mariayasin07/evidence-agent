from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Source:
    id: int = 0
    title: str = ""
    url: str = ""
    snippet: str = ""
    collection: str = ""
    query: str = ""
    year: Optional[int] = None
    authors: str = ""
    venue: str = ""
    doi: str = ""
    cited_by: int = 0
    kind: str = ""
    score: int = 0
    tier: str = ""

    def link(self) -> str:
        return self.url or (f"https://doi.org/{self.doi}" if self.doi else "")

    def to_dict(self):
        return asdict(self)


@dataclass
class Finding:
    n: int = 0
    claim: str = ""
    evidence: str = ""
    source_id: int = 0
    corroborating: List[int] = field(default_factory=list)
    evidence_type: str = "descriptive"
    certainty: str = "medium"
    statistic: str = ""
    caveat: str = ""
    status: str = ""
    detail: str = ""
    confidence: str = ""
    rank: float = 0.0
