import json
import subprocess
import sys
from pathlib import Path

import pytest

from test_generate import write_prices


def test_schedule_respects_intraday_expiry(tmp_path):
    prices = tmp_path / "prices.csv"
    output = tmp_path / "intraday.json"
    write_prices(prices)
    generator = Path(__file__).with_name("generate.py")

    result = subprocess.run(
        [sys.executable, str(generator), "--prices", str(prices),
         "--start", "2024-03-11T09:30:00-04:00",
         "--end", "2024-03-11T16:00:00-04:00", "--output", str(output)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    with output.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    assert len(payload["schedule"]) == 1
    row = payload["schedule"][0]
    assert row["start_utc"] == "2024-03-11T13:30:00Z"
    assert row["end_utc"] == "2024-03-11T20:00:00Z"
    assert row["weighted_days"] == pytest.approx(6.5 / 24)
    assert row["remaining_fraction"] == pytest.approx(1.0)
