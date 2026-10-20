"""Vet the explicitly approved #143 dependency bytes; never reuse its source."""
import base64
import csv
from email.parser import BytesParser
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys
import zipfile

from pip._vendor.packaging.markers import default_environment
from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.tags import compatible_tags, cpython_tags, parse_tag
from pip._vendor.packaging.utils import canonicalize_name
from pip._vendor.packaging.version import Version

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[1]
ARCHIVE = REPO / ".azure-sandbox/issue143-f650fed-built.zip"
EXPECTED = "c1a276b62af37da8810c0c120b9cbe8cdff913fc76f43e51399f50db61d540f7"
PREFIX = ".python_packages/lib/site-packages/"
STAGE = ROOT / ".release/dependencies"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    require(sys.version_info[:2] == (3, 11), "validator must run on Python 3.11")
    require(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == EXPECTED, "archive SHA mismatch")
    require(not STAGE.exists(), "immutable staging directory already exists")
    platforms = ["manylinux_2_28_x86_64", "manylinux_2_17_x86_64", "manylinux2014_x86_64"]
    tags = set(cpython_tags((3, 11), platforms=platforms))
    tags.update(compatible_tags((3, 11), interpreter="cp311", platforms=platforms))
    members = {}
    with zipfile.ZipFile(ARCHIVE) as archive:
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            require(not path.is_absolute() and ".." not in path.parts
                    and "\\" not in info.filename and ":" not in info.filename,
                    "unsafe archive path")
            mode = info.external_attr >> 16
            require(not stat.S_ISLNK(mode), "archive symlink")
            if not info.filename.startswith(PREFIX) or info.is_dir():
                continue
            name = info.filename[len(PREFIX):]
            require(name not in members, "duplicate dependency path")
            require(not any(p == ".env" or p.startswith(".env.") for p in path.parts),
                    "configuration member")
            require(name not in {"local.settings.json", "host.json", "function_app.py"}
                    and not name.startswith("telemetry_pipeline/"), "old source/config member")
            require(path.suffix.lower() not in {".pyd", ".dll", ".exe"}, "Windows binary")
            members[name] = archive.read(info)
    records = [n for n in members if n.endswith(".dist-info/RECORD")]
    require(records, "no wheel records")
    covered = set()
    distributions = {}
    dependencies = {}
    wheels = {}
    unhashed = []
    for record in records:
        directory = record.rsplit("/", 1)[0]
        metadata = BytesParser().parsebytes(members[directory + "/METADATA"])
        name = canonicalize_name(metadata["Name"])
        require(name not in distributions, "duplicate distribution")
        version = Version(metadata["Version"])
        distributions[name] = str(version)
        python = metadata.get("Requires-Python")
        if python:
            from pip._vendor.packaging.specifiers import SpecifierSet
            require(Version("3.11.9") in SpecifierSet(python), "Requires-Python mismatch: " + name)
        dependencies[name] = metadata.get_all("Requires-Dist", [])
        wheel = BytesParser().parsebytes(members[directory + "/WHEEL"])
        wheel_tags = set()
        for tag in wheel.get_all("Tag", []):
            wheel_tags.update(parse_tag(tag))
        require(bool(tags & wheel_tags), "incompatible wheel: " + name)
        wheels[name] = sorted(str(t) for t in wheel_tags)
        for entry, digest, size in csv.reader(io.StringIO(members[record].decode())):
            p = PurePosixPath(entry)
            if ".." in p.parts:
                # Oryx relocates pip console scripts into site-packages/bin.
                # Verify their RECORD hashes too, but do not deploy CLI launchers.
                require(entry.startswith(("../../bin/", "../../../bin/")), "unsafe RECORD path")
                entry = "bin/" + p.name
            require(entry in members, "missing RECORD member: " + entry)
            covered.add(entry)
            if digest:
                algorithm, expected = digest.split("=", 1)
                require(algorithm == "sha256", "unexpected RECORD algorithm")
                actual = base64.urlsafe_b64encode(hashlib.sha256(members[entry]).digest()).rstrip(b"=").decode()
                require(actual == expected and len(members[entry]) == int(size),
                        "RECORD mismatch: " + entry)
            else:
                require(entry == record or entry.endswith(".pyc"), "unhashed dependency code")
                unhashed.append(entry)
    require(set(members) <= covered, "unowned dependency files: " + repr(sorted(set(members) - covered)[:20]))
    environment = default_environment()
    environment.update(python_version="3.11", python_full_version="3.11.9",
                       sys_platform="linux", platform_system="Linux",
                       platform_machine="x86_64", os_name="posix", extra="")
    pending = [line for line in (ROOT / "src/telemetry-pipeline/requirements.txt").read_text().splitlines()
               if line.strip() and not line.lstrip().startswith("#")]
    checked = set()
    while pending:
        raw = pending.pop()
        requirement = Requirement(raw)
        if requirement.marker and not requirement.marker.evaluate(environment):
            continue
        name = canonicalize_name(requirement.name)
        require(name in distributions, "missing dependency: " + name)
        require(Version(distributions[name]) in requirement.specifier, "dependency version mismatch: " + raw)
        contexts = {""} | set(requirement.extras)
        for extra in contexts:
            if (name, extra) in checked:
                continue
            checked.add((name, extra))
            env = dict(environment, extra=extra)
            for child in dependencies[name]:
                parsed = Requirement(child)
                if not parsed.marker or parsed.marker.evaluate(env):
                    pending.append(str(parsed).split(";")[0])
    native = {}
    for name, data in members.items():
        if name.endswith(".so"):
            require(data[:6] == b"\x7fELF\x02\x01" and struct.unpack_from("<H", data, 18)[0] == 62,
                    "not ELF64 little-endian x86_64: " + name)
            glibc = sorted(set(m.decode() for m in re.findall(rb"GLIBC_[0-9]+\.[0-9]+", data)))
            require(all(tuple(map(int, v[6:].split("."))) <= (2, 28) for v in glibc),
                    "GLIBC requirement exceeds manylinux_2_28: " + name)
            native[name] = {"elf": "ELF64 x86_64", "glibcSymbols": glibc}
    inventory = {}
    for name, data in sorted(members.items()):
        if name.startswith("bin/") or "__pycache__" in PurePosixPath(name).parts or name.endswith(".pyc"):
            continue
        destination = STAGE / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        inventory[name] = hashlib.sha256(data).hexdigest()
    receipt = {
        "archiveSha256": EXPECTED, "distributionVersions": distributions,
        "wheelTags": wheels, "nativeEvidence": native, "recordCount": len(records),
        "recordUnhashedMetadataOrBytecode": len(unhashed),
        "dependencyFileCount": len(inventory), "dependencySha256": inventory,
        "closureContextsChecked": len(checked),
        "compatibilityLimit": "Static wheel/ELF/GLIBC evidence, not a Linux import/runtime acceptance test.",
    }
    (ROOT / ".release/dependency-vetting.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in
                      ("archiveSha256", "recordCount", "dependencyFileCount", "closureContextsChecked")}))


if __name__ == "__main__":
    main()
