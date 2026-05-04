# LLM Bench CLI

`LLM Bench CLI` - консольный benchmarking-стенд для оценки защитных конфигураций LLM на safety/utility датасетах через OpenAI-compatible API endpoint. Проект используется для воспроизводимого сравнения профилей защит по ASR/FPR/TPR, utility и latency.

## Возможности

- запуск benchmark-а на локальном или удаленном OpenAI-compatible API;
- профили защиты D0-D3: baseline, system prompt, prefilter/wrapping, postfilter;
- safety и utility датасеты в YAML/JSONL;
- сохранение case-level артефактов каждого запуска;
- агрегация run directories в results matrix;
- построение таблиц и графиков для анализа компромисса safety/utility/latency.

## Структура Репозитория

```text
bench/      основной пакет и CLI entrypoint bench.cli:app
configs/    конфиги target/model/defense профилей
data/       малые датасеты и локальные подготовленные выборки
scripts/    запуск матрицы, агрегация, графики, подготовка данных
docs/       документация по воспроизведению, артефактам и разработке
examples/   небольшие примеры артефактов
tests/      минимальные автоматические проверки
results/    агрегированные результаты курсовой матрицы
runs_matrix/ сырые run directories полной матрицы
```

Канонические результаты курсовой матрицы лежат в репозитории: сырые run directories в `runs_matrix/` и `runs_mistral_q5/`, агрегированные таблицы в `results/`, дополнительные audit-артефакты в `artifacts/`. Отдельный реестр экспериментов находится в [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md). Новые ad-hoc запуски по умолчанию пишите в `runs/`; эта директория остается локальной и закрыта в `.gitignore`.

## Быстрый Старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,analysis]"
bench --help
```

На Windows используйте активацию окружения, принятую для вашей shell, например `.venv\Scripts\activate`.

## Проверка Датасета

```bash
bench validate-dataset \
  --in data/pilot_20.jsonl \
  --out tmp/dataset_validation_report.json
```

Команда проверяет базовую схему: `id`, `type`, `messages`, роли сообщений, уникальность идентификаторов, обязательные поля utility-кейсов и предупреждения по `category`/`family_id`.

## Проверка Подключения К Модели

```bash
bench doctor --config configs/local_1234.yaml
```

Нужен доступный OpenAI-compatible endpoint. Для локальной проверки подходит, например, LM Studio с API server на `http://localhost:1234/v1`. Модель, `base_url` и имя переменной с API key задаются в конфиге или переопределяются флагами CLI.

## Минимальный Запуск

```bash
bench run \
  --config configs/local_1234.yaml \
  --dataset data/pilot_20.jsonl \
  --out runs
```

После успешного запуска внутри `runs/<run_id>/` появятся:

- `run_config.json` - фактическая конфигурация запуска и provenance;
- `preflight.json` - результат проверки endpoint-а;
- `cases.jsonl` - построчные case-level результаты;
- `summary.json` - агрегированные метрики;
- `report.md` - человекочитаемый отчет.

Небольшой пример такой структуры лежит в [examples/minimal_result](examples/minimal_result/README.md).

## Воспроизведение Полной Матрицы

Инструкция по smoke run, полному запуску D0-D3, агрегации и графикам описана в [docs/REPRODUCING_MATRIX.md](docs/REPRODUCING_MATRIX.md).

## Проведенные Эксперименты

Сводка уже выполненных запусков и ссылки на артефакты описаны в [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md). Кратко: в репозитории сохранена матрица из 48 комбинаций модель x defense config, включая сырые `cases.jsonl`, `summary.json`, `report.md` по каждому запуску и агрегированные CSV/Markdown-отчеты.
