import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch
import uuid
import zipfile


SPEC = importlib.util.spec_from_file_location(
    "function_package", Path(__file__).with_name("build-function-package.py"))
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class FunctionPackageTests(unittest.TestCase):
    def setUp(self):
        self.path = builder.ROOT / ".release-tests" / uuid.uuid4().hex
        self.deps = self.path / "dependencies"
        self.deps.mkdir(parents=True)
        (self.deps / "synthetic_dependency.py").write_bytes(b"synthetic = True\r\n")

    def tearDown(self):
        shutil.rmtree(self.path)
        if not any(self.path.parent.iterdir()):
            self.path.parent.rmdir()

    @patch.object(builder, "source_members")
    def test_reproducible_package_keeps_exact_source_and_dependency_bytes(self, source):
        source.return_value = {"function_app.py": b"# synthetic\r\n", "host.json": b"{}\n"}
        first = builder.write_package("a" * 40, self.deps, self.path / "one.zip")
        second = builder.write_package("a" * 40, self.deps, self.path / "two.zip")
        self.assertEqual(first["packageSha256"], second["packageSha256"])
        with zipfile.ZipFile(self.path / "one.zip") as package:
            self.assertEqual(package.read("function_app.py"), b"# synthetic\r\n")
            self.assertEqual(package.read(".python_packages/lib/site-packages/synthetic_dependency.py"),
                             b"synthetic = True\r\n")
        with self.assertRaisesRegex(ValueError, "immutable"):
            builder.write_package("a" * 40, self.deps, self.path / "one.zip")

    @patch.object(builder, "source_members", return_value={"host.json": b"{}"})
    def test_dependency_rejects_windows_binary_and_escaping_output(self, source):
        (self.deps / "unsafe.pyd").write_bytes(b"synthetic")
        with self.assertRaisesRegex(ValueError, "Windows binaries"):
            builder.write_package("a" * 40, self.deps, self.path / "bad.zip")
        self.assertFalse((self.path / "bad.zip").exists())
        with self.assertRaisesRegex(ValueError, "inside this worktree"):
            builder.local_path(builder.ROOT.parent / "not-read")

    @patch.object(builder.subprocess, "run")
    def test_git_archive_uses_binary_bytes_and_requires_guard_source(self, run):
        files = {
            "function_app.py": b"# synthetic \xff\r\n",
            "host.json": b"{}\n",
            "requirements.txt": b"# approved synthetic dependency\n",
        }
        files.update({"telemetry_pipeline/" + name: b"# synthetic\n"
                      for name in builder.RUNTIME_MODULES})
        files["telemetry_pipeline/function_app.py"] = (
            b'@app.function_name(name="TelemetryTransform")\ndef transform(): pass\n'
            b'@app.function_name(name="DurableGenAIOutbox")\ndef outbox(): pass\n'
        )
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, data in files.items():
                archive.writestr(builder.PREFIX + name, data)
        run.return_value = subprocess.CompletedProcess([], 0, stdout=buffer.getvalue())
        self.assertEqual(builder.source_members("b" * 40), files)
        args, kwargs = run.call_args
        self.assertIn("core.autocrlf=false", args[0])
        self.assertIn("core.eol=lf", args[0])
        self.assertNotIn("text", kwargs)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(builder.PREFIX + "host.json", b"{}")
        run.return_value = subprocess.CompletedProcess([], 0, stdout=buffer.getvalue())
        with self.assertRaisesRegex(ValueError, "source-isolation policy"):
            builder.source_members("b" * 40)

    @patch.object(builder.subprocess, "run")
    def test_rejects_legacy_modules_and_extra_registered_functions(self, run):
        files = {
            "function_app.py": b"# synthetic\n", "host.json": b"{}\n",
            "requirements.txt": b"# synthetic\n",
            **{"telemetry_pipeline/" + name: b"# synthetic\n" for name in builder.RUNTIME_MODULES},
        }
        files["telemetry_pipeline/function_app.py"] = (
            b'@app.function_name(name="UnexpectedFunction")\ndef unexpected(): pass\n'
        )
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, "w") as archive:
                    for name, data in files.items():
                        archive.writestr(builder.PREFIX + name, data)
                    if legacy:
                        archive.writestr(builder.PREFIX + "telemetry_pipeline/batch.py", b"# obsolete\n")
                run.return_value = subprocess.CompletedProcess([], 0, stdout=buffer.getvalue())
                with self.assertRaisesRegex(ValueError, "exactly"):
                    builder.source_members("b" * 40)


if __name__ == "__main__":
    unittest.main()
