"""GUI v1.7 display-only regression tests (v1.4 suite carried forward + evidence display).

Run from the AI-Benchmark project root:
    python -m unittest discover -s tests -v

The Flask integration tests require the project's normal dependencies and
aibenchmark package to be importable from the project root.
"""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class MethodologyDefinitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "methodology.json").read_text(encoding="utf-8"))

    def test_all_seven_sections_exist(self):
        self.assertEqual(len(self.data["sections"]), 7)
        self.assertEqual(
            [s["id"] for s in self.data["sections"]],
            ["problem-scores", "category-means", "capability-reliability",
             "selection", "latency-failures", "limitations", "not-stored"]
        )

    def test_run23_uses_task_weighted_blended_score(self):
        text = " ".join(
            b["text"] for section in self.data["sections"]
            for b in section["blocks"]
        )
        self.assertIn("2.667 ÷ 10 = 0.267", text)
        self.assertIn("displayed as 0.27", text)
        self.assertIn("incorrect", text)
        self.assertIn("0.29", text)

    def test_historical_baselines_are_separate(self):
        text = " ".join(
            b["text"] for section in self.data["sections"]
            for b in section["blocks"]
        )
        self.assertIn("Run 22", text)
        self.assertIn("Run 24", text)
        self.assertIn("Run 23 itself used 4096-token caps", text)

    def test_run26_groq_example_is_present(self):
        section = next(s for s in self.data["sections"] if s["id"] == "capability-reliability")
        text = " ".join(b["text"] for b in section["blocks"])
        self.assertIn("13 passing reference checks and one failing assertion", text)
        self.assertIn("False == 0", text)
        self.assertIn("100%", text)
        self.assertIn("0.50", text)

    def test_missing_data_is_disclosed(self):
        section = next(s for s in self.data["sections"] if s["id"] == "not-stored")
        text = " ".join(b["text"] for b in section["blocks"]).lower()
        for term in ("per-test pass counts", "token counts", "per-attempt"):
            self.assertIn(term, text)

    def test_dashboard_legends_are_in_shared_definition_file(self):
        self.assertEqual(
            set(self.data["dashboard_legends"]),
            {"score", "capability", "latency", "evidence"}
        )
        dashboard = (ROOT / "templates" / "dashboard.html").read_text()
        self.assertIn("methodology.dashboard_legends.score", dashboard)
        self.assertIn("methodology.dashboard_legends.capability", dashboard)
        self.assertIn("methodology.dashboard_legends.latency", dashboard)
        self.assertIn("methodology.dashboard_legends.evidence", dashboard)

    def test_failure_count_is_complement_of_report_classifier(self):
        source = (ROOT / "app.py").read_text()
        self.assertIn("return not _is_valid_evaluation(error_type)", source)
        self.assertNotIn("def is_infra", source)
        self.assertNotIn("HTTPError", source)

    def test_evidence_browser_is_read_only_and_timestamp_limited(self):
        source = (ROOT / "app.py").read_text()
        self.assertIn('@app.route("/evidence")', source)
        self.assertIn('delta <= 24 * 60 * 60', source)
        self.assertIn('path.read_text(encoding="utf-8", errors="replace")', source)
        self.assertNotIn('write_text(', source)

    def test_failure_breakdown_uses_report_classifier(self):
        source = (ROOT / "app.py").read_text()
        self.assertIn('"reference_gate": 0', source)
        self.assertIn('"execution_error": 0', source)
        self.assertIn('"truncation": 0', source)
        self.assertIn('if not _is_valid_evaluation(row.error_type)', source)


    def test_evidence_section_distinguishes_legacy_from_instrumented(self):
        section = next(s for s in self.data["sections"] if s["id"] == "not-stored")
        text = " ".join(b["text"] for b in section["blocks"])
        self.assertIn("runs 1-26", text)
        self.assertIn("not recorded", text)
        self.assertIn("not measured", text)
        self.assertIn("never zero", text)

try:
    import flask  # noqa: F401
    import app as gui_app
    FLASK_AVAILABLE = True
except Exception:
    FLASK_AVAILABLE = False


