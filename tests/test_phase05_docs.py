import re
import unittest
from pathlib import Path


class Phase05DocsTests(unittest.TestCase):
    def read(self, path):
        return Path(path).read_text(encoding="utf-8")

    def test_required_phase05_documents_exist(self):
        required = [
            "docs/skill-design-experience.md",
            "docs/anti-patterns.md",
            "docs/comparison/axe-side-evidence.md",
            "docs/comparison/dba-assistant-reuse-record.md",
            "docs/reviews/project-phase-01-to-05-summary.md",
            "docs/reviews/phase-05-review.md",
            "docs/reviews/phase-05-closeout.md",
        ]

        missing = [path for path in required if not Path(path).exists()]

        self.assertEqual(missing, [])

    def test_skill_design_experience_answers_seven_questions(self):
        doc = self.read("docs/skill-design-experience.md")
        required_questions = [
            "What should a Skill own?",
            "What should a Tool or custom function own?",
            "How can agent behavior be driven by Skill as much as possible?",
            "How can business flow avoid being over-hardcoded in code?",
            "How can Skill become a core project asset?",
            "How should assets, scripts, references, and profiles be managed around a Skill?",
            "How can the project preserve LLM decision capability while keeping results reliable and auditable?",
        ]

        missing = [question for question in required_questions if question not in doc]

        self.assertEqual(missing, [])

    def test_anti_patterns_have_required_sections(self):
        doc = self.read("docs/anti-patterns.md")
        required_titles = [
            "Hard-Coding Local Absolute Paths",
            "LLM Performs Deterministic Arithmetic",
            "Parser Failures Hidden Behind Success",
            "Silent Fallback Parsers",
            "Scripts Become the Workflow Brain",
            "Thresholds Inside SKILL.md",
            "Report Layout Inside SKILL.md",
            "read_file for /tmp Outputs",
            "Introducing src Too Early",
            "Multiple Execution Entrypoints",
        ]

        for title in required_titles:
            with self.subTest(title=title):
                self.assertIn(title, doc)
        self.assertGreaterEqual(len(re.findall(r"Problem\n", doc)), 10)
        self.assertGreaterEqual(len(re.findall(r"Why it is harmful\n", doc)), 10)
        self.assertGreaterEqual(len(re.findall(r"Observed or possible example\n", doc)), 10)
        self.assertGreaterEqual(len(re.findall(r"Preferred pattern\n", doc)), 10)

    def test_axe_side_evidence_covers_six_dimensions_and_limitations(self):
        doc = self.read("docs/comparison/axe-side-evidence.md")
        for dimension in [
            "C1 Skill readability",
            "C2 Run stability",
            "C3 LLM decision space",
            "C4 token / latency",
            "C5 Debuggability",
            "C6 Cross-scenario reuse",
        ]:
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, doc)
        self.assertIn("Unavailable metric", doc)
        self.assertIn("manual axe vs DeepAgents comparison", doc)

    def test_reuse_record_documents_reused_and_discarded_choices(self):
        doc = self.read("docs/comparison/dba-assistant-reuse-record.md")
        for section in [
            "Logic Reused",
            "Logic Intentionally Discarded",
            "Directory Structure Not Reused",
            "Parser Strategy Changes",
            "Skill vs Script vs Tools Boundary Changes",
            "Why the axe Structure Is Different",
        ]:
            with self.subTest(section=section):
                self.assertIn(section, doc)

    def test_final_summary_states_ready_for_manual_comparison(self):
        doc = self.read("docs/reviews/project-phase-01-to-05-summary.md")
        for phase in ["Phase-01", "Phase-02", "Phase-03", "Phase-04", "Phase-05"]:
            with self.subTest(phase=phase):
                self.assertIn(phase, doc)
        self.assertIn("Ready for manual comparison: yes", doc)
        self.assertIn("Known Limitations", doc)
        self.assertIn("Recommended Next Step", doc)

    def test_phase_closeouts_01_to_05_exist(self):
        missing = [
            phase
            for phase in ["01", "02", "03", "04", "05"]
            if not Path("docs/reviews/phase-%s-closeout.md" % phase).exists()
        ]

        self.assertEqual(missing, [])

    def test_no_generated_run_archives_are_committed(self):
        prohibited = [
            path
            for path in Path(".").rglob("*")
            if ".git" not in path.parts
            and (
                path.match("tmp/axe_rdb_assistant/*")
                or path.match("docs/reviews/phase04-repeat-*/result.json")
                or path.match("audit/meta.json")
            )
        ]

        self.assertEqual([str(path) for path in prohibited], [])


if __name__ == "__main__":
    unittest.main()
