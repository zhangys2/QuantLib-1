from datetime import date, datetime, timedelta, timezone

import polars as pl

from test_parquet_schedule import run_generator


UTC = timezone.utc


def continuous_prices(path, days):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = [start + timedelta(minutes=5 * i) for i in range(days * 288 + 1)]
    prices = [100.0 if i % 2 == 0 else 101.0 for i in range(len(timestamps))]
    pl.DataFrame({"observed_at": timestamps, "mid_price": prices}).write_parquet(path)


def test_dst_transition_uses_real_utc_intervals(tmp_path):
    prices, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    continuous_prices(prices, 3)
    result = run_generator(
        prices, output, "--timezone", "America/New_York", "--calendar", "always",
        "--start", "2024-03-10T01:55:00-05:00", "--end", "2024-03-10T03:05:00-04:00",
    )
    assert result.returncode == 0, result.stderr
    rows = pl.read_parquet(output).to_dicts()
    assert len(rows) == 2
    assert [row["minute_of_day"] for row in rows] == [115, 180]
    assert rows[0]["start_utc"] == datetime(2024, 3, 10, 6, 55, tzinfo=UTC)
    assert rows[-1]["end_utc"] == datetime(2024, 3, 10, 7, 5, tzinfo=UTC)


def test_unidentified_closed_period_preserves_existing_output(tmp_path):
    prices, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    continuous_prices(prices, 3)
    output.write_bytes(b"existing schedule")
    result = run_generator(
        prices, output, "--timezone", "UTC", "--calendar", "weekends",
        "--start", "2024-01-06T00:00:00Z", "--end", "2024-01-07T00:00:00Z",
    )
    assert result.returncode != 0
    assert output.read_bytes() == b"existing schedule"


def test_custom_holidays_are_used_and_cannot_be_overwritten(tmp_path):
    prices = tmp_path / "prices.parquet"
    output = tmp_path / "schedule.parquet"
    holidays = tmp_path / "holidays.parquet"
    continuous_prices(prices, 6)
    pl.DataFrame({"date": [date(2024, 1, 2), date(2024, 1, 3)]}).write_parquet(holidays)
    arguments = (
        "--timezone", "UTC", "--calendar", "custom", "--weekend-days", "5,6",
        "--holidays", str(holidays), "--start", "2024-01-03T12:00:00Z",
        "--end", "2024-01-03T12:10:00Z",
    )
    result = run_generator(prices, output, *arguments)
    assert result.returncode == 0, result.stderr
    assert pl.read_parquet(output)["category"].to_list() == ["holiday", "holiday"]

    previous = holidays.read_bytes()
    result = run_generator(prices, holidays, *arguments)
    assert result.returncode != 0
    assert holidays.read_bytes() == previous
