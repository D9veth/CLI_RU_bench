# Проведенные Эксперименты

Этот файл фиксирует исследовательские запуски, которые намеренно хранятся в репозитории вместе с кодом. Он нужен как реестр артефактов для курсовой работы и как точка входа для проверки уже выполненной матрицы.

## Сохраненные Артефакты

| путь | назначение | статус |
| --- | --- | --- |
| `runs_matrix/` | 47 run directories полной матрицы | хранится в репозитории |
| `runs_mistral_q5/` | 1 run directory, использованный как часть полной матрицы | хранится в репозитории |
| `results/results_matrix_full.csv` | агрегированная полная матрица | хранится в репозитории |
| `results/results_matrix_target_full.csv` | целевая агрегированная таблица матрицы | хранится в репозитории |
| `results/matrix_report.md` | Markdown-отчет по заполнению матрицы | хранится в репозитории |
| `results/fill_missing_matrix_index.csv` | индекс дозаполнения матрицы | хранится в репозитории |
| `results_matrix.csv` | root-level агрегированная таблица совместимости со старыми скриптами | хранится в репозитории |
| `pareto_matrix.png` | готовый Pareto-график | хранится в репозитории |
| `artifacts/audit_demo*` | малые audit/demo артефакты | хранится в репозитории |

Ad-hoc запуски, которые не входят в каноническую матрицу, лучше писать в `runs/`: эта директория остается локальной и не попадает в git.

## Область Матрицы

Источник сводки: `results/matrix_report.md`.

- Датасет запуска: `data/merged_safety_utility_big.jsonl`.
- Target combinations: `48`.
- Сохраненные run folders: `48` total (`47` в `runs_matrix/`, `1` в `runs_mistral_q5/`).
- Модели: Gemma 3 12B, Llama 3.1 8B Instruct, Mistral 7B Q5, Qwen 2.5 7B Instruct.
- Профили защит: D0, D1, D2, D3.
- Defense configs: `d0_base`, `d0_lowtemp`, `d1_base`, `d1_lowtemp`, `d2_base`, `d2_lowtemp`, `d2_postfilter_strict`, `d3_soft`, `d3_soft_lowtemp`, `d3_strict`, `d3_strict_lowtemp`, `d3_strict_lowtok`.

## Карта Запусков

| family | model_key | defense_key | profile | run_id | root |
| --- | --- | --- | --- | --- | --- |
| Gemma | gemma_3_12b | d0_base | D0 | `20260305T120000Z_eced48` | `runs_matrix/` |
| Gemma | gemma_3_12b | d0_lowtemp | D0 | `20260306T123700Z_25f22a` | `runs_matrix/` |
| Gemma | gemma_3_12b | d1_base | D1 | `20260307T131400Z_7c569e` | `runs_matrix/` |
| Gemma | gemma_3_12b | d1_lowtemp | D1 | `20260308T135100Z_a50c7c` | `runs_matrix/` |
| Gemma | gemma_3_12b | d2_base | D2 | `20260309T142800Z_ac3b04` | `runs_matrix/` |
| Gemma | gemma_3_12b | d2_lowtemp | D2 | `20260310T150500Z_5609c5` | `runs_matrix/` |
| Gemma | gemma_3_12b | d2_postfilter_strict | D2 | `20260311T154200Z_845755` | `runs_matrix/` |
| Gemma | gemma_3_12b | d3_soft | D3 | `20260312T161900Z_107063` | `runs_matrix/` |
| Gemma | gemma_3_12b | d3_soft_lowtemp | D3 | `20260313T165600Z_360c82` | `runs_matrix/` |
| Gemma | gemma_3_12b | d3_strict | D3 | `20260314T173300Z_753eb2` | `runs_matrix/` |
| Gemma | gemma_3_12b | d3_strict_lowtemp | D3 | `20260315T181000Z_1d96b5` | `runs_matrix/` |
| Gemma | gemma_3_12b | d3_strict_lowtok | D3 | `20260316T184700Z_4e0f15` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d0_base | D0 | `20260317T093500Z_9f330b` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d0_lowtemp | D0 | `20260318T101200Z_7dec10` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d1_base | D1 | `20260319T104900Z_a4d0ad` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d1_lowtemp | D1 | `20260320T112600Z_855abf` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d2_base | D2 | `20260321T120300Z_183fb4` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d2_lowtemp | D2 | `20260322T124000Z_92962e` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d2_postfilter_strict | D2 | `20260323T131700Z_a0aa93` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d3_soft | D3 | `20260324T135400Z_7c5509` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d3_soft_lowtemp | D3 | `20260325T143100Z_b287ac` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d3_strict | D3 | `20260326T150800Z_2dd804` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d3_strict_lowtemp | D3 | `20260327T154500Z_0871d8` | `runs_matrix/` |
| Llama | llama_3_1_8b_instruct | d3_strict_lowtok | D3 | `20260328T162200Z_e8fc51` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d0_base | D0 | `20260329T024800Z_6fe11f` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d0_lowtemp | D0 | `20260330T091514Z_431f89` | `runs_mistral_q5/` |
| Mistral | mistral_7b_instruct_q5 | d1_base | D1 | `20260331T032500Z_e2b469` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d1_lowtemp | D1 | `20260401T040200Z_253b72` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d2_base | D2 | `20260402T043900Z_444515` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d2_lowtemp | D2 | `20260403T051600Z_f9cfd3` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d2_postfilter_strict | D2 | `20260404T055300Z_eec753` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d3_soft | D3 | `20260405T063000Z_bd69aa` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d3_soft_lowtemp | D3 | `20260406T070700Z_02c8fb` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d3_strict | D3 | `20260407T074400Z_c7ae63` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d3_strict_lowtemp | D3 | `20260408T082100Z_00b562` | `runs_matrix/` |
| Mistral | mistral_7b_instruct_q5 | d3_strict_lowtok | D3 | `20260409T085800Z_ceed14` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d0_base | D0 | `20260410T192400Z_cea8d1` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d0_lowtemp | D0 | `20260411T200100Z_85924c` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d1_base | D1 | `20260412T203800Z_d8611e` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d1_lowtemp | D1 | `20260413T211500Z_afd44e` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d2_base | D2 | `20260414T215200Z_41279d` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d2_lowtemp | D2 | `20260415T222900Z_46d94c` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d2_postfilter_strict | D2 | `20260416T230600Z_a311da` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d3_soft | D3 | `20260417T234300Z_ec8488` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d3_soft_lowtemp | D3 | `20260418T002000Z_bfc470` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d3_strict | D3 | `20260419T005700Z_0284a8` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d3_strict_lowtemp | D3 | `20260420T013400Z_6679ca` | `runs_matrix/` |
| Qwen | qwen2_5_7b_instruct | d3_strict_lowtok | D3 | `20260421T021100Z_fc7ddd` | `runs_matrix/` |

## Как Проверить

Сырые артефакты одного запуска:

```bash
ls runs_matrix/20260410T192400Z_cea8d1
```

Агрегированная матрица:

```bash
python scripts/aggregate_results.py \
  --runs runs_matrix \
  --runs runs_mistral_q5 \
  --out results/results_matrix_full.csv \
  --warnings-out results/aggregation_warnings.csv
```

График:

```bash
python scripts/plot_pareto.py \
  --in results/results_matrix_full.csv \
  --out pareto_matrix.png
```

## Ограничение Интерпретации

Эти результаты зависят от модели, runtime, параметров генерации, датасета и текущих правил evaluator-а. ASR в таблицах остается эвристической proxy-метрикой, а не ручной верификацией вредоносного успеха.
