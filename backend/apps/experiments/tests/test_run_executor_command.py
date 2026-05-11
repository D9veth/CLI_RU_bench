import json

import pytest

from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun
from apps.experiments.services.run_executor import build_cli_command


def create_run():
    dataset = Dataset.objects.create(
        name="Pilot",
        slug="pilot",
        file_path="data/pilot.jsonl",
        dataset_type=Dataset.DatasetType.PILOT,
    )
    profile = DefenseProfile.objects.create(
        name="D1",
        slug="d1",
        level=DefenseProfile.Level.D1,
        parameters_json={"system_prompt_path": "prompts/safety_system_ru_v1.txt"},
    )
    endpoint = ModelEndpoint.objects.create(
        name="Local LM Studio",
        slug="local-lm-studio",
        provider=ModelEndpoint.Provider.LMSTUDIO,
        model_name="local-model",
        base_url="http://localhost:1234/v1",
    )
    return BenchmarkRun.objects.create(
        run_id="command_run",
        title="Command run",
        model_endpoint=endpoint,
        dataset=dataset,
        defense_profile=profile,
        temperature_override=0.1,
        max_tokens_override=64,
    )


@pytest.mark.django_db
def test_build_cli_command_uses_config_dataset_and_out(tmp_path, monkeypatch):
    monkeypatch.setattr("apps.experiments.services.run_executor.get_repo_root", lambda: tmp_path)
    run = create_run()
    command = build_cli_command(run)

    assert command[:2] == ["bench", "run"]
    assert "--config" in command
    assert "--dataset" in command
    assert "--out" in command
    assert "--resume" in command

    config_path = command[command.index("--config") + 1]
    dataset_path = command[command.index("--dataset") + 1]
    out_path = command[command.index("--out") + 1]
    assert config_path.endswith("runs_web/command_run/web_run_config.json")
    assert dataset_path.endswith("data/pilot.jsonl")
    assert out_path.endswith("runs_web")

    generated_config = json.loads((tmp_path / "runs_web" / "command_run" / "web_run_config.json").read_text())
    assert generated_config["target"]["base_url"] == "http://localhost:1234/v1"
    assert generated_config["target"]["model"] == "local-model"
    assert generated_config["generation"]["temperature"] == 0.1
    assert generated_config["generation"]["max_tokens"] == 64
    assert generated_config["defense"]["profile"] == "D1"
