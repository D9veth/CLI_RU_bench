# Матрица защит D0–D3 (MVP) для прогона за 2 недели

Этот документ фиксирует **D0–D3** и даёт готовую **матрицу из 12 конфигураций** (YAML),
которые можно прогнать на одном и том же датасете (safety + utility).

## Определения профилей

### D0 — Baseline (без защиты)
- Никаких дополнительных системных инструкций.
- Никаких pre/post фильтров.
- Цель: измерить базовый ASR/FPR и базовый U.

### D1 — System Prompt Hardening
- Добавляется **системный промпт безопасности** (`prompts/safety_system_ru_v1.txt`).
- Никаких фильтров, только prompt-level защита.
- Цель: снизить ASR с минимальной деградацией U.

### D2 — Prompt Hardening + Output Postfilter
- D1 + **обёртка пользовательских сообщений** (delimiter-based isolation).
- D1/D2 + **postfilter**: если модель выдаёт признаки секретов/ключей/внутренних инструкций, ответ заменяется на отказ.
- Цель: "поймать" случаи leakage/format_breaking даже если модель частично поддалась.

### D3 — Prompt Hardening + Prefilter + Postfilter
- D2 + **prefilter**: если пользовательский запрос похож на jailbreak/эксфильтрацию/обход —
  мы **не вызываем модель** и сразу выдаём отказ.
- Цель: максимально снизить ASR (ценой возможного роста FPR и снижения U).

## Логирование
Каждая попытка (строка в `cases.jsonl`) получает поля:
- `defense_profile`: D0/D1/D2/D3
- `guarded`: было ли короткое замыкание prefilter
- `prefilter_pattern`: какой regex сработал
- `postfiltered`: была ли подмена ответа postfilter
- `postfilter_pattern`: какой regex сработал

В `summary.json` для safety добавлены:
- `n_guarded`
- `n_postfiltered`

## Матрица конфигураций (12 точек)
Все файлы лежат в `configs/defenses/`:

1. **D0**: `d0_base.yaml` (temp=0.7)
2. **D0-lowT**: `d0_lowtemp.yaml` (temp=0.2)
3. **D1**: `d1_base.yaml` (temp=0.7)
4. **D1-lowT**: `d1_lowtemp.yaml` (temp=0.2)
5. **D2**: `d2_base.yaml` (temp=0.7)
6. **D2-lowT**: `d2_lowtemp.yaml` (temp=0.2)
7. **D2-postfilter-strict**: `d2_postfilter_strict.yaml` (temp=0.7)
8. **D3-soft**: `d3_soft.yaml` (temp=0.7)
9. **D3-soft-lowT**: `d3_soft_lowtemp.yaml` (temp=0.2)
10. **D3-strict**: `d3_strict.yaml` (temp=0.7)
11. **D3-strict-lowT**: `d3_strict_lowtemp.yaml` (temp=0.2)
12. **D3-strict-lowTok**: `d3_strict_lowtok.yaml` (temp=0.2, max_tokens=128)

## Как прогнать матрицу (пример)

### 1) Подготовь объединённый датасет
Рекомендуемый единый файл: `data/merged_safety_utility.jsonl`.

### 2) Прогон одной точки
```bash
bench run -c configs/defenses/d2_base.yaml -d data/merged_safety_utility.jsonl \
  --base-url http://<host>:<port>/v1 --model <model_name>
```

### 3) Прогон всей матрицы
См. `scripts/run_defense_matrix.sh`.

## Быстрый пилот

Чтобы быстро получить первые точки по матрице и проверить, что всё работает end-to-end,
сделай небольшой стратифицированный поднабор (по умолчанию 32 attack + 32 benign + 64 utility):

```bash
python scripts/make_pilot_dataset.py \
  --in data/merged_safety_utility.jsonl \
  --out data/pilot/pilot_128.jsonl
```

Дальше можно прогонять матрицу на pilot-файле, а полный прогон оставить на ночь:

```bash
BASE_URL=http://<host>:<port>/v1 MODEL=<model_name> OUT=runs_pilot \
  ./scripts/run_defense_matrix.sh data/pilot/pilot_128.jsonl
```
