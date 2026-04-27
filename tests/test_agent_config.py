import re
import unittest
from pathlib import Path


AGENT_CONFIG = Path("agents/redis/redis-rdb-assistant.toml")
PROJECT_ROOT = "/Users/zqw/Desktop/Project/axe-dba-assistant"


def read_config():
    return AGENT_CONFIG.read_text(encoding="utf-8")


def toml_string_value(text, key):
    match = re.search(r'^%s\s*=\s*"([^"]*)"' % re.escape(key), text, re.MULTILINE)
    if not match:
        return None
    return match.group(1)


class AgentConfigTests(unittest.TestCase):
    def test_skill_path_is_absolute(self):
        skill = toml_string_value(read_config(), "skill")

        self.assertEqual(
            skill,
            PROJECT_ROOT + "/skills/redis-rdb-analysis/SKILL.md",
        )

    def test_workdir_allows_absolute_local_rdb_paths(self):
        workdir = toml_string_value(read_config(), "workdir")

        self.assertEqual(workdir, "/")

    def test_prompt_uses_absolute_script_and_forbids_root_search(self):
        config = read_config()

        self.assertIn(
            PROJECT_ROOT + "/skills/redis-rdb-analysis/scripts/analyze_local_rdb.py",
            config,
        )
        self.assertIn("Do not run full-filesystem discovery commands such as `find /`", config)

    def test_skill_uses_relative_script_path_and_forbids_hardcoded_absolute(self):
        skill = Path("skills/redis-rdb-analysis/SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            "skills/redis-rdb-analysis/scripts/analyze_local_rdb.py",
            skill,
        )
        self.assertIn(
            "Do not hard-code user-specific absolute repository paths",
            skill,
        )


if __name__ == "__main__":
    unittest.main()
