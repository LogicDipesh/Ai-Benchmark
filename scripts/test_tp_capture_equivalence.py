"""Equivalence regression for TP observational capture (2026-11-02, run 31).

MANDATORY before run 31 (approved acceptance conditions):
  1. Capture enabled and disabled produce identical scores.
  2. Status and error classification remain identical.
  3. Truncated and non-truncated provider responses are covered.
  4. Recorded judge responses produce identical parsed scores.
  5. Artifact contents match the original prompt, response, metadata
     and judge output.
  6. The correct engine-supplied run ID is attached.
  7. Missing provider metadata remains NULL (never inferred).
  8. Artifact-write failure does not affect the benchmark result.
Plus: a deliberately failing artifact write leaves the TP evaluation
outcome exactly unchanged.

Method: saved-input fixtures only — no live provider or judge calls.
The provider transport and the judge transport are stubbed; every
other line executed is the real shipped code (real TP evaluator,
real tp_artifacts writer, real engine helper). "Disabled" means the
evaluator runs and its tp_capture key is ignored, exactly as the old
engine did; "enabled" means the same result also flows through the
engine's artifact writer. Run from the project root:
    python test_tp_capture_equivalence.py
"""

import contextlib
import io
import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import requests

import aibenchmark.categories.thinking_planning as tp_mod
import aibenchmark.tp_artifacts as tp_art
from aibenchmark.categories.thinking_planning import evaluate_thinking_planning
from aibenchmark.engine import _maybe_write_tp_artifact

PROBLEM = {
    "id": "plan_001_test",
    "prompt": "PLAN PROMPT: design a rate limiter in Python.",
    "judge_rubric": "RUBRIC: clarity, correctness, completeness.",
}

PLAN_FULL = "## Plan\n1. Token bucket.\n2. Per-user counters.\n3. Tests."
PLAN_CUT = "## Plan\n1. Token bucket.\n2. Per-user cou"


class FakeResp:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(
                f"{self.status_code} error", response=self)


def judge_payload(raw, finish="stop", usage=None):
    payload = {"choices": [{"message": {"content": raw},
                             "finish_reason": finish}]}
    if usage is not None:
        payload["usage"] = usage
    return payload


def stub_provider(result):
    mod = SimpleNamespace()

    def run_prompt(model, prompt, max_tokens=None, timeout=None):
        assert prompt == PROBLEM["prompt"], "prompt must be preserved exactly"
        assert max_tokens == 4096, "TP cap must stay 4096"
        return result

    mod.run_prompt = run_prompt
    return mod


def provider_result(response, success=True, error_type=None, truncated=False,
                    finish=None, usage=None, legacy=False):
    kw = dict(response=response, success=success, latency_ms=1234,
              error_type=error_type, truncated=truncated)
    if not legacy:
        kw["finish_reason"] = finish
        kw["usage"] = usage
    return SimpleNamespace(**kw)


