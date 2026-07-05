"""Heuristics for finding repeated binary structures."""

from __future__ import annotations

from collections import Counter

from fmparser.structures import RepeatedStructureCandidate


def repeated_structures(
    data: bytes,
    *,
    min_record_length: int = 4,
    max_record_length: int = 64,
    min_count: int = 3,
) -> tuple[RepeatedStructureCandidate, ...]:
    """Find repeated chunks that may indicate arrays or fixed-width records."""

    candidates: list[RepeatedStructureCandidate] = []
    for record_length in range(min_record_length, max_record_length + 1):
        for offset in range(0, min(record_length, len(data))):
            chunks = [
                data[index : index + record_length]
                for index in range(offset, len(data) - record_length + 1, record_length)
            ]
            counts = Counter(chunks)
            if not counts:
                continue
            _chunk, count = counts.most_common(1)[0]
            if count >= min_count:
                confidence = min(0.2 + (count / max(1, len(chunks))) * 0.8, 0.95)
                candidates.append(
                    RepeatedStructureCandidate(
                        offset=offset,
                        record_length=record_length,
                        count=count,
                        confidence=confidence,
                        reason="same fixed-width chunk appears repeatedly",
                    )
                )
    return tuple(sorted(candidates, key=lambda item: (-item.confidence, item.record_length))[:50])
