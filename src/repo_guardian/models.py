from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Finding:
    id: str
    severity: Severity
    category: str
    title: str
    evidence: list[str]
    impact: str
    confidence: Confidence
    recommendation: str
    suggested_fix: str | None = None
    source: str = "static"
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["severity"] = self.severity.value
        value["confidence"] = self.confidence.value
        return value


@dataclass
class Score:
    category: str
    value: int
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditResult:
    root: str
    stacks: list[str]
    scores: list[Score]
    findings: list[Finding]
    commands: list[dict[str, Any]] = field(default_factory=list)

    @property
    def overall(self) -> int:
        return round(sum(score.value for score in self.scores) / len(self.scores)) if self.scores else 0

    def to_dict(self) -> dict[str, Any]:
        return {"root": self.root, "stacks": self.stacks, "overall": self.overall,
                "scores": [s.to_dict() for s in self.scores],
                "findings": [f.to_dict() for f in self.findings], "commands": self.commands}

