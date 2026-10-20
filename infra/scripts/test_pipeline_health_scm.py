"""Synthetic-only contracts: no network, bearer acquisition, or publication."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import urllib.error

SPEC = importlib.util.spec_from_file_location(
    "scm_helper", Path(__file__).with_name("pipeline-health-scm.py"))
SCM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCM)


class ScmHelperTests(unittest.TestCase):
    def test_paths_are_exact_get_allowlist(self):
        self.assertTrue(SCM.allowed_get(SCM.DEPLOYMENTS))
        self.assertTrue(SCM.allowed_get(SCM.SCM + "/api/vfs/site/wwwroot/function_app.py"))
        for suffix in ("/api/command", "/api/vfs/site/wwwroot/",
                       "/api/vfs/site/wwwroot/.env",
                       "/api/vfs/site/wwwroot/local.settings.json",
                       "/api/vfs/site/wwwroot/../.env", "/api/settings"):
            self.assertFalse(SCM.allowed_get(SCM.SCM + suffix))

    def test_no_post_without_explicit_gate(self):
        c = SCM.Channel("synthetic")
        c.opener = Mock()
        with self.assertRaisesRegex(SCM.SafeFailure, "ZipPostNotAuthorized"):
            c.request(SCM.SCM + "/api/zipdeploy?isAsync=true", "test", body=b"fake")
        c.opener.open.assert_not_called()
        with self.assertRaisesRegex(SCM.SafeFailure, "ZipPostNotAuthorized"):
            SCM.publish_once(c, False)

    def test_mismatched_zip_rejected_before_network(self):
        c = SCM.Channel("synthetic")
        c.opener = Mock()
        with self.assertRaisesRegex(SCM.SafeFailure, "ZipDigestMismatch"):
            c.request(SCM.SCM + "/api/zipdeploy?isAsync=true", "test",
                      body=b"fake", authorize_post=True)
        c.opener.open.assert_not_called()

    def test_http_failures_are_actionable_without_body_or_credentials(self):
        c = SCM.Channel("synthetic")
        c.opener = Mock()
        c.opener.open.side_effect = urllib.error.HTTPError(
            SCM.SCM, 403, "DO_NOT_EMIT", {}, io.BytesIO(b"private-body"))
        with self.assertRaises(SCM.SafeFailure) as caught:
            c.request(SCM.DEPLOYMENTS, "arm-deployments")
        value = str(caught.exception)
        self.assertIn("Forbidden", value)
        self.assertIn("403", value)
        self.assertNotIn("DO_NOT_EMIT", value)
        self.assertNotIn("private-body", value)
        self.assertNotIn("synthetic", value)

    def test_redirects_are_never_followed(self):
        self.assertIsNone(SCM.NoRedirect().redirect_request(None, None, 302, None, None, None))

    def test_cli_throttling_is_explicit_without_frontdoor_reference_dump(self):
        response = Mock(returncode=1, stderr="Too Many Requests (Ref A: sensitive-ref)", stdout="")
        with patch.object(SCM.subprocess, "run", return_value=response):
            with self.assertRaises(SCM.SafeFailure) as caught:
                SCM.bearer()
        self.assertEqual(caught.exception.safe["httpStatus"], 429)
        self.assertEqual(caught.exception.safe["code"], "TokenEndpointThrottled")
        self.assertNotIn("sensitive-ref", str(caught.exception))

    def test_baseline_candidate_is_exact_original_source(self):
        hashes = SCM.candidate("baseline")
        self.assertEqual(set(hashes), set(SCM.SOURCE_NAMES))
        self.assertNotIn("telemetry_pipeline/source_policy.py", hashes)

    def test_get_proof_binds_before_after_and_hashes(self):
        channel = Mock()
        identity = {"id": SCM.BASELINE_ID, "status": 4}
        source = {"function_app.py": SCM.digest(b"synthetic-code")}
        row = {"id": SCM.BASELINE_ID, "active": True, "complete": True, "status": 4}
        channel.request.side_effect = [
            (200, json.dumps(row).encode(), {}), (200, b"synthetic-code", {})]
        with patch.object(SCM, "candidate", return_value=source), \
                patch.object(SCM, "active", side_effect=[identity, identity]):
            result = SCM.proof(channel, "baseline")
        self.assertTrue(result["allSourceBytesMatch"])
        self.assertEqual(result["postCount"], 0)
        self.assertNotIn("synthetic-code", json.dumps(result))

    def test_deployment_change_invalidates_binding(self):
        channel = Mock()
        row = {"id": SCM.BASELINE_ID, "active": True, "complete": True, "status": 4}
        channel.request.return_value = (200, json.dumps(row).encode(), {})
        with patch.object(SCM, "candidate", return_value={}), \
                patch.object(SCM, "active", side_effect=[
                    {"id": SCM.BASELINE_ID}, {"id": "different"}]):
            with self.assertRaisesRegex(SCM.SafeFailure, "DeploymentChangedDuringReadback"):
                SCM.proof(channel, "baseline")

    def test_missing_allowlisted_file_is_recorded_without_discovery(self):
        channel = Mock()
        identity = {"id": SCM.BASELINE_ID, "status": 4}
        row = {"id": SCM.BASELINE_ID, "active": True, "complete": True, "status": 4}
        channel.request.side_effect = [
            (200, json.dumps(row).encode(), {}),
            SCM.SafeFailure("vfs:function_app.py", "NotFound", httpStatus=404)]
        with patch.object(SCM, "candidate", return_value={"function_app.py": "expected"}), \
                patch.object(SCM, "active", side_effect=[identity, identity]):
            result = SCM.proof(channel, "baseline")
        self.assertFalse(result["allSourceBytesMatch"])
        self.assertEqual(result["fileFailures"]["function_app.py"]["httpStatus"], 404)
        self.assertEqual(channel.request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
