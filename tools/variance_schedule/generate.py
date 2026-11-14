#!/usr/bin/env python3
"""Calibrate an SPX variance calendar and write a runtime schedule."""

import argparse
import csv
import json
import math
import os
import sys
import tempfile
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import qlnb as ql
from scipy.optimize import nnls


ET = ZoneInfo("America/New_York")
UTC = timezone.utc
CATEGORIES = ("weekday", "weekend", "holiday")
NYSE = ql.UnitedStates(ql.UnitedStatesMarket.NYSE)


def is_business_day(d):
    return NYSE.is_business_day(ql.Date(d.day, ql.Month(d.month), d.year))


def category(d):
    if is_business_day(d):
        return "weekday"
    return "weekend" if d.weekday() >= 5 else "holiday"


def midnight_utc(d):
    return datetime.combine(d, time.min, ET).astimezone(UTC)


def parse_boundary(value):
    try:
        return midnight_utc(date.fromisoformat(value))
    except ValueError:
        try:
            result = datetime.fromisoformat(value)
            if result.tzinfo is None or result.utcoffset() is None:
                raise ValueError("timestamp requires a UTC offset")
            return result.astimezone(UTC)
        except ValueError as error:
            raise argparse.ArgumentTypeError(str(error)) from error


def utc_string(t):
    return t.astimezone(UTC).isoformat().replace("+00:00", "Z")


def day_intervals(start, end):
    cursor = start.astimezone(UTC)
    end = end.astimezone(UTC)
    while cursor < end:
        d = cursor.astimezone(ET).date()
        stop = min(end, midnight_utc(d + timedelta(days=1)))
        yield d, cursor, stop
        cursor = stop


def exposures(start, end):
    result = np.zeros(3)
    for d, cursor, stop in day_intervals(start, end):
        index = CATEGORIES.index(category(d))
        result[index] += (stop - cursor).total_seconds() / 86400.0
    return result


def read_prices(path):
    rows = []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or not {"timestamp", "close"} <= set(reader.fieldnames):
            raise ValueError("price CSV must have timestamp and close columns")
        for row in reader:
            timestamp = datetime.fromisoformat(row["timestamp"])
            price = float(row["close"])
            if (timestamp.tzinfo is None or timestamp.utcoffset() is None
                    or not math.isfinite(price) or price <= 0):
                raise ValueError("timestamps need UTC offsets and prices must be finite and positive")
            rows.append((timestamp.astimezone(UTC), price))

    rows.sort()
    previous_date = None
    for timestamp, _ in rows:
        local_date = timestamp.astimezone(ET).date()
        if local_date == previous_date or not is_business_day(local_date):
            raise ValueError("price CSV must have at most one close per NYSE business date")
        previous_date = local_date
    return rows


def missing_business_day(d0, d1):
    d = d0 + timedelta(days=1)
    while d < d1:
        if is_business_day(d):
            return True
        d += timedelta(days=1)
    return False


def calibrate(rows, source):
    X, returns = [], []
    skipped = 0
    for (t0, p0), (t1, p1) in zip(rows, rows[1:]):
        d0, d1 = t0.astimezone(ET).date(), t1.astimezone(ET).date()
        if missing_business_day(d0, d1):
            skipped += 1
            continue
        X.append(exposures(t0, t1))
        returns.append(math.log(p1) - math.log(p0))

    X, returns = np.asarray(X), np.asarray(returns)
    if len(returns) == 0 or np.linalg.matrix_rank(X) < 3:
        raise ValueError("need enough history with weekday, weekend, and holiday exposures")

    elapsed_days = X.sum(axis=1)
    drift_per_day = returns.sum() / elapsed_days.sum()
    squared_residuals = (returns - drift_per_day * elapsed_days) ** 2
    rates, _ = nnls(X, squared_residuals)
    if not np.isfinite(rates).all() or rates[0] <= 0:
        raise ValueError("weekday variance estimate must be finite and positive")
    weights = rates / rates[0]
    if not np.isfinite(weights).all():
        raise ValueError("calibrated weights must be finite")

    return {
        "source": str(source),
        "first_observation_utc": utc_string(rows[0][0]),
        "last_observation_utc": utc_string(rows[-1][0]),
        "returns_used": len(returns),
        "returns_skipped_missing_sessions": skipped,
        "returns_with_category_exposure": {
            name: int(np.count_nonzero(X[:, i])) for i, name in enumerate(CATEGORIES)
        },
        "drift_per_elapsed_day": float(drift_per_day),
        "variance_per_24h": {name: float(rates[i]) for i, name in enumerate(CATEGORIES)},
        "weights": {name: float(weights[i]) for i, name in enumerate(CATEGORIES)},
    }


def make_schedule(start, end, calibration):
    if end <= start:
        raise ValueError("end must be after start")

    rows = []
    for d, start_utc, end_utc in day_intervals(start, end):
        day_category = category(d)
        weight = calibration["weights"][day_category]
        weighted_days = weight * (end_utc - start_utc).total_seconds() / 86400.0
        rows.append({
            "local_date": d.isoformat(),
            "start_utc": utc_string(start_utc),
            "end_utc": utc_string(end_utc),
            "category": day_category,
            "weight": weight,
            "weighted_days": weighted_days,
        })

    remaining = 0.0
    for row in reversed(rows):
        remaining += row["weighted_days"]
        row["remaining_weighted_days"] = remaining
    if not math.isfinite(remaining) or remaining <= 0:
        raise ValueError("schedule must have positive finite total weighted time")
    for row in rows:
        row["remaining_fraction"] = row["remaining_weighted_days"] / remaining

    return {
        "format_version": 1,
        "calendar": "UnitedStates::NYSE",
        "timezone": "America/New_York",
        "range_start_utc": utc_string(start),
        "range_end_utc": utc_string(end),
        "calibration": calibration,
        "total_weighted_days": remaining,
        "schedule": rows,
    }


def write_schedule(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False) as stream:
            temp_path = Path(stream.name)
            json.dump(payload, stream, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prices", required=True, type=Path, help="CSV of timestamped closes")
    parser.add_argument("--start", required=True, type=parse_boundary,
                        help="start: YYYY-MM-DD (New York midnight) or timestamp with offset")
    parser.add_argument("--end", required=True, type=parse_boundary,
                        help="exclusive end: date (New York midnight) or timestamp with offset")
    parser.add_argument("--output", required=True, type=Path, help="output JSON file")
    args = parser.parse_args()

    try:
        if args.prices.resolve() == args.output.resolve():
            raise ValueError("output must not overwrite the input prices")
        rows = read_prices(args.prices)
        calibration = calibrate(rows, args.prices)
        payload = make_schedule(args.start, args.end, calibration)
        if rows[-1][0] > args.start:
            print("Warning: price history extends into the schedule; avoid look-ahead in backtests.",
                  file=sys.stderr)
        write_schedule(args.output, payload)
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")

    weights = calibration["weights"]
    print(f"Wrote {len(payload['schedule'])} days to {args.output}")
    print(f"Weights: weekday={weights['weekday']:.8g}, weekend={weights['weekend']:.8g}, "
          f"holiday={weights['holiday']:.8g}; returns used: {calibration['returns_used']}")


if __name__ == "__main__":
    main()
