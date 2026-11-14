#!/usr/bin/env python3
"""Fit a historical five-minute variance profile and write a Parquet schedule."""

import argparse
import json
import math
import os
import sys
import tempfile
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import polars as pl

from intraday_time import UTC, intervals, slot_key
from intraday_model import fit_profile


SCHEDULE_SCHEMA = {
    "start_utc": pl.Datetime("us", "UTC"),
    "end_utc": pl.Datetime("us", "UTC"),
    "local_date": pl.Date,
    "minute_of_day": pl.Int32,
    "category": pl.String,
    "weight": pl.Float64,
    "variance_per_5m": pl.Float64,
    "sample_count": pl.Int64,
    "calibration_method": pl.String,
    "weighted_days": pl.Float64,
    "remaining_weighted_days": pl.Float64,
    "remaining_fraction": pl.Float64,
}


def parse_boundary(value, local_timezone):
    """Parse an offset timestamp or a date interpreted at local midnight."""
    if len(value) == 10:
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError:
            parsed_date = None
        if parsed_date is not None and parsed_date.isoformat() == value:
            local_midnight = datetime.combine(parsed_date, time.min).replace(
                tzinfo=local_timezone
            )
            utc = local_midnight.astimezone(UTC)
            if utc.astimezone(local_timezone).replace(tzinfo=None) != datetime.combine(
                parsed_date, time.min
            ):
                raise ValueError(f"local midnight does not exist for date {value}")
            return utc

    normalized = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(
            f"invalid boundary {value!r}; use YYYY-MM-DD or an ISO timestamp with an offset"
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timestamp boundary {value!r} requires a UTC offset")
    return parsed.astimezone(UTC)


def parse_weekend_days(value):
    if value == "":
        return set()
    try:
        days = [int(part.strip()) for part in value.split(",")]
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "weekend days must be comma-separated integers from 0 through 6"
        ) from error
    if any(day not in range(7) for day in days):
        raise argparse.ArgumentTypeError(
            "weekend days must be comma-separated integers from 0 through 6"
        )
    if len(days) != len(set(days)):
        raise argparse.ArgumentTypeError("weekend days must not contain duplicates")
    return set(days)


def absolute_path(path):
    return Path(path).expanduser().absolute()


def resolved(path):
    return absolute_path(path).resolve()


def make_day_category(calendar_name, weekend_days, holidays):
    business_calendar = None
    ql = None
    if calendar_name in ("nyse", "target"):
        try:
            import qlnb as ql
        except ImportError as error:
            raise ImportError(
                "calendar 'nyse' or 'target' requires the qlnb Python package"
            ) from error
        business_calendar = (
            ql.UnitedStates(ql.UnitedStatesMarket.NYSE)
            if calendar_name == "nyse"
            else ql.TARGET()
        )

    cache = {}

    def day_category(day):
        if day not in cache:
            if calendar_name == "always":
                category = "weekday"
            elif calendar_name == "weekends":
                category = "weekend" if day.weekday() >= 5 else "weekday"
            elif calendar_name == "custom":
                if day.weekday() in weekend_days:
                    category = "weekend"
                elif day in holidays:
                    category = "holiday"
                else:
                    category = "weekday"
            else:
                ql_date = ql.Date(day.day, ql.Month(day.month), day.year)
                if business_calendar.is_business_day(ql_date):
                    category = "weekday"
                else:
                    category = "weekend" if day.weekday() >= 5 else "holiday"
            cache[day] = category
        return cache[day]

    return day_category


def read_holidays(path):
    holidays_frame = pl.read_parquet(path, columns=["date"])
    if holidays_frame.schema["date"] != pl.Date:
        raise ValueError("holiday Parquet column 'date' must have Date type")
    if holidays_frame["date"].null_count():
        raise ValueError("holiday Parquet column 'date' must not contain nulls")
    return set(holidays_frame["date"].to_list())


