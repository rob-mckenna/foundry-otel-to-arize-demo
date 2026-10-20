"""Synthetic transport tests. Live receipt evidence is separate, never mocked."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import Mock, patch
import uuid

SPEC = importlib.util.spec_from_file_location("adapter", Path(__file__).with_name("issue147-validation-adapter.py"))
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


class OfficialValidationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.receipts = adapter.WORKTREE / ".azure" / ("adapter-unit-" + uuid.uuid4().hex)
        self.receipts.mkdir(parents=True)
        helper = self.receipts / "synthetic-helper.ps1"
        helper.write_text("# Synthetic unit-test transport fixture only", encoding="utf-8")
        compiled = self.receipts / "synthetic-template.json"
        compiled.write_text('{"resources": []}', encoding="utf-8")
        self.patches = [
            patch.object(adapter, "HELPER", helper),
            patch.object(adapter, "HELPER_HASH", adapter.sha(helper)),
            patch.object(adapter, "COMPILED", compiled),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        if self.receipts.exists():
            shutil.rmtree(self.receipts)

    def test_all_five_actual_recipe_checks_reach_cli_in_order_and_keep_exact_wrapper(self):
        requests = (["version"], ["account", "show"], ["bicep", "build"],
                    ["deployment", "sub", "validate"], ["deployment", "sub", "what-if"])
        responses = [
            {"azure-cli": "synthetic"},
            {"id": adapter.SUB, "state": "Enabled"},
            {},
            {"status": "Succeeded", "correlationId": "11111111-1111-1111-1111-111111111111", "errorCode": None},
            {"status": "Succeeded", "changes": [
                {"resourceId": "/subscriptions/synthetic/resourceGroups/synthetic", "changeType": "Create", "properties": "never persist"}]},
        ]
        calls = []
        for request, response, expected in zip(requests, responses, adapter.CHECKS):
            def runner(args, **kwargs):
                calls.append((args, kwargs))
                return subprocess.CompletedProcess(args, 0, json.dumps(response), "")
            result = adapter.run_check(adapter.identify(request), self.receipts, runner)
            self.assertEqual(result["check"], expected)
            self.assertEqual(result["exitCode"], 0)
        self.assertEqual(len(calls), 5)
        self.assertEqual([args[1:1 + len(request)] for (args, _), request in zip(calls, requests)], list(requests))
        for args, kwargs in calls:
            self.assertEqual(args[args.index("--subscription") + 1], adapter.SUB)
            self.assertEqual(kwargs["env"]["AZURE_CONFIG_DIR"], str(adapter.TEAM_ROOT / ".azure-config"))
            self.assertEqual(kwargs["env"]["AZURE_LOGGING_ENABLE_LOG_FILE"], "false")
        build_args = calls[2][0]
        self.assertEqual(build_args[build_args.index("--file") + 1], str(adapter.TEMPLATE))
        for args, _ in calls[3:]:
            self.assertEqual(args[args.index("--template-file") + 1], str(adapter.COMPILED))
            self.assertEqual(args[args.index("--validation-level") + 1], "Provider")
            self.assertNotIn("group", args)
            self.assertNotIn("--parameters", args)  # wrapper embeds unchanged profile
        whatif = calls[4][0]
        self.assertEqual(whatif[whatif.index("--result-format") + 1], "ResourceIdOnly")
        self.assertEqual(result["changeCounts"]["Create"], 1)
        self.assertNotIn("never persist", (self.receipts / "5-what-if.json").read_text())

    def test_no_mutation_or_skipping_checks_and_no_receipt_overwrite(self):
        for request in (["deployment", "sub", "create"], ["group", "create"],
                        ["provider", "register"], ["login"], ["account", "set"],
                        ["keyvault", "secret", "show"]):
            with self.assertRaises(ValueError):
                adapter.identify(request)
        runner = Mock(return_value=subprocess.CompletedProcess([], 1, "", "ERROR: AuthorizationFailed - denied"))
        adapter.run_check("cli", self.receipts, runner)
        for check in adapter.CHECKS:
            with self.assertRaises(ValueError):
                adapter.run_check(check, self.receipts, runner)
        self.assertEqual(runner.call_count, 1)

    def test_redactor_preserves_actual_null_string_diagnostic_and_codes(self):
        diagnostic = ("InvalidTemplate - Deployment template validation failed: The template resource keyVault "
                      "... Evaluation result of language expression [parameters('keyVaultName')] is type Null, expected type String.")
        raw = "ERROR: " + json.dumps({"error": {"code": "InvalidTemplate", "message": diagnostic,
             "properties": {"password": "synthetic-never-persist"},
             "details": [{"code": "InvalidTemplate", "message":
                         "token=EXAMPLE_SYNTHETIC password=synthetic-hidden AccountKey=EXAMPLE_SYNTHETIC; "
                         'password: "synthetic spaced credential" SharedAccessSignature=synthetic-hidden '
                         "https://synthetic.invalid/path?sig=synthetic-hidden "
                         "eyJsynthetic.eyJsynthetic.synthetic sk-syntheticcredential"}]}})
        safe = adapter.failure_diagnostic(raw)
        self.assertEqual(safe["errorCodes"], ["InvalidTemplate"])
        self.assertIn(diagnostic, safe["diagnostic"])
        for hidden in ("EXAMPLE_SYNTHETIC", "synthetic-hidden", "synthetic-never-persist", "synthetic spaced credential", "?sig=", "eyJsynthetic", "sk-syntheticcredential"):
            self.assertNotIn(hidden, json.dumps(safe))
        self.assertLessEqual(len(safe["diagnostic"]), 1600)
        plain = adapter.failure_diagnostic("ERROR: " + diagnostic)
        self.assertIn("InvalidTemplate", plain["errorCodes"])
        self.assertIn("type Null, expected type String", plain["diagnostic"])


if __name__ == "__main__":
    unittest.main()
