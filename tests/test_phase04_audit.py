import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path("skills/redis-rdb-analysis/scripts/analyze_local_rdb.py")
COMPARE_SCRIPT = Path("tools/audit/compare_repeated_runs.py")
HIGH_VERSION_RDB = Path("tests/fixtures/rdb/high_version/redis_v12_hash_with_hfe.rdb")


class Phase04AuditArchiveTests(unittest.TestCase):
    def run_script(self, rdb_path, output_dir):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--rdb",
                str(rdb_path),
                "--output-dir",
                str(output_dir),
                "--user-request",
                "Please analyze this RDB with audit archive.",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    @unittest.skipUnless(HIGH_VERSION_RDB.exists(), "high-version RDB fixture is unavailable")
    def test_success_run_writes_required_audit_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "phase04-success"

            completed = self.run_script(HIGH_VERSION_RDB, output_dir)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            for relative in [
                "audit/meta.json",
                "audit/stdout.log",
                "audit/stderr.log",
                "audit/axe_verbose.log",
                "audit/trace.json",
                "input/user_request.txt",
                "input/rdb.fingerprint",
                "result.json",
                "summary.txt",
                "report.docx",
            ]:
                self.assertTrue((output_dir / relative).exists(), relative)

            meta = json.loads((output_dir / "audit/meta.json").read_text(encoding="utf-8"))
            result = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["run_id"], output_dir.name)
            self.assertEqual(meta["status"], "success")
            self.assertEqual(meta["exit_code"], 0)
            self.assertEqual(meta["rdb_sha256"], result["input"]["sha256"])
            self.assertEqual(meta["parser_strategy"], "HdtRdbCli")
            self.assertEqual(meta["parser_binary"], result["parser_binary"])
            self.assertIn("analyze_local_rdb.py", meta["command"])
            self.assertEqual(meta["agent"], "redis-rdb-assistant")
            self.assertEqual(meta["skill"], "skills/redis-rdb-analysis/SKILL.md")
            self.assertIsInstance(meta["duration_ms"], int)
            self.assertGreaterEqual(meta["duration_ms"], 0)

    def test_failed_run_writes_required_audit_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "phase04-failed"
            missing_rdb = Path(temp_dir) / "missing.rdb"

            completed = self.run_script(missing_rdb, output_dir)

            self.assertNotEqual(completed.returncode, 0)
            meta = json.loads((output_dir / "audit/meta.json").read_text(encoding="utf-8"))
            result = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["status"], "failed")
            self.assertEqual(meta["exit_code"], completed.returncode)
            self.assertEqual(meta["rdb_sha256"], "")
            self.assertEqual(result["status"], "failed")
            self.assertTrue((output_dir / "audit/stdout.log").exists())
            self.assertTrue((output_dir / "audit/stderr.log").exists())

    def test_default_output_dir_stays_outside_repository_root(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--rdb", "/tmp/nonexistent-phase04.rdb"],
            text=True,
            capture_output=True,
            check=False,
        )

        output_dir = Path(completed.stdout.strip().splitlines()[-1])
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(str(output_dir).startswith("/tmp/axe_rdb_assistant/"))
        self.assertFalse(str(output_dir.resolve()).startswith(str(Path.cwd().resolve())))


class Phase04RepeatabilityTests(unittest.TestCase):
    def write_result(self, directory, overrides=None):
        directory.mkdir(parents=True, exist_ok=True)
        result = {
            "input": {"sha256": "abc"},
            "summary": {
                "total_keys": 1,
                "db_count": 1,
                "type_distribution": {"hash": 1},
                "ttl": {"keys_with_ttl": 0, "keys_without_ttl": 1},
            },
            "parser_strategy": "HdtRdbCli",
            "outputs": {"output_dir": str(directory)},
            "generated_at": "volatile",
        }
        if overrides:
            result.update(overrides)
        (directory / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def test_repeatability_compare_passes_for_stable_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            for index in range(3):
                self.write_result(base / ("run-%s" % index), {"generated_at": "volatile-%s" % index})
            output_path = base / "repeatability.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(COMPARE_SCRIPT),
                    "--result",
                    str(base / "run-0/result.json"),
                    "--result",
                    str(base / "run-1/result.json"),
                    "--result",
                    str(base / "run-2/result.json"),
                    "--output",
                    str(output_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            comparison = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(comparison["status"], "pass")
            self.assertEqual(comparison["compared_runs"], 3)
            self.assertEqual(comparison["stable_fields"]["summary.total_keys"]["status"], "stable")

    def test_repeatability_compare_fails_for_different_type_distribution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            self.write_result(base / "run-0")
            self.write_result(base / "run-1")
            self.write_result(
                base / "run-2",
                {
                    "summary": {
                        "total_keys": 1,
                        "db_count": 1,
                        "type_distribution": {"string": 1},
                        "ttl": {"keys_with_ttl": 0, "keys_without_ttl": 1},
                    }
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(COMPARE_SCRIPT),
                    "--result",
                    str(base / "run-0/result.json"),
                    "--result",
                    str(base / "run-1/result.json"),
                    "--result",
                    str(base / "run-2/result.json"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            comparison = json.loads(completed.stdout)
            self.assertEqual(comparison["status"], "fail")
            self.assertEqual(
                comparison["stable_fields"]["summary.type_distribution"]["status"],
                "mismatch",
            )


if __name__ == "__main__":
    unittest.main()
