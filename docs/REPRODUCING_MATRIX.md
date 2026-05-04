# Воспроизведение Экспериментальной Матрицы

Этот документ описывает воспроизводимый путь от проверки окружения до полной матрицы защитных конфигураций.

## Предусловия

- Python 3.10+.
- Установленный пакет: `pip install -e ".[dev,analysis]"`.
- Локальный или удаленный OpenAI-compatible endpoint.
- Подготовленные датасеты в `data/`.
- Для локального endpoint-а можно использовать LM Studio или совместимый сервер.

## Проверка Окружения

```bash
bench --help
bench validate-dataset --in data/pilot_20.jsonl --out tmp/dataset_validation_report.json
bench doctor --config configs/local_1234.yaml
```

`bench doctor` отправляет короткий preflight-запрос к модели. Если endpoint или модель отличаются от `configs/local_1234.yaml`, задайте их в конфиге или используйте флаги `--base-url`, `--endpoint-url`, `--model`, `--api-key-env` при `bench run`.

## Smoke Run

```bash
bench run \
  --config configs/local_1234.yaml \
  --dataset data/pilot_20.jsonl \
  --out runs
```

Smoke run нужен для проверки схемы датасета, доступности модели, записи `cases.jsonl`, `summary.json` и `report.md`. Для быстрой диагностики используйте `data/pilot_20.jsonl`, а не полный датасет.

## Полный Запуск Матрицы

В репозитории есть два способа запуска набора defense-конфигов.

### Через Python Wrapper

```bash
python scripts/run_matrix.py \
  --configs-dir configs/defenses \
  --dataset data/merged_safety_utility.jsonl \
  --split test \
  --dataset-version course-v1 \
  --repeats 1 \
  --out runs_matrix \
  --base-url http://localhost:1234/v1 \
  --model your-model-name \
  --api-key-env OPENAI_API_KEY
```

`scripts/run_matrix.py` сам находит YAML-конфиги в `configs/defenses/`, пропускает `_target_placeholder.yaml` и smoke-конфиги, затем последовательно вызывает `bench run`.

### Через Shell Script

```bash
BASE_URL=http://localhost:1234/v1 \
MODEL=your-model-name \
OUT=runs_matrix \
API_KEY_ENV=OPENAI_API_KEY \
scripts/run_defense_matrix.sh data/merged_safety_utility.jsonl
```

Этот вариант проходит по `configs/defenses/*.yaml` и пишет run directories в `$OUT`.

## Агрегация Результатов

```bash
python scripts/aggregate_results.py \
  --runs runs_matrix \
  --runs runs_mistral_q5 \
  --out results/results_matrix_full.csv \
  --warnings-out results/aggregation_warnings.csv \
  --report-json results/aggregation_report.json
```

Скрипт читает `run_config.json`, `summary.json` и при необходимости `cases.jsonl`, затем строит нормализованную таблицу. Неполные run directories не ломают агрегацию, но попадают в warnings.

## Построение Графиков

Pareto-график:

```bash
python scripts/plot_pareto.py \
  --in results/results_matrix_full.csv \
  --out results/pareto.png
```

Набор графиков для анализа:

```bash
python scripts/plot_results_suite.py \
  --results results/results_matrix_full.csv \
  --exports-dir analysis_exports \
  --out-dir results/figures
```

Если нужны дополнительные CSV для `analysis_exports`, используйте существующие скрипты подготовки/экспорта из `scripts/` под конкретный сценарий анализа.

## Ожидаемые Выходы

- `results/results_matrix_full.csv` - агрегированная матрица запусков;
- `results/matrix_report.md` - человекочитаемый отчет, если он был подготовлен отдельным analysis workflow;
- `results/pareto.png` и `results/figures/*.png` - графики;
- `runs_matrix/<run_id>/` - сырые артефакты каждого запуска.

