import unittest

from bench.core.dataset import Case, Message
from bench.core.metrics import aggregate_metrics


def _case(case_id: str, case_type: str, expected_action: str) -> Case:
    return Case(
        case_id=case_id,
        case_type=case_type,
        category=f"{case_type}_category",
        family_id=f"{case_type}_family",
        scenario="single_turn",
        messages=[Message(role="user", content="test")],
        expected_action=expected_action,
    )


class MetricsAggregationTests(unittest.TestCase):
    def test_safety_and_utility_metrics_keep_current_semantics(self):
        cases_by_id = {
            "attack_blocked": _case("attack_blocked", "attack", "safe_refusal"),
            "attack_success": _case("attack_success", "attack", "safe_refusal"),
            "benign_ok": _case("benign_ok", "benign", "allow"),
            "utility_ok": _case("utility_ok", "utility", "allow"),
        }
        rows = [
            {
                "case_id": "attack_blocked",
                "repeat": 0,
                "case_type": "attack",
                "status": "ok",
                "predicted_action": "refuse",
                "goal_hit": False,
                "blocked_attack": True,
                "latency_ms": 10.0,
            },
            {
                "case_id": "attack_success",
                "repeat": 0,
                "case_type": "attack",
                "status": "ok",
                "predicted_action": "comply",
                "goal_hit": True,
                "blocked_attack": False,
                "latency_ms": 20.0,
            },
            {
                "case_id": "benign_ok",
                "repeat": 0,
                "case_type": "benign",
                "status": "ok",
                "predicted_action": "comply",
                "false_positive": False,
                "latency_ms": 30.0,
            },
            {
                "case_id": "utility_ok",
                "repeat": 0,
                "case_type": "utility",
                "status": "ok",
                "utility_task": "ruMMLU",
                "utility_score": 0.75,
                "utility_details": {"accuracy": 0.75},
            },
        ]

        summary = aggregate_metrics(rows, cases_by_id)

        self.assertEqual(summary["safety"]["counts"], {"TP": 1, "FP": 0, "TN": 1, "FN": 1})
        self.assertEqual(summary["safety"]["asr"], 0.5)
        self.assertEqual(summary["safety"]["tpr"], 0.5)
        self.assertEqual(summary["safety"]["fpr"], 0.0)
        self.assertEqual(summary["utility"]["u_mean"], 0.75)
        self.assertEqual(summary["n_attempts"], 4)


if __name__ == "__main__":
    unittest.main()
