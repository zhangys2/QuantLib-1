import csv
import hashlib
import io
import json
import math
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import pytest


HERE = Path(__file__).resolve().parent
GENERATOR = HERE / "generate_intraday.py"
UTC = timezone.utc
sys.path.insert(0, str(HERE))
import generate_intraday  # noqa: E402
from test_bundle import GENERATED_BUNDLE_MESSAGE, configured_cpp_test_executable  # noqa: E402


def run_generator(prices, *arguments):
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--prices", str(prices),
         "--timestamp-column", "observed_at", "--price-column", "mid_price",
         *map(str, arguments)],
        capture_output=True, text=True,
    )


def write_prices(path, start, days, prices_for_step=None):
    """Five-minute grid from start for `days` days; steps alternate +-0.01 in log price."""
    steps = days * 288
    timestamps = [start + timedelta(minutes=5 * i) for i in range(steps + 1)]
    if prices_for_step is None:
        log_price, prices = math.log(100.0), []
        for index in range(steps + 1):
            prices.append(math.exp(log_price))
            log_price += 0.01 if index % 2 == 0 else -0.01
    else:
        prices = prices_for_step(steps)
    pl.DataFrame({"observed_at": timestamps, "mid_price": prices}).write_parquet(path)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def cpp_loads_in_configured_build(bundle, mode=None):
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    loader = configured_cpp_test_executable()
    if loader is not None:
        environment = {
            **os.environ,
            "QL_VARIANCE_CLOCK_BUNDLE_DIR": str(bundle),
            "QL_VARIANCE_CLOCK_BUNDLE_SNAPSHOT": manifest["snapshot_id"],
        }
        if mode is not None:
            environment["QL_VARIANCE_CLOCK_BUNDLE_MODE"] = mode
        result = subprocess.run(
            [str(loader), "--run_test=QuantLibTests/VarianceBundleLoaderTests/"
                          "testDirectoryWrapperLoadsACompleteBundle", "--log_level=message"],
            env=environment,
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert GENERATED_BUNDLE_MESSAGE in result.stdout + result.stderr, \
            "the C++ generated-bundle hook did not run"
    return manifest


def cpp_results(bundle, mode=None, snapshot=None):
    """Run the generated-bundle hook in the configured C++ build."""
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    loader = configured_cpp_test_executable()
    if loader is None:
        return []
    environment = {
        **os.environ,
        "QL_VARIANCE_CLOCK_BUNDLE_DIR": str(bundle),
        "QL_VARIANCE_CLOCK_BUNDLE_SNAPSHOT": snapshot or manifest["snapshot_id"],
    }
    if mode is not None:
        environment["QL_VARIANCE_CLOCK_BUNDLE_MODE"] = mode
    return [subprocess.run(
        [str(loader), "--run_test=QuantLibTests/VarianceBundleLoaderTests/"
                      "testDirectoryWrapperLoadsACompleteBundle", "--log_level=message"],
        env=environment, capture_output=True, text=True)]


def test_explicit_cpp_loader_binary_must_exist(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(
        json.dumps({"snapshot_id": "test-snapshot"}), encoding="utf-8")
    monkeypatch.setenv(
        "QL_VARIANCE_CLOCK_BUNDLE_TEST_EXECUTABLE",
        str(tmp_path / "missing-quantlib-test-suite"),
    )

    with pytest.raises(FileNotFoundError, match="QL_VARIANCE_CLOCK_BUNDLE_TEST_EXECUTABLE"):
        cpp_results(bundle)


def utc_generator_arguments(bundle, **overrides):
    values = {"--timezone": "UTC", "--calendar": "always",
              "--start": "2024-02-05T00:00:00Z", "--end": "2024-02-06T00:00:00Z",
              "--generated-at": "2024-02-05T00:00:00Z", "--min-samples": "1"}
    values.update(overrides)
    arguments = ["--bundle-dir", bundle]
    for key, value in values.items():
        if value is not None:
            arguments += [key, value]
    return arguments


def test_exactly_zero_slots_become_zero_rows_with_warnings(tmp_path):
    def flat_at_two_slots(steps):
        price, prices = 1.0, []
        for index in range(steps + 1):
            prices.append(price)
            if index % 288 not in (100, 200):
                price = 2.0 if price == 1.0 else 1.0
        return prices

    prices, bundle = tmp_path / "prices.parquet", tmp_path / "bundle"
    write_prices(prices, datetime(2024, 1, 1, tzinfo=UTC), 35, flat_at_two_slots)
    # Every slot has exactly 35 returns, so --min-samples 35 is the boundary: all are direct.
    result = run_generator(prices, *utc_generator_arguments(bundle, **{"--min-samples": "35"}))
    assert result.returncode == 0, result.stderr

    rows = read_csv(bundle / "slot_evidence.csv")
    zero = [row for row in rows if row["estimation_method"] == "zero"]
    assert [int(row["minute_of_day"]) for row in zero] == [500, 1000]
    assert all(row["warning_codes"] == "ZERO_RATE_SLOT" for row in zero)
    assert sum(row["estimation_method"] == "direct" for row in rows) == 286
    weights = {int(row["minute_of_day"]): float(row["weight"])
               for row in read_csv(bundle / "profiles.csv")}
    assert weights[500] == weights[1000] == 0.0 and weights[0] > 0.0
    manifest = cpp_loads_in_configured_build(bundle)
    assert [(w["code"], w["minute_of_day"]) for w in manifest["warnings"]] == [
        ("ZERO_RATE_SLOT", 500), ("ZERO_RATE_SLOT", 1000)]


def _prices_with_one_missing_observation(path):
    write_prices(path, datetime(2024, 1, 1, tzinfo=UTC), 35)
    frame = pl.read_parquet(path)
    frame.filter(pl.int_range(pl.len()) != 5 * 288 + 101).write_parquet(path)


def test_gap_pool_threshold_is_required_and_checked_at_its_boundary(tmp_path):
    prices = tmp_path / "prices.parquet"
    _prices_with_one_missing_observation(prices)
    # The missing observation leaves slots 500 and 505 with 34 direct returns; with
    # --min-samples 35 only those two slots are pooled.
    common = {"--min-samples": "35"}
    result = run_generator(prices, *utc_generator_arguments(tmp_path / "none", **common))
    assert result.returncode != 0
    assert "pooled bundle slots require --gap-pool-threshold" in result.stderr
    assert not (tmp_path / "none").exists()

    bundle = tmp_path / "one"
    result = run_generator(prices, *utc_generator_arguments(
        bundle, **common, **{"--gap-pool-threshold": "1"}))
    assert result.returncode == 0, result.stderr
    rows = read_csv(bundle / "slot_evidence.csv")
    pooled = [row for row in rows if row["estimation_method"] == "pooled"]
    assert [int(row["minute_of_day"]) for row in pooled] == [500, 505]
    assert sum(row["estimation_method"] == "direct" for row in rows) == 286
    first = pooled[0]
    assert (first["target_return_count"], first["target_distinct_local_date_count"]) == ("34", "34")
    assert first["source_group_id"] and first["grouping_label"] and first["fallback_id"] == ""
    assert first["source_return_count"] == "34"
    assert first["source_distinct_local_date_count"] == "34"
    cpp_loads_in_configured_build(bundle)

    count = int(first["gap_pool_return_count"])
    assert count > 1
    ok = run_generator(prices, *utc_generator_arguments(
        tmp_path / "at", **common, **{"--gap-pool-threshold": str(count)}))
    assert ok.returncode == 0, ok.stderr
    short = run_generator(prices, *utc_generator_arguments(
        tmp_path / "above", **common, **{"--gap-pool-threshold": str(count + 1)}))
    assert short.returncode != 0 and "fewer gap returns" in short.stderr
    assert not (tmp_path / "above").exists()


@pytest.mark.parametrize("first_day, cutoff, start, end, transition_utc, hours", [
    (datetime(2024, 10, 20, tzinfo=UTC), "2024-11-06T00:00:00Z",
     "2024-10-28T00:00:00Z", "2024-11-08T00:00:00Z", "2024-11-03T06:00:00Z", 25),
    (datetime(2024, 2, 25, tzinfo=UTC), "2024-03-12T00:00:00Z",
     "2024-03-05T00:00:00Z", "2024-03-14T00:00:00Z", "2024-03-10T07:00:00Z", 23),
])
def test_dst_transitions_map_fold_runs_and_count_repeated_local_slots(
        tmp_path, first_day, cutoff, start, end, transition_utc, hours):
    prices, bundle = tmp_path / "prices.parquet", tmp_path / "bundle"
    write_prices(prices, first_day, 20)
    result = run_generator(prices, *utc_generator_arguments(
        bundle, **{"--timezone": "America/New_York", "--cutoff": cutoff, "--start": start,
                   "--end": end, "--generated-at": cutoff, "--min-samples": "2"}))
    assert result.returncode == 0, result.stderr
    cpp_loads_in_configured_build(bundle)

    runs = read_csv(bundle / "timezone_mapping.csv")
    for previous, current in zip(runs, runs[1:]):
        assert previous["end_utc"] == current["start_utc"]
    assert (runs[0]["start_utc"], runs[-1]["end_utc"]) == (start, end)
    fall_back = hours == 25
    if fall_back:
        # -04:00, then the repeated hour (fold 1) at -05:00, then -05:00 again.
        assert [(r["offset_seconds"], r["fold"]) for r in runs] == [
            ("-14400", "0"), ("-18000", "1"), ("-18000", "0")]
        repeated = datetime.fromisoformat(runs[1]["end_utc"].replace("Z", "+00:00")) - \
            datetime.fromisoformat(runs[1]["start_utc"].replace("Z", "+00:00"))
        assert repeated == timedelta(hours=1)
        assert runs[1]["start_utc"] == transition_utc
    else:
        assert [(r["offset_seconds"], r["fold"]) for r in runs] == [
            ("-18000", "0"), ("-14400", "0")]
        assert runs[1]["start_utc"] == transition_utc

    local_day = "2024-11-03" if fall_back else "2024-03-10"
    session = next(r for r in read_csv(bundle / "session_segments.csv")
                   if r["local_date"] == local_day)
    length = datetime.fromisoformat(session["end_utc"].replace("Z", "+00:00")) - \
        datetime.fromisoformat(session["start_utc"].replace("Z", "+00:00"))
    assert length == timedelta(hours=hours)

    rows = {int(r["minute_of_day"]): r for r in read_csv(bundle / "slot_evidence.csv")}
    repeated_slot = rows[60]  # local 01:00, occurring twice on the fall-back day
    skipped_slot = rows[120]  # local 02:00, absent on the spring-forward day
    difference = int(repeated_slot["target_return_count"]) - int(
        repeated_slot["target_distinct_local_date_count"])
    assert difference == (1 if fall_back else 0)
    if not fall_back:
        assert int(skipped_slot["target_return_count"]) == int(
            skipped_slot["target_distinct_local_date_count"])


def test_calendar_categories_map_to_profiles_and_date_types(tmp_path):
    prices, holidays, bundle = (tmp_path / "prices.parquet", tmp_path / "holidays.parquet",
                                tmp_path / "bundle")
    write_prices(prices, datetime(2024, 1, 1, tzinfo=UTC), 35)
    pl.DataFrame({"date": [date(2024, 1, 15), date(2024, 2, 7)]}).write_parquet(holidays)
    result = run_generator(prices, *utc_generator_arguments(
        bundle, **{"--calendar": "custom", "--holidays": holidays,
                   "--end": "2024-02-12T00:00:00Z", "--generated-at": "2024-02-05T00:00:00Z"}))
    assert result.returncode == 0, result.stderr
    days = {r["local_date"]: r for r in read_csv(bundle / "market_days.csv")}
    assert len(days) == 7
    expected = {"2024-02-05": ("full_day", "1"), "2024-02-06": ("full_day", "1"),
                "2024-02-07": ("holiday", "3"), "2024-02-08": ("full_day", "1"),
                "2024-02-09": ("full_day", "1"), "2024-02-10": ("weekend", "2"),
                "2024-02-11": ("weekend", "2")}
    assert {k: (v["date_type"], v["profile_id"]) for k, v in days.items()} == expected
    assert all(v["is_open"] == "true" and v["selection_reason"] == "date_type_session_pattern"
               for v in days.values())
    manifest = cpp_loads_in_configured_build(bundle)
    assert [c["profile_id"] for c in manifest["profile_calibrations"]] == [1, 2, 3]
    assert len(read_csv(bundle / "profiles.csv")) == 3 * 288


def test_bundle_provenance_cutoff_reporting_and_identity(tmp_path):
    prices = tmp_path / "prices.parquet"
    write_prices(prices, datetime(2024, 1, 1, tzinfo=UTC), 35)
    first = tmp_path / "first"
    result = run_generator(prices, *utc_generator_arguments(
        first, **{"--generated-at": "2024-02-05T12:00:00Z"}))
    assert result.returncode == 0, result.stderr
    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    cutoff = manifest["price_cutoff_utc"]
    assert cutoff == "2024-02-05T00:00:00Z" == manifest["calibration_settings"]["price_cutoff_utc"]
    assert manifest["generated_at_utc"] == "2024-02-05T12:00:00Z"
    assert manifest["calendar_as_of_utc"] == manifest["timezone_as_of_utc"] == cutoff
    assert {e["available_at_utc"] for e in manifest["evidence"]} == {cutoff}
    assert [c["calibration_as_of_utc"] for c in manifest["profile_calibrations"]] == [cutoff]
    evidence = {e["role"]: e for e in manifest["evidence"]}
    assert set(evidence) == {"calendar_source", "price_input", "timezone_rules"}
    assert evidence["price_input"]["content_sha256"] == hashlib.sha256(
        prices.read_bytes()).hexdigest()
    assert str(tmp_path) not in json.dumps(manifest), "local paths must not leak into bundles"
    assert manifest["timezone_rules_sha256"] == manifest["files"]["timezone_mapping.csv"]
    cpp_loads_in_configured_build(first)

    # An earlier cutoff excludes the last day of observations; the count is reported.
    earlier = tmp_path / "earlier"
    result = run_generator(prices, *utc_generator_arguments(
        earlier, **{"--cutoff": "2024-02-04T00:00:00Z"}))
    assert result.returncode == 0, result.stderr
    assert "excluded 288 price observations after --cutoff" in result.stderr
    other = json.loads((earlier / "manifest.json").read_text(encoding="utf-8"))
    assert other["price_cutoff_utc"] == "2024-02-04T00:00:00Z"
    assert other["snapshot_id"] != manifest["snapshot_id"]

    # Settings that change only the manifest still change the snapshot identity.
    thresholded = tmp_path / "thresholded"
    result = run_generator(prices, *utc_generator_arguments(
        thresholded, **{"--generated-at": "2024-02-05T12:00:00Z", "--gap-pool-threshold": "1"}))
    assert result.returncode == 0, result.stderr
    for name in manifest["files"]:
        assert (thresholded / name).read_bytes() == (first / name).read_bytes()
    third = json.loads((thresholded / "manifest.json").read_text(encoding="utf-8"))
    assert third["calibration_settings"]["gap_pool_return_threshold"] == 1
    assert third["snapshot_id"] != manifest["snapshot_id"]

    # Likewise for the minimum direct-return count: every slot has 35 returns, so 1 and 2
    # classify all slots the same way and the CSV files do not change.
    minimum = tmp_path / "minimum"
    result = run_generator(prices, *utc_generator_arguments(
        minimum, **{"--generated-at": "2024-02-05T12:00:00Z", "--min-samples": "2"}))
    assert result.returncode == 0, result.stderr
    for name in manifest["files"]:
        assert (minimum / name).read_bytes() == (first / name).read_bytes()
    fourth = json.loads((minimum / "manifest.json").read_text(encoding="utf-8"))
    assert fourth["calibration_settings"]["minimum_direct_returns"] == 2
    assert fourth["snapshot_id"] != manifest["snapshot_id"]

    # A cutoff after the generation time is rejected before anything is written.
    rejected = tmp_path / "rejected"
    result = run_generator(prices, *utc_generator_arguments(
        rejected, **{"--cutoff": "2024-02-05T00:00:01Z"}))
    assert result.returncode != 0 and "must not be later than --generated-at" in result.stderr
    assert not rejected.exists()


def test_historical_bundle_is_reconstruction_only(tmp_path):
    prices, bundle = tmp_path / "prices.parquet", tmp_path / "bundle"
    write_prices(prices, datetime(2024, 1, 1, tzinfo=UTC), 35)
    result = run_generator(prices, *utc_generator_arguments(
        bundle, **{"--generated-at": "2024-02-06T00:00:00Z"}))
    assert result.returncode == 0, result.stderr
    assert ("generated_at_utc is at or after coverage_end_utc; "
            "bundle loads only in Reconstruction mode") in result.stderr

    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["generated_at_utc"] == manifest["coverage_end_utc"]
    cpp_loads_in_configured_build(bundle, mode="reconstruction_only")


RECONSTRUCTION_WARNING = ("generated_at_utc is at or after coverage_end_utc; "
                          "bundle loads only in Reconstruction mode")


def test_generation_time_boundary_around_the_coverage_end(tmp_path):
    prices = tmp_path / "prices.parquet"
    write_prices(prices, datetime(2024, 1, 1, tzinfo=UTC), 35)
    # coverage_end_utc is 2024-02-06T00:00:00Z and exclusive.
    just_before = tmp_path / "before"
    result = run_generator(prices, *utc_generator_arguments(
        just_before, **{"--generated-at": "2024-02-05T23:59:59Z"}))
    assert result.returncode == 0, result.stderr
    assert "Reconstruction" not in result.stderr
    cpp_loads_in_configured_build(just_before)

    for name, generated_at in (("equal", "2024-02-06T00:00:00Z"),
                               ("after", "2024-02-07T00:00:00Z"),
                               ("later", "2024-02-06T00:00:01Z")):
        bundle = tmp_path / name
        result = run_generator(prices, *utc_generator_arguments(
            bundle, **{"--generated-at": generated_at}))
        assert result.returncode == 0, result.stderr
        assert RECONSTRUCTION_WARNING in result.stderr
        assert json.loads((bundle / "manifest.json").read_text(
            encoding="utf-8"))["generated_at_utc"] == generated_at
        cpp_loads_in_configured_build(bundle, mode="reconstruction_only")

    # Without --generated-at the current time is used, which is after a historical window.
    default = tmp_path / "default"
    result = run_generator(prices, *utc_generator_arguments(
        default, **{"--generated-at": None}))
    assert result.returncode == 0, result.stderr
    assert RECONSTRUCTION_WARNING in result.stderr
    cpp_loads_in_configured_build(default, mode="reconstruction_only")


def test_generated_bundle_hook_rejects_mismatched_modes(tmp_path):
    prices = tmp_path / "prices.parquet"
    write_prices(prices, datetime(2024, 1, 1, tzinfo=UTC), 35)
    normal, historical = tmp_path / "normal", tmp_path / "historical"
    for bundle, generated_at in ((normal, "2024-02-05T00:00:00Z"),
                                 (historical, "2024-02-06T00:00:00Z")):
        result = run_generator(prices, *utc_generator_arguments(
            bundle, **{"--generated-at": generated_at}))
        assert result.returncode == 0, result.stderr

    # A bundle that Strict mode accepts is not a Reconstruction-only bundle.
    for result in cpp_results(normal, mode="reconstruction_only"):
        assert result.returncode != 0
        assert "Strict mode accepted a Reconstruction-only bundle" in result.stdout + result.stderr
    # The default hook loads in Strict mode first, which a historical bundle fails.
    for result in cpp_results(historical):
        assert result.returncode != 0
        assert "Strict generated_at_utc must be before coverage_end_utc" in (
            result.stdout + result.stderr)
    for result in cpp_results(normal, mode="bogus"):
        assert result.returncode != 0
        assert "unknown QL_VARIANCE_CLOCK_BUNDLE_MODE value: bogus" in (
            result.stdout + result.stderr)
    # The expected snapshot identity is checked in the Reconstruction-only path as well.
    for result in cpp_results(historical, mode="reconstruction_only", snapshot="wrong-id"):
        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "provenance.snapshotId == expectedSnapshot has failed" in output
        assert "!= wrong-id]" in output


def bundle_files(tag):
    return {name: f"{tag}-{name}".encode() for name in (
        "manifest.json", "profiles.csv", "market_days.csv",
        "session_segments.csv", "timezone_mapping.csv", "slot_evidence.csv")}


def read_directory(path):
    return {entry.name: entry.read_bytes() for entry in path.iterdir()}


def test_bundle_directory_is_replaced_whole_without_leftovers(tmp_path):
    target = tmp_path / "bundle"
    generate_intraday.atomic_write_bundle(target, bundle_files("old"))
    assert read_directory(target) == bundle_files("old")
    generate_intraday.atomic_write_bundle(target, bundle_files("new"))
    assert read_directory(target) == bundle_files("new")
    assert [entry.name for entry in tmp_path.iterdir()] == ["bundle"]


def test_failed_swap_restores_the_previous_bundle(tmp_path, monkeypatch):
    target = tmp_path / "bundle"
    generate_intraday.atomic_write_bundle(target, bundle_files("old"))
    real_replace = os.replace

    def failing_replace(source, destination, *args, **kwargs):
        if ".stage-" in Path(source).name:
            raise OSError("injected swap failure")
        return real_replace(source, destination, *args, **kwargs)

    monkeypatch.setattr(generate_intraday.os, "replace", failing_replace)
    with pytest.raises(OSError, match="injected swap failure"):
        generate_intraday.atomic_write_bundle(target, bundle_files("new"))
    assert read_directory(target) == bundle_files("old")
    assert [entry.name for entry in tmp_path.iterdir()] == ["bundle"]


def test_bundle_destination_must_be_a_real_directory(tmp_path):
    real = tmp_path / "real"
    generate_intraday.atomic_write_bundle(real, bundle_files("old"))
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        generate_intraday.atomic_write_bundle(link, bundle_files("new"))
    assert read_directory(real) == bundle_files("old")

    plain = tmp_path / "plain"
    plain.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="not a directory"):
        generate_intraday.atomic_write_bundle(plain, bundle_files("new"))
    assert plain.read_text(encoding="utf-8") == "keep"


def test_pooled_slot_without_any_direct_observation_is_rejected(tmp_path):
    # Dropping the observation at slot 101 of every day leaves slots 100 and 101 with no
    # direct return at all. Phase B requires a pooled slot to have at least one direct
    # date, so the generator must refuse instead of writing a bundle the loader rejects.
    prices, bundle = tmp_path / "prices.parquet", tmp_path / "bundle"
    def three_step_cycle(steps):
        # The two steps merged by the missing observation (indices 100 and 101 mod 3) do not
        # cancel, so the pooled variance is positive and the slot is not a zero slot.
        log_price, values = math.log(100.0), []
        for index in range(steps + 1):
            values.append(math.exp(log_price))
            log_price += (0.01, 0.01, -0.02)[index % 3]
        return values

    write_prices(prices, datetime(2024, 1, 1, tzinfo=UTC), 35, three_step_cycle)
    pl.read_parquet(prices).filter(pl.int_range(pl.len()) % 288 != 101).write_parquet(prices)
    result = run_generator(prices, *utc_generator_arguments(
        bundle, **{"--min-samples": "35", "--gap-pool-threshold": "1"}))
    assert result.returncode != 0
    assert "cannot represent pooled slot without direct observations" in result.stderr
    assert not bundle.exists()
