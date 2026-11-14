"""Fit normalized five-minute variance profiles from timestamped prices."""

from collections import Counter
from datetime import datetime
import math

import numpy as np
import polars as pl
from scipy.optimize import nnls

from intraday_time import FIVE_MINUTES, UTC, floor_slot, intervals, slot_key


def fit_profile(bars, local_timezone, day_category, required_slots, min_samples):
    """Fit observed slot rates and identify missing rates from multi-slot gaps.

    Prices are point observations at bar closes.  A return from ``t`` to
    ``t + n*5m`` is allocated across the UTC slots beginning at ``t``.
    """
    if not isinstance(bars, pl.DataFrame):
        raise TypeError("bars must be a Polars DataFrame")
    if bars.columns != ["timestamp", "price"]:
        raise ValueError("bars must contain exactly timestamp and price columns")
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 1:
        raise ValueError("min_samples must be a positive integer")
    if not hasattr(local_timezone, "utcoffset"):
        raise ValueError("local_timezone must be a timezone")
    if not callable(day_category):
        raise ValueError("day_category must be callable")
    try:
        required = set(required_slots)
    except TypeError as exc:
        raise ValueError("required_slots must be an iterable of slot keys") from exc
    for key in required:
        if (not isinstance(key, tuple) or len(key) != 2
                or key[0] not in ("weekday", "weekend", "holiday")
                or isinstance(key[1], bool) or not isinstance(key[1], int)
                or not 0 <= key[1] < 1440 or key[1] % 5):
            raise ValueError(f"invalid required slot key: {key!r}")
    timestamp_dtype = bars.schema["timestamp"]
    if timestamp_dtype.base_type() != pl.Datetime:
        raise ValueError("timestamp must be a timezone-aware Polars Datetime")
    if timestamp_dtype.time_zone is None:
        raise ValueError("timestamp values must be timezone-aware")
    if bars.schema["price"] != pl.Float64:
        raise ValueError("price must have Polars Float64 dtype")
    if bars.height < 2:
        raise ValueError("at least two price observations are required")
    if bars.null_count().row(0) != (0, 0):
        raise ValueError("timestamp and price values must not be null")

    ordered = bars.sort("timestamp")
    timestamp_column = ordered.get_column("timestamp")
    ticks_per_second = {"ns": 1_000_000_000, "us": 1_000_000, "ms": 1_000}
    ticks = ticks_per_second.get(timestamp_dtype.time_unit)
    if ticks is None:
        raise ValueError("unsupported timestamp precision")
    grid_ticks = 300 * ticks
    epoch_ticks = timestamp_column.cast(pl.Int64).to_list()
    if any(value % grid_ticks for value in epoch_ticks):
        raise ValueError("all timestamps must lie exactly on the five-minute UTC grid")

    raw_times = timestamp_column.to_list()
    prices = ordered.get_column("price").to_list()
    timestamps = []
    for value in raw_times:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp values must be timezone-aware")
        timestamp = value.astimezone(UTC)
        if floor_slot(timestamp) != timestamp:
            raise ValueError("all timestamps must lie exactly on the five-minute UTC grid")
        if timestamps and timestamp <= timestamps[-1]:
            raise ValueError("timestamps must be unique")
        timestamps.append(timestamp)
    if any(not math.isfinite(price) or price <= 0 for price in prices):
        raise ValueError("prices must be positive and finite")

    elapsed_units = []
    log_returns = []
    for previous, current, previous_price, current_price in zip(
            timestamps, timestamps[1:], prices, prices[1:]):
        seconds = (current - previous).total_seconds()
        units_float = seconds / FIVE_MINUTES.total_seconds()
        units = int(units_float)
        if units < 1 or units != units_float:
            raise ValueError("observation timestamps must be strictly increasing five-minute intervals")
        elapsed_units.append(units)
        log_returns.append(math.log(current_price) - math.log(previous_price))

    total_units = sum(elapsed_units)
    drift = math.fsum(log_returns) / total_units
    returns = []
    direct_rows = []
    residual_squares = []
    for start, end, units, log_return in zip(
            timestamps, timestamps[1:], elapsed_units, log_returns):
        residual = log_return - drift * units
        squared = residual * residual
        if not math.isfinite(squared):
            raise ValueError("non-finite log-return residual; price range is too large")
        residual_squares.append(squared)
        counts = Counter()
        for slot_start, _, _ in intervals(start, end):
            key = slot_key(slot_start, local_timezone, day_category)
            if key[0] not in ("weekday", "weekend", "holiday"):
                raise ValueError(f"day_category returned invalid category: {key[0]!r}")
            counts[key] += 1
        if sum(counts.values()) != units:
            raise ValueError("internal interval allocation did not preserve five-minute exposure")
        returns.append((squared, counts, units))
        if units == 1:
            key, = counts
            direct_rows.append({"category": key[0], "minute": key[1], "residual_sq": squared})

    # Polars performs the observed-rate estimation and sample-count aggregation.
    if direct_rows:
        direct_groups = (
            pl.DataFrame(direct_rows)
            .group_by(["category", "minute"])
            .agg(pl.col("residual_sq").mean().alias("mean_sq"),
                 pl.len().alias("sample_count"))
        )
        direct = {
            (row["category"], row["minute"]): (float(row["mean_sq"]), int(row["sample_count"]))
            for row in direct_groups.iter_rows(named=True)
        }
    else:
        direct = {}
    known = {key: value for key, (value, count) in direct.items() if count >= min_samples}
    unknown_categories = {
        key[0] for _, counts, _ in returns for key in counts if key not in known
    }
    unknown_categories.update(key[0] for key in required if key not in known)
    categories = sorted(unknown_categories)
    category_index = {category: index for index, category in enumerate(categories)}

    equations = []
    responses = []
    for squared, counts, _ in returns:
        row = np.zeros(len(categories), dtype=np.float64)
        known_contribution = 0.0
        has_unknown = False
        for key, count in counts.items():
            rate = known.get(key)
            if rate is None:
                has_unknown = True
                row[category_index[key[0]]] += count
            else:
                known_contribution += rate * count
        if has_unknown:
            equations.append(row)
            responses.append(squared - known_contribution)

    pooled = {}
    if categories:
        matrix = np.asarray(equations, dtype=np.float64).reshape((-1, len(categories)))
        response = np.asarray(responses, dtype=np.float64)
        if matrix.shape[0] == 0 or np.linalg.matrix_rank(matrix) < len(categories):
            raise ValueError(
                "insufficient history to identify pooled variance for categories "
                f"{', '.join(categories)}; collect observations spanning gaps that expose "
                "each unknown category"
            )
        estimates, _ = nnls(matrix, response)
        if not np.all(np.isfinite(estimates)):
            raise ValueError("non-finite pooled variance estimate")
        pooled = {category: float(estimates[index]) for category, index in category_index.items()}

    reference = math.fsum(residual_squares) / total_units
    if not math.isfinite(reference) or reference <= 0:
        raise ValueError("price history has zero or non-finite residual variance")

    profile = {}
    for key in required:
        direct_estimate = known.get(key)
        if direct_estimate is not None:
            variance, sample_count = direct_estimate, direct[key][1]
            method = "observed"
        else:
            variance = pooled[key[0]]
            sample_count = direct.get(key, (0.0, 0))[1]
            method = "gap_pool"
        weight = variance / reference
        if not math.isfinite(variance) or variance < 0 or not math.isfinite(weight) or weight < 0:
            raise ValueError(f"invalid fitted variance for slot {key!r}")
        profile[key] = {
            "variance_per_5m": float(variance),
            "sample_count": int(sample_count),
            "calibration_method": method,
            "weight": float(weight),
        }

    diagnostics = {
        "reference_variance_per_5m": float(reference),
        "first_observation_utc": timestamps[0].isoformat(),
        "last_observation_utc": timestamps[-1].isoformat(),
        "returns_used": len(returns),
        "direct_returns": sum(units == 1 for units in elapsed_units),
        "gap_returns": sum(units > 1 for units in elapsed_units),
        "pooled_variance_per_5m": pooled,
        "log_drift_per_5m": float(drift),
    }
    return profile, diagnostics
