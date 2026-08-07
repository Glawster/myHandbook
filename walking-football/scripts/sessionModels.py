"""Typed data models for walking football sessions."""

from dataclasses import dataclass, fields
from typing import Any


@dataclass(frozen=True)
class Session:
    """Validated content used to populate one session document."""

    sessionNumber: int
    sessionTitle: str
    theme: str
    keyPhrase: str
    duration: str
    players: str
    equipment: tuple[str, ...]
    objectives: tuple[str, ...]
    warmup: str = ""
    drill1: str = ""
    drill2: str = ""
    drill3: str = ""
    matchPractice: str = ""
    coolDown: str = ""
    coachingPoints: str = ""
    commonMistakes: str = ""
    analysis: str = ""
    sessionSummary: str = ""
    nextSession: str = ""

    ## placeholders

    def placeholdersBuild(self) -> dict[str, str]:
        """Return template placeholder names mapped to display text."""
        values: dict[str, str] = {}
        for modelField in fields(self):
            if modelField.name == "sessionNumber":
                continue
            value: Any = getattr(self, modelField.name)
            values[modelField.name] = "\n".join(value) if isinstance(value, tuple) else str(value)
        return values
