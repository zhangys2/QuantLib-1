# Five-minute variance schedules

`generate_intraday.py` fits a five-minute variance-rate profile from timestamped
prices and writes a schedule to a single Parquet file. It is not specific to an
instrument. Supply the market's time zone and a calendar that classifies its
days; classification never removes prices or assumes that weekends or holidays
have zero variance.

The existing [`generate.py`](generate.py) and [`README.md`](README.md) remain
available for one-close-per-day CSV input. The intraday generator has a separate
Parquet schema and does not alter the daily tool.

## Setup

Use Python 3.12 or newer. From the repository root:

```bash
python3 -m venv .venv-variance
. .venv-variance/bin/activate
python -m pip install -r tools/variance_schedule/intraday-requirements.txt
```

Only `--calendar nyse` and `--calendar target` require `qlnb` built from this
checkout; see the daily-tool README for its setup. The `always`, `weekends`,
and `custom` calendars do not require QuantLib Python bindings. Polars reads and
writes Parquet; no PyArrow installation is required.

## Input prices

The input is a Parquet file with two columns by default:

- `timestamp`: a timezone-aware Parquet `Datetime`, representing the instant of
  the price observation. Times must lie on the UTC five-minute grid.
- `close`: the positive finite price at that instant.

Use `--timestamp-column` and `--price-column` for different column names.
Rows may be unordered, but timestamps must be unique. Only the two selected
columns are read. A price at `10:00` means the price observed at `10:00`, not
the end of a bar whose start is `10:00`. Adjust start-stamped vendor bars to
their actual observation instants before calibration. Include actual timestamps
on early-close days and do not forward-fill missing prices.

For example, convert offset-aware CSV strings to a typed UTC Parquet column:

```python
import polars as pl

bars = pl.read_csv("bars.csv").with_columns(
    pl.col("timestamp").str.to_datetime(time_zone="UTC", strict=True)
)
bars.write_parquet("bars.parquet")
```

Inputs must already include correct UTC offsets or timezone information. A
naive timestamp cannot distinguish the repeated hour when daylight saving time
ends. The market timezone's offset must align to a five-minute grid for the
historical and schedule dates. Obtain several representative years of prices
and verify the session and holiday data for the market being modeled.

## Generate a schedule

```bash
python tools/variance_schedule/generate_intraday.py \
  --prices /path/to/bars.parquet \
  --timestamp-column timestamp --price-column close \
  --timezone America/New_York --calendar nyse \
  --start 2027-01-04T09:30:00-05:00 \
  --end 2027-03-19T16:00:00-04:00 \
  --output schedules/intraday.parquet
```

`--start` is inclusive and `--end` is exclusive. Each accepts an ISO timestamp
with a UTC offset, or a `YYYY-MM-DD` date interpreted as local midnight in the
specified timezone. The generator clips the first and last five-minute slots
to the exact boundaries. For an option, supply the actual expiry instant, not
the following midnight. The timestamp's offset must be correct for daylight
saving time.

`--calendar` is required:

- `always`: classify all dates as weekdays.
- `weekends`: classify Saturday and Sunday as weekends, with no holidays.
- `nyse` or `target`: use the corresponding QuantLib holiday calendar.
- `custom`: supply `--weekend-days` as comma-separated Python weekday numbers
  (`0` is Monday and `6` is Sunday; default `5,6`) and optionally supply
  `--holidays holidays.parquet`. An empty weekend-days string means no weekends.
  The holiday file must have a Polars `Date` column named `date`. On a date
  listed as both weekend and holiday, the weekend category takes precedence.

For example, create a custom holiday file with:

```python
from datetime import date
import polars as pl

pl.DataFrame({"date": [date(2027, 1, 1), date(2027, 12, 25)]}).write_parquet(
    "holidays.parquet"
)
```

The program replaces an existing output atomically and never overwrites its
price or custom-holiday inputs. It warns if price history extends past the
schedule start; for backtests, supply only data known at that start. A schedule
with zero total weighted time is rejected.

## Calibration and missing hours

Each return is the log price change between consecutive observations. A return
spanning exactly five minutes contributes its squared drift-adjusted return to
its local start-time and day-category bucket. Buckets with at least
`--min-samples` observations, default 2, use their observed average variance.

