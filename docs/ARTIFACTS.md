# Артефакты Запуска

Каждый `bench run` создает отдельную директорию `runs/<run_id>/` или `<out>/<run_id>/`. Минимальный пример лежит в `examples/minimal_result/`.

## `run_config.json`

Фактическая конфигурация запуска. Включает секции `target`, `generation`, `defense`, `run`, а также provenance-поля:

- `dataset_path`, `dataset_id`, `dataset_version`, `dataset_split`;
- `dataset_hash`;
- `config_hash`;
- `scoring_rules_hash`;
- `code_version`;
- `started_at`, `finished_at`;
- `config_source_path`, `config_source_name`, если запуск был сделан из файла конфига.

## `preflight.json`

Результат проверки доступности модели до основного запуска:

- `ok`;
- `provider`;
- `base_url`;
- `model`;
- `latency_ms`;
- `error`, если проверка не прошла;
- `raw_sample` с коротким content/usage-фрагментом успешного ответа.

## `cases.jsonl`

Построчные результаты по кейсам. Один JSON object на одну попытку case/repeat.

Типичные поля текущего формата:

- идентификация: `case_id`, `repeat`, `case_type`, `category`, `family_id`;
- ожидание: `expected_action`;
- запрос: `request_messages`;
- runtime: `latency_ms`, `status`, `called_model`, `cache_hit`, `error_type`, `error_message`;
- prefilter/postfilter: `prefilter_hit`, `prefilter_pattern`, `prefilter_action`, `postfilter_hit`, `postfilter_pattern`, `postfilter_action`;
- ответ: `raw_text`, `final_text`, `response_text`;
- safety scoring: `predicted_action`, `refused`, `success`, `goal_hit`, `matched_goal_indicator`, `partial`, `success_attack`, `blocked_attack`, `false_positive`, `true_negative`, `refusal_signals`, `refusal_signal_strength`, `strong_refusal_signals`, `weak_refusal_signals`;
- utility scoring: `utility_task`, `utility_score`, `utility_details`, `utility_debug`;
- защита: `defense_profile`, `defense_effective`.

В исходных датасетах поле входных сообщений называется `messages`; в артефакте запуска сохраняются уже подготовленные к отправке `request_messages`, включая system prompt и wrapping, если они были включены defense-профилем.

`status` обычно принимает `ok`, `filtered_prefilter`, `filtered_postfilter`, `timeout`, `http_error` или `parse_error`.

## `summary.json`

Агрегированные метрики по всем строкам `cases.jsonl`:

- общие счетчики: `n_attempts`, `n_ok_attempts`, `n_failed_attempts`, `failure_rate`, `parse_error_rate`, `status_counts`;
- safety-блок: `counts`, `asr`, `tpr`, `fpr`, strict/lenient варианты, latency p50/p95, разрезы `by_category` и `by_family_id`;
- utility-блок: `u_mean`, `n_scored`, `by_task`;
- `run_meta`, если summary был записан через CLI после завершения запуска.

## `report.md`

Человекочитаемый Markdown-отчет по `summary.json`: количество attempts, safety metrics, разрезы по категориям, utility metrics и разрезы по задачам.

## Как Сейчас Считается ASR

ASR является эвристической proxy-метрикой текущего evaluator-а. Для attack-like кейсов агрегатор считает `ASR = FN / (TP + FN)`, где `FN` означает, что attack-labeled кейс не был заблокирован как безопасный отказ с учетом `goal_hit`. Это полезно для сравнительной автоматической оценки конфигураций, но не является доказательством фактического вредоносного успеха атаки.
