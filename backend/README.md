# Backend веб-приложения

Backend предоставляет инфраструктуру веб-приложения LLM Bench: пользователей, роли, JWT-аутентификацию, health endpoint, модели экспериментов, импорт CLI/project-артефактов и MVP-запуск benchmark-а через существующий CLI.

## Роли пользователей

- `admin` - полный доступ к backend API, включая управление пользователями.
- `researcher` - роль для создания и запуска экспериментов на следующих этапах.
- `viewer` - роль по умолчанию для обычных пользователей, предназначена для просмотра на следующих этапах.

Superuser автоматически получает роль `admin`, если роль не указана. Обычный пользователь по умолчанию получает роль `viewer`.

## Установка зависимостей

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Миграции

```bash
python manage.py makemigrations
python manage.py migrate
```

## Создание superuser

```bash
python manage.py createsuperuser
```

## Запуск сервера

```bash
python manage.py runserver
```

## Запуск тестов

```bash
pytest
```

## Начальное заполнение

```bash
python manage.py seed_demo_data
```

Команда идемпотентно создает demo-набор `DefenseProfile` D0-D3, пример `Dataset` на основе локального файла из `data/` и `ModelEndpoint` для локального OpenAI-compatible endpoint.

## Экспериментальные сущности

- `Dataset` - описание датасета и счетчики типов кейсов.
- `DefenseProfile` - профиль защиты D0-D3 или custom с путем к YAML и JSON-параметрами.
- `ModelEndpoint` - описание OpenAI-compatible endpoint, модели и дефолтных generation-настроек.
- `BenchmarkRun` - запись запуска benchmark-а без фактического запуска процесса на этом этапе.
- `RunMetrics` - агрегированные метрики запуска. `proxy_asr` означает эвристическую proxy-метрику текущего evaluator-а.
- `RunArtifact` - metadata артефакта запуска: путь, тип и размер.
- `ProjectArtifact` - metadata полезного файла проекта: датасета, конфига, отчёта, таблицы, графика, JSON/JSONL, лога, документа или скрипта.

`proxy_asr` - эвристическая proxy-метрика текущего evaluator-а. Она показывает долю атакующих кейсов без распознанного безопасного отказа или с найденным индикатором цели атаки и не является строгим доказательством фактического вредоносного успеха атаки.

## Импорт CLI-артефактов

Backend умеет искать существующие run directories в `runs/`, `runs_matrix/`, `runs_mistral_q5/`, `results/`, `artifacts/` и `runs_web/`. Директория считается запуском, если в ней есть `summary.json`, `report.md` или `cases.jsonl`.

```bash
python manage.py ingest_runs --dry-run
python manage.py ingest_runs
```

Команда идемпотентно создает или обновляет `Dataset`, `DefenseProfile`, `ModelEndpoint`, `BenchmarkRun`, `RunMetrics` и `RunArtifact`. Повторный запуск не создает дубликаты запусков и артефактов.

## Импорт артефактов проекта

Backend умеет сканировать полезные файлы проекта в `data/`, `configs/`, `runs/`, `runs_matrix/`, `runs_mistral_q5/`, `runs_web/`, `results/`, `artifacts/`, `docs/` и `scripts/`.

```bash
python manage.py ingest_project_artifacts --dry-run
python manage.py ingest_project_artifacts
python manage.py ingest_project_artifacts --type figure
```

Команда создает или обновляет `ProjectArtifact` и хранит только metadata: относительный путь, тип, источник, расширение, размер, line count, sha256 и связи с `BenchmarkRun`, `Dataset` или `DefenseProfile`, если они определены. Содержимое больших файлов в БД не сохраняется.

API:

- `GET /api/project-artifacts/` - список с фильтрами `artifact_type`, `source_dir`, `related_run`, `search`, `limit`, `offset`.
- `GET /api/project-artifacts/{id}/` - metadata файла.
- `GET /api/project-artifacts/{id}/preview/` - безопасный preview для text/json/jsonl/csv/markdown/log или информация для image.
- `GET /api/project-artifacts/{id}/raw/` - чтение локального файла через защищенный endpoint.
- `POST /api/project-artifacts/ingest/` - импорт из API, только `researcher/admin`.

## Создание запуска

`researcher` или `admin` может создать pending-запуск через API:

```http
POST /api/runs/
```

Минимальное тело:

```json
{
  "title": "Smoke run",
  "model_endpoint": 1,
  "dataset": 1,
  "defense_profile": 1,
  "temperature": 0.2,
  "max_tokens": 128,
  "extra_params": {
    "repeats": 1
  }
}
```

Backend автоматически выставляет `created_by`, `status=pending`, `output_dir=runs_web/<run_id>` и сохраняет snapshot выбранных model/dataset/defense/runtime параметров.

## Запуск benchmark из backend

MVP executor запускает существующий CLI через `subprocess` в background thread:

```http
POST /api/runs/{id}/start/
GET /api/runs/{id}/logs/
POST /api/runs/{id}/cancel/
```

Команда строится в форме:

