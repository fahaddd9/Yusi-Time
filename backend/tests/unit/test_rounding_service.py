"""
Rounding Service — Unit Tests
Implementation Plan §4.2 — every boundary condition must be covered.
These are pure-function tests; no DB or async fixtures needed.
"""
import pytest
from app.services.rounding_service import RoundingMode, RoundingResult, RoundingRule, round_duration


# ─── NONE mode ────────────────────────────────────────────────────────────────

def test_none_mode_returns_unchanged():
    result = round_duration(3780, RoundingRule(RoundingMode.NONE, None))
    assert result.rounded_seconds == 3780
    assert result.raw_seconds == 3780
    assert result.rounding_mode == RoundingMode.NONE
    assert result.rounding_interval_minutes is None


def test_none_mode_with_interval_ignores_interval():
    # interval_minutes is irrelevant when mode is NONE
    result = round_duration(1234, RoundingRule(RoundingMode.NONE, 15))
    assert result.rounded_seconds == 1234


def test_none_mode_zero_seconds():
    result = round_duration(0, RoundingRule(RoundingMode.NONE, None))
    assert result.rounded_seconds == 0


# ─── NEAREST mode ─────────────────────────────────────────────────────────────

def test_nearest_15min_just_below_half_rounds_down():
    # 1h 3m = 3780s. Half of 15min = 450s. 3780 - 3600 = 180s < 450 → rounds DOWN to 3600
    result = round_duration(3780, RoundingRule(RoundingMode.NEAREST, 15))
    assert result.rounded_seconds == 3600


def test_nearest_15min_above_half_rounds_up():
    # 1h 8m = 4080s. 4080 - 3600 = 480s > 450 → rounds UP to 4500
    result = round_duration(4080, RoundingRule(RoundingMode.NEAREST, 15))
    assert result.rounded_seconds == 4500


def test_nearest_15min_exactly_half_rounds_up():
    # 1h 7m 30s = 4050s. Exactly half of 15min from 3600 → rounds UP to 4500
    result = round_duration(4050, RoundingRule(RoundingMode.NEAREST, 15))
    assert result.rounded_seconds == 4500


def test_nearest_exactly_on_boundary_unchanged():
    # 1h exactly = 3600s, which is a 15-min boundary → stays 3600
    result = round_duration(3600, RoundingRule(RoundingMode.NEAREST, 15))
    assert result.rounded_seconds == 3600


def test_nearest_zero_seconds():
    result = round_duration(0, RoundingRule(RoundingMode.NEAREST, 15))
    assert result.rounded_seconds == 0


# ─── UP (ceiling) mode ────────────────────────────────────────────────────────

def test_up_exactly_on_interval_stays():
    # 1h = 3600s, exactly on a 15-min boundary → no change (Implementation Plan §4.2)
    result = round_duration(3600, RoundingRule(RoundingMode.UP, 15))
    assert result.rounded_seconds == 3600


def test_up_one_second_over_rounds_up_to_next():
    # 3601s → ceil to next 15-min mark = 4500 (Implementation Plan §4.2)
    result = round_duration(3601, RoundingRule(RoundingMode.UP, 15))
    assert result.rounded_seconds == 4500


def test_up_zero_seconds():
    result = round_duration(0, RoundingRule(RoundingMode.UP, 15))
    assert result.rounded_seconds == 0


def test_up_1min_interval():
    result = round_duration(61, RoundingRule(RoundingMode.UP, 1))
    assert result.rounded_seconds == 120  # ceil(61/60)*60


def test_up_30min_interval():
    result = round_duration(1801, RoundingRule(RoundingMode.UP, 30))
    assert result.rounded_seconds == 3600  # ceil(1801/1800)*1800


# ─── DOWN (floor) mode ────────────────────────────────────────────────────────

def test_down_just_below_boundary_rounds_to_previous():
    # 4499s → floor(4499/900)*900 = 4*900 = 3600 (Implementation Plan §4.2)
    result = round_duration(4499, RoundingRule(RoundingMode.DOWN, 15))
    assert result.rounded_seconds == 3600


def test_down_exactly_on_boundary_unchanged():
    result = round_duration(3600, RoundingRule(RoundingMode.DOWN, 15))
    assert result.rounded_seconds == 3600


def test_down_zero_seconds():
    result = round_duration(0, RoundingRule(RoundingMode.DOWN, 15))
    assert result.rounded_seconds == 0


def test_down_5min_interval():
    # 299s is less than one 5-min interval (300s) → floor rounds to 0
    result = round_duration(299, RoundingRule(RoundingMode.DOWN, 5))
    assert result.rounded_seconds == 0  # floor(299/300)*300 = 0*300 = 0


def test_down_5min_interval_above_one_interval():
    # 301s is just over one 5-min interval (300s) → floor rounds to 300
    result = round_duration(301, RoundingRule(RoundingMode.DOWN, 5))
    assert result.rounded_seconds == 300  # floor(301/300)*300 = 1*300 = 300


# ─── All valid intervals ───────────────────────────────────────────────────────

@pytest.mark.parametrize("interval", [1, 5, 6, 10, 15, 30])
def test_all_valid_intervals_produce_result(interval):
    """All six DB-valid rounding_interval_minutes values must work without error."""
    result = round_duration(3661, RoundingRule(RoundingMode.UP, interval))
    interval_s = interval * 60
    assert result.rounded_seconds % interval_s == 0


# ─── Result shape ─────────────────────────────────────────────────────────────

def test_result_contains_correct_raw_seconds():
    result = round_duration(3780, RoundingRule(RoundingMode.UP, 15))
    assert result.raw_seconds == 3780


def test_result_contains_interval_minutes():
    result = round_duration(3780, RoundingRule(RoundingMode.UP, 15))
    assert result.rounding_interval_minutes == 15


def test_result_interval_none_when_mode_is_none():
    result = round_duration(3780, RoundingRule(RoundingMode.NONE, None))
    assert result.rounding_interval_minutes is None


def test_result_is_RoundingResult_dataclass():
    result = round_duration(3600, RoundingRule(RoundingMode.NEAREST, 15))
    assert isinstance(result, RoundingResult)
