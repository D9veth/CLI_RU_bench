from __future__ import annotations

import csv
import json
from pathlib import Path

from bench.core.manual_audit import (
    BLIND_COLUMNS,
    create_audit_sample,
    redact_secrets_in_text,
    score_annotations,
    validate_annotations,
)


FIXTURES = Path(__file__).parent / "fixtures"
CASES = FIXTURES / "audit_cases.jsonl"
ANNOTATIONS = FIXTURES / "audit_annotations_filled.csv"
MANIFEST = FIXTURES / "audit_manifest.json"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_audit_sample_creates_blind_csv_and_manifest(tmp_path: Path):
    out = tmp_path / "audit"
    result = create_audit_sample(cases_files=[CASES], out_dir=out, n=20, seed=42)

    blind = out / "audit_sample_blind.csv"
    manifest = out / "audit_manifest.json"
    with_evaluator = out / "audit_sample_with_evaluator.csv"

    assert result["selected"] == 20
    assert blind.exists()
    assert manifest.exists()
    assert with_evaluator.exists()

    rows = _read_csv(blind)
    assert len(rows) == 20
    assert list(rows[0]) == BLIND_COLUMNS
    assert not any(column.startswith("evaluator_") for column in rows[0])

    manifest_data = _read_json(manifest)
    assert len(manifest_data["selected_sample_ids"]) == 20
    assert manifest_data["evaluator_labels"]
    assert "evaluator_attack_success" in next(iter(manifest_data["evaluator_labels"].values()))


def test_audit_sample_is_deterministic(tmp_path: Path):
    out_a = tmp_path / "audit_a"
    out_b = tmp_path / "audit_b"
    create_audit_sample(cases_files=[CASES], out_dir=out_a, n=20, seed=123)
    create_audit_sample(cases_files=[CASES], out_dir=out_b, n=20, seed=123)

    cases_a = [
        (case["run_id"], case["case_id"])
        for case in _read_json(out_a / "audit_manifest.json")["normalized_cases"]
    ]
    cases_b = [
        (case["run_id"], case["case_id"])
        for case in _read_json(out_b / "audit_manifest.json")["normalized_cases"]
    ]
    assert cases_a == cases_b


def test_redaction(tmp_path: Path):
    text = (
        "sk-testmanualaudit1234567890abcdef "
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature123 "
        "-----BEGIN PRIVATE KEY-----\nFAKEFAKEFAKEFAKE\n-----END PRIVATE KEY-----"
    )
    redacted = redact_secrets_in_text(text)
    assert "sk-testmanualaudit1234567890abcdef" not in redacted
    assert "eyJhbGciOiJIUzI1NiJ9" not in redacted
    assert "FAKEFAKEFAKEFAKE" not in redacted
    assert "[REDACTED_API_KEY]" in redacted
    assert "[REDACTED_JWT]" in redacted
    assert "[REDACTED_PRIVATE_KEY]" in redacted

    out = tmp_path / "audit"
    create_audit_sample(cases_files=[CASES], out_dir=out, n=20, seed=42)
    blind_text = (out / "audit_sample_blind.csv").read_text(encoding="utf-8")
    assert "sk-testmanualaudit1234567890abcdef" not in blind_text
    assert "supersecretexample12345" not in blind_text
    assert "FAKEFAKEFAKEFAKE" not in blind_text


def test_validate_accepts_valid_annotations():
    result = validate_annotations(annotations_path=ANNOTATIONS, manifest_path=MANIFEST)
    assert result["ok"] is True
    assert result["total_rows"] == 8
    assert result["invalid_values"] == []


def test_validate_rejects_invalid_values(tmp_path: Path):
    bad = tmp_path / "bad.csv"
    text = ANNOTATIONS.read_text(encoding="utf-8")
    bad.write_text(text.replace("AUDIT-000001,run_a,atk_001", "AUDIT-000001,run_a,atk_001"), encoding="utf-8")
    rows = _read_csv(bad)
    rows[0]["human_attack_success"] = "maybe"
    with bad.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = validate_annotations(annotations_path=bad, manifest_path=MANIFEST)
    assert result["ok"] is False
    assert result["invalid_values"][0]["field"] == "human_attack_success"


def test_score_attack_success_metrics(tmp_path: Path):
    result = score_annotations(
        annotations_path=ANNOTATIONS,
        manifest_path=MANIFEST,
        out_dir=tmp_path / "scored",
        bootstrap=0,
    )
    assert result["metrics_rows"] > 0
    metrics = _read_csv(tmp_path / "scored" / "metrics_summary.csv")
    attack = next(row for row in metrics if row["task"] == "attack_success" and row["group_by"] == "overall")
    assert attack["tp"] == "1"
    assert attack["fp"] == "1"
    assert attack["fn"] == "1"
    assert attack["tn"] == "1"
    assert float(attack["precision"]) == 0.5
    assert float(attack["recall"]) == 0.5
    assert float(attack["f1"]) == 0.5


def test_score_false_refusal_on_benign_only(tmp_path: Path):
    score_annotations(
        annotations_path=ANNOTATIONS,
        manifest_path=MANIFEST,
        out_dir=tmp_path / "scored",
        bootstrap=0,
    )
    metrics = _read_csv(tmp_path / "scored" / "metrics_summary.csv")
    false_refusal = next(row for row in metrics if row["task"] == "false_refusal" and row["group_by"] == "overall")
    assert false_refusal["n"] == "4"
    assert false_refusal["tp"] == "1"
    assert false_refusal["fp"] == "1"
    assert false_refusal["fn"] == "1"
    assert false_refusal["tn"] == "1"


def test_ambiguous_excluded(tmp_path: Path):
    ambiguous = tmp_path / "ambiguous.csv"
    rows = _read_csv(ANNOTATIONS)
    rows[0]["human_ambiguous"] = "1"
    with ambiguous.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    score_annotations(
        annotations_path=ambiguous,
        manifest_path=MANIFEST,
        out_dir=tmp_path / "scored",
        bootstrap=0,
    )
    metrics = _read_csv(tmp_path / "scored" / "metrics_summary.csv")
    attack = next(row for row in metrics if row["task"] == "attack_success" and row["group_by"] == "overall")
    assert attack["n"] == "3"


def test_missing_prediction_field_does_not_crash(tmp_path: Path):
    manifest = _read_json(MANIFEST)
    for case in manifest["normalized_cases"]:
        case["evaluator_leakage"] = None
    manifest_path = tmp_path / "manifest_no_leakage.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    result = score_annotations(
        annotations_path=ANNOTATIONS,
        manifest_path=manifest_path,
        out_dir=tmp_path / "scored",
        bootstrap=0,
    )
    assert any("leakage" in warning for warning in result["warnings"])
    metrics = _read_csv(tmp_path / "scored" / "metrics_summary.csv")
    assert any(row["task"] == "attack_success" for row in metrics)


def test_group_metrics_min_group_size(tmp_path: Path):
    score_annotations(
        annotations_path=ANNOTATIONS,
        manifest_path=MANIFEST,
        out_dir=tmp_path / "scored",
        bootstrap=0,
        by="category",
        min_group_size=3,
    )
    metrics = _read_csv(tmp_path / "scored" / "metrics_summary.csv")
    assert all(row["group_by"] == "overall" for row in metrics)
