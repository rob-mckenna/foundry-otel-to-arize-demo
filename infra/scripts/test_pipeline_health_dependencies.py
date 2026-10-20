"""Synthetic-only archive staging safety contracts."""
import base64
import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location(
    "dependency_stage", Path(__file__).with_name("stage-pipeline-health-dependencies.py"))
STAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STAGER)


class DependencyStagingTests(unittest.TestCase):
    def fixture(self, root, tag="py3-none-any", extra=None, corrupt=False):
        files = {
            "example/__init__.py": b"",
            "example-1.0.dist-info/METADATA": b"Name: example\nVersion: 1.0\nRequires-Python: >=3.8\n",
            "example-1.0.dist-info/WHEEL": ("Wheel-Version: 1.0\nTag: " + tag + "\n").encode(),
        }
        rows = []
        for name, data in files.items():
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            rows.append(f"{name},sha256={digest},{len(data)}")
        record = "example-1.0.dist-info/RECORD"
        files[record] = ("\n".join(rows) + f"\n{record},,\n").encode()
        if corrupt:
            files["example/__init__.py"] = b"changed"
        archive = root / "input.zip"
        with zipfile.ZipFile(archive, "w") as z:
            for name, data in files.items():
                z.writestr(STAGER.PREFIX + name, data)
            z.writestr("function_app.py", b"OLD SOURCE NEVER STAGED")
            if extra:
                z.writestr(extra, b"bad")
        req = root / "src/telemetry-pipeline/requirements.txt"
        req.parent.mkdir(parents=True)
        req.write_text("example>=1.0\n")
        return archive

    def execute(self, *, tag="py3-none-any", extra=None, corrupt=False, missing=False):
        # Generated synthetic test files are worktree-contained.
        parent = STAGER.ROOT / ".release"
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            root = Path(directory)
            archive = self.fixture(root, tag, extra, corrupt)
            if missing:
                (root / "src/telemetry-pipeline/requirements.txt").write_text("missing>=1\n")
            with patch.multiple(STAGER, ROOT=root, ARCHIVE=archive,
                                EXPECTED=hashlib.sha256(archive.read_bytes()).hexdigest(),
                                STAGE=root / ".release/dependencies"):
                with contextlib.redirect_stdout(io.StringIO()):
                    STAGER.main()
                self.assertTrue((STAGER.STAGE / "example/__init__.py").exists())
                self.assertFalse((STAGER.STAGE / "function_app.py").exists())

    def test_only_vetted_dependencies_staged(self):
        self.execute()

    def test_record_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "RECORD mismatch"):
            self.execute(corrupt=True)

    def test_windows_wheel_rejected(self):
        with self.assertRaisesRegex(ValueError, "incompatible wheel"):
            self.execute(tag="cp311-cp311-win_amd64")

    def test_traversal_rejected_even_outside_selected_tree(self):
        with self.assertRaisesRegex(ValueError, "unsafe archive path"):
            self.execute(extra="../escape")

    def test_missing_closure_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing dependency"):
            self.execute(missing=True)


if __name__ == "__main__":
    unittest.main()
