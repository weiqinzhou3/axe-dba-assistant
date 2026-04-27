import unittest
from pathlib import Path


class Phase01StructureTests(unittest.TestCase):
    def test_required_phase01_files_exist(self):
        required = [
            "agents/redis/redis-rdb-assistant.toml",
            "skills/redis-rdb-analysis/SKILL.md",
            "skills/redis-rdb-analysis/scripts/analyze_local_rdb.py",
            "skills/redis-rdb-analysis/references/redis_bigkey_thresholds.yaml",
            "skills/redis-rdb-analysis/references/redis_risk_levels.yaml",
            "skills/redis-rdb-analysis/references/redis_recommendations.yaml",
            "skills/redis-rdb-analysis/references/profiles/default.yaml",
            "skills/redis-rdb-analysis/references/profiles/rcs.yaml",
            "skills/redis-rdb-analysis/references/profiles/concise.yaml",
            "skills/redis-rdb-analysis/assets/docx_templates/minimal_report_template.docx",
            "tools/docx_renderer/render_docx.py",
            "tools/docx_renderer/README.md",
            "tools/validation/validate_result.py",
            "tools/validation/README.md",
            "docs/reviews/phase-01-review.md",
            "docs/reviews/phase-01-closeout.md",
        ]

        missing = [path for path in required if not Path(path).exists()]

        self.assertEqual(missing, [])

    def test_prohibited_phase01_directories_do_not_exist(self):
        self.assertFalse(Path("src").exists())
        self.assertFalse(Path("scripts").exists())

    def test_skill_contains_required_sections(self):
        skill = Path("skills/redis-rdb-analysis/SKILL.md").read_text()
        required_sections = [
            "Task Definition",
            "Supported Inputs",
            "Intent Recognition Rules",
            "Local RDB Analysis Flow",
            "Script Usage Rules",
            "Output Requirements",
            "Evidence and Source Requirements",
            "Validation Requirements",
            "Uncertainty Handling",
            "Forbidden Behaviors",
        ]

        missing = [section for section in required_sections if section not in skill]

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
