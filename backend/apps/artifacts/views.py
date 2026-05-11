import csv
import json
import mimetypes
from pathlib import Path

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.accounts.permissions import IsResearcherOrAdmin, IsViewerOrAbove
from apps.artifacts.models import ProjectArtifact, RunArtifact
from apps.artifacts.serializers import ProjectArtifactSerializer, RunArtifactSerializer
from apps.artifacts.services.project_artifact_scanner import (
    get_repo_root,
    import_all_project_artifacts,
)
from apps.common.viewsets import RolePermissionViewSetMixin
from apps.experiments.models import BenchmarkRun

MAX_PREVIEW_BYTES = 100 * 1024


class RunArtifactViewSet(RolePermissionViewSetMixin, viewsets.ModelViewSet):
    serializer_class = RunArtifactSerializer
    queryset = RunArtifact.objects.select_related("run").all()


class ProjectArtifactViewSet(RolePermissionViewSetMixin, viewsets.ModelViewSet):
    read_actions = {"list", "retrieve", "preview", "raw"}
    write_actions = {"create", "update", "partial_update", "ingest"}
    serializer_class = ProjectArtifactSerializer
    queryset = ProjectArtifact.objects.select_related(
        "related_run",
        "related_dataset",
        "related_defense_profile",
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()
        artifact_type = self.request.query_params.get("artifact_type")
        source_dir = self.request.query_params.get("source_dir")
        related_run = self.request.query_params.get("related_run")
        search = self.request.query_params.get("search")
        if artifact_type:
            queryset = queryset.filter(artifact_type=artifact_type)
        if source_dir:
            queryset = queryset.filter(source_dir=source_dir)
        if related_run:
            queryset = queryset.filter(related_run_id=related_run)
        if search:
            queryset = (queryset.filter(file_path__icontains=search) | queryset.filter(name__icontains=search)).distinct()
        return queryset.order_by("source_dir", "artifact_type", "file_path")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()
        limit = _parse_int(request.query_params.get("limit"), default=100, minimum=1, maximum=500)
        offset = _parse_int(request.query_params.get("offset"), default=0, minimum=0, maximum=1000000)
        serializer = self.get_serializer(queryset[offset : offset + limit], many=True)
        return Response({"count": total, "limit": limit, "offset": offset, "results": serializer.data})

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        artifact = self.get_object()
        try:
            path = _safe_artifact_path(artifact)
        except ValueError:
            return Response({"detail": "Invalid artifact path."}, status=400)
        if not path.is_file():
            return Response({"message": "Preview is not available", "missing": True})
        return Response(_build_preview(artifact, path, request))

    @action(detail=True, methods=["get"])
    def raw(self, request, pk=None):
        artifact = self.get_object()
        try:
            path = _safe_artifact_path(artifact)
        except ValueError:
            return Response({"detail": "Invalid artifact path."}, status=400)
        if not path.is_file():
            return Response({"detail": "File not found."}, status=404)
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return FileResponse(path.open("rb"), content_type=content_type, filename=path.name)

    @action(detail=False, methods=["post"], permission_classes=[IsResearcherOrAdmin])
    def ingest(self, request):
        dry_run = bool(request.data.get("dry_run", False))
        artifact_type = request.data.get("artifact_type") or None
        summary = import_all_project_artifacts(get_repo_root(), dry_run=dry_run, artifact_type=artifact_type)
        return Response(summary)

    def perform_destroy(self, instance):
        instance.delete()


class RunArtifactsByRunView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request, pk):
        run = get_object_or_404(BenchmarkRun, pk=pk)
        artifacts = RunArtifact.objects.filter(run=run).order_by("artifact_type", "id")
        data = RunArtifactSerializer(artifacts, many=True).data
        project_artifacts = ProjectArtifact.objects.filter(related_run=run).order_by("artifact_type", "file_path")
        for artifact in ProjectArtifactSerializer(project_artifacts, many=True).data:
            data.append(
                {
                    "id": artifact["id"],
                    "run": run.id,
                    "run_id": run.run_id,
                    "run_title": run.title,
                    "artifact_type": artifact["artifact_type"],
                    "file_path": artifact["file_path"],
                    "size_bytes": artifact["size_bytes"],
                    "created_at": artifact["created_at"],
                    "source": "project_artifact",
                    "project_artifact": artifact,
                }
            )
        return Response(data)


def _safe_artifact_path(artifact: ProjectArtifact) -> Path:
    repo_root = get_repo_root().resolve()
    path = (repo_root / artifact.file_path).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError:
        raise ValueError("Artifact path is outside repository root.")
    return path


def _build_preview(artifact: ProjectArtifact, path: Path, request) -> dict:
    if artifact.artifact_type == ProjectArtifact.ArtifactType.FIGURE:
        return {
            "type": "image",
            "message": "Image preview is available via raw endpoint.",
            "view_url": request.build_absolute_uri(f"/api/project-artifacts/{artifact.id}/raw/"),
            "metadata": artifact.metadata_json,
        }
    if artifact.extension == "csv":
        return _csv_preview(path)
    if artifact.extension == "jsonl":
        return _jsonl_preview(path)
    if artifact.extension == "json":
        return _json_preview(path)
    if artifact.extension in {"md", "log", "txt", "yaml", "yml", "py", "sh", "toml", "ini"}:
        return _text_preview(path, preview_type=artifact.extension or "text")
    return {"type": artifact.artifact_type, "message": "Preview is not available", "metadata": artifact.metadata_json}


def _text_preview(path: Path, preview_type: str = "text") -> dict:
    text = _read_limited_text(path)
    return {"type": preview_type, "text": text, "truncated": path.stat().st_size > MAX_PREVIEW_BYTES}


def _json_preview(path: Path) -> dict:
    if path.stat().st_size > MAX_PREVIEW_BYTES:
        return _text_preview(path, "json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _text_preview(path, "json")
    return {"type": "json", "text": json.dumps(data, ensure_ascii=False, indent=2), "truncated": False}


def _jsonl_preview(path: Path) -> dict:
    rows = []
    with path.open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            if len(rows) >= 50:
                break
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"raw": line.strip()})
    return {"type": "jsonl", "rows": rows, "truncated": (path.stat().st_size > MAX_PREVIEW_BYTES or len(rows) >= 50)}


def _csv_preview(path: Path) -> dict:
    rows = []
    columns = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames or []
        for row in reader:
            if len(rows) >= 50:
                break
            rows.append(row)
    return {"type": "csv", "columns": columns, "rows": rows, "truncated": (path.stat().st_size > MAX_PREVIEW_BYTES or len(rows) >= 50)}


def _read_limited_text(path: Path) -> str:
    with path.open("rb") as file:
        data = file.read(MAX_PREVIEW_BYTES)
    return data.decode("utf-8", errors="ignore")


def _parse_int(value, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))
