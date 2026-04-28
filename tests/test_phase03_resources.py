import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from zipfile import ZipFile


SKILL_ROOT = Path("skills/redis-rdb-analysis")
SCRIPT = SKILL_ROOT / "scripts/analyze_local_rdb.py"
HIGH_VERSION_RDB = Path("tests/fixtures/rdb/high_version/redis_v12_hash_with_hfe.rdb")


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class Phase03ResourceTests(unittest.TestCase):
    def test_required_reference_profile_and_asset_files_exist(self):
        required = [
            SKILL_ROOT / "references/redis_bigkey_thresholds.yaml",
            SKILL_ROOT / "references/redis_risk_levels.yaml",
            SKILL_ROOT / "references/redis_recommendations.yaml",
            SKILL_ROOT / "references/redis_type_notes.yaml",
            SKILL_ROOT / "references/ttl_risk_rules.yaml",
            SKILL_ROOT / "references/profiles/default.yaml",
            SKILL_ROOT / "references/profiles/rcs.yaml",
            SKILL_ROOT / "references/profiles/concise.yaml",
            SKILL_ROOT / "assets/report_outline.yaml",
            SKILL_ROOT / "assets/docx_templates/minimal_report_template.docx",
            SKILL_ROOT / "assets/examples/summary_example.txt",
            SKILL_ROOT / "assets/examples/result_example.json",
        ]

        missing = [str(path) for path in required if not path.exists()]

        self.assertEqual(missing, [])

    def test_reference_yaml_files_are_parseable_and_structured(self):
        references = {
            "redis_bigkey_thresholds.yaml": ["thresholds"],
            "redis_risk_levels.yaml": ["levels"],
            "redis_recommendations.yaml": ["recommendations"],
            "redis_type_notes.yaml": ["types"],
            "ttl_risk_rules.yaml": ["rules"],
        }

        for filename, required_keys in references.items():
            with self.subTest(filename=filename):
                data = load_yaml(SKILL_ROOT / "references" / filename)
                self.assertIsInstance(data, dict)
                self.assertEqual(data.get("version"), 1)
                for key in required_keys:
                    self.assertIn(key, data)

    def test_bigkey_thresholds_define_required_type_rules(self):
        data = load_yaml(SKILL_ROOT / "references/redis_bigkey_thresholds.yaml")
        thresholds = data["thresholds"]

        for key in ["string", "hash", "list", "set", "zset", "stream"]:
            with self.subTest(threshold=key):
                self.assertIn(key, thresholds)
                self.assertIn("metric", thresholds[key])
                self.assertIn("warning", thresholds[key])
                self.assertIn("critical", thresholds[key])
                self.assertIn("rationale", thresholds[key])

    def test_risk_levels_use_required_severity_names(self):
        data = load_yaml(SKILL_ROOT / "references/redis_risk_levels.yaml")

        self.assertEqual(
            set(data["levels"].keys()),
            {"info", "low", "medium", "high", "critical"},
        )
        for level in data["levels"].values():
            self.assertIn("meaning", level)

    def test_profiles_have_required_fields_and_no_execution_logic(self):
        required_fields = {
            "language",
            "detail_level",
            "include_docx",
            "include_json",
            "include_summary",
            "report_style",
            "max_findings",
        }
        forbidden_fields = {"parser", "parser_strategy", "command", "script", "rdb_binary"}

        for profile_path in sorted((SKILL_ROOT / "references/profiles").glob("*.yaml")):
            with self.subTest(profile=profile_path.name):
                data = load_yaml(profile_path)
                self.assertTrue(required_fields.issubset(data.keys()))
                self.assertFalse(forbidden_fields.intersection(data.keys()))
                self.assertIsInstance(data["max_findings"], int)
                self.assertGreater(data["max_findings"], 0)

    def test_report_outline_has_required_sections(self):
        data = load_yaml(SKILL_ROOT / "assets/report_outline.yaml")
        sections = data["sections"]
        section_ids = [section["id"] for section in sections]

        self.assertEqual(
            section_ids,
            [
                "analysis_target",
                "parser_metadata",
                "basic_statistics",
                "ttl_overview",
                "type_distribution",
                "findings",
                "validation_results",
                "uncertainties_and_limitations",
                "generated_outputs",
            ],
        )
        for section in sections:
            self.assertIn("heading", section)
            self.assertIn("source", section)

    def test_skill_is_thin_and_points_to_resources(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("references/redis_bigkey_thresholds.yaml", skill)
        self.assertIn("assets/report_outline.yaml", skill)
        self.assertNotIn("/Users/", skill)
        self.assertNotIn("1048576", skill)
        self.assertNotIn("100000", skill)


class Phase03ScriptIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(HIGH_VERSION_RDB.exists(), "high-version RDB fixture is unavailable")
    def test_script_includes_profile_and_reference_metadata(self):
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
                    "--profile",
                    "concise",
                    "--user-request",
                    "Please analyze this RDB concisely.",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["profile"]["name"], "concise")
            self.assertEqual(result["profile"]["source"], "references/profiles/concise.yaml")
            self.assertEqual(result["resources"]["report_outline"], "assets/report_outline.yaml")
            self.assertEqual(result["resources"]["references_status"], "available")

    @unittest.skipUnless(HIGH_VERSION_RDB.exists(), "high-version RDB fixture is unavailable")
    def test_docx_uses_external_report_outline_headings(self):
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
                    "Please analyze this RDB.",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            outline = load_yaml(SKILL_ROOT / "assets/report_outline.yaml")
            with ZipFile(output_dir / "report.docx") as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")

            for section in outline["sections"]:
                self.assertIn(section["heading"], document_xml)

    def test_unknown_profile_fails_with_reviewable_outputs(self):
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
                    "--profile",
                    "missing-profile",
                    "--user-request",
                    "Analyze with unknown profile.",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            result = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "failed")
            self.assertIn("profile not found", "\n".join(result["errors"]))
            self.assertTrue(result["outputs"]["result_json"]["exists"])


if __name__ == "__main__":
    unittest.main()
