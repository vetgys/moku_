**"Обработка данных"**: извлечение сущностей и
категоризация причин статусов заявлений из полусвободного текста
`status_comment`. Категоризация — **только regex-правила**

## Быстрый старт

docker compose up -d        
pip install -r requirements.txt

$env:PYTHONPATH="pipeline"
python pipeline/load_source_csv.py data/moku_tech_task.csv

python -c "from pg_loader import run_load print(run_load())"

Для отображения категорий:
docker compose exec postgres psql -h localhost -U vetgy -d moku_repos -c "SELECT reason_category_label, count(*) FROM application_status_enriched GROUP BY 1 ORDER BY 2 DESC LIMIT 15;"

## Схема данных

См. `sql/schema.sql`:
- `source_application_status` — источник 
- `application_status_enriched` — витрина 
- `category_rules` — задел под перенос rule-layer в данные БД
- `uncategorized_candidates` — очередь текстов, не подошедших ни под одно
  правило
- `pipeline_run_log` — журнал запусков обработки