@unittest.skipUnless(FLASK_AVAILABLE, "Flask and project package dependencies required")
class FlaskIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = gui_app.app.test_client()

    def test_methodology_route_renders_all_sections(self):
        response = self.client.get("/methodology")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("How scores work", body)
        self.assertIn("What this dashboard cannot show", body)

    def test_sidebar_and_footer_link_methodology(self):
        response = self.client.get("/methodology")
        body = response.get_data(as_text=True)
        self.assertIn('href="/methodology"', body)
        self.assertIn("GUI 1.7", body)

    def test_request_failure_count_uses_report_classifier(self):
        rows = [
            SimpleNamespace(provider="groq", category="coding", model="m",
                             score=1.0, latency_ms=10, error_type="valid"),
            SimpleNamespace(provider="groq", category="coding", model="m",
                             score=0.0, latency_ms=20, error_type="connection_error"),
            SimpleNamespace(provider="groq", category="coding", model="m",
                             score=0.0, latency_ms=30, error_type="judge_error"),
            SimpleNamespace(provider="groq", category="coding", model="m",
                             score=0.0, latency_ms=40, error_type="sandbox_timeout"),
        ]
        with patch.object(gui_app, "_is_valid_evaluation",
                          side_effect=lambda e: e in ("valid", "sandbox_timeout")), \
             patch.object(gui_app, "get_runs",
                          return_value=[SimpleNamespace(id=999, timestamp="2026-10-31", notes="test")]), \
             patch.object(gui_app, "get_results_for_run", return_value=rows):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("2 request failures", body)
        self.assertIn("Request failures", body)

    def test_evidence_browser_empty_state(self):
        with patch.object(gui_app, "FAILURE_ARTIFACTS_DIR", ROOT / "missing_artifacts"):
            response = self.client.get("/evidence")
        self.assertEqual(response.status_code, 200)
        self.assertIn("No matching failure artifacts", response.get_data(as_text=True))

    def test_failure_breakdown_counts_categories(self):
        rows = [
            SimpleNamespace(provider="groq", category="testing", error_type="reference_impl_failed"),
            SimpleNamespace(provider="groq", category="testing", error_type="execution_error"),
            SimpleNamespace(provider="groq", category="testing", error_type="truncated_at_cap"),
            SimpleNamespace(provider="groq", category="testing", error_type="connection_error"),
        ]
        with patch.object(gui_app, "_is_valid_evaluation",
                          side_effect=lambda e: e in ("reference_impl_failed", "execution_error", "truncated_at_cap")):
            result = gui_app.failure_class_breakdown(rows)
        self.assertEqual(result["testing"], {
            "reference_gate": 1, "execution_error": 1, "truncation": 1,
            "request_failure": 1, "other_valid_output": 0,
        })
        self.assertEqual(result["coding"]["request_failure"], 0)

    def test_failure_breakdown_splits_truncation_suffix(self):
        # A combined stored value counts in BOTH its base class and
        # truncation; it must not vanish into "other" or hide the base
        # failure. Standalone values are unchanged.
        rows = [
            SimpleNamespace(provider="groq", category="coding", error_type="execution_error"),
            SimpleNamespace(provider="groq", category="coding", error_type="execution_error; truncated_at_cap"),
            SimpleNamespace(provider="groq", category="coding", error_type="truncated_at_cap"),
            SimpleNamespace(provider="groq", category="coding", error_type="sandbox_timeout"),
        ]
        with patch.object(gui_app, "_is_valid_evaluation", return_value=True):
            result = gui_app.failure_class_breakdown(rows)
        self.assertEqual(result["coding"], {
            "reference_gate": 0, "execution_error": 2, "truncation": 2,
            "request_failure": 0, "other_valid_output": 1,
        })

    def test_dashboard_uses_shared_definitions_for_legends(self):
        with patch.object(gui_app, "get_runs", return_value=[]):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # Empty state remains truthful; methodology stays accessible from nav.
        self.assertIn("Dashboard", response.get_data(as_text=True))