A longer gap contains only one aggregate return. For unobserved or undersampled
buckets, the generator pools an unknown variance rate by day category and fits
those rates using returns across gaps and other undersampled intervals. It
subtracts estimated contributions of buckets that are directly observed. The
fit is nonnegative and requires enough independent gap exposures to identify
the needed category rates; if it cannot, generation fails rather than inventing
one. Check the data, calendar, requested range, and sample threshold if that
happens. A fitted zero can be a constrained-fit boundary, not evidence of zero
risk.

This pooled rate is **not** a measured five-minute shape within the gap. For
example, cash-market bars alone cannot identify the distribution of a weekend
price change across individual overnight slots. Use suitable, consistently
timestamped futures or other proxy prices if you need finer observation of
those periods. Do not mix different instruments into one price series without a
properly constructed continuous proxy.

Each slot is constant over five minutes; no linear interpolation is applied.
`weight` is its fitted variance per five minutes divided by the historical
reference variance per five minutes. Actual elapsed seconds, rather than wall
clock subtraction, determine durations across daylight-saving changes.
Calendars classify whole dates only: they do not automatically alter a profile
on early-close days or for exceptional intraday events.

## Parquet format and runtime use

The output is one Parquet file, atomically replaced in its destination
directory. It contains a row per covered five-minute slot or clipped partial
slot:

| Column | Meaning |
| --- | --- |
| `start_utc`, `end_utc` | Timezone-aware UTC boundaries; start inclusive, end exclusive. |
| `local_date`, `minute_of_day`, `category` | Local five-minute slot and calendar category. |
| `weight`, `variance_per_5m` | Relative rate and unnormalized fitted variance per five minutes. |
| `sample_count`, `calibration_method` | Direct five-minute return count and `observed` or `gap_pool`. |
| `weighted_days` | Weight multiplied by actual elapsed seconds / 86,400. |
| `remaining_weighted_days` | Weighted time from this row's start to schedule end, including this row. |
| `remaining_fraction` | Remaining weighted time divided by the initial total, at this row's start. |

Parquet file metadata key `variance_schedule` contains JSON with format
version, calendar, timezone, interval boundaries, and calibration diagnostics.
Read the rows and metadata at runtime using Polars:

```python
import json
from datetime import datetime, timezone
import polars as pl

path = "schedules/intraday.parquet"
schedule = pl.read_parquet(path)
metadata = json.loads(pl.read_parquet_metadata(path)["variance_schedule"])


def remaining_fraction_at(timestamp):
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must have a UTC offset")
    timestamp = timestamp.astimezone(timezone.utc)
    start = datetime.fromisoformat(metadata["range_start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(metadata["range_end_utc"].replace("Z", "+00:00"))
    if not start <= timestamp <= end:
        raise ValueError("timestamp is outside the schedule")
    if timestamp == end:
        return 0.0
    match = schedule.filter(
        (pl.col("start_utc") <= timestamp) & (timestamp < pl.col("end_utc"))
    )
    if match.height != 1:
        raise ValueError("schedule has a gap or overlapping rows")
    row = match.row(0, named=True)
    after_row = row["remaining_weighted_days"] - row["weighted_days"]
    within_row = row["weight"] * (row["end_utc"] - timestamp).total_seconds() / 86400
    return (after_row + within_row) / schedule["remaining_weighted_days"][0]


at = datetime.fromisoformat("2027-01-04T15:00:00+00:00")
print(remaining_fraction_at(at))
```

A C++ consumer can use an Apache Arrow/Parquet reader. Alternatively, Polars can
export rows to CSV for a runtime without Parquet support:

```python
pl.read_parquet("schedules/intraday.parquet").write_csv("schedules/intraday.csv")
```

For fixed initial implied total variance `V0`, multiplying by the remaining
fraction allocates that variance across time. Reprice the option to obtain
price decay; the fraction itself is not dollar theta. Historical estimates are
physical-measure statistics, not necessarily risk-neutral option-implied
variance. Gap pooling, sparse holiday samples, regime changes, jumps, stale
prices, and proxy basis risk can all affect the fitted schedule; inspect sample
counts and diagnostics and validate against independent data and option prices.
