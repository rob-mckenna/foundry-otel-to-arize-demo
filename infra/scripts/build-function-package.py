"""Build an immutable durable-bridge Function ZIP from git and approved Linux dependencies."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[2]
PREFIX = "src/telemetry-pipeline/"
RUNTIME_MODULES = {
    "__init__.py", "envelope.py", "mapping.py", "source_policy.py",
    "durable.py", "durable_store.py", "durable_runtime.py", "strict_sender.py",
    "function_app.py",
}


def source_members(head):
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ValueError("source-head must be the finalized full lowercase commit SHA")
    archive = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
         "archive", "--format=zip", head, "--", PREFIX],
        cwd=ROOT, capture_output=True, check=True, timeout=60,
    ).stdout
    members = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        for name in source.namelist():
            relative = name.removeprefix(PREFIX)
            if name.startswith(PREFIX) and (
                relative in {"function_app.py", "host.json", "requirements.txt"}
                or (relative.startswith("telemetry_pipeline/") and relative.endswith(".py"))
            ):
                members[relative] = source.read(name)
    expected = {"function_app.py", "host.json", "requirements.txt"} | {
        "telemetry_pipeline/" + name for name in RUNTIME_MODULES
    }
    if set(members) != expected:
        raise ValueError("commit must contain exactly the durable Function runtime and source-isolation policy")
    tree = ast.parse(members["telemetry_pipeline/function_app.py"])
    names = [
        keyword.value.value
        for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for decorator in node.decorator_list
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr == "function_name"
        for keyword in decorator.keywords
        if keyword.arg == "name" and isinstance(keyword.value, ast.Constant)
    ]
    if sorted(names) != ["DurableGenAIOutbox", "TelemetryTransform"]:
        raise ValueError("commit must register exactly TelemetryTransform and DurableGenAIOutbox")
    return members


def local_path(value):
    path = Path(value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("build inputs and outputs must stay inside this worktree")
    return path


def write_package(head, dependencies, output):
    dependencies, output = local_path(dependencies), local_path(output)
    if not dependencies.is_dir() or output.is_relative_to(dependencies):
        raise ValueError("use an existing approved dependency tree and a separate output path")
    if output.exists() or output.with_suffix(".receipt.json").exists():
        raise ValueError("immutable output already exists; do not overwrite release evidence")
    members = source_members(head)
    source_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(members.items())}
    dependency_hashes = {}
    for file in sorted(dependencies.rglob("*")):
        if file.is_symlink() or not file.resolve().is_relative_to(dependencies):
            raise ValueError("dependency symlinks/external paths are not allowed")
        if not file.is_file():
            continue
        name = file.relative_to(dependencies).as_posix()
        if file.suffix.lower() in {".pyd", ".dll", ".exe"} or any(
            p == ".env" or p.startswith(".env.") for p in file.relative_to(dependencies).parts
        ):
            raise ValueError("Windows binaries or secret configuration in dependency tree")
        if "__pycache__" in file.parts or file.suffix == ".pyc":
            continue
        data = file.read_bytes()
        members[f".python_packages/lib/site-packages/{name}"] = data
        dependency_hashes[name] = hashlib.sha256(data).hexdigest()
    if not dependency_hashes:
        raise ValueError("dependency tree is empty")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for name, data in sorted(members.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            package.writestr(entry, data)
    with zipfile.ZipFile(output) as package:
        for name, data in members.items():
            if package.read(name) != data:
                raise ValueError("package byte parity failed")
    receipt = {
        "sourceHead": head,
        "sourceSha256": source_hashes,
        "dependencySha256": dependency_hashes,
        "packageSha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "memberCount": len(members),
    }
    output.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--dependencies", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = write_package(args.source_head, args.dependencies, args.output)
    print(json.dumps({key: receipt[key] for key in ("sourceHead", "packageSha256", "memberCount")}))


if __name__ == "__main__":
    main()
