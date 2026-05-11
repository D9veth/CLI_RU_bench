import json

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.artifacts.models import ProjectArtifact
from apps.artifacts.services.project_artifact_scanner import (
    classify_artifact,
    import_all_project_artifacts,
    iter_candidate_files,
)
from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_repo(root):
    (root / "backend").mkdir()
    (root / "bench").mkdir()
    (root / "data").mkdir()
    (root / "configs").mkdir()
    (root / "runs" / "demo").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "results").mkdir()
    (root / "data" / "pilot_20.jsonl").write_text('{"id": 1, "prompt": "test"}\n', encoding="utf-8")
    (root / "configs" / "D1.yaml").write_text("level: D1\nname: policy\n", encoding="utf-8")
    (root / "runs" / "demo" / "summary.json").write_text('{"proxy_asr": 0.1}', encoding="utf-8")
    (root / "runs" / "demo" / "report.md").write_text("# Demo report\n\nOK", encoding="utf-8")
    (root / "results" / "summary.csv").write_text("model,proxy_asr\nlocal,0.1\n", encoding="utf-8")
    (root / "docs" / "WEB_APP.md").write_text("# Web app\n", encoding="utf-8")


@pytest.mark.django_db
def test_project_artifact_scanner_imports_useful_files_idempotently(tmp_path):
    create_repo(tmp_path)
    dataset = Dataset.objects.create(
        name="Pilot",
        slug="pilot",
        file_path="data/pilot_20.jsonl",
        dataset_type=Dataset.DatasetType.PILOT,
    )
    profile = DefenseProfile.objects.create(
        name="D1",
        slug="d1",
        level=DefenseProfile.Level.D1,
        yaml_path="configs/D1.yaml",
    )
    model_endpoint = ModelEndpoint.objects.create(
        name="Local",
        slug="local",
        provider=ModelEndpoint.Provider.LMSTUDIO,
        model_name="local",
        base_url="http://localhost:1234/v1",
    )
    run = BenchmarkRun.objects.create(
        run_id="demo",
        title="Demo",
        dataset=dataset,
        defense_profile=profile,
        model_endpoint=model_endpoint,
        output_dir="runs/demo",
    )

    files = list(iter_candidate_files(tmp_path))
    assert tmp_path / "data" / "pilot_20.jsonl" in files
    assert classify_artifact(tmp_path / "results" / "summary.csv", tmp_path) == ProjectArtifact.ArtifactType.TABLE

    summary = import_all_project_artifacts(tmp_path)
    second_summary = import_all_project_artifacts(tmp_path)

    assert summary["imported"] == ProjectArtifact.objects.count()
    assert second_summary["imported"] == 0
    assert second_summary["updated"] == summary["imported"]
    assert ProjectArtifact.objects.get(file_path="data/pilot_20.jsonl").related_dataset == dataset
    assert ProjectArtifact.objects.get(file_path="configs/D1.yaml").related_defense_profile == profile
    assert ProjectArtifact.objects.get(file_path="runs/demo/report.md").related_run == run


@pytest.mark.django_db
def test_project_artifact_api_preview_raw_and_ingest(tmp_path, monkeypatch, django_user_model):
    create_repo(tmp_path)
    monkeypatch.setattr("apps.artifacts.views.get_repo_root", lambda: tmp_path)
    monkeypatch.setattr("apps.artifacts.management.commands.ingest_project_artifacts.get_repo_root", lambda: tmp_path)

    admin = django_user_model.objects.create_user(
        username="admin",
        password="test-password",
        role=django_user_model.Role.ADMIN,
    )
    viewer = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )

    call_command("ingest_project_artifacts", root=str(tmp_path), dry_run=True)
    response = client_for(admin).post("/api/project-artifacts/ingest/", {"dry_run": False}, format="json")
    assert response.status_code == 200
    assert response.data["imported"] > 0

    list_response = client_for(viewer).get("/api/project-artifacts/?artifact_type=markdown")
    assert list_response.status_code == 200
    artifact_id = list_response.data["results"][0]["id"]

    preview = client_for(viewer).get(f"/api/project-artifacts/{artifact_id}/preview/")
    assert preview.status_code == 200
    assert "Web app" in preview.data["text"]

    raw = client_for(viewer).get(f"/api/project-artifacts/{artifact_id}/raw/")
    assert raw.status_code == 200
    assert b"Web app" in b"".join(raw.streaming_content)

    viewer_ingest = client_for(viewer).post("/api/project-artifacts/ingest/", {"dry_run": True}, format="json")
    assert viewer_ingest.status_code == 403


@pytest.mark.django_db
def test_project_artifact_json_preview(tmp_path, monkeypatch, django_user_model):
    create_repo(tmp_path)
    monkeypatch.setattr("apps.artifacts.views.get_repo_root", lambda: tmp_path)
    artifact = ProjectArtifact.objects.create(
        name="summary.json",
        artifact_type=ProjectArtifact.ArtifactType.JSON,
        file_path="runs/demo/summary.json",
        source_dir="runs",
        extension="json",
        size_bytes=(tmp_path / "runs" / "demo" / "summary.json").stat().st_size,
    )
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )

    response = client_for(user).get(f"/api/project-artifacts/{artifact.id}/preview/")

    assert response.status_code == 200
    assert json.loads(response.data["text"])["proxy_asr"] == 0.1