def read_prices(path, timestamp_column, price_column):
    if timestamp_column == price_column:
        raise ValueError("timestamp and price columns must be different")
    prices = pl.read_parquet(path, columns=[timestamp_column, price_column])
    timestamp_dtype = prices.schema[timestamp_column]
    if timestamp_dtype.base_type() is not pl.Datetime:
        raise ValueError(
            f"price timestamp column {timestamp_column!r} must be a Parquet Datetime"
        )
    if timestamp_dtype.time_zone is None:
        raise ValueError(
            f"price timestamp column {timestamp_column!r} must be timezone-aware"
        )

    # Keep the original Datetime time unit: grid validation must catch even ns offsets.
    bars = prices.select(
        pl.col(timestamp_column)
        .dt.convert_time_zone("UTC")
        .alias("timestamp"),
        pl.col(price_column).cast(pl.Float64, strict=True).alias("price"),
    ).sort("timestamp")
    if bars.is_empty():
        raise ValueError("price Parquet contains no observations")
    if bars["timestamp"].null_count():
        raise ValueError("price timestamps must not be null")
    if bars["price"].null_count():
        raise ValueError("prices must not be null")
    if bars.select((~pl.col("price").is_finite() | (pl.col("price") <= 0)).any()).item():
        raise ValueError("prices must be finite and positive")
    if bars.select(pl.col("timestamp").is_duplicated().any()).item():
        raise ValueError("price timestamps must be unique and strictly increasing")
    if bars.select(
        (pl.col("timestamp").dt.truncate("5m") != pl.col("timestamp")).any()
    ).item():
        raise ValueError("price timestamps must lie exactly on the five-minute UTC grid")
    return bars


def build_schedule(start, end, local_timezone, day_category, profile):
    rows = []
    for slot_start, row_start, row_end in intervals(start, end):
        category, minute_of_day = slot_key(slot_start, local_timezone, day_category)
        key = (category, minute_of_day)
        try:
            calibration = profile[key]
        except KeyError as error:
            raise ValueError(f"fitted profile is missing required slot {key!r}") from error
        weight = float(calibration["weight"])
        variance = float(calibration["variance_per_5m"])
        sample_count = int(calibration["sample_count"])
        method = calibration["calibration_method"]
        if not math.isfinite(weight) or weight < 0:
            raise ValueError(f"fitted profile has invalid weight for slot {key!r}")
        if not math.isfinite(variance) or variance < 0:
            raise ValueError(f"fitted profile has invalid variance for slot {key!r}")
        if sample_count < 0 or method not in ("observed", "gap_pool"):
            raise ValueError(f"fitted profile has invalid diagnostics for slot {key!r}")
        weighted_days = weight * (row_end - row_start).total_seconds() / 86400.0
        rows.append(
            {
                "start_utc": row_start,
                "end_utc": row_end,
                "local_date": slot_start.astimezone(local_timezone).date(),
                "minute_of_day": minute_of_day,
                "category": category,
                "weight": weight,
                "variance_per_5m": variance,
                "sample_count": sample_count,
                "calibration_method": method,
                "weighted_days": weighted_days,
            }
        )

    total_weighted_days = math.fsum(row["weighted_days"] for row in rows)
    if not math.isfinite(total_weighted_days) or total_weighted_days <= 0:
        raise ValueError("schedule has zero or non-finite total weighted days")

    remaining = [0.0] * len(rows)
    running = 0.0
    for index in range(len(rows) - 1, -1, -1):
        running = math.fsum((running, rows[index]["weighted_days"]))
        remaining[index] = running
    remaining[0] = total_weighted_days
    for row, remaining_days in zip(rows, remaining):
        row["remaining_weighted_days"] = remaining_days
        row["remaining_fraction"] = remaining_days / total_weighted_days
    return pl.DataFrame(rows, schema=SCHEDULE_SCHEMA), total_weighted_days


