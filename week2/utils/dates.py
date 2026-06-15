"""Deterministic deadline arithmetic (PRD §5.1, §11 mitigation).

Contractual periods are computed in code, not by the LLM, so the generator only
narrates dates we already calculated. Georgia convention (PRD corpus): day one is
the day AFTER the binding date; deadlines landing on a weekend or US federal
holiday roll forward to the next business day.
"""
from __future__ import annotations

import datetime as dt

# Fixed-date US federal holidays sufficient for deadline rolling. Floating
# holidays can be added if a transaction window needs them.
_FIXED_HOLIDAYS = {(1, 1), (6, 19), (7, 4), (11, 11), (12, 25)}


def is_business_day(d: dt.date) -> bool:
    return d.weekday() < 5 and (d.month, d.day) not in _FIXED_HOLIDAYS


def next_business_day(d: dt.date) -> dt.date:
    while not is_business_day(d):
        d += dt.timedelta(days=1)
    return d


def deadline_from(binding_date: dt.date, period_days: int,
                  roll_to_business_day: bool = True) -> dt.date:
    """Deadline = binding_date + period_days (day one is the day after binding)."""
    target = binding_date + dt.timedelta(days=period_days)
    return next_business_day(target) if roll_to_business_day else target


def days_until(target: dt.date, today: dt.date | None = None) -> int:
    return (target - (today or dt.date.today())).days