```bash
bench run \
  --config runs_web/<run_id>/web_run_config.json \
  --dataset <dataset.file_path> \
  --out runs_web \
  --resume runs_web/<run_id> \
  --resume-force \
  --base-url <model_endpoint.base_url> \
  --model <model_endpoint.model_name>
```

`web_run_config.json` генерируется из `ModelEndpoint`, `DefenseProfile`, runtime overrides и `extra_params`. После завершения executor сохраняет `stdout.log` и `stderr.log`, регистрирует CLI-артефакты, обновляет `RunMetrics` из `summary.json` и переводит запуск в `completed` или `failed`.

Этот executor не предназначен для production-нагрузки. Для production later нужны Celery/Redis, PostgreSQL, worker isolation и полноценное управление жизненным циклом процессов.

## Основные endpoints

- `GET /api/health/` - health check без авторизации.
- `POST /api/auth/token/` - получение JWT access/refresh token.
- `POST /api/auth/token/refresh/` - обновление access token.
- `GET /api/auth/me/` - текущий пользователь.
- `GET /api/auth/users/` - список пользователей, только `admin`.
- `POST /api/auth/users/` - создание пользователя, только `admin`.
- `PATCH /api/auth/users/{id}/` - обновление пользователя, только `admin`.
- `DELETE /api/auth/users/{id}/` - soft-delete пользователя через `is_active=False`, только `admin`.
- `GET /api/datasets/` и `GET /api/datasets/{id}/` - чтение датасетов.
- `POST /api/datasets/` и `PATCH /api/datasets/{id}/` - создание и обновление датасетов, только `researcher/admin`.
- `DELETE /api/datasets/{id}/` - soft-delete датасета, только `admin`.
- `GET /api/defense-profiles/` и `GET /api/defense-profiles/{id}/` - чтение профилей защиты.
- `POST /api/defense-profiles/` и `PATCH /api/defense-profiles/{id}/` - создание и обновление профилей защиты, только `researcher/admin`.
- `DELETE /api/defense-profiles/{id}/` - soft-delete профиля защиты, только `admin`.
- `GET /api/model-endpoints/` и `GET /api/model-endpoints/{id}/` - чтение model endpoints.
- `POST /api/model-endpoints/` и `PATCH /api/model-endpoints/{id}/` - создание и обновление model endpoints, только `researcher/admin`.
- `DELETE /api/model-endpoints/{id}/` - soft-delete model endpoint, только `admin`.
- `GET /api/runs/` и `GET /api/runs/{id}/` - чтение запусков.
- `GET /api/runs/?status=pending&dataset=1&model_endpoint=1&defense_profile=1&created_by=1` - фильтрация списка запусков.
- `POST /api/runs/` и `PATCH /api/runs/{id}/` - создание и обновление запусков, только `researcher/admin`.
- `DELETE /api/runs/{id}/` - отмена незавершенного запуска или удаление completed-запуска, только `admin`.
- `POST /api/runs/{id}/start/` - запуск pending benchmark-а через backend executor, только `researcher/admin`.
- `POST /api/runs/{id}/cancel/` - отмена pending-запуска; остановка running-процесса в MVP не реализована.
- `GET /api/runs/{id}/logs/` - чтение `stdout.log` и `stderr.log`.
- `GET /api/runs/{id}/metrics/` - метрики конкретного запуска.
- `POST /api/run-metrics/` и `PATCH /api/run-metrics/{id}/` - создание и обновление метрик, только `researcher/admin`.
- `GET /api/runs/{id}/artifacts/` - артефакты конкретного запуска.
- `GET /api/runs/{id}/report/` - markdown-отчет запуска из `report.md`.
- `GET /api/runs/{id}/cases/?limit=100` - первые кейсы из `cases.jsonl`, максимум 1000.
- `POST /api/runs/ingest/` - импорт CLI-артефактов в БД, только `researcher/admin`.
- `GET /api/dashboard/` - агрегаты для dashboard: счетчики, средние метрики, последние запуски, распределения и heatmap-данные.
- `GET /api/results/` - completed runs с основными метриками.
- `GET /api/results/pareto/` - точки для Pareto-графика.
- `GET /api/results/heatmap/` - строки, колонки и значения `proxy_asr` для heatmap.
- `GET /api/artifacts/` и `GET /api/artifacts/{id}/` - чтение артефактов.
- `POST /api/artifacts/` и `PATCH /api/artifacts/{id}/` - создание и обновление артефактов, только `researcher/admin`.
- `DELETE /api/artifacts/{id}/` - удаление артефакта, только `admin`.
- `GET /api/project-artifacts/` и `GET /api/project-artifacts/{id}/` - чтение артефактов проекта.
- `GET /api/project-artifacts/{id}/preview/` - предпросмотр небольших файлов или первых строк.
- `GET /api/project-artifacts/{id}/raw/` - raw-доступ к файлу внутри repo root.
- `POST /api/project-artifacts/ingest/` - импорт артефактов проекта, только `researcher/admin`.
