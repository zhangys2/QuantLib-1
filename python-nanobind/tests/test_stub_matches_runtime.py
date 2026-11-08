"""The type stubs must describe what the runtime actually has.

`_qlnb.pyi` documents the native snake_case API; the SWIG-style camelCase
aliases that `qlnb.compat` installs at import time are declared in
`compat.pyi`.  Both checks run in a fresh interpreter, because importing
`qlnb.compat` patches the native classes in place.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "src" / "qlnb"

# Known mismatches that predate this check.  Anything not listed here fails.
# SwapSpreadIndex is exposed as a factory function, not a class; OAS is a
# stubbed attribute of the callable bonds that the runtime does not provide.
KNOWN_NATIVE_MISSING = {
    "SwapSpreadIndex": [
        "day_counter",
        "fixing",
        "fixing_calendar",
        "fixing_days",
        "gearing1",
        "gearing2",
        "name",
        "swap_index1",
        "swap_index2",
        "value_date",
    ],
    "CallableFixedRateBond": ["OAS"],
    "CallableZeroCouponBond": ["OAS"],
}

_PROBE = """
import importlib, json, sys
module, members = sys.argv[1], json.loads(sys.stdin.read())
mod = importlib.import_module(module)
missing = {}
for cls, names in members.items():
    obj = getattr(mod, cls, None)
    if obj is None:
        missing[cls] = ["<class>"]
        continue
    gone = [n for n in names if not hasattr(obj, n)]
    if gone:
        missing[cls] = gone
print(json.dumps(missing))
"""


def stub_members(path: Path) -> dict[str, list[str]]:
    """Class members declared in a stub: methods and annotated attributes."""
    members: dict[str, list[str]] = {}
    current = None
    for line in path.read_text().splitlines():
        match = re.match(r"class (\w+)", line)
        if match:
            current = members.setdefault(match.group(1), [])
            continue
        if line[:1] not in (" ", "", "#"):
            current = None
            continue
        if current is None:
            continue
        match = re.match(r"    def (\w+)\(", line) or re.match(r"    (\w+): ", line)
        if match and not match.group(1).startswith("__"):
            if match.group(1) not in current:
                current.append(match.group(1))
    return members


def missing_at_runtime(module: str, members: dict[str, list[str]]) -> dict[str, list[str]]:
    result = subprocess.run(
        [sys.executable, "-c", _PROBE, module],
        input=json.dumps(members),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_native_stub_matches_runtime():
    missing = missing_at_runtime("qlnb", stub_members(PACKAGE / "_qlnb.pyi"))
    assert {k: sorted(v) for k, v in missing.items()} == KNOWN_NATIVE_MISSING


def test_native_stub_has_no_camel_case_methods():
    camel = {
        cls: [n for n in names if re.match(r"[a-z]+[A-Z]", n)]
        for cls, names in stub_members(PACKAGE / "_qlnb.pyi").items()
    }
    assert {k: v for k, v in camel.items() if v} == {}


def test_compat_stub_matches_runtime():
    members = stub_members(PACKAGE / "compat.pyi")
    assert members, "compat.pyi declares no classes"
    assert missing_at_runtime("qlnb.compat", members) == {}
