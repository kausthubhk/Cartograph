from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from cartograph.contracts import Contract, ContractError, load_contract
from cartograph.planner import plan_scenarios
from cartograph.providers import FixtureProvider, UnsupportedScenario


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "contracts" / "cancel_job.json"


class ContractTests(unittest.TestCase):
    def test_loads_and_plans_declared_behavior(self) -> None:
        contract = load_contract(SAMPLE)
        self.assertEqual(contract.method, "CancelJob")
        self.assertEqual([case.scenario_id for case in plan_scenarios(contract)], ["terminal-no-event"])

    def test_rejects_duplicate_scenario_ids(self) -> None:
        raw = json.loads(SAMPLE.read_text(encoding="utf-8"))
        raw["behaviors"].append(dict(raw["behaviors"][0]))
        with self.assertRaisesRegex(ContractError, "unique"):
            Contract.from_dict(raw)

    def test_rejects_missing_required_contract_fields(self) -> None:
        with self.assertRaisesRegex(ContractError, "missing required"):
            Contract.from_dict({"service": "Jobs"})

    def test_rejects_whitespace_only_required_values(self) -> None:
        raw = json.loads(SAMPLE.read_text(encoding="utf-8"))
        raw["method"] = "   "
        with self.assertRaisesRegex(ContractError, "method"):
            Contract.from_dict(raw)

    def test_rejects_duplicate_fields(self) -> None:
        raw = json.loads(SAMPLE.read_text(encoding="utf-8"))
        raw["fields"] = ["job_id", "job_id"]
        with self.assertRaisesRegex(ContractError, "duplicates"):
            Contract.from_dict(raw)

    def test_fixture_provider_is_explicitly_bounded(self) -> None:
        contract = load_contract(SAMPLE)
        behavior = plan_scenarios(contract)[0]
        rendered = FixtureProvider().generate(contract, behavior)
        self.assertIn("TestCancelJob_TerminalJobDoesNotPublish", rendered)
        self.assertIn("not output from a language model", rendered)

        unsupported = Contract(
            service="Jobs",
            method="StartJob",
            input_type="StartJobRequest",
            field_names=("job_id",),
            behaviors=contract.behaviors,
        )
        with self.assertRaises(UnsupportedScenario):
            FixtureProvider().generate(unsupported, behavior)

    @unittest.skipUnless(shutil.which("go"), "Go toolchain is required for integration checks")
    def test_generated_assertion_passes_and_detects_behavior_regression(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            demo = Path(temp_dir)
            for name in ("go.mod", "cancel_job.go", "errors.go"):
                shutil.copy2(ROOT / "demo" / name, demo / name)
            generated = FixtureProvider().generate(load_contract(SAMPLE), plan_scenarios(load_contract(SAMPLE))[0])
            generated_path = demo / "cartograph_generated_test.go"
            generated_path.write_text(generated, encoding="utf-8")

            passing = subprocess.run(
                ["go", "test", "./..."], cwd=demo, text=True, capture_output=True, check=False
            )
            self.assertEqual(passing.returncode, 0, passing.stdout + passing.stderr)

            implementation = (demo / "cancel_job.go").read_text(encoding="utf-8")
            broken = implementation.replace(
                "if s.states[req.JobID] == StateTerminal {\n\t\treturn nil\n\t}",
                "if s.states[req.JobID] == StateTerminal {\n\t\ts.events = append(s.events, Event{JobID: req.JobID, Name: \"JobCancelled\"})\n\t\treturn nil\n\t}",
            )
            self.assertNotEqual(broken, implementation, "regression mutation did not apply")
            (demo / "cancel_job.go").write_text(broken, encoding="utf-8")
            failing = subprocess.run(
                ["go", "test", "./..."], cwd=demo, text=True, capture_output=True, check=False
            )
            self.assertNotEqual(failing.returncode, 0, "generated assertion missed injected regression")


if __name__ == "__main__":
    unittest.main()
