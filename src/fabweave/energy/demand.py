from __future__ import annotations

from collections import defaultdict

from fabweave.core.units import finite_non_negative


def partition_loads(loads: list[tuple[int, float]]) -> tuple[list[tuple[int, float]], tuple[int, ...]]:
    """Split readings into finite, non-negative loads and bad-reading timestamps.

    ``invalid_timestamps`` records, in first-seen order, the timestamp of every
    negative or non-finite reading so callers can fail closed without losing
    the evidence.  Valid readings sharing a timestamp with a bad reading are
    retained so window aggregation still runs over the trustworthy data.
    """
    valid: list[tuple[int, float]] = []
    invalid_timestamps: list[int] = []
    for timestamp, value in loads:
        try:
            finite_non_negative(value, "load")
        except (TypeError, ValueError):
            invalid_timestamps.append(timestamp)
        else:
            valid.append((timestamp, value))
    return valid, tuple(dict.fromkeys(invalid_timestamps))


def invalid_load_timestamps(loads: list[tuple[int, float]]) -> tuple[int, ...]:
    """Timestamps of readings that are negative or non-finite, in first-seen order."""
    return partition_loads(loads)[1]


def coincident_peak(loads: list[tuple[int, float]], window: int) -> float:
    if window <= 0:
        raise ValueError("window must be positive")
    grouped: dict[int, float] = defaultdict(float)
    for timestamp, value in loads:
        grouped[timestamp] += finite_non_negative(value, "load")
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
