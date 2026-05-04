from pathlib import Path
import unittest

from bench.core.dataset_validate import validate_dataset_file


class DatasetValidationTests(unittest.TestCase):
    def test_pilot_20_dataset_is_valid(self):
        report = validate_dataset_file(Path("data/pilot_20.jsonl"))

        self.assertTrue(report.ok)
        self.assertEqual(report.counts["n_items"], 20)
        self.assertEqual(report.counts["n_errors"], 0)
        self.assertGreater(report.counts["n_attack"], 0)
        self.assertGreater(report.counts["n_benign"], 0)
        self.assertGreater(report.counts["n_utility"], 0)


if __name__ == "__main__":
    unittest.main()
