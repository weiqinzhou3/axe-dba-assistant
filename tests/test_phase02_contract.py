import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from tools.validation.validate_result import validate_result


SCRIPT = Path("skills/redis-rdb-analysis/scripts/analyze_local_rdb.py")
HIGH_VERSION_RDB = Path("tests/fixtures/rdb/high_version/redis_v12_hash_with_hfe.rdb")


class Phase02ContractTests(unittest.TestCase):
    def run_script(self, rdb_path, output_dir, user_request="Please analyze this RDB."):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--rdb",
                str(rdb_path),
                "--output-dir",
                str(output_dir),
                "--user-request",
                user_request,
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    @unittest.skipUnless(HIGH_VERSION_RDB.exists(), "high-version RDB fixture is unavailable")
    def test_success_result_has_phase02_contract_and_output_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "out"

            completed = self.run_script(
                HIGH_VERSION_RDB,
                output_dir,
                "Please analyze this RDB and generate a formal report.",
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads((output_dir / "result.json").read_text())
            self.assertEqual(result["schema_version"], "phase-02.v1")
            self.assertTrue(result["parser_required"])
            self.assertEqual(result["parser_strategy"], "HdtRdbCli")
            self.assertEqual(result["parser_binary"], result["summary"]["parser_binary"])
            self.assertEqual(result["parser_warnings"], [])
            self.assertEqual(result["outputs"]["output_dir"], str(output_dir))
            for output_id in ["summary_txt", "result_json", "report_docx"]:
                self.assertTrue(result["outputs"][output_id]["exists"], output_id)
                self.assertTrue(Path(result["outputs"][output_id]["path"]).exists(), output_id)

    @unittest.skipUnless(HIGH_VERSION_RDB.exists(), "high-version RDB fixture is unavailable")
    def test_summary_and_docx_include_phase02_metadata_from_result_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "out"

            completed = self.run_script(HIGH_VERSION_RDB, output_dir)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads((output_dir / "result.json").read_text())
            summary = (output_dir / "summary.txt").read_text()
            self.assertIn("2. Parser Metadata", summary)
            self.assertIn("Parser required: true", summary)
            self.assertIn("Parser strategy: %s" % result["parser_strategy"], summary)
            self.assertIn("5. Generated Outputs", summary)
            self.assertIn(result["outputs"]["report_docx"]["path"], summary)

            with ZipFile(output_dir / "report.docx") as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")
            self.assertIn("Parser Metadata", document_xml)
            self.assertIn(result["parser_strategy"], document_xml)
            self.assertIn("Phase-01 / Phase-02 limitations", document_xml)

    def test_failed_result_has_phase02_contract_and_failed_output_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "out"
            missing_rdb = Path(temp_dir) / "missing.rdb"

            completed = self.run_script(missing_rdb, output_dir)

            self.assertNotEqual(completed.returncode, 0)
            result = json.loads((output_dir / "result.json").read_text())
            self.assertEqual(result["schema_version"], "phase-02.v1")
            self.assertEqual(result["status"], "failed")
            self.assertTrue(result["parser_required"])
            self.assertEqual(result["parser_strategy"], "HdtRdbCli")
            self.assertEqual(result["parser_binary"], "unavailable")
            self.assertTrue(result["outputs"]["summary_txt"]["exists"])
            self.assertTrue(result["outputs"]["result_json"]["exists"])
            self.assertTrue(result["outputs"]["report_docx"]["exists"])
            self.assertEqual(result["validation"]["mechanical"]["status"], "fail")
            self.assertEqual(result["validation"]["sufficiency"]["status"], "insufficient")

    def test_missing_hdt_path_is_failed_not_partial(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            rdb = base / "empty.rdb"
            rdb.write_bytes(b"REDIS0009\xff\x00\x00\x00\x00\x00\x00\x00\x00")
            output_dir = base / "out"
            env = dict(os.environ)
            env["PATH"] = ""

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--rdb",
                    str(rdb),
                    "--output-dir",
                    str(output_dir),
                    "--user-request",
                    "Analyze without rdb on PATH.",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertNotEqual(completed.returncode, 0)
            result = json.loads((output_dir / "result.json").read_text())
            self.assertEqual(result["status"], "failed")
            self.assertIn("HDT3213 rdb CLI is required on PATH", "\n".join(result["errors"]))
            self.assertEqual(result["parser_binary"], "unavailable")

    def test_invalid_path_rdb_is_failed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            rdb = base / "empty.rdb"
            rdb.write_bytes(b"REDIS0009\xff\x00\x00\x00\x00\x00\x00\x00\x00")
            fake_bin = base / "bin"
            fake_bin.mkdir()
            fake_rdb = fake_bin / "rdb"
            fake_rdb.write_text(
                "#!/bin/sh\n"
                "echo 'usage: legacy rdbtools'\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake_rdb.chmod(0o755)
            output_dir = base / "out"
            env = dict(os.environ)
            env["PATH"] = str(fake_bin)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--rdb",
                    str(rdb),
                    "--output-dir",
                    str(output_dir),
                    "--user-request",
                    "Analyze with invalid PATH rdb.",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertNotEqual(completed.returncode, 0)
            result = json.loads((output_dir / "result.json").read_text())
            self.assertEqual(result["status"], "failed")
            self.assertIn("PATH rdb is not the required HDT3213 rdb CLI", "\n".join(result["errors"]))

    def test_hdt_command_failure_is_failed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            rdb = base / "empty.rdb"
            rdb.write_bytes(b"REDIS0009\xff\x00\x00\x00\x00\x00\x00\x00\x00")
            fake_bin = base / "bin"
            fake_bin.mkdir()
            fake_rdb = fake_bin / "rdb"
            fake_rdb.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = \"-h\" ]; then\n"
                "  echo 'Usage of hdt-rdb'\n"
                "  echo 'command for rdb: json'\n"
                "  echo '-show-global-meta'\n"
                "  echo '-max-depth'\n"
                "  exit 0\n"
                "fi\n"
                "echo 'synthetic HDT failure' >&2\n"
                "exit 42\n",
                encoding="utf-8",
            )
            fake_rdb.chmod(0o755)
            output_dir = base / "out"
            env = dict(os.environ)
            env["PATH"] = str(fake_bin)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--rdb",
                    str(rdb),
                    "--output-dir",
                    str(output_dir),
                    "--user-request",
                    "Analyze with failing HDT command.",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertNotEqual(completed.returncode, 0)
            result = json.loads((output_dir / "result.json").read_text())
            self.assertEqual(result["status"], "failed")
            self.assertIn("HDT rdb command failed with exit code 42", "\n".join(result["errors"]))
            self.assertEqual(result["validation"]["mechanical"]["status"], "fail")


class Phase02ValidationTests(unittest.TestCase):
    def minimal_result(self):
        return {
            "schema_version": "phase-02.v1",
            "status": "success",
            "generated_at": "2026-04-28T00:00:00+00:00",
            "parser_required": True,
            "parser_strategy": "HdtRdbCli",
            "parser_binary": "/usr/local/bin/rdb",
            "parser_warnings": [],
            "input": {"rdb_path": "/tmp/dump.rdb", "sha256": "a" * 64, "source": "input.rdb_path"},
            "summary": {
                "total_keys": 1,
                "db_count": 1,
                "type_distribution": {"hash": 1},
                "ttl": {"keys_with_ttl": 0, "keys_without_ttl": 1},
                "source": "analysis.hdt_rdb_cli",
            },
            "findings": [{"finding": "One hash key exists.", "severity": "info", "source": "summary.type_distribution"}],
            "validation": {},
            "uncertainties": [],
            "errors": [],
            "outputs": {
                "output_dir": "/tmp/out",
                "summary_txt": {"path": "/tmp/out/summary.txt", "exists": True},
                "result_json": {"path": "/tmp/out/result.json", "exists": True},
                "report_docx": {"path": "/tmp/out/report.docx", "exists": True},
            },
        }

    def test_validate_result_rejects_missing_phase02_top_level_fields(self):
        result = self.minimal_result()
        del result["schema_version"]

        validation = validate_result(result)

        self.assertEqual(validation["mechanical"]["status"], "fail")
        self.assertIn("missing required field: schema_version", "\n".join(validation["mechanical"]["details"]))

    def test_validate_result_rejects_negative_numeric_fields(self):
        result = self.minimal_result()
        result["summary"]["db_count"] = -1

        validation = validate_result(result)

        self.assertEqual(validation["logical"]["status"], "fail")
        self.assertIn("summary.db_count must be non-negative", "\n".join(validation["logical"]["details"]))

    def test_validate_result_rejects_ttl_total_mismatch(self):
        result = self.minimal_result()
        result["summary"]["ttl"]["keys_without_ttl"] = 0

        validation = validate_result(result)

        self.assertEqual(validation["logical"]["status"], "fail")
        self.assertIn("ttl total", "\n".join(validation["logical"]["details"]))

    def test_validate_result_rejects_finding_without_source(self):
        result = self.minimal_result()
        del result["findings"][0]["source"]

        validation = validate_result(result)

        self.assertEqual(validation["mechanical"]["status"], "fail")
        self.assertIn("findings[0].source is required", "\n".join(validation["mechanical"]["details"]))

    def test_validate_result_rejects_empty_outputs_metadata(self):
        result = self.minimal_result()
        result["outputs"] = {}

        validation = validate_result(result)

        self.assertEqual(validation["mechanical"]["status"], "fail")
        self.assertIn("outputs.output_dir is required", "\n".join(validation["mechanical"]["details"]))

    def test_failed_result_skips_logical_validation_when_no_logical_data_error(self):
        result = self.minimal_result()
        result["status"] = "failed"

        validation = validate_result(result)

        self.assertEqual(validation["mechanical"]["status"], "fail")
        self.assertEqual(validation["logical"]["status"], "skipped")
        self.assertEqual(validation["sufficiency"]["status"], "insufficient")


if __name__ == "__main__":
    unittest.main()
