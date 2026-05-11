# LLM Bench Frontend

Vite + React + TypeScript frontend для веб-интерфейса LLM Bench. Интерфейс использует существующий Django API из `backend/` и не запускает benchmark напрямую: запуск идет через backend endpoint.

## Установка

```bash
cd frontend
npm install
```

## Env

Создайте локальный `.env` по примеру:

```bash
cp .env.example .env
```

Основная настройка:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Запуск dev

```bash
npm run dev
```

По умолчанию Vite слушает `http://127.0.0.1:5173`.

## Build

```bash
npm run build
```

## Страницы

- `/login` - вход по JWT.
- `/dashboard` - обзор запусков, метрик и распределений.
- `/runs` - список benchmark-запусков, статусы, start/cancel.
- `/runs/new` - создание запуска, только `admin/researcher`.
- `/runs/:id` - детали запуска, метрики, report, cases, artifacts, logs.
- `/results` - аналитика completed runs, Pareto и heatmap.
- `/artifacts` - артефакты проекта, фильтры, preview и raw-файлы.
- `/datasets` - справочник датасетов.
- `/configs` - профили защиты.
- `/models` - model endpoints.
- `/users` - пользователи, только `admin`.
- `/settings` - настройки frontend/API и текущий пользователь.

## Роли

- `admin` - полный доступ, включая пользователей.
- `researcher` - создание и запуск benchmark-запусков, редактирование справочников.
- `viewer` - просмотр dashboard/results/runs и справочников.

## Импорт артефактов проекта

Страница `/artifacts` работает с backend endpoint-ами:

- `GET /api/project-artifacts/`
- `GET /api/project-artifacts/{id}/preview/`
- `GET /api/project-artifacts/{id}/raw/`
- `POST /api/project-artifacts/ingest/`

Кнопка "Импортировать артефакты" видна только `admin` и `researcher`. `viewer` может смотреть таблицу, metadata, preview и raw-файлы.

Backend-команды:

```bash
cd backend
python manage.py ingest_project_artifacts --dry-run
python manage.py ingest_project_artifacts
```
