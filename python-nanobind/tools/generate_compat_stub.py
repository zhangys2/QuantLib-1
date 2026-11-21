#!/usr/bin/env python3
"""Generate qlnb.compat alias declarations from the runtime alias table."""

import argparse
import ast
import keyword
import re
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALIASES_PATH = ROOT / "src" / "qlnb" / "_compat_aliases.py"
NATIVE_STUB = ROOT / "src" / "qlnb" / "_qlnb.pyi"
COMPAT_STUB = ROOT / "src" / "qlnb" / "compat.pyi"
COMPAT_SOURCE = ROOT / "src" / "qlnb" / "compat.py"
BEGIN_MARKER = "# BEGIN GENERATED COMPAT ALIASES"
END_MARKER = "# END GENERATED COMPAT ALIASES"


def module_assignments(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    result = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name):
            result[target.id] = ast.literal_eval(node.value)
    return result


def native_classes():
    tree = ast.parse(NATIVE_STUB.read_text(), filename=str(NATIVE_STUB))
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def native_exports():
    tree = ast.parse(NATIVE_STUB.read_text(), filename=str(NATIVE_STUB))
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def find_methods(classes, class_name, target, seen=()):
    if class_name in seen or class_name not in classes:
        return []
    cls = classes[class_name]
    methods = [
        node
        for node in cls.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == target
    ]
    if methods:
        return methods
    for base in cls.bases:
        if isinstance(base, ast.Name):
            methods = find_methods(classes, base.id, target, seen + (class_name,))
            if methods:
                return methods
    return []


def qualify_compat_parameter_types(
    declaration, method, start_line, line_offsets, class_names
):
    declaration_start = line_offsets[start_line - 1]
    replacements = []
    parameters = (
        list(method.args.posonlyargs)
        + list(method.args.args)
        + list(method.args.kwonlyargs)
        + ([method.args.vararg] if method.args.vararg else [])
        + ([method.args.kwarg] if method.args.kwarg else [])
    )
    for parameter in parameters:
        if parameter.annotation is None:
            continue
        for node in ast.walk(parameter.annotation):
            if isinstance(node, ast.Name) and node.id in class_names:
                begin = line_offsets[node.lineno - 1] + node.col_offset - declaration_start
                end = line_offsets[node.end_lineno - 1] + node.end_col_offset - declaration_start
                replacements.append((begin, end, f"_native.{node.id}"))
    for begin, end, replacement in sorted(replacements, reverse=True):
        declaration = declaration[:begin] + replacement + declaration[end:]
    return declaration


def module_class_shadows(class_names):
    tree = ast.parse(COMPAT_SOURCE.read_text(), filename=str(COMPAT_SOURCE))
    installer_index = next(
        index
        for index, node in enumerate(tree.body)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "_install_aliases"
    )
    shadows = set()
    for node in tree.body[installer_index + 1 :]:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id not in class_names:
                continue
            value = node.value
            native_class = (
                isinstance(value, ast.Attribute)
                and isinstance(value.value, ast.Name)
                and value.value.id == "_ql"
                and value.attr == target.id
            )
            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "getattr"
                and len(value.args) >= 2
                and isinstance(value.args[0], ast.Name)
                and value.args[0].id == "_ql"
                and isinstance(value.args[1], ast.Constant)
                and value.args[1].value == target.id
            ):
                native_class = True
            if not native_class:
                shadows.add(target.id)
    return shadows


