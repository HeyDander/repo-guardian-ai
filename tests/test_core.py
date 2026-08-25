import json
import tempfile
import unittest
from pathlib import Path
from repo_guardian.audit import audit
from repo_guardian.cli import main, render
from repo_guardian.repository import Repository


class RepoGuardianTests(unittest.TestCase):
    def make_repo(self, files):
        root = Path(tempfile.mkdtemp())
        for name, content in files.items():
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
        return root

    def test_empty_repository_is_valid_and_explains_missing_docs(self):
        result = audit(self.make_repo({}), "full")
        self.assertEqual(result.stacks, [])
        self.assertTrue(any(f.id == "RG-DOC-001" for f in result.findings))
        self.assertEqual(result.overall, 98)

    def test_security_finding_has_real_line_evidence_without_secret_value(self):
        secret = "live-" + "secret-value"
        dangerous = "os." + "system"
        root = self.make_repo({"app.py": "TOKEN = '" + secret + "'\nimport os\n" + dangerous + "(user_input)\n"})
        result = audit(root, "security")
        finding = next(f for f in result.findings if f.id == "RG-SEC-001")
        self.assertIn("app.py:1", finding.evidence)
        self.assertNotIn("not-a-real-token-12345", " ".join(finding.evidence))
        self.assertEqual(finding.confidence.value, "MEDIUM")

    def test_security_ignores_documented_secret_placeholders(self):
        root = self.make_repo({"config.py": "WIFI_PASSWORD = 'YOUR_PASSWORD'\nAPI_TOKEN = 'PLACEHOLDER_TOKEN'\n"})
        result = audit(root, "security")
        self.assertEqual(result.findings, [])

    def test_no_test_fixture_is_reported(self):
        result = audit(self.make_repo({"pyproject.toml": "[project]\nname='x'\n", "app.py": "print('x')\n"}), "tests")
        self.assertEqual(result.findings[0].id, "RG-TST-001")

    def test_stack_detection_supports_polyglot_markers(self):
        root = self.make_repo({"package.json": '{"dependencies":{"react":"1"}}', "main.go": "package main\n", "Dockerfile": "FROM python:3.11\n"})
        result = audit(root, "docs")
        self.assertIn("Node.js", result.stacks); self.assertIn("Go", result.stacks); self.assertIn("Docker", result.stacks)

    def test_fixture_only_markers_do_not_change_detected_stack(self):
        root = self.make_repo({"README.md": "# project\n", "tests/fixtures/package.json": "{}", "tests/fixtures/main.go": "package main\n"})
        result = audit(root, "docs")
        self.assertEqual(result.stacks, [])

    def test_full_audit_does_not_report_empty_review_as_a_finding(self):
        result = audit(self.make_repo({"README.md": "# project\n"}), "full")
        self.assertFalse(any(f.id == "RG-REV-002" for f in result.findings))

    def test_missing_repository_returns_friendly_cli_error(self):
        from repo_guardian.cli import main
        missing = Path(tempfile.mkdtemp()) / "missing-project"
        self.assertEqual(main(["full", "--repo", str(missing)]), 2)

    def test_safe_runner_blocks_destructive_tokens(self):
        result = Repository(self.make_repo({})).safe_command(["git", "reset", "--hard"])
        self.assertTrue(result.skipped)

    def test_json_output_is_machine_readable(self):
        root = self.make_repo({"README.md": "# x\n"})
        result = audit(root, "docs")
        payload = json.loads(json.dumps(result.to_dict()))
        self.assertIn("findings", payload); self.assertEqual(payload["overall"], 100)

    def test_dependency_mode_reports_missing_lockfile_and_wide_range(self):
        root = self.make_repo({"package.json": '{"dependencies":{"demo":"*"}}'})
        result = audit(root, "dependencies")
        ids = {finding.id for finding in result.findings}
        self.assertIn("RG-DEP-001", ids)
        self.assertIn("RG-DEP-002", ids)

    def test_performance_mode_reports_query_inside_loop_with_medium_confidence(self):
        root = self.make_repo({"app.py": "for user in users:\n    rows = db.execute('SELECT * FROM users')\n"})
        result = audit(root, "performance")
        self.assertEqual(result.findings[0].id, "RG-PERF-001")
        self.assertEqual(result.findings[0].confidence.value, "MEDIUM")

    def test_architecture_mode_reports_oversized_module(self):
        root = self.make_repo({"large.py": "\n".join(["value = 1"] * 301)})
        result = audit(root, "architecture")
        self.assertEqual(result.findings[0].id, "RG-ARC-001")

    def test_release_mode_uses_git_state_and_ci_evidence(self):
        root = self.make_repo({"app.py": "print('x')\n"})
        result = audit(root, "release")
        ids = {finding.id for finding in result.findings}
        self.assertIn("RG-REL-002", ids)
        self.assertIn("RG-REL-003", ids)

    def test_project_commands_are_discovered_without_execution(self):
        root = self.make_repo({"package.json": '{"scripts":{"test":"pytest","lint":"ruff check ."}}', "Makefile": "build:\n\t@echo build\n"})
        result = audit(root, "docs")
        commands = result.commands[2]["result"]
        names = {command["name"] for command in commands}
        self.assertIn("npm:test", names)
        self.assertIn("make:build", names)

    def test_fail_on_threshold_allows_medium_findings_to_be_reported(self):
        from repo_guardian.cli import main
        root = self.make_repo({"app.py": "for item in items:\n    fetch(url)\n"})
        self.assertEqual(main(["performance", "--repo", str(root), "--fail-on", "high"]), 0)
        self.assertEqual(main(["performance", "--repo", str(root), "--fail-on", "medium"]), 1)

    def test_strict_agent_contract_contains_truth_scope_and_verification_gates(self):
        project_root = Path(__file__).parents[1]
        contract = (project_root / "docs" / "agent-contract.md").read_text()
        skill = (project_root / "SKILL.md").read_text()
        for phrase in ("IN SCOPE", "OUT OF SCOPE", "NOT RUN", "Minimal patch rule", "Verification gate", "SCOPE CHECK"):
            self.assertIn(phrase, contract)
        self.assertIn("Strict Engineer Contract", skill)
        self.assertIn("agent-contract.md", skill)


if __name__ == "__main__": unittest.main()
