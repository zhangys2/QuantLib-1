import csv
import json
import math
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


GENERATOR = Path(__file__).with_name("generate.py")
ET = ZoneInfo("America/New_York")
UTC = timezone.utc


def write_prices(path):
    holidays = {date(2024, 1, 15), date(2024, 2, 19)}
    counts = defaultdict(int)
    d = date(2024, 1, 2)
    last = None
    price = 100.0
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["timestamp", "close"])
        while d <= date(2024, 2, 27):
            if d.weekday() < 5 and d not in holidays:
                if last is not None:
                    gap = (d - last).days
                    variance = {1: 0.0001, 3: 0.00016, 4: 0.00021}[gap]
                    sign = 1 if counts[gap] % 2 == 0 else -1
                    price *= math.exp(sign * math.sqrt(variance))
                    counts[gap] += 1
                writer.writerow([datetime.combine(d, time(16), ET).isoformat(), price])
                last = d
            d += timedelta(days=1)


def test_generate_runtime_schedule(tmp_path):
    prices = tmp_path / "prices.csv"
    output = tmp_path / "schedules" / "spx.json"
    write_prices(prices)

    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--prices", str(prices),
         "--start", "2024-03-09", "--end", "2024-04-02", "--output", str(output)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    with output.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    assert payload["format_version"] == 1
    assert payload["calibration"]["returns_used"] == 38
    assert payload["calibration"]["weights"] == pytest.approx(
        {"weekday": 1.0, "weekend": 0.3, "holiday": 0.5}, abs=1e-9
    )

    schedule = payload["schedule"]
    by_date = {row["local_date"]: row for row in schedule}
    assert by_date["2024-03-29"]["category"] == "holiday"
    assert by_date["2024-03-29"]["weight"] == pytest.approx(0.5, abs=1e-9)
    dst = by_date["2024-03-10"]
    assert dst["category"] == "weekend"
    assert dst["start_utc"] == "2024-03-10T05:00:00Z"
    assert dst["end_utc"] == "2024-03-11T04:00:00Z"
    assert dst["weighted_days"] == pytest.approx(0.3 * 23 / 24, abs=1e-9)
    assert by_date["2024-03-11"]["weight"] == pytest.approx(1.0)

    total = math.fsum(row["weighted_days"] for row in schedule)
    assert payload["total_weighted_days"] == pytest.approx(total)
    assert schedule[0]["remaining_fraction"] == pytest.approx(1.0)
    for i, row in enumerate(schedule):
        remaining = math.fsum(item["weighted_days"] for item in schedule[i:])
        assert row["remaining_weighted_days"] == pytest.approx(remaining)
        assert row["remaining_fraction"] == pytest.approx(remaining / total)

    # A runtime reader can calculate the fraction at an instant within a day.
    instant = datetime(2024, 3, 10, 16, tzinfo=UTC)
    end = datetime.fromisoformat(dst["end_utc"].replace("Z", "+00:00"))
    after_day = dst["remaining_weighted_days"] - dst["weighted_days"]
    remaining = after_day + dst["weight"] * (end - instant).total_seconds() / 86400
    subsequent = math.fsum(row["weighted_days"] for row in schedule
                           if row["local_date"] > "2024-03-10")
    assert remaining / total == pytest.approx((subsequent + 0.3 * 0.5) / total)
