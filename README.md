Реализация раздела ТЗ **"Обработка данных"**: извлечение сущностей и
категоризация причин статусов заявлений из полусвободного текста
`status_comment`. Категоризация - **только regex-правила**

## Быстрый старт

```bash
cp .env  
docker compose up -d        
pip install -r requirements.txt

PYTHONPATH=pipeline python3 pipeline/load_source_csv.py data/moku_tech_task.csv

PYTHONPATH=pipeline python3 -c "
from pg_loader import run_load
print(run_load())
"
```


## Схема данных

См. `sql/schema.sql`:
- `source_application_status` — источник 
- `application_status_enriched` — витрина 
- `category_rules` — задел под перенос rule-layer в данные БД
- `uncategorized_candidates` — очередь текстов, не подошедших ни под одно
  правило
- `pipeline_run_log` — журнал запусков обработки