class TpCaptureEquivalenceTests(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
        self._env.start()
        self._orig_providers = tp_mod.PROVIDERS
        self._orig_interval = tp_mod._JUDGE_MIN_INTERVAL_S
        tp_mod._JUDGE_MIN_INTERVAL_S = 0
        tp_mod._JUDGE_LAST_TIME = 0.0
        self._tmp = tempfile.TemporaryDirectory()
        self._dir_patch = mock.patch.object(tp_art, "ARTIFACTS_DIR", self._tmp.name)
        self._dir_patch.start()
        self.addCleanup(self._tmp.cleanup)

    def tearDown(self):
        self._dir_patch.stop()
        tp_mod.PROVIDERS = self._orig_providers
        tp_mod._JUDGE_MIN_INTERVAL_S = self._orig_interval
        self._env.stop()

    def _run_case(self, provider_res, judge_post):
        """Returns (off_triple, on_result, artifact_or_None)."""
        tp_mod.PROVIDERS = {"stub": {"module": stub_provider(provider_res)}}
        with mock.patch.object(tp_mod.requests, "post", side_effect=judge_post):
            off = evaluate_thinking_planning(PROBLEM, "stub", "stub-model")
        off_triple = (off["score"], off["status"], off["error_type"])
        tp_mod.PROVIDERS = {"stub": {"module": stub_provider(provider_res)}}
        tp_mod._JUDGE_LAST_TIME = 0.0
        with mock.patch.object(tp_mod.requests, "post", side_effect=judge_post):
            on = evaluate_thinking_planning(PROBLEM, "stub", "stub-model")
        on_triple = (on["score"], on["status"], on["error_type"])
        self.assertEqual(off_triple, on_triple,
                         "capture on/off must give identical score/status/error")
        self.assertIn("tp_capture", on, "evaluator must return a capture dict")
        with contextlib.redirect_stderr(io.StringIO()):
            _maybe_write_tp_artifact(999, on)
        files = sorted(os.listdir(self._tmp.name))
        artifact = None
        if files:
            self.assertEqual(len(files), 1, "exactly one artifact per case")
            with open(os.path.join(self._tmp.name, files[0])) as fh:
                artifact = json.load(fh)
            self.assertIn("__run999__", files[0],
                          "artifact filename must carry the engine run ID")
        return off_triple, on, artifact

    @staticmethod
    def _judge_ok(raw, finish="stop", usage=None):
        def post(url, headers=None, json=None, timeout=None):
            return FakeResp(200, judge_payload(raw, finish, usage))
        return post

    def test_non_truncated_full_metadata(self):
        usage = {"prompt_tokens": 141, "completion_tokens": 500, "total_tokens": 641}
        judge_raw = '```json\n{"score": 0.8}\n```'
        pres = provider_result(PLAN_FULL, finish="stop", usage=usage)
        triple, on, art = self._run_case(
            pres, self._judge_ok(judge_raw, usage={"prompt_tokens": 10,
                                                   "completion_tokens": 20,
                                                   "total_tokens": 30}))
        self.assertEqual(triple, (0.8, "passed", None))
        self.assertEqual(art["run_id"], 999)
        self.assertEqual(art["problem_id"], "plan_001_test")
        self.assertEqual(art["provider"], "stub")
        self.assertEqual(art["model"], "stub-model")
        self.assertEqual(art["prompt"], PROBLEM["prompt"])
        self.assertEqual(art["response"], PLAN_FULL)
        self.assertEqual(art["finish_reason"], "stop")
        self.assertEqual(art["truncated"], False)
        self.assertEqual(art["usage"], usage)
        self.assertEqual(art["judge"]["raw"], judge_raw)
        self.assertEqual(art["judge"]["score"], 0.8)
        self.assertEqual(art["judge"]["finish_reason"], "stop")
        self.assertEqual(art["judge"]["usage"],
                         {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30})

    def test_truncated_response(self):
        usage = {"prompt_tokens": 141, "completion_tokens": 4096,
                 "total_tokens": 4237,
                 "completion_tokens_details": {"reasoning_tokens": 3900}}
        pres = provider_result(PLAN_CUT, truncated=True, finish="length", usage=usage)
        triple, on, art = self._run_case(pres, self._judge_ok("0.6"))
        self.assertEqual(triple, (0.6, "passed", "truncated_at_cap"))
        self.assertEqual(art["response"], PLAN_CUT)
        self.assertEqual(art["finish_reason"], "length")
        self.assertEqual(art["truncated"], True)
        self.assertEqual(art["usage"], usage)
        self.assertEqual(art["judge"]["raw"], "0.6")
        self.assertEqual(art["judge"]["score"], 0.6)

    def test_missing_metadata_stays_null(self):
        # Usage present but WITHOUT total_tokens: the artifact must
        # not invent it by summing prompt + completion.
        usage = {"prompt_tokens": 100, "completion_tokens": 200}
        pres = provider_result(PLAN_FULL, finish=None, usage=usage)
        triple, on, art = self._run_case(
            pres, self._judge_ok('```json\n{"score": 1.0}\n```'))
        self.assertEqual(triple, (1.0, "passed", None))
        self.assertIsNone(art["finish_reason"])
        self.assertEqual(art["usage"], usage)
        self.assertNotIn("total_tokens", art["usage"])

    def test_judge_unparseable_preserves_raw(self):
        prose = "This plan is quite good overall, no number attached."
        pres = provider_result(PLAN_FULL, finish="stop", usage=None)
        triple, on, art = self._run_case(pres, self._judge_ok(prose))
        self.assertEqual(triple[0], 0.0)
        self.assertEqual(triple[1], "failed")
        self.assertTrue(triple[2].startswith("judge_error"))
        self.assertEqual(art["judge"]["raw"], prose)
        self.assertIsNone(art["judge"]["score"])

    def test_judge_429_fail_fast(self):
        def post(url, headers=None, json=None, timeout=None):
            return FakeResp(429, text="quota exceeded for today")
        pres = provider_result(PLAN_FULL, finish="stop", usage=None)
        triple, on, art = self._run_case(pres, post)
        self.assertEqual(triple[0], 0.0)
        self.assertTrue(triple[2].startswith("judge_error"))
        self.assertIn("429", triple[2])
        self.assertIsNone(art["judge"]["raw"])
        self.assertIsNone(art["judge"]["score"])

    def test_provider_failure_still_captured(self):
        pres = provider_result("", success=False, error_type="connection_error")
        triple, on, art = self._run_case(pres, self._judge_ok("0.9"))
        self.assertEqual(triple, (0.0, "failed", "connection_error"))
        self.assertEqual(art["response"], "")
        self.assertIsNone(art["judge"])
        self.assertEqual(art["error_type"], "connection_error")

    def test_legacy_provider_result_shape(self):
        # A provider result without finish_reason/usage attributes
        # must capture NULLs, not crash and not invent values.
        pres = provider_result(PLAN_FULL, legacy=True)
        triple, on, art = self._run_case(
            pres, self._judge_ok('{"score": 0.9}'))
        self.assertEqual(triple, (0.9, "passed", None))
        self.assertIsNone(art["finish_reason"])
        self.assertIsNone(art["usage"])

    def test_artifact_write_failure_leaves_outcome_unchanged(self):
        usage = {"prompt_tokens": 141, "completion_tokens": 500, "total_tokens": 641}
        pres = provider_result(PLAN_FULL, finish="stop", usage=usage)
        tp_mod.PROVIDERS = {"stub": {"module": stub_provider(pres)}}
        with mock.patch.object(tp_mod.requests, "post",
                                side_effect=self._judge_ok('{"score": 0.8}')):
            result = evaluate_thinking_planning(PROBLEM, "stub", "stub-model")
        self.assertEqual((result["score"], result["status"], result["error_type"]),
                         (0.8, "passed", None))
        # Point the writer at an existing FILE instead of a directory:
        # makedirs fails, the writer returns None, nothing raises.
        blocker = os.path.join(self._tmp.name, "blocker")
        with open(blocker, "w") as fh:
            fh.write("not a directory")
        with mock.patch.object(tp_art, "ARTIFACTS_DIR", blocker):
            with contextlib.redirect_stderr(io.StringIO()):
                _maybe_write_tp_artifact(999, result)
        self.assertEqual((result["score"], result["status"], result["error_type"]),
                         (0.8, "passed", None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
