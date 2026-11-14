# SPX variance schedules

`generate.py` fits weekday, weekend and holiday variance rates to historical
SPX closes and writes one self-contained JSON schedule. A consumer can load the
file at runtime without Python, NumPy, SciPy, or QuantLib Python bindings.

The schedule is a **variance clock**, not an option-price or volatility forecast.
The fitted values are illustrative historical estimates until validated against
the intended market and pricing model.

## Setup

From the repository root, use Python 3.12 or newer. The `qlnb` package is built
from this checkout and requires a C++ toolchain and Boost; see
[`python-nanobind/README.md`](../../python-nanobind/README.md) for its build
prerequisites.

```bash
python3 -m venv .venv-variance
. .venv-variance/bin/activate
python -m pip install ./python-nanobind -r tools/variance_schedule/requirements.txt
```

If `qlnb` is already installed in your active environment, install only the
requirements file. The generator uses the `qlnb` NYSE calendar; it does not
require a Python binding for `VarianceCalendar`.

## Historical prices

Prepare a CSV with these exact column names:

```csv
timestamp,close
2024-01-05T16:00:00-05:00,100.0
2024-01-08T16:00:00-05:00,101.0
```

These prices demonstrate the format, not real SPX prices. Supply several years
of actual, consistently sourced SPX **price-index** closes, including the
correct close timestamp and UTC offset for each session. Use the actual close
time on early-close days. Do not forward-fill weekends or holidays. The program
requires positive finite prices, an offset on every timestamp, and at most one
close per NYSE business date. Rows may be unordered.

Returns spanning a missing NYSE business-day observation are excluded. The
calibration requires enough distinct weekday, weekend and holiday exposures to
identify all three rates. The JSON records sample counts, skipped intervals,
and the first and last observation, so inspect these before use. Update and
validate the underlying NYSE holiday calendar for the dates in your data.

## Generate

```bash
python tools/variance_schedule/generate.py \
  --prices /path/to/spx_closes.csv \
  --start 2027-01-04T09:30:00-05:00 \
  --end 2027-03-19T16:00:00-04:00 \
  --output schedules/spx-2027-03-19.json
```

`--start` is inclusive and `--end` is exclusive. Both accept an ISO timestamp
with a UTC offset, or `YYYY-MM-DD` for midnight in `America/New_York`. Use the
actual option valuation and expiry instants: an expiry at 16:00 is **not** the
same as midnight at the end of its date. The first and last rows can therefore
be partial days. The offset in a timestamp must reflect the applicable daylight
saving time.

The output directory is created if necessary. An existing output file is
replaced atomically; the input price file cannot be used as the output. A
running consumer must reopen or reload the file to see an updated schedule.

All input rows are used for calibration. For backtesting, provide only closes
available by the schedule start; otherwise the generator warns about look-ahead.
A zero-total-weight interval cannot be normalized and is rejected.

## File format

The JSON document has `format_version: 1`, `calendar`, `timezone`,
`range_start_utc`, `range_end_utc`, `calibration`, `total_weighted_days`, and a
`schedule` array. `calibration.weights` contains `weekday`, `weekend`, and
`holiday` rates relative to weekday = 1. `calibration.variance_per_24h` contains
the unnormalized fitted rates.

Each schedule row has:

| Field | Meaning |
| --- | --- |
| `local_date` | New York date determining its NYSE day category. |
| `start_utc`, `end_utc` | Inclusive start and exclusive end of the row, in UTC. |
| `category`, `weight` | Day category and dimensionless variance-rate multiplier. |
| `weighted_days` | Weight multiplied by actual elapsed seconds / 86,400. |
| `remaining_weighted_days` | Weighted time from this row's start to the schedule end, including this row. |
| `remaining_fraction` | Remaining weighted time divided by `total_weighted_days`, at this row's start. |

Rows cover the requested interval without gaps. Daylight-saving transition days
can contain 23 or 25 elapsed hours. The last row's `remaining_fraction` is its
fraction at the **start** of that row; the fraction is zero at `range_end_utc`.

## Read and use at runtime

This Python example needs only the standard library. It calculates the
fraction at an arbitrary instant, including within a partial day:

```python
import json
from datetime import datetime, timezone


def remaining_fraction_at(schedule, timestamp):
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must have a UTC offset")
    timestamp = timestamp.astimezone(timezone.utc)

    def parse(value):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    start = parse(schedule["range_start_utc"])
    end = parse(schedule["range_end_utc"])
    if not start <= timestamp <= end:
        raise ValueError("timestamp is outside the schedule")
    if timestamp == end:
        return 0.0

    for row in schedule["schedule"]:
        row_start, row_end = parse(row["start_utc"]), parse(row["end_utc"])
        if row_start <= timestamp < row_end:
            after_row = row["remaining_weighted_days"] - row["weighted_days"]
            within_row = row["weight"] * (row_end - timestamp).total_seconds() / 86400
            return (after_row + within_row) / schedule["total_weighted_days"]
    raise ValueError("schedule has a gap")


with open("schedules/spx-2027-03-19.json", encoding="utf-8") as stream:
    schedule = json.load(stream)

at = datetime.fromisoformat("2027-01-04T15:00:00+00:00")
fraction = remaining_fraction_at(schedule, at)
print(fraction)
```

For a fixed initial implied total variance `V0`, `V0 * fraction` allocates that
variance according to this clock. Reprice the option using the resulting
remaining variance and your assumptions for spot, rates, dividends, and the
volatility surface; the fraction is **not** a dollar-theta schedule.

C++ consumers can read the same file with Boost.PropertyTree, already a QuantLib
dependency. This complete example prints the stored rows:

```cpp
#include <boost/property_tree/json_parser.hpp>
#include <boost/property_tree/ptree.hpp>
#include <iostream>

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "usage: read_schedule schedule.json\n";
        return 1;
    }
    boost::property_tree::ptree data;
    boost::property_tree::read_json(argv[1], data);
    for (const auto& item : data.get_child("schedule")) {
        const auto& row = item.second;
        std::cout << row.get<std::string>("local_date") << ' '
                  << row.get<std::string>("start_utc") << ' '
                  << row.get<std::string>("end_utc") << ' '
                  << row.get<double>("weight") << ' '
                  << row.get<double>("remaining_fraction") << '\n';
    }
}
```

The persisted rows are the authoritative schedule. Alternatively, the three
stored weights can construct a C++ `VarianceCalendar` with a flat profile and
`UnitedStates(UnitedStates::NYSE)`; its classification then depends on the
calendar rules in the QuantLib build used at runtime.

## Model limitations

The fit regresses squared close-to-close log returns on elapsed weekday,
weekend and holiday time, with nonnegative rates and one drift per elapsed day.
It assumes additive category variances and a constant rate within each category.
A zero rate can be a constrained-fit boundary rather than evidence of zero
risk. Holiday estimates in particular can be unstable; assess them across
historical periods and with uncertainty estimates.

Daily closes do not identify five-minute, overnight-versus-session, early-close,
or within-weekend variance profiles. Obtain appropriately timestamped
intraday data or suitable futures/option proxies and recalibrate before adding
such profiles. Historical variance is under the physical measure; option
pricing uses risk-neutral expectations, so validate the calendar against
option-implied prices. NYSE cash-equity hours and holidays are not a complete
Cboe SPX-options trading schedule.
