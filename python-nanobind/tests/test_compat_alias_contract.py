import csv
import json
import os
import subprocess
import sys

from pathlib import Path

SNAP = r'''
import json, sys, inspect
import qlnb
if sys.argv[1] == "B":
    import qlnb.compat
out = {"module": sorted(n for n in vars(qlnb) if not n.startswith("_")), "classes": {}}
for n, v in vars(qlnb).items():
    if inspect.isclass(v) and not n.startswith("_"):
        out["classes"][n] = sorted(m for m in vars(v) if not m.startswith("_") )
print(json.dumps(out))
'''

def snap(mode):
    # The child must import the same qlnb as this process, also when it was put on sys.path
    # by a conftest or by pytest's pythonpath setting rather than by PYTHONPATH.
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in sys.path if p))
    result = subprocess.run([sys.executable, "-c", SNAP, mode], capture_output=True, text=True,
                            env=env)
    assert result.returncode == 0, f"snapshot subprocess failed (mode {mode}):\n{result.stderr}"
    return json.loads(result.stdout)

def camel(s):
    p = s.split("_")
    return p[0] + "".join(t[:1].upper() + t[1:] for t in p[1:])

def unwrap(x):
    for attr in ("__func__", "fget"):
        if hasattr(x, attr):
            return getattr(x, attr)
    return x

def inventory():
    A, B = snap("A"), snap("B")
    import inspect, qlnb, qlnb.compat as compat
    rows = []
    for cls, members in sorted(B["classes"].items()):
        before = set(A["classes"].get(cls, [])); C = getattr(qlnb, cls); d = vars(C)
        for a in sorted(set(members) - before):
            raw = d[a]
            kind = ("staticmethod" if isinstance(raw, staticmethod) else "classmethod" if isinstance(raw, classmethod) else
                    "property" if isinstance(raw, property) else "method" if callable(raw) else "class constant")
            if cls not in A["classes"]: kind = "compat-defined class member"
            def lookup(t):
                for K in C.__mro__:
                    if t in vars(K): return vars(K)[t]
            cands = [t for t in set(dir(C)) - set(members) | before if t != a and lookup(t) is not None and unwrap(lookup(t)) is unwrap(raw)]
            cands.sort(key=lambda t: (camel(t) != a, "_" not in t, t))
            target = cands[0] if cands else "wrapper/proxy"
            rows.append([cls, a, target, kind, "mechanical" if cands and camel(target) == a else "exception" if cands else "wrapper/proxy"])
    for a in sorted(set(B["module"]) - set(A["module"])):
        v = getattr(qlnb, a); cands = [t for t in A["module"] if getattr(qlnb, t, None) is v]
        kind = "class" if inspect.isclass(v) else "module-level function" if callable(v) else "module constant"
        rows.append(["<module>", a, cands[0] if cands else "wrapper/proxy", kind, "mechanical" if cands and camel(cands[0]) == a else "exception" if cands else "wrapper/proxy"])
    for a in sorted(n for n in vars(compat) if not n.startswith("_") and n not in B["module"]):
        v=vars(compat)[a]; kind="class" if inspect.isclass(v) else "module-level function" if callable(v) else "module constant"
        rows.append(["<compat>",a,"wrapper/proxy",kind,"wrapper/proxy"])
    return rows

def test_compat_alias_contract():
    manifest = Path(__file__).with_name("compat_aliases_manifest.csv")
    with manifest.open(newline="") as f:
        expected = list(csv.reader(f))[1:]
    actual = inventory()
    added, missing = sorted(set(map(tuple, actual)) - set(map(tuple, expected))), sorted(set(map(tuple, expected)) - set(map(tuple, actual)))
    assert not added and not missing, (
        f"Added rows: {added}\nMissing rows: {missing}\n"
        "If the alias table in qlnb/compat.py changed on purpose, update "
        "tests/compat_aliases_manifest.csv to match.")
