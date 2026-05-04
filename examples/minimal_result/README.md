# Minimal Result Example

Эта папка показывает минимальную структуру результата одного `bench run`.

Файлы:

- `run_config.json` - пример фактической конфигурации и provenance-полей;
- `preflight.json` - пример успешной проверки OpenAI-compatible endpoint-а;
- `cases.jsonl` - три post-run строки: attack, benign и utility;
- `summary.json` - агрегированные метрики по этим строкам;
- `report.md` - человекочитаемый Markdown-отчет.

Реальный run directory имеет тот же набор основных файлов и обычно лежит в `runs/<run_id>/` или в директории, переданной через `bench run --out`.

`report.md` можно открыть обычным Markdown-viewer-ом или текстовым редактором. `summary.json` удобно смотреть через `jq`, Python или любой JSON viewer.