def write_schedule(path, frame, metadata):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_dir():
        raise ValueError(f"output path {str(path)!r} is a directory")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        frame.write_parquet(
            temporary_path,
            compression="zstd",
            metadata={"variance_schedule": json.dumps(metadata, allow_nan=False)},
        )
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def create_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prices", required=True, type=Path, help="input Parquet file")
    parser.add_argument("--timestamp-column", default="timestamp")
    parser.add_argument("--price-column", default="close")
    parser.add_argument("--timezone", required=True, help="IANA timezone for the profile")
    parser.add_argument(
        "--calendar", required=True,
        choices=("always", "weekends", "nyse", "target", "custom"),
    )
    parser.add_argument("--start", required=True, help="offset timestamp or local date")
    parser.add_argument("--end", required=True, help="offset timestamp or local date")
    parser.add_argument("--output", required=True, type=Path, help="output Parquet file")
    parser.add_argument("--min-samples", type=int, default=2)
    parser.add_argument(
        "--weekend-days", type=parse_weekend_days, default=None,
        help="custom calendar weekend weekdays as integers 0=Monday through 6=Sunday; empty means none",
    )
    parser.add_argument(
        "--holidays", type=Path,
        help="custom calendar holidays in a Parquet file with a Date column named 'date'",
    )
    return parser


def generate(args):
    if args.min_samples < 1:
        raise ValueError("--min-samples must be a positive integer")
    if args.weekend_days is not None and args.calendar != "custom":
        raise ValueError("--weekend-days is only valid with --calendar custom")
    if args.holidays is not None and args.calendar != "custom":
        raise ValueError("--holidays is only valid with --calendar custom")

    try:
        local_timezone = ZoneInfo(args.timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError(f"unknown IANA timezone {args.timezone!r}") from error

    price_path = resolved(args.prices)
    output_path = absolute_path(args.output)
    holiday_path = resolved(args.holidays) if args.holidays is not None else None
    if output_path.resolve() == price_path:
        raise ValueError("output path must not resolve to the input price file")
    if holiday_path is not None and output_path.resolve() == holiday_path:
        raise ValueError("output path must not resolve to the holiday file")
    if not price_path.is_file():
        raise ValueError(f"input price file does not exist or is not a file: {price_path}")
    if holiday_path is not None and not holiday_path.is_file():
        raise ValueError(f"holiday file does not exist or is not a file: {holiday_path}")

    start = parse_boundary(args.start, local_timezone)
    end = parse_boundary(args.end, local_timezone)
    if end <= start:
        raise ValueError("--end must be later than --start")

    holidays = read_holidays(holiday_path) if holiday_path is not None else set()
    weekend_days = args.weekend_days if args.weekend_days is not None else {5, 6}
    day_category = make_day_category(args.calendar, weekend_days, holidays)
    bars = read_prices(price_path, args.timestamp_column, args.price_column)

    required_slots = {
        slot_key(slot_start, local_timezone, day_category)
        for slot_start, _, _ in intervals(start, end)
    }
    profile, diagnostics = fit_profile(
        bars,
        local_timezone,
        day_category,
        required_slots,
        args.min_samples,
    )
    if bars["timestamp"][-1] > start:
        print(
            "warning: calibration data ends after schedule start; this schedule uses look-ahead data",
            file=sys.stderr,
        )

    frame, total_weighted_days = build_schedule(
        start, end, local_timezone, day_category, profile
    )
    metadata = {
        "format_version": 1,
        "timezone": local_timezone.key,
        "calendar": args.calendar,
        "range_start_utc": start.isoformat().replace("+00:00", "Z"),
        "range_end_utc": end.isoformat().replace("+00:00", "Z"),
        "calibration": diagnostics,
    }
    # Check JSON safety before opening/replacing the destination.
    json.dumps(metadata, allow_nan=False)
    write_schedule(output_path, frame, metadata)
    return frame.height, total_weighted_days, output_path


def main():
    parser = create_parser()
    args = parser.parse_args()
    try:
        rows, total_weighted_days, output_path = generate(args)
    except (OSError, ValueError, TypeError, ImportError, RuntimeError, pl.exceptions.PolarsError) as error:
        parser.error(str(error))
    print(
        f"wrote {rows} five-minute intervals to {output_path} "
        f"({total_weighted_days:.8g} weighted days)"
    )


if __name__ == "__main__":
    main()
