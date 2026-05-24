# LLM Bench CLI

`LLM Bench CLI` - консольный benchmarking-стенд для оценки защитных конфигураций LLM на safety/utility датасетах через OpenAI-compatible API endpoint. Проект используется для воспроизводимого сравнения профилей защит по ASR/FPR/TPR, utility и latency.

## Возможности

- запуск benchmark-а на локальном или удаленном OpenAI-compatible API;
- профили защиты D0-D3: baseline, system prompt, normalization, prompt-injection policy, DLP, schema validation, prefilter/wrapping, postfilter;
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

## Backend веб-приложения

Базовая backend-инфраструктура Django/DRF находится в [backend/README.md](backend/README.md).

## Frontend веб-приложения

React/Vite dashboard находится в [frontend/README.md](frontend/README.md).

```bash
cd frontend
npm install
npm run dev
npm run build
```

Для локального домена используется `http://llmtest.local:5173`; backend API ожидается на `http://llmtest.local:8000`.

## Проверка Датасета

```bash
bench validate-dataset \
  --in data/pilot_20.jsonl \
  --out tmp/dataset_validation_report.json
```

Команда проверяет базовую схему: `id`, `type`, `messages`, роли сообщений, уникальность идентификаторов, обязательные поля utility-кейсов и предупреждения по `category`/`family_id`.

Regression smoke:

```bash
bench validate-dataset --in data/regression/smoke_50.jsonl
scripts/run_regression_smoke.sh
```

## Manual evaluator audit

```bash
bench audit sample --runs-dir results --out manual_audit/evaluator_audit_v1 --n 250 --seed 42
bench audit validate --annotations manual_audit/evaluator_audit_v1/audit_sample_blind_filled.csv --manifest manual_audit/evaluator_audit_v1/audit_manifest.json
bench audit score --annotations manual_audit/evaluator_audit_v1/audit_sample_blind_filled.csv --manifest manual_audit/evaluator_audit_v1/audit_manifest.json --out manual_audit/evaluator_audit_v1/scored --bootstrap 2000
```

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

## Backend/frontend и Docker

```bash
cd backend
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

cd ../frontend
npm ci
npm run dev
npm run build
```

Docker compose:

```bash
cp .env.example .env
docker compose build
docker compose up -d
docker compose ps
```

Тесты и clean release archive:

```bash
make test
make clean-release
```

## Воспроизведение Полной Матрицы

Инструкция по smoke run, полному запуску D0-D3, агрегации и графикам описана в [docs/REPRODUCING_MATRIX.md](docs/REPRODUCING_MATRIX.md).

## Проведенные Эксперименты

Сводка уже выполненных запусков и ссылки на артефакты описаны в [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md). Кратко: в репозитории сохранена матрица из 48 комбинаций модель x defense config, включая сырые `cases.jsonl`, `summary.json`, `report.md` по каждому запуску и агрегированные CSV/Markdown-отчеты.
