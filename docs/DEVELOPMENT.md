# Разработка

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,analysis]"
```

`dev` ставит тестовый раннер, `analysis` - зависимости для графиков и CSV-анализа.

## Тесты

```bash
python -m pytest
```

Тесты написаны так, чтобы их можно было запустить и стандартным unittest:

```bash
python -m unittest discover -s tests
```

## Добавление Защитных Профилей

- Добавляйте новые конфиги в `configs/defenses/` или `configs/defenses_ablation/`.
- Для основных D0-D3 вариантов сохраняйте явное `defense.profile`.
- Не меняйте смысл профилей без отдельной миграции результатов.
- Для новых prefilter/postfilter правил используйте существующую структуру `FilterConfig`: `enabled`, `patterns`, `mode`, `action`, `case_sensitive`.
- Если меняются scoring rules, учитывайте, что `scoring_rules_hash` попадет в `run_config.json`.

## Добавление Датасетов

- Для малых проверочных наборов используйте `data/pilot_*.jsonl` или отдельные небольшие sample-файлы.
- Для больших локальных сборок используйте имена, закрытые в `.gitignore`, или добавьте точечное правило.
- Каждый новый датасет проверяйте командой:

```bash
bench validate-dataset --in path/to/dataset.jsonl --out tmp/dataset_validation_report.json
```

## Большие Результаты

Не коммитьте `runs/`, `runs_matrix/`, `runs_mistral_q5/`, `results/`, `artifacts/`, root-level PNG/CSV с результатами и большие локальные датасеты. Для передачи полной матрицы используйте отдельный архив, release asset, внешнее хранилище или приложение к курсовой работе.