def generated_aliases():
    assignments = module_assignments(ALIASES_PATH)
    aliases = assignments["_ALIASES"]
    static_methods = set(assignments["_STATIC_METHODS"])
    classes = native_classes()
    shadows = module_class_shadows({row[0] for row in aliases})
    compat_class_names = {
        class_name
        for class_name, alias, _ in aliases
        if class_name not in shadows and not keyword.iskeyword(alias)
    }
    native_lines = NATIVE_STUB.read_text().splitlines()
    native_source = NATIVE_STUB.read_text()
    line_offsets = []
    offset = 0
    for line in native_source.splitlines(keepends=True):
        line_offsets.append(offset)
        offset += len(line)
    grouped = {}
    skipped = {}
    for class_name, alias, target in aliases:
        if class_name in shadows:
            # The compatibility module exports a different object under this class name.
            skipped.setdefault("compat exports a different object under this class name",
                               []).append(f"{class_name}.{alias}")
            continue
        if keyword.iskeyword(alias):
            # Python syntax cannot spell an attribute whose name is a keyword.
            skipped.setdefault("the alias is a Python keyword", []).append(
                f"{class_name}.{alias}")
            continue
        if class_name not in classes:
            raise ValueError(f"native stub has no class {class_name}")
        methods = find_methods(classes, class_name, target)
        if not methods:
            raise ValueError(f"native stub has no target {class_name}.{target}")
        is_static = any(
            isinstance(decorator, ast.Name) and decorator.id == "staticmethod"
            for decorator in methods[0].decorator_list
        )
        if is_static != ((class_name, alias) in static_methods):
            raise ValueError(f"static method metadata disagrees for {class_name}.{alias}")
        declarations = []
        for method in methods:
            start = min(
                [method.lineno] + [decorator.lineno for decorator in method.decorator_list]
            )
            declaration = "\n".join(native_lines[start - 1 : method.end_lineno])
            declaration = qualify_compat_parameter_types(
                declaration, method, start, line_offsets, compat_class_names
            )
            declaration = textwrap.dedent(declaration)
            declaration = declaration.replace(f"def {target}(", f"def {alias}(", 1)
            # Property accessors are decorated with `@<name>.setter` and similar.
            declaration = re.sub(rf"^@{re.escape(target)}\.", f"@{alias}.", declaration,
                                 flags=re.MULTILINE)
            declarations.append(textwrap.indent(declaration, "    "))
        grouped.setdefault(class_name, []).extend(declarations)

    blocks = []
    for class_name in sorted(grouped):
        methods = "\n\n".join(grouped[class_name])
        blocks.append(f"class {class_name}(_native.{class_name}):\n{methods}")
    notes = ["# Not generated (runtime aliases only):"]
    for reason, rows in sorted(skipped.items()):
        notes.append(f"#   {reason}:")
        notes.extend(f"#     {row}" for row in rows)
    return "\n".join(notes) + "\n\n" + "\n\n".join(blocks)


def native_imports():
    assignments = module_assignments(ALIASES_PATH)
    aliases = assignments["_ALIASES"]
    shadows = module_class_shadows({row[0] for row in aliases})
    compat_classes = {
        class_name
        for class_name, alias, _ in aliases
        if class_name not in shadows and not keyword.iskeyword(alias)
    }
    names = sorted(native_exports() - compat_classes - {"Any", "Iterable", "Sequence", "overload"})
    return "from qlnb._qlnb import (\n" + "".join(
        f"    {name},\n" for name in names
    ) + ")"


def render_stub():
    current = COMPAT_STUB.read_text()
    generated = generated_aliases()
    current = current.replace(
        "from qlnb._qlnb import *  # noqa: F403", native_imports()
    )
    if BEGIN_MARKER in current or END_MARKER in current:
        if current.count(BEGIN_MARKER) != 1 or current.count(END_MARKER) != 1:
            raise ValueError("compat.pyi must contain one generated-section marker pair")
        begin = current.index(BEGIN_MARKER) + len(BEGIN_MARKER)
        end = current.index(END_MARKER, begin)
        return current[:begin] + "\n\n" + generated + "\n\n" + current[end:]

    start = current.index("class BarrierOption(")
    end = current.index("def __getattr__", start)
    section = f"{BEGIN_MARKER}\n\n{generated}\n\n{END_MARKER}\n\n"
    return current[:start] + section + current[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if compat.pyi is stale")
    parser.add_argument("--output", type=Path, help="write generated stub to this path")
    args = parser.parse_args()
    if args.check and args.output:
        parser.error("--check and --output cannot be combined")

    try:
        rendered = render_stub()
    except (KeyError, OSError, SyntaxError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    if args.check:
        if COMPAT_STUB.read_text() != rendered:
            print("compat.pyi is stale; run tools/generate_compat_stub.py", file=sys.stderr)
            return 1
        print("compat.pyi is up to date")
        return 0

    output = args.output or COMPAT_STUB
    output.write_text(rendered)
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
