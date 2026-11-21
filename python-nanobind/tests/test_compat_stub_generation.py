import ast
import csv
import importlib.util
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


def alias_rows():
    tree = ast.parse(ALIAS_SOURCE.read_text())
    assignment = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_ALIASES"
                for target in node.targets)
    )
    return ast.literal_eval(assignment.value)


def test_only_the_documented_alias_rows_lack_a_stub_declaration():
    stub = ast.parse((PYTHON_NANOBIND / "src" / "qlnb" / "compat.pyi").read_text())
    declared = {
        (node.name, member.name)
        for node in stub.body
        if isinstance(node, ast.ClassDef)
        for member in node.body
        if isinstance(member, ast.FunctionDef)
    }
    undeclared = sorted(
        f"{cls}.{alias}" for cls, alias, _ in alias_rows() if (cls, alias) not in declared
    )
    # EverestOption.yield is a Python keyword; compat exports a factory under the
    # YoYInflationIndex name, so no class can be declared there.
    assert undeclared == [
        "EverestOption.yield",
        "YoYInflationIndex.addFixing",
        "YoYInflationIndex.availabilityLag",
        "YoYInflationIndex.clearFixings",
        "YoYInflationIndex.lastFixingDate",
    ]


def test_generator_copies_descriptor_kinds(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("generate_compat_stub", GENERATOR)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    (tmp_path / "_qlnb.pyi").write_text(
        "class Base:\n"
        "    def base_method(self, x: int) -> int: ...\n"
        "class Foo(Base):\n"
        "    @property\n"
        "    def some_value(self) -> float: ...\n"
        "    @some_value.setter\n"
        "    def some_value(self, v: float) -> None: ...\n"
        "    @staticmethod\n"
        "    def make_thing(a: int) -> Foo: ...\n"
        "    @overload\n"
        "    def over_load(self, a: int) -> int: ...\n"
        "    @overload\n"
        "    def over_load(self, a: str) -> str: ...\n"
    )
    (tmp_path / "_compat_aliases.py").write_text(
        "_ALIASES = (('Foo', 'baseMethod', 'base_method'), ('Foo', 'makeThing', 'make_thing'),\n"
        "            ('Foo', 'overLoad', 'over_load'), ('Foo', 'someValue', 'some_value'))\n"
        "_STATIC_METHODS = {('Foo', 'makeThing')}\n"
    )
    (tmp_path / "compat.py").write_text("def _install_aliases(): pass\n_install_aliases()\n")
    (tmp_path / "compat.pyi").write_text(
        "# BEGIN GENERATED COMPAT ALIASES\n# END GENERATED COMPAT ALIASES\n")
    monkeypatch.setattr(generator, "ALIASES_PATH", tmp_path / "_compat_aliases.py")
    monkeypatch.setattr(generator, "NATIVE_STUB", tmp_path / "_qlnb.pyi")
    monkeypatch.setattr(generator, "COMPAT_STUB", tmp_path / "compat.pyi")
    monkeypatch.setattr(generator, "COMPAT_SOURCE", tmp_path / "compat.py")

    rendered = generator.render_stub()

    assert "def baseMethod(self, x: int) -> int: ..." in rendered  # inherited from Base
    assert "@staticmethod\n    def makeThing(a: int) -> Foo: ..." in rendered
    assert rendered.count("@overload") == 2
    assert "@property\n    def someValue(self) -> float: ..." in rendered
    assert "@someValue.setter\n    def someValue(self, v: float) -> None: ..." in rendered
    assert "some_value" not in rendered
