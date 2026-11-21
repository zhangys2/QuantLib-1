import ast
import csv
import subprocess
import sys
from pathlib import Path


PYTHON_NANOBIND = Path(__file__).resolve().parents[1]
ALIAS_SOURCE = PYTHON_NANOBIND / "src" / "qlnb" / "_compat_aliases.py"
MANIFEST = Path(__file__).with_name("compat_aliases_manifest.csv")
GENERATOR = PYTHON_NANOBIND / "tools" / "generate_compat_stub.py"


def test_alias_table_matches_manifest_rows():
    tree = ast.parse(ALIAS_SOURCE.read_text())
    assignment = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_ALIASES"
                for target in node.targets)
    )
    aliases = ast.literal_eval(assignment.value)

    with MANIFEST.open(newline="") as source:
        manifest_rows = list(csv.DictReader(source))
    expected = [
        (row["class"], row["alias"], row["target"])
        for row in manifest_rows
        if row["rule"] in {"mechanical", "exception"}
    ]
    assert aliases == tuple(expected)


def test_compat_stub_is_current():
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=PYTHON_NANOBIND,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
