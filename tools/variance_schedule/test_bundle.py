import hashlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import pytest


GENERATOR = Path(__file__).with_name("generate_intraday.py")
UTC = timezone.utc
CPP_TEST_EXECUTABLE = "QL_VARIANCE_CLOCK_BUNDLE_TEST_EXECUTABLE"


def configured_cpp_test_executable():
    configured = os.environ.get(CPP_TEST_EXECUTABLE)
    if configured is None:
        return None
    executable = Path(configured)
    if not executable.is_file():
        raise FileNotFoundError(
            f"{CPP_TEST_EXECUTABLE} names a missing C++ test executable: {executable}")
    return executable


def test_cpp_loader_integration_configuration():
    if configured_cpp_test_executable() is None:
        pytest.skip(
            f"C++ bundle round trips require {CPP_TEST_EXECUTABLE}; "
            "pure Python bundle assertions still run without it")


def invoke_generator(prices, *arguments):
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--prices", str(prices),
         "--timestamp-column", "observed_at", "--price-column", "mid_price",
         *arguments],
        capture_output=True, text=True,
    )


def test_cutoff_excludes_observations_before_fitting(tmp_path):
    prices = tmp_path / "prices.parquet"
    output = tmp_path / "schedule.parquet"
    timestamps = [
        datetime(2024, 1, 1, 0, minute, tzinfo=UTC)
        for minute in (0, 5, 10, 15)
    ]
    pl.DataFrame({
        "observed_at": timestamps,
        "mid_price": [100.0, 101.0, 100.0, 10_000.0],
    }).write_parquet(prices)

    result = invoke_generator(
        prices, "--output", output, "--timezone", "UTC", "--calendar", "always",
        "--start", "2024-01-01T00:00:00Z", "--end", "2024-01-01T00:10:00Z",
        "--min-samples", "1", "--cutoff", "2024-01-01T00:10:00Z",
    )

    assert result.returncode == 0, result.stderr
    metadata = json.loads(pl.read_parquet_metadata(output)["variance_schedule"])
    calibration = metadata["calibration"]
    assert calibration["returns_used"] == 2
    assert calibration["cutoff_excluded_observations"] == 1
    expected_returns = [
        math.log(101.0) - math.log(100.0),
        math.log(100.0) - math.log(101.0),
    ]
    drift = math.fsum(expected_returns) / 2
    expected_reference = math.fsum((value - drift) ** 2 for value in expected_returns) / 2
    assert calibration["reference_variance_per_5m"] == expected_reference


def _write_bundle_prices(path):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    interval_count = 35 * 288
    timestamps = [start + timedelta(minutes=5 * i) for i in range(interval_count + 1)]
    prices = []
    log_price = math.log(100.0)
    for index in range(interval_count + 1):
        prices.append(math.exp(log_price))
        if index < interval_count:
            log_price += 0.01 if index % 2 == 0 else -0.01
    del timestamps[5 * 288 + 101]
    del prices[5 * 288 + 101]
    pl.DataFrame({"observed_at": timestamps, "mid_price": prices}).write_parquet(path)


def test_bundle_is_deterministic_and_loads_in_configured_cpp_build(tmp_path):
    prices = tmp_path / "prices.parquet"
    _write_bundle_prices(prices)
    start = "2024-02-05T00:00:00Z"
    end = "2024-02-06T00:00:00Z"
    generated_at = start
    bundles = [tmp_path / "bundle-one", tmp_path / "bundle-two"]

    for bundle in bundles:
        result = invoke_generator(
            prices, "--bundle-dir", bundle, "--timezone", "UTC", "--calendar", "always",
            "--start", start, "--end", end, "--generated-at", generated_at,
            "--min-samples", "36", "--gap-pool-threshold", "1",
        )
        assert result.returncode == 0, result.stderr

    expected_names = {
        "manifest.json", "profiles.csv", "market_days.csv",
        "session_segments.csv", "timezone_mapping.csv", "slot_evidence.csv",
    }
    assert {path.name for path in bundles[0].iterdir()} == expected_names
    assert {
        path.name: path.read_bytes() for path in bundles[0].iterdir()
    } == {
        path.name: path.read_bytes() for path in bundles[1].iterdir()
    }
    manifest = json.loads((bundles[0] / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["files"]) == expected_names - {"manifest.json"}
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((bundles[0] / name).read_bytes()).hexdigest() == digest
    assert manifest["calibration_settings"]["minimum_direct_returns"] == 36
    assert manifest["calibration_settings"]["gap_pool_return_threshold"] == 1
    assert manifest["continuous_futures_lineage"] is None
    assert "pooled" in (bundles[0] / "slot_evidence.csv").read_text(encoding="utf-8")

    loader = configured_cpp_test_executable()
    if loader is not None:
        environment = {
            **os.environ,
            "QL_VARIANCE_CLOCK_BUNDLE_DIR": str(bundles[0]),
            "QL_VARIANCE_CLOCK_BUNDLE_SNAPSHOT": manifest["snapshot_id"],
        }
        result = subprocess.run(
            [
                str(loader),
                "--run_test=QuantLibTests/VarianceBundleLoaderTests/"
                "testDirectoryWrapperLoadsACompleteBundle",
                "--log_level=message",
            ],
            env=environment, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
