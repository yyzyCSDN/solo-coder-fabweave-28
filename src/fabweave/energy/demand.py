from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from fabweave.core.units import finite_non_negative


@dataclass(frozen=True, slots=True)
class LoadFault:
    """A single rejected demand reading; never silently dropped."""

    timestamp: int
    value: float
    reason: str


def inspect_loads(loads: list[tuple[int, float]]) -> tuple[LoadFault, ...]:
    """Return every negative or non-finite reading as rejection evidence."""
    faults: list[LoadFault] = []
    for timestamp, value in loads:
        if not math.isfinite(value):
            faults.append(LoadFault(timestamp, value, "non_finite"))
        elif value < 0:
            faults.append(LoadFault(timestamp, value, "negative"))
    return tuple(faults)


def coincident_peak(loads: list[tuple[int, float]], window: int) -> float:
    if window <= 0:
        raise ValueError("window must be positive")
    if inspect_loads(loads):
        raise ValueError("loads must be finite and non-negative")
    grouped: dict[int, float] = defaultdict(float)
    for timestamp, value in loads:
        grouped[timestamp] += value
    ordered = sorted(grouped.items())
    best = 0.0
    left = 0
    total = 0.0
    for timestamp, value in ordered:
        total += value
        while left < len(ordered) and timestamp - ordered[left][0] >= window:
            total -= ordered[left][1]
            left += 1
        best = max(best, total)
    return best


def demand_violations(loads: list[tuple[int, float]], windows: list[tuple[int, float]]) -> tuple[int, ...]:
    violations = []
    for width, limit in windows:
        if coincident_peak(loads, width) > finite_non_negative(limit, "demand limit"):
            violations.append(width)
    return tuple(sorted(violations))
