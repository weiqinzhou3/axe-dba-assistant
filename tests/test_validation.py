import unittest

from tools.validation.validate_result import validate_result


class ValidateResultTests(unittest.TestCase):
    def minimal_result(self):
        return {
            "status": "success",
            "input": {
                "rdb_path": "/tmp/dump.rdb",
                "sha256": "a" * 64,
                "source": "input.rdb_path",
            },
            "summary": {
                "total_keys": 0,
                "db_count": 0,
                "type_distribution": {},
                "ttl": {
                    "keys_with_ttl": 0,
                    "keys_without_ttl": 0,
                },
                "source": "analysis.rdb_parser",
            },
            "findings": [],
            "validation": {
                "mechanical": {"status": "pass", "details": []},
                "logical": {"status": "pass", "details": []},
                "sufficiency": {"status": "sufficient", "details": []},
            },
            "uncertainties": [],
            "errors": [],
        }

    def test_validate_result_accepts_minimal_success_contract(self):
        validation = validate_result(self.minimal_result())

        self.assertEqual(validation["mechanical"]["status"], "pass")
        self.assertEqual(validation["logical"]["status"], "pass")
        self.assertEqual(validation["sufficiency"]["status"], "sufficient")

    def test_validate_result_rejects_invalid_status(self):
        result = self.minimal_result()
        result["status"] = "done"

        validation = validate_result(result)

        self.assertEqual(validation["mechanical"]["status"], "fail")
        self.assertIn("status must be one of", "\n".join(validation["mechanical"]["details"]))

    def test_validate_result_checks_type_distribution_total(self):
        result = self.minimal_result()
        result["summary"]["total_keys"] = 3
        result["summary"]["type_distribution"] = {"string": 2}

        validation = validate_result(result)

        self.assertEqual(validation["logical"]["status"], "fail")
        self.assertIn("type_distribution total", "\n".join(validation["logical"]["details"]))


if __name__ == "__main__":
    unittest.main()