class EvidenceDisplayTests(unittest.TestCase):
    @unittest.skipUnless(FLASK_AVAILABLE, "Flask and project package dependencies required")
    def test_none_is_not_recorded_never_zero(self):
        self.assertEqual(gui_app.evidence_display(None),
                         {"text": "not recorded", "state": "not_recorded"})

    @unittest.skipUnless(FLASK_AVAILABLE, "Flask and project package dependencies required")
    def test_direct_clean_and_partial(self):
        self.assertEqual(
            gui_app.evidence_display({"passed": 3, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 3})["text"],
            "3 of 3 passed")
        self.assertEqual(
            gui_app.evidence_display({"passed": 2, "failed": 1, "skipped": 0,
                                      "errors": 0, "collected": 3})["text"],
            "2 of 3 passed (1 failed)")
        self.assertEqual(
            gui_app.evidence_display({"passed": 2, "failed": 0, "skipped": 1,
                                      "errors": 0, "collected": 3})["text"],
            "2 of 3 passed (1 skipped)")

    @unittest.skipUnless(FLASK_AVAILABLE, "Flask and project package dependencies required")
    def test_gate_failed_kills_not_measured_never_zero(self):
        ev = {"gate_outcome": "failed",
              "gate": {"passed": 3, "failed": 1, "skipped": 0, "errors": 0,
                       "collected": 4},
              "mutants_killed": None, "mutants_total": 2, "mutants": {}}
        text = gui_app.evidence_display(ev)["text"]
        self.assertIn("kills not measured", text)
        self.assertNotIn("killed 0", text)

    @unittest.skipUnless(FLASK_AVAILABLE, "Flask and project package dependencies required")
    def test_gate_passed_shows_kills_and_no_tests_case(self):
        ev = {"gate_outcome": "passed",
              "gate": {"passed": 3, "failed": 0, "skipped": 0, "errors": 0,
                       "collected": 3},
              "mutants_killed": 2, "mutants_total": 2, "mutants": {}}
        self.assertIn("killed 2/2", gui_app.evidence_display(ev)["text"])
        ev = {"gate_outcome": "not_run",
              "gate": {"passed": 0, "failed": 0, "skipped": 0, "errors": 0,
                       "collected": 0},
              "mutants_killed": None, "mutants_total": 2, "mutants": {}}
        self.assertIn("gate: no tests", gui_app.evidence_display(ev)["text"])


@unittest.skipUnless(FLASK_AVAILABLE, "Flask and project package dependencies required")
class EvidenceRenderTests(unittest.TestCase):
    def setUp(self):
        self.client = gui_app.app.test_client()
        self.run = SimpleNamespace(id=27, timestamp="2026-10-31T00:00:00+00:00",
                                   notes="evidence run")

    def _rows(self):
        return [
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_001", score=1.0, latency_ms=10,
                            status="passed", error_type=None,
                            evidence={"passed": 3, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 3}),
            SimpleNamespace(provider="groq", model="m", category="testing",
                            problem_id="testing_002", score=0.0, latency_ms=20,
                            status="failed", error_type="reference_impl_failed",
                            evidence={"gate_outcome": "failed",
                                      "gate": {"passed": 3, "failed": 1,
                                               "skipped": 0, "errors": 0,
                                               "collected": 4},
                                      "mutants_killed": None, "mutants_total": 2,
                                      "mutants": {}}),
            SimpleNamespace(provider="nvidia", model="m", category="coding",
                            problem_id="coding_001", score=0.0, latency_ms=30,
                            status="failed", error_type="error: HTTPError 503: x",
                            evidence=None),
        ]

    def test_run_detail_shows_counts_and_not_measured(self):
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run", return_value=self._rows()), \
             patch.object(gui_app, "FAILURE_ARTIFACTS_DIR", ROOT / "missing_artifacts"):
            response = self.client.get("/run/27")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Test counts", body)
        self.assertIn("3 of 3 passed", body)
        self.assertIn("kills not measured", body)
        self.assertNotIn("killed 0/", body)
        # Legacy-style row (no evidence) renders "not recorded", never 0.
        self.assertIn("not recorded", body)

    def test_dashboard_shows_recorded_fraction(self):
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run", return_value=self._rows()):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Test counts", body)
        # groq coding: 1/1 recorded; nvidia coding: 0 recorded.
        self.assertIn("1/1", body)
        self.assertIn("not recorded", body)

    def test_legacy_rows_without_evidence_attribute_render_not_recorded(self):
        rows = [SimpleNamespace(provider="groq", model="m", category="coding",
                                problem_id="coding_001", score=1.0, latency_ms=10,
                                status="passed", error_type=None)]
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run", return_value=rows), \
             patch.object(gui_app, "FAILURE_ARTIFACTS_DIR", ROOT / "missing_artifacts"):
            response = self.client.get("/run/27")
        self.assertEqual(response.status_code, 200)
        self.assertIn("not recorded", response.get_data(as_text=True))

    def test_methodology_renders_evidence_era_section(self):
        response = self.client.get("/methodology")
        body = response.get_data(as_text=True)
        self.assertIn("runs 1-26", body)
        self.assertIn("not measured", body)


