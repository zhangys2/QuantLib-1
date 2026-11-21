#!/usr/bin/env python3
"""Fit a historical five-minute variance profile and write a Parquet schedule."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import sys
import tempfile
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import polars as pl

from atomic_output import atomic_write
from intraday_time import UTC, intervals, slot_key
from intraday_model import fit_profile


SCHEDULE_SCHEMA = {
    "start_utc": pl.Datetime("us", "UTC"),
    "end_utc": pl.Datetime("us", "UTC"),
    "local_date": pl.Date,
    "minute_of_day": pl.Int32,
    "fold": pl.Int8,
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
            naive_midnight = datetime.combine(parsed_date, time.min)
            candidates = [
                naive_midnight.replace(tzinfo=local_timezone, fold=fold)
                for fold in (0, 1)
            ]
            valid = [
                candidate
                for candidate in candidates
                if candidate.astimezone(UTC).astimezone(local_timezone).replace(
                    tzinfo=None
                ) == naive_midnight
            ]
            if not valid:
                raise ValueError(f"local midnight does not exist for date {value}")
            if (
                len(valid) == 2
                and valid[0].utcoffset() != valid[1].utcoffset()
            ):
                raise ValueError(
                    f"local midnight is ambiguous for date {value}; "
                    "supply an explicit UTC offset"
                )
            return valid[0].astimezone(UTC)

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
        local_start = slot_start.astimezone(local_timezone)
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
                "local_date": local_start.date(),
                "minute_of_day": minute_of_day,
                "fold": local_start.fold,
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

    def writer(stream):
        frame.write_parquet(
            stream,
            compression="zstd",
            metadata={"variance_schedule": json.dumps(metadata, allow_nan=False)},
        )

    atomic_write(path, writer)


def parse_utc_instant(value, option):
    normalized = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"{option} must be an ISO-8601 UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{option} must be an ISO-8601 UTC timestamp")
    return parsed.astimezone(UTC)


def format_utc(value):
    return value.isoformat(timespec="microseconds" if value.microsecond else "seconds").replace(
        "+00:00", "Z"
    )


def csv_bytes(header, rows):
    from io import StringIO

    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def timezone_mapping_bytes(start, end, local_timezone):
    def state(instant):
        local = instant.astimezone(local_timezone)
        return int(local.utcoffset().total_seconds()), local.fold

    rows = []
    run_start = start
    current = state(start)
    cursor = start
    step = timedelta(minutes=5)
    while cursor < end:
        probe = min(cursor + step, end)
        if state(probe) != current:
            low = int(cursor.timestamp())
            high = int(probe.timestamp())
            while high - low > 1:
                middle = (low + high) // 2
                if state(datetime.fromtimestamp(middle, UTC)) == current:
                    low = middle
                else:
                    high = middle
            transition = datetime.fromtimestamp(high, UTC)
            rows.append((format_utc(run_start), format_utc(transition), *current))
            run_start = transition
            current = state(transition)
        cursor = probe
    if run_start < end:
        rows.append((format_utc(run_start), format_utc(end), *current))
    return csv_bytes(
        ("start_utc", "end_utc", "offset_seconds", "fold"), rows
    )


def bundle_day_bounds(start, end, local_timezone):
    first = start.astimezone(local_timezone).date()
    last = (end - timedelta(microseconds=1)).astimezone(local_timezone).date()
    day = first
    while day <= last:
        local_start = datetime.combine(day, time.min, tzinfo=local_timezone).astimezone(UTC)
        local_end = datetime.combine(
            day + timedelta(days=1), time.min, tzinfo=local_timezone
        ).astimezone(UTC)
        yield day, max(start, local_start), min(end, local_end)
        day += timedelta(days=1)


def atomic_write_bundle(bundle_path, files):
    if bundle_path.is_symlink():
        raise ValueError("bundle directory must not be a symlink")
    if bundle_path.exists() and not bundle_path.is_dir():
        raise ValueError("bundle path exists and is not a directory")
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{bundle_path.name}.stage-", dir=bundle_path.parent))
    backup = None
    try:
        for name, content in files.items():
            (stage / name).write_bytes(content)
        if bundle_path.exists():
            backup = bundle_path.with_name(
                f".{bundle_path.name}.backup-{os.getpid()}-{uuid.uuid4().hex}"
            )
            os.replace(bundle_path, backup)
        try:
            os.replace(stage, bundle_path)
        except OSError:
            if backup is not None:
                os.replace(backup, bundle_path)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
        if backup is not None and backup.exists():
            shutil.rmtree(backup)


def write_bundle(bundle_path, prices_path, start, end, cutoff, generated_at,
                 args, local_timezone, day_category, holidays, profile, diagnostics):
    category_ids = {"weekday": 1, "weekend": 2, "holiday": 3}
    covered_days = list(bundle_day_bounds(start, end, local_timezone))
    categories = sorted({
        day_category(day) for day, _, _ in covered_days
    }, key=lambda category: category_ids[category])
    profile_ids = {category: category_ids[category] for category in categories}
    market_days = []
    sessions = []
    for day, segment_start, segment_end in covered_days:
        category = day_category(day)
        date_type = {
            "weekday": "full_day", "weekend": "weekend", "holiday": "holiday"
        }[category]
        market_days.append((
            day.isoformat(), date_type, "true", profile_ids[category], "default",
            "date_type_session_pattern",
        ))
        sessions.append((
            day.isoformat(), format_utc(segment_start), format_utc(segment_end),
            f"{day.isoformat()}-all-day", "", "all-day-price-series", "",
            "calendar",
        ))

    profile_rows = []
    slot_rows = []
    warning_rows = []
    for category in categories:
        profile_id = profile_ids[category]
        for minute in range(0, 1440, 5):
            fitted = profile[(category, minute)]
            variance = fitted["variance_per_5m"]
            method = fitted["calibration_method"]
            if variance == 0:
                estimation_method = "zero"
                weight = 0.0
                warning_codes = ["ZERO_RATE_SLOT"]
                warning_rows.append({
                    "code": "ZERO_RATE_SLOT", "severity": "warning",
                    "profile_id": profile_id, "target_group_id": "default",
                    "minute_of_day": minute, "evidence_ids": ["price"],
                })
            elif method == "observed":
                estimation_method = "direct"
                weight = fitted["weight"]
                warning_codes = []
            else:
                estimation_method = "pooled"
                weight = fitted["weight"]
                warning_codes = []
                if fitted["distinct_local_date_count"] < 1:
                    raise ValueError(
                        f"cannot represent pooled slot without direct observations: "
                        f"{category} {minute}"
                    )
                if args.gap_pool_threshold is None:
                    raise ValueError(
                        "pooled bundle slots require --gap-pool-threshold"
                    )
                if fitted["gap_pool_return_count"] < args.gap_pool_threshold:
                    raise ValueError(
                        f"pooled slot {category} {minute} has fewer gap returns than "
                        "--gap-pool-threshold"
                    )
            profile_rows.append((profile_id, minute, repr(float(variance)), repr(float(weight))))
            if estimation_method == "pooled":
                source_group = f"{category}-same-slot"
                source_returns = fitted["sample_count"]
                source_dates = fitted["distinct_local_date_count"]
                grouping = f"{category}-gap-pool"
                gap_count = fitted["gap_pool_return_count"]
            else:
                source_group = grouping = ""
                source_returns = source_dates = gap_count = "not_applicable"
            slot_rows.append((
                profile_id, "default", minute, source_group, fitted["sample_count"],
                source_returns, fitted["distinct_local_date_count"], source_dates,
                estimation_method, grouping, gap_count, "",
                ",".join(warning_codes),
                json.dumps(["price"], separators=(",", ":")),
            ))

    profiles_data = csv_bytes(
        ("profile_id", "minute_of_day", "variance_per_5m", "weight"), profile_rows
    )
    market_days_data = csv_bytes(
        ("local_date", "date_type", "is_open", "profile_id", "target_group_id",
         "selection_reason"), market_days
    )
    sessions_data = csv_bytes(
        ("local_date", "start_utc", "end_utc", "session_id", "trading_date",
         "source_session_id", "claimed_local_offset_seconds", "source_evidence_id"),
        sessions,
    )
    timezone_data = timezone_mapping_bytes(start, end, local_timezone)
    slots_data = csv_bytes(
        ("profile_id", "target_group_id", "minute_of_day", "source_group_id",
         "target_return_count", "source_return_count", "target_distinct_local_date_count",
         "source_distinct_local_date_count", "estimation_method", "grouping_label",
         "gap_pool_return_count", "fallback_id", "warning_codes", "evidence_ids_json"),
        slot_rows,
    )
    file_data = {
        "profiles.csv": profiles_data,
        "market_days.csv": market_days_data,
        "session_segments.csv": sessions_data,
        "timezone_mapping.csv": timezone_data,
        "slot_evidence.csv": slots_data,
    }
    digests = {name: hashlib.sha256(content).hexdigest()
               for name, content in file_data.items()}
    price_digest = hashlib.sha256(prices_path.read_bytes()).hexdigest()
    calendar_digest = hashlib.sha256(
        f"{args.calendar}|{sorted(args.weekend_days or {5, 6})}|{sorted(holidays)}".encode()
    ).hexdigest()
    timezone_digest = digests["timezone_mapping.csv"]
    cutoff_text = format_utc(cutoff)
    as_of = cutoff_text
    calendar_version = f"{args.calendar}-v1"
    try:
        timezone_version = importlib.metadata.version("tzdata")
        timezone_database = "Python tzdata"
    except importlib.metadata.PackageNotFoundError:
        timezone_version = "system"
        timezone_database = "system zoneinfo"
    evidence = [
        {
            "evidence_id": "calendar", "role": "calendar_source",
            "source_id": f"builtin-calendar:{args.calendar}",
            "revision_id": calendar_version, "published_at_utc": None,
            "available_at_utc": as_of, "uri": f"builtin:calendar:{args.calendar}",
            "content_sha256": calendar_digest, "attestation_ref": "builtin-calendar-v1",
        },
        {
            "evidence_id": "price", "role": "price_input", "source_id": "price-parquet",
            "revision_id": price_digest, "published_at_utc": None,
            "available_at_utc": as_of, "uri": f"file:{prices_path.name}",
            "content_sha256": price_digest, "attestation_ref": "input-file-sha256",
        },
        {
            "evidence_id": "timezone", "role": "timezone_rules",
            "source_id": local_timezone.key, "revision_id": timezone_version,
            "published_at_utc": None, "available_at_utc": as_of,
            "uri": f"zoneinfo:{local_timezone.key}", "content_sha256": timezone_digest,
            "attestation_ref": "zoneinfo-release",
        },
    ]
    warnings = sorted(
        warning_rows,
        key=lambda item: (item["profile_id"], item["target_group_id"],
                          item["minute_of_day"], item["code"]),
    )
    manifest = {
        "format_version": 1,
        "snapshot_id": "variance-schedule-" + hashlib.sha256(json.dumps({
            "files": digests, "price": price_digest, "calendar": calendar_digest,
            "cutoff": cutoff_text, "start": format_utc(start), "end": format_utc(end),
            "minimum_direct_returns": args.min_samples,
            "gap_pool_return_threshold": args.gap_pool_threshold,
        }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24],
        "generated_at_utc": format_utc(generated_at),
        "coverage_start_utc": format_utc(start),
        "coverage_end_utc": format_utc(end),
        "clock_origin_utc": format_utc(start),
        "market_id": "intraday-price-series",
        "iana_zone": local_timezone.key,
        "reference_variance_per_5m": repr(diagnostics["reference_variance_per_5m"]),
        "reference_unit": "variance_per_5m",
        "price_cutoff_utc": cutoff_text,
        "calendar_version": calendar_version,
        "calendar_as_of_utc": as_of,
        "calendar_evidence_ids": ["calendar"],
        "timezone_database": timezone_database,
        "timezone_version": timezone_version,
        "timezone_as_of_utc": as_of,
        "timezone_evidence_ids": ["timezone"],
        "timezone_rules_sha256": timezone_digest,
        "calibration_settings": {
            "method": "historical_variance_over_common_reference",
            "minimum_direct_returns": args.min_samples,
            "gap_pool_return_threshold": args.gap_pool_threshold,
            "price_cutoff_utc": cutoff_text,
        },
        "profile_calibrations": [
            {"profile_id": profile_ids[category], "calibration_as_of_utc": as_of,
             "evidence_ids": ["price"]}
            for category in categories
        ],
        "evidence": evidence,
        "fallback_approvals": [],
        "warnings": warnings,
        "files": digests,
        "continuous_futures_lineage": None,
    }
    files = dict(file_data)
    files["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    atomic_write_bundle(bundle_path, files)


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
    parser.add_argument("--output", type=Path, help="output Parquet file")
    parser.add_argument("--bundle-dir", type=Path, help="output frozen Phase B bundle directory")
    parser.add_argument("--cutoff", help="exclude observations after this UTC timestamp")
    parser.add_argument("--generated-at", help="bundle manifest generation time (UTC)")
    parser.add_argument(
        "--gap-pool-threshold", type=int,
        help="required Phase B threshold when bundle slots use the gap-pool estimator",
    )
    parser.add_argument("--min-samples", type=int, default=30)
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
    if args.output is None and args.bundle_dir is None:
        raise ValueError("specify --output, --bundle-dir, or both")
    if args.generated_at is not None and args.bundle_dir is None:
        raise ValueError("--generated-at is only valid with --bundle-dir")
    if args.gap_pool_threshold is not None and args.gap_pool_threshold < 1:
        raise ValueError("--gap-pool-threshold must be a positive integer")

    try:
        local_timezone = ZoneInfo(args.timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError(f"unknown IANA timezone {args.timezone!r}") from error

    price_path = resolved(args.prices)
    output_path = absolute_path(args.output) if args.output is not None else None
    bundle_path = absolute_path(args.bundle_dir) if args.bundle_dir is not None else None
    holiday_path = resolved(args.holidays) if args.holidays is not None else None
    if output_path is not None and output_path.resolve() == price_path:
        raise ValueError("output path must not resolve to the input price file")
    if output_path is not None and holiday_path is not None and output_path.resolve() == holiday_path:
        raise ValueError("output path must not resolve to the holiday file")
    if bundle_path is not None and bundle_path.is_symlink():
        raise ValueError("bundle directory must not be a symlink")
    if bundle_path is not None:
        bundle_resolved = bundle_path.resolve()
        if price_path == bundle_resolved or price_path.is_relative_to(bundle_resolved):
            raise ValueError("bundle directory must not contain the input price file")
        if holiday_path is not None and holiday_path.is_relative_to(bundle_resolved):
            raise ValueError("bundle directory must not contain the holiday file")
        if output_path is not None and (
            output_path.resolve() == bundle_resolved
            or output_path.resolve().is_relative_to(bundle_resolved)
        ):
            raise ValueError("Parquet output must not be inside the bundle directory")
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
    cutoff = parse_utc_instant(args.cutoff, "--cutoff") if args.cutoff else (
        start if bundle_path is not None else None
    )
    excluded = 0
    if cutoff is not None:
        eligible_bars = bars.filter(pl.col("timestamp") <= cutoff)
        excluded = bars.height - eligible_bars.height
        if excluded:
            print(f"note: excluded {excluded} price observations after --cutoff "
                  f"{format_utc(cutoff)} before fitting", file=sys.stderr)
        bars = eligible_bars
        if bars.height < 2:
            raise ValueError("at least two price observations must be at or before --cutoff")

    required_slots = {
        slot_key(slot_start, local_timezone, day_category)
        for slot_start, _, _ in intervals(start, end)
    }
    if bundle_path is not None:
        bundle_categories = {
            day_category(day) for day, _, _ in bundle_day_bounds(start, end, local_timezone)
        }
        required_slots = {
            (category, minute)
            for category in bundle_categories
            for minute in range(0, 1440, 5)
        }
    profile, diagnostics = fit_profile(
        bars,
        local_timezone,
        day_category,
        required_slots,
        args.min_samples,
    )
    diagnostics["cutoff_excluded_observations"] = excluded
    if cutoff is not None:
        diagnostics["cutoff_utc"] = format_utc(cutoff)
    if bars["timestamp"][-1] > start:
        print(
            "warning: calibration data ends after schedule start; this schedule uses look-ahead data",
            file=sys.stderr,
        )
    for category, rate in diagnostics["pooled_variance_per_5m"].items():
        if rate == 0:
            print(
                f"warning: pooled variance rate is exactly zero for category {category!r}",
                file=sys.stderr,
            )

    frame, total_weighted_days = build_schedule(start, end, local_timezone, day_category, profile)
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
    generated_at = None
    if bundle_path is not None:
        if cutoff is None:
            raise ValueError("bundle price cutoff could not be determined")
        generated_at = (
            parse_utc_instant(args.generated_at, "--generated-at")
            if args.generated_at else datetime.now(UTC)
        )
        if cutoff > generated_at:
            raise ValueError("--cutoff must not be later than --generated-at")
        if generated_at >= end:
            print(
                "warning: generated_at_utc is at or after coverage_end_utc; "
                "bundle loads only in Reconstruction mode",
                file=sys.stderr,
            )
    if output_path is not None:
        write_schedule(output_path, frame, metadata)
    if bundle_path is not None:
        write_bundle(
            bundle_path, price_path, start, end, cutoff, generated_at, args,
            local_timezone, day_category, holidays, profile, diagnostics,
        )
    return frame.height, total_weighted_days, output_path or bundle_path


def main():
    parser = create_parser()
    args = parser.parse_args()
    try:
        rows, total_weighted_days, output_path = generate(args)
    except (OSError, ValueError, TypeError, ImportError, RuntimeError, pl.exceptions.PolarsError) as error:
        parser.error(str(error))
    if args.output is None:
        print(f"wrote Phase B bundle to {output_path}")
    else:
        print(
            f"wrote {rows} five-minute intervals to {output_path} "
            f"({total_weighted_days:.8g} weighted days)"
        )


if __name__ == "__main__":
    main()
