"""Date-calculation helper correctness (§10.1, PRD §5.1)."""
import datetime as dt

from copilot.utils.dates import (
    days_until, deadline_from, is_business_day, next_business_day,
)


def test_due_diligence_deadline_from_sample_contract():
    # Binding June 1 2026 + 10 days = June 11 2026 (a Thursday, business day).
    binding = dt.date(2026, 6, 1)
    assert deadline_from(binding, 10) == dt.date(2026, 6, 11)


def test_deadline_rolls_off_weekend():
    # June 1 2026 + 5 days = June 6 (Saturday) -> rolls to Monday June 8.
    binding = dt.date(2026, 6, 1)
    assert deadline_from(binding, 5) == dt.date(2026, 6, 8)


def test_deadline_without_rolling():
    binding = dt.date(2026, 6, 1)
    assert deadline_from(binding, 5, roll_to_business_day=False) == dt.date(2026, 6, 6)


def test_holiday_is_not_a_business_day():
    assert not is_business_day(dt.date(2026, 7, 4))   # Independence Day (Saturday)
    assert next_business_day(dt.date(2026, 7, 4)) == dt.date(2026, 7, 6)


def test_days_until():
    assert days_until(dt.date(2026, 7, 15), today=dt.date(2026, 6, 13)) == 32