@unittest.skipUnless(FLASK_AVAILABLE, "Flask and project package dependencies required")
class TestDetailTests(unittest.TestCase):
    def setUp(self):
        self.client = gui_app.app.test_client()
        self.run = SimpleNamespace(id=28, timestamp="2026-11-01T10:00:00+00:00",
                                   notes="pertest run")

    def _rows(self):
        return [
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_001", score=0.667, latency_ms=10,
                            status="partial", error_type=None,
                            evidence={"passed": 2, "failed": 1, "skipped": 0,
                                      "errors": 0, "collected": 3,
                                      "tests": [
                                          {"name": "test_solution.py::test_a",
                                           "status": "passed"},
                                          {"name": "test_solution.py::test_b",
                                           "status": "failed"},
                                          {"name": "test_solution.py::test_c",
                                           "status": "passed"}]}),
            SimpleNamespace(provider="zhipu", model="m", category="testing",
                            problem_id="testing_001", score=0.0, latency_ms=20,
                            status="failed", error_type="reference_impl_failed",
                            evidence={"gate_outcome": "failed",
                                      "gate": {"passed": 5, "failed": 1,
                                               "skipped": 0, "errors": 0,
                                               "collected": 6},
                                      "mutants_killed": None, "mutants_total": 3,
                                      "mutants": {},
                                      "tests": [
                                          {"name": "..\\test_generated.py::test_single_character",
                                           "status": "failed"},
                                          {"name": "..\\test_generated.py::test_nested_brackets",
                                           "status": "passed"}]}),
            SimpleNamespace(provider="gemma", model="m", category="testing",
                            problem_id="testing_002", score=1.0, latency_ms=30,
                            status="passed", error_type=None,
                            evidence={"gate_outcome": "passed",
                                      "gate": {"passed": 3, "failed": 0,
                                               "skipped": 0, "errors": 0,
                                               "collected": 3},
                                      "mutants_killed": 3, "mutants_total": 3,
                                      "mutants": {},
                                      "tests": [
                                          {"name": "test_generated.py::test_x",
                                           "status": "passed"},
                                          {"name": "test_generated.py::test_y",
                                           "status": "passed"}]}),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_002", score=0.0, latency_ms=40,
                            status="error", error_type="execution_error",
                            evidence={"passed": 0, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 0, "tests": []}),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_003", score=1.0, latency_ms=50,
                            status="passed", error_type=None, evidence=None),
            SimpleNamespace(provider="groq", model="m", category="debugging",
                            problem_id="debug_001", score=1.0, latency_ms=60,
                            status="passed", error_type=None,
                            evidence={"passed": 3, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 3}),
            SimpleNamespace(provider="groq", model="m", category="thinking-planning",
                            problem_id="plan_001", score=1.0, latency_ms=70,
                            status="passed", error_type=None, evidence=None),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_004", score=0.0, latency_ms=80,
                            status="failed", error_type="error: HTTPError 429: x",
                            evidence=None),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_005", score=1.0, latency_ms=90,
                            status="passed", error_type=None,
                            evidence={"passed": 2, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 2,
                                      "tests": [
                                          {"name": "test_solution.py::test_ok",
                                           "status": "passed"},
                                          {"name": "test_solution.py::test_future",
                                           "status": "xfail"}]}),
        ]

    def _get_detail(self, category, problem, provider, rows=None):
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run",
                          return_value=rows if rows is not None else self._rows()), \
             patch.object(gui_app, "FAILURE_ARTIFACTS_DIR", ROOT / "missing_artifacts"):
            return self.client.get(f"/run/28/detail/{category}/{problem}/{provider}")

    def test_recorded_direct_list(self):
        response = self._get_detail("coding", "coding_001", "groq")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn(">test_a<", body)
        self.assertIn(">test_b<", body)
        self.assertIn(">test_c<", body)
        self.assertIn("2 of 3 passed (1 failed)", body)
        self.assertNotIn("Per-test detail was not recorded", body)

    def test_gate_failed_strips_prefix_and_shows_not_measured(self):
        response = self._get_detail("testing", "testing_001", "zhipu")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        # Backslash-prefixed stored names display stripped to bare names.
        self.assertIn(">test_single_character<", body)
        self.assertIn(">test_nested_brackets<", body)
        self.assertIn("reference-gate run", body)
        self.assertIn("kills not measured", body)
        self.assertNotIn("killed 0/", body)

    def test_gate_passed_shows_kills(self):
        response = self._get_detail("testing", "testing_002", "gemma")
        body = response.get_data(as_text=True)
        self.assertIn("killed 3/3", body)
        self.assertIn(">test_x<", body)

    def test_no_tests_state(self):
        response = self._get_detail("coding", "coding_002", "groq")
        body = response.get_data(as_text=True)
        self.assertIn("No tests ran for this evaluation", body)
        self.assertIn("Execution or collection error", body)
        self.assertNotIn("Per-test detail was not recorded", body)

    def test_not_recorded_reasons(self):
        legacy = self._get_detail("coding", "coding_003", "groq")
        self.assertIn("predates per-test capture",
                      legacy.get_data(as_text=True))
        old_shape = self._get_detail("debugging", "debug_001", "groq")
        self.assertIn("predates per-test capture",
                      old_shape.get_data(as_text=True))
        plan = self._get_detail("thinking-planning", "plan_001", "groq")
        self.assertIn("judge scores, not pytest tests",
                      plan.get_data(as_text=True))
        failed = self._get_detail("coding", "coding_004", "groq")
        self.assertIn("failed before evaluation",
                      failed.get_data(as_text=True))

    def test_xfail_note(self):
        response = self._get_detail("coding", "coding_005", "groq")
        body = response.get_data(as_text=True)
        self.assertIn(">test_future<", body)
        self.assertIn("not counted in the score", body)

    def test_detail_404s(self):
        self.assertEqual(
            self._get_detail("coding", "coding_999", "groq").status_code, 404)
        self.assertEqual(
            self._get_detail("bogus", "coding_001", "groq").status_code, 404)
        with patch.object(gui_app, "get_runs", return_value=[]):
            self.assertEqual(
                self.client.get("/run/999/detail/coding/coding_001/groq").status_code,
                404)

    def test_run_detail_links_to_detail_pages(self):
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run", return_value=self._rows()), \
             patch.object(gui_app, "FAILURE_ARTIFACTS_DIR", ROOT / "missing_artifacts"):
            response = self.client.get("/run/28")
        body = response.get_data(as_text=True)
        self.assertIn("/run/28/detail/coding/coding_001/groq", body)
        self.assertIn("View tests", body)

    def test_artifact_link_present_and_absent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            name = "testing_001_valid_parentheses__zhipu__20261101-100500.md"
            (pathlib.Path(tmpdir) / name).write_text("# artifact\n")
            rows = [SimpleNamespace(provider="zhipu", model="m", category="testing",
                                    problem_id="testing_001_valid_parentheses",
                                    score=0.0, latency_ms=20, status="failed",
                                    error_type="reference_impl_failed",
                                    evidence={"gate_outcome": "failed",
                                              "gate": {"passed": 1, "failed": 1,
                                                       "skipped": 0, "errors": 0,
                                                       "collected": 2},
                                              "mutants_killed": None,
                                              "mutants_total": 2, "mutants": {},
                                              "tests": []})]
            with patch.object(gui_app, "get_runs", return_value=[self.run]), \
                 patch.object(gui_app, "get_results_for_run", return_value=rows), \
                 patch.object(gui_app, "FAILURE_ARTIFACTS_DIR", pathlib.Path(tmpdir)):
                response = self.client.get(
                    "/run/28/detail/testing/testing_001_valid_parentheses/zhipu")
            body = response.get_data(as_text=True)
            self.assertIn("View failure artifact", body)
            self.assertIn(name, body)
        absent = self._get_detail("coding", "coding_001", "groq")
        self.assertNotIn("View failure artifact",
                         absent.get_data(as_text=True))

    def test_methodology_identities_block(self):
        response = self.client.get("/methodology")
        body = response.get_data(as_text=True)
        self.assertIn("Test identities", body)
        self.assertIn("runs 1-27", body)


