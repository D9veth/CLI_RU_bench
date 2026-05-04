import json
from pathlib import Path
import unittest


EXAMPLE_DIR = Path("examples/minimal_result")


class MinimalResultExampleTests(unittest.TestCase):
    def test_minimal_result_has_expected_files_and_shape(self):
        required = {
            "README.md",
            "run_config.json",
            "preflight.json",
            "cases.jsonl",
            "summary.json",
            "report.md",
        }
        self.assertTrue(EXAMPLE_DIR.is_dir())
        self.assertTrue(required.issubset({p.name for p in EXAMPLE_DIR.iterdir()}))

        run_config = json.loads((EXAMPLE_DIR / "run_config.json").read_text(encoding="utf-8"))
        preflight = json.loads((EXAMPLE_DIR / "preflight.json").read_text(encoding="utf-8"))
        summary = json.loads((EXAMPLE_DIR / "summary.json").read_text(encoding="utf-8"))
        rows = [
            json.loads(line)
            for line in (EXAMPLE_DIR / "cases.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(run_config["target"]["provider"], "openai_compatible")
        self.assertIn("dataset_hash", run_config)
        self.assertTrue(preflight["ok"])
        self.assertEqual(summary["n_attempts"], len(rows))
        self.assertEqual({row["case_type"] for row in rows}, {"attack", "benign", "utility"})
        self.assertTrue(all("request_messages" in row for row in rows))
        self.assertTrue(all("status" in row for row in rows))

    def test_minimal_result_does_not_contain_obvious_secret_tokens(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in EXAMPLE_DIR.iterdir()
            if path.is_file()
        )

        self.assertNotIn("sk-", combined)
        self.assertNotIn("Bearer ", combined)


if __name__ == "__main__":
    unittest.main()
