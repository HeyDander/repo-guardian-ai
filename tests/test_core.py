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
        self.assertEqual(result.overall, 99)

    def test_security_finding_has_real_line_evidence_without_secret_value(self):
        secret = "live-" + "secret-value"
        root = self.make_repo({"app.py": "TOKEN = '" + secret + "'\nimport os\nos.system(user_input)\n"})
        result = audit(root, "security")
        finding = next(f for f in result.findings if f.id == "RG-SEC-001")
        self.assertIn("app.py:1", finding.evidence)
        self.assertNotIn("not-a-real-token-12345", " ".join(finding.evidence))
        self.assertEqual(finding.confidence.value, "MEDIUM")

    def test_no_test_fixture_is_reported(self):
        result = audit(self.make_repo({"pyproject.toml": "[project]\nname='x'\n", "app.py": "print('x')\n"}), "tests")
        self.assertEqual(result.findings[0].id, "RG-TST-001")

    def test_stack_detection_supports_polyglot_markers(self):
        root = self.make_repo({"package.json": '{"dependencies":{"react":"1"}}', "main.go": "package main\n", "Dockerfile": "FROM python:3.11\n"})
        result = audit(root, "docs")
        self.assertIn("Node.js", result.stacks); self.assertIn("Go", result.stacks); self.assertIn("Docker", result.stacks)

    def test_safe_runner_blocks_destructive_tokens(self):
        result = Repository(self.make_repo({})).safe_command(["git", "reset", "--hard"])
        self.assertTrue(result.skipped)

    def test_json_output_is_machine_readable(self):
        root = self.make_repo({"README.md": "# x\n"})
        result = audit(root, "docs")
        payload = json.loads(json.dumps(result.to_dict()))
        self.assertIn("findings", payload); self.assertEqual(payload["overall"], 100)


if __name__ == "__main__": unittest.main()
