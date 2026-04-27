import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


SCRIPT = Path("skills/redis-rdb-analysis/scripts/analyze_local_rdb.py")
HIGH_VERSION_RDB = Path(
    "/Users/zqw/Desktop/Project/dba_assistant/tests/fixtures/rdb/high_version/redis_v12_hash_with_hfe.rdb"
)


class AnalyzeLocalRdbTests(unittest.TestCase):
    def test_analyze_local_rdb_generates_required_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            rdb = base / "empty.rdb"
            rdb.write_bytes(b"REDIS0009\xff\x00\x00\x00\x00\x00\x00\x00\x00")
            output_dir = base / "out"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--rdb",
                    str(rdb),
                    "--output-dir",
                    str(output_dir),
                    "--user-request",
                    "Please analyze this local Redis RDB file.",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output_dir / "summary.txt").exists())
            self.assertTrue((output_dir / "result.json").exists())
            self.assertTrue((output_dir / "report.docx").exists())
            self.assertTrue((output_dir / "input" / "user_request.txt").exists())
            self.assertTrue((output_dir / "input" / "rdb.fingerprint").exists())

            result = json.loads((output_dir / "result.json").read_text())
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["summary"]["total_keys"], 0)
            self.assertEqual(result["summary"]["db_count"], 0)
            self.assertEqual(result["validation"]["mechanical"]["status"], "pass")
            self.assertEqual(result["validation"]["logical"]["status"], "pass")

            summary = (output_dir / "summary.txt").read_text()
            self.assertIn("1. Analysis Target", summary)
            self.assertIn("Analysis status: success", summary)

            with ZipFile(output_dir / "report.docx") as archive:
                self.assertIn("word/document.xml", archive.namelist())

    def test_analyze_local_rdb_missing_file_returns_failed_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            output_dir = base / "out"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--rdb",
                    str(base / "missing.rdb"),
                    "--output-dir",
                    str(output_dir),
                    "--user-request",
                    "Analyze missing file.",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            result = json.loads((output_dir / "result.json").read_text())
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["validation"]["mechanical"]["status"], "fail")
            self.assertTrue(result["errors"])

    @unittest.skipUnless(HIGH_VERSION_RDB.exists(), "original high-version RDB fixture is unavailable")
    def test_analyze_local_rdb_uses_hdt_tool_for_high_version_rdb(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "out"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--rdb",
                    str(HIGH_VERSION_RDB),
                    "--output-dir",
                    str(output_dir),
                    "--user-request",
                    "Analyze high version RDB.",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads((output_dir / "result.json").read_text())
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["summary"]["total_keys"], 1)
            self.assertEqual(result["summary"]["type_distribution"], {"hash": 1})
            self.assertEqual(result["validation"]["logical"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
