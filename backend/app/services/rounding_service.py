"""
Rounding service — Implementation Plan §4.2, TRD v1.2 §6.6.

Applies server-side rounding to every time entry save operation.
The original raw seconds are NEVER stored — only the rounded value is persisted.
(PRD §5 Rounding, API Spec §2 RoundingResult)

Valid intervals: 1, 5, 6, 10, 15, 30 minutes (DB Schema §4.3 workspaces.rounding_interval_minutes)
"""
import math
from dataclasses import dataclass
from enum import Enum


class RoundingMode(str, Enum):
    NONE = "none"
    NEAREST = "nearest"
    UP = "up"
    DOWN = "down"


@dataclass
class RoundingRule:
    mode: RoundingMode
    interval_minutes: int | None  # Required when mode != NONE


@dataclass
class RoundingResult:
    """
    Always returned alongside any time entry save response (API Spec §2).
    Frontend uses this to display the mandatory rounding toast (PRD §7).
    """
    raw_seconds: int
    rounded_seconds: int
    rounding_mode: RoundingMode
    rounding_interval_minutes: int | None


def round_duration(raw_seconds: int, rule: RoundingRule) -> RoundingResult:
    """
    Apply rounding to a raw duration in seconds.

    Implementation Plan §4.2 — exact boundary behaviour:
    - NONE: return raw_seconds unchanged
    - NEAREST: round to nearest interval (Python round() uses banker's rounding,
      so we use the classic >= 0.5 rule explicitly via int(x + 0.5))
    - UP: ceiling to next interval boundary (already on boundary → unchanged)
    - DOWN: floor to previous interval boundary (already on boundary → unchanged)
    """
    if rule.mode == RoundingMode.NONE or not rule.interval_minutes:
        return RoundingResult(
            raw_seconds=raw_seconds,
            rounded_seconds=raw_seconds,
            rounding_mode=rule.mode,
            rounding_interval_minutes=None,
        )

    interval_s = rule.interval_minutes * 60

    if rule.mode == RoundingMode.NEAREST:
        # Use standard arithmetic rounding (0.5 rounds up) not banker's rounding
        rounded = math.floor(raw_seconds / interval_s + 0.5) * interval_s
    elif rule.mode == RoundingMode.UP:
        rounded = math.ceil(raw_seconds / interval_s) * interval_s
    else:  # DOWN
        rounded = (raw_seconds // interval_s) * interval_s

    return RoundingResult(
        raw_seconds=raw_seconds,
        rounded_seconds=int(rounded),
        rounding_mode=rule.mode,
        rounding_interval_minutes=rule.interval_minutes,
    )