@unittest.skipUnless(FLASK_AVAILABLE, "Flask and project package dependencies required")
class ScoreBreakdownTests(unittest.TestCase):
    def setUp(self):
        self.client = gui_app.app.test_client()
        self.run = SimpleNamespace(id=28, timestamp="2026-11-01T10:00:00+00:00",
                                   notes="breakdown run")

    def _detail_rows(self):
        return [
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_001", score=1.0, latency_ms=10,
                            status="passed", error_type=None,
                            evidence={"passed": 3, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 3,
                                      "tests": [{"name": "test_solution.py::test_a",
                                                 "status": "passed"}] * 3}),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_002", score=1.0, latency_ms=20,
                            status="passed", error_type=None,
                            evidence={"passed": 2, "failed": 0, "skipped": 1,
                                      "errors": 0, "collected": 3,
                                      "tests": [{"name": "test_solution.py::test_a",
                                                 "status": "passed"},
                                                {"name": "test_solution.py::test_b",
                                                 "status": "passed"},
                                                {"name": "test_solution.py::test_c",
                                                 "status": "skipped"}]}),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_003", score=0.667, latency_ms=30,
                            status="partial", error_type=None,
                            evidence={"passed": 2, "failed": 1, "skipped": 0,
                                      "errors": 0, "collected": 3,
                                      "tests": [{"name": "test_solution.py::test_a",
                                                 "status": "passed"},
                                                {"name": "test_solution.py::test_b",
                                                 "status": "passed"},
                                                {"name": "test_solution.py::test_c",
                                                 "status": "failed"},
                                                {"name": "test_solution.py::test_d",
                                                 "status": "xfail"}]}),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_004", score=0.0, latency_ms=40,
                            status="error",
                            error_type="execution_error; truncated_at_cap",
                            evidence={"passed": 0, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 0, "tests": []}),
            SimpleNamespace(provider="gemma", model="m", category="testing",
                            problem_id="testing_001", score=1.0, latency_ms=50,
                            status="passed", error_type=None,
                            evidence={"gate_outcome": "passed",
                                      "gate": {"passed": 3, "failed": 0,
                                               "skipped": 0, "errors": 0,
                                               "collected": 3},
                                      "mutants_killed": 3, "mutants_total": 3,
                                      "mutants": {}, "tests": []}),
            SimpleNamespace(provider="zhipu", model="m", category="testing",
                            problem_id="testing_002", score=0.0, latency_ms=60,
                            status="failed", error_type="reference_impl_failed",
                            evidence={"gate_outcome": "failed",
                                      "gate": {"passed": 5, "failed": 1,
                                               "skipped": 0, "errors": 0,
                                               "collected": 6},
                                      "mutants_killed": None, "mutants_total": 3,
                                      "mutants": {}, "tests": []}),
            SimpleNamespace(provider="openrouter", model="m", category="testing",
                            problem_id="testing_003", score=0.0, latency_ms=70,
                            status="failed",
                            error_type="no_tests_ran; truncated_at_cap",
                            evidence={"gate_outcome": "not_run",
                                      "gate": {"passed": 0, "failed": 0,
                                               "skipped": 0, "errors": 0,
                                               "collected": 0},
                                      "mutants_killed": None, "mutants_total": 2,
                                      "mutants": {}, "tests": []}),
            SimpleNamespace(provider="openrouter", model="m", category="debugging",
                            problem_id="debug_001", score=0.0, latency_ms=80,
                            status="timeout", error_type="sandbox_timeout",
                            evidence=None),
            SimpleNamespace(provider="zhipu", model="m", category="coding",
                            problem_id="coding_005", score=0.0, latency_ms=90,
                            status="failed",
                            error_type="error: HTTPError 429: x",
                            evidence=None),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_006", score=1.0, latency_ms=100,
                            status="passed", error_type=None, evidence=None),
            SimpleNamespace(provider="groq", model="m", category="thinking-planning",
                            problem_id="plan_001", score=1.0, latency_ms=110,
                            status="passed", error_type=None, evidence=None),
            SimpleNamespace(provider="openrouter", model="m", category="thinking-planning",
                            problem_id="plan_002", score=1.0, latency_ms=120,
                            status="passed", error_type="truncated_at_cap",
                            evidence=None),
            SimpleNamespace(provider="nvidia", model="m", category="thinking-planning",
                            problem_id="plan_003", score=0.0, latency_ms=130,
                            status="failed", error_type="judge_error",
                            evidence=None),
        ]

    def _get_detail(self, category, problem, provider):
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run",
                          return_value=self._detail_rows()), \
             patch.object(gui_app, "FAILURE_ARTIFACTS_DIR", ROOT / "missing_artifacts"):
            return self.client.get(f"/run/28/detail/{category}/{problem}/{provider}")

    def test_direct_clean_formula(self):
        body = self._get_detail("coding", "coding_001", "groq").get_data(as_text=True)
        self.assertIn("How this score was calculated", body)
        self.assertIn("Score = 3 ÷ 3 = 1.000.", body)
        self.assertNotIn("Why zero", body)

    def test_direct_skipped_denominator(self):
        body = self._get_detail("coding", "coding_002", "groq").get_data(as_text=True)
        self.assertIn("Score = 2 ÷ 2 = 1.000.", body)
        self.assertIn("Skipped: 1 (not counted in the denominator).", body)
        self.assertIn("Collected 3 tests in total; 2 counted toward the score.", body)

    def test_direct_partial_and_xfail(self):
        body = self._get_detail("coding", "coding_003", "groq").get_data(as_text=True)
        self.assertIn("Score = 2 ÷ 3 = 0.667.", body)
        self.assertIn("Expected-failure markers: 1 listed, not counted in the score.", body)

    def test_direct_no_tests_truncated(self):
        body = self._get_detail("coding", "coding_004", "groq").get_data(as_text=True)
        self.assertIn("No counted tests ran", body)
        self.assertIn("Output was truncated at the token limit", body)
        self.assertIn("Why zero:", body)
        self.assertIn("could not run", body)

    def test_gate_passed_formula(self):
        body = self._get_detail("testing", "testing_001", "gemma").get_data(as_text=True)
        self.assertIn("Reference gate passed (3/3 checks).", body)
        self.assertIn("Mutants killed: 3/3.", body)
        self.assertIn("Score = 3 ÷ 3 = 1.000.", body)

    def test_gate_failed_zero_reason(self):
        body = self._get_detail("testing", "testing_002", "zhipu").get_data(as_text=True)
        self.assertIn("Reference gate failed (5/6 passed (1 failed)).", body)
        self.assertIn("Mutant scoring never ran", body)
        self.assertIn("Why zero:", body)
        self.assertIn("by design", body)

    def test_gate_not_run_zero_reason(self):
        body = self._get_detail("testing", "testing_003", "openrouter").get_data(as_text=True)
        self.assertIn("Reference gate did not run", body)
        self.assertIn("no tests were collected", body)

    def test_timeout_and_request_zero_reasons(self):
        timeout = self._get_detail("debugging", "debug_001", "openrouter").get_data(as_text=True)
        self.assertIn("execution timed out", timeout)
        self.assertIn("10-second sandbox limit", timeout)
        request = self._get_detail("coding", "coding_005", "zhipu").get_data(as_text=True)
        self.assertIn("Request failure", request)
        self.assertIn("excluded from capability", request)

    def test_unavailable_legacy_row(self):
        body = self._get_detail("coding", "coding_006", "groq").get_data(as_text=True)
        self.assertIn("Counts were not recorded", body)
        self.assertNotIn("Why zero", body)

    def test_judge_blocks(self):
        scored = self._get_detail("thinking-planning", "plan_001", "groq").get_data(as_text=True)
        self.assertIn("Judge score = 1.000.", scored)
        self.assertIn("criterion-level marks are not stored", scored)
        truncated = self._get_detail("thinking-planning", "plan_002", "openrouter").get_data(as_text=True)
        self.assertIn("Output was truncated at the token limit", truncated)
        judge_err = self._get_detail("thinking-planning", "plan_003", "nvidia").get_data(as_text=True)
        self.assertIn("No plan score exists", judge_err)
        self.assertIn("Judge error", judge_err)

    def test_contribution_line(self):
        rows = [
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_001", score=1.0, latency_ms=10,
                            status="passed", error_type=None,
                            evidence={"passed": 3, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 3, "tests": []}),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_002", score=0.0, latency_ms=20,
                            status="failed", error_type=None,
                            evidence={"passed": 0, "failed": 3, "skipped": 0,
                                      "errors": 0, "collected": 3, "tests": []}),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_003", score=1.0, latency_ms=30,
                            status="passed", error_type=None,
                            evidence={"passed": 3, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 3, "tests": []}),
        ]
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run", return_value=rows), \
             patch.object(gui_app, "FAILURE_ARTIFACTS_DIR", ROOT / "missing_artifacts"):
            response = self.client.get("/run/28/detail/coding/coding_002/groq")
        body = response.get_data(as_text=True)
        self.assertIn("(1.000 + 0.000 + 1.000) ÷ 3 = 0.667", body)
        self.assertIn("/run/28/breakdown/coding/groq", body)

    def test_breakdown_page_and_mean_equality(self):
        rows = [
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_001", score=1.0, latency_ms=10,
                            status="passed", error_type=None,
                            evidence={"passed": 3, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 3}),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_002", score=1.0, latency_ms=20,
                            status="passed", error_type=None,
                            evidence={"passed": 2, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 2}),
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_003", score=0.0, latency_ms=30,
                            status="failed",
                            error_type="error: HTTPError 429: x",
                            evidence=None),
            SimpleNamespace(provider="nvidia", model="m", category="coding",
                            problem_id="coding_001", score=0.5, latency_ms=40,
                            status="partial", error_type=None,
                            evidence={"passed": 1, "failed": 1, "skipped": 0,
                                      "errors": 0, "collected": 2}),
            SimpleNamespace(provider="contamination_check", model="m",
                            category="coding", problem_id="coding_001",
                            score=1.0, latency_ms=1, status="passed",
                            error_type=None, evidence=None),
        ]
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run", return_value=rows):
            response = self.client.get("/run/28/breakdown/coding/groq")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("(1.000 + 1.000 + 0.000) ÷ 3 = 0.667", body)
        self.assertIn("3/3 passed", body)
        self.assertIn("No evaluation (request failure)", body)
        self.assertIn("Capability (valid evaluations only) = 1.000 over 2/3", body)
        # The breakdown mean must equal the dashboard's mean exactly.
        summary = gui_app.summarize(rows)
        self.assertAlmostEqual(summary[("coding", "groq")]["score"], 2 / 3)
        self.assertNotIn("contamination_check", body)

    def test_breakdown_404s(self):
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run", return_value=[]):
            self.assertEqual(
                self.client.get("/run/28/breakdown/coding/groq").status_code, 404)
            self.assertEqual(
                self.client.get("/run/28/breakdown/bogus/groq").status_code, 404)
            self.assertEqual(
                self.client.get("/run/28/breakdown/coding/contamination_check").status_code,
                404)
        with patch.object(gui_app, "get_runs", return_value=[]):
            self.assertEqual(
                self.client.get("/run/999/breakdown/coding/groq").status_code, 404)

    def test_score_cells_are_links(self):
        rows = [
            SimpleNamespace(provider="groq", model="m", category="coding",
                            problem_id="coding_001", score=1.0, latency_ms=10,
                            status="passed", error_type=None,
                            evidence={"passed": 3, "failed": 0, "skipped": 0,
                                      "errors": 0, "collected": 3}),
        ]
        with patch.object(gui_app, "get_runs", return_value=[self.run]), \
             patch.object(gui_app, "get_results_for_run", return_value=rows), \
             patch.object(gui_app, "FAILURE_ARTIFACTS_DIR", ROOT / "missing_artifacts"):
            detail = self.client.get("/run/28")
            dashboard = self.client.get("/")
        detail_body = detail.get_data(as_text=True)
        self.assertIn('<a href="/run/28/detail/coding/coding_001/groq">1.000</a>',
                      detail_body)
        self.assertIn("/run/28/breakdown/coding/groq",
                      dashboard.get_data(as_text=True))

    def test_score_calculation_unit_cases(self):
        calc = gui_app.score_calculation(SimpleNamespace(
            category="testing", score=0.0, error_type=None,
            evidence={"gate_outcome": "passed",
                      "gate": {"passed": 2, "failed": 0, "skipped": 0,
                               "errors": 0, "collected": 2},
                      "mutants_killed": 0, "mutants_total": 2, "mutants": {}}))
        self.assertIn("no mutants were killed", calc["zero_reason"])
        basis = gui_app.score_basis(SimpleNamespace(
            category="debugging", score=0.0, error_type="sandbox_timeout",
            evidence=None))
        self.assertEqual(basis, "Execution timed out")


if __name__ == "__main__":
    unittest.main()
