import os
import uuid
from datetime import datetime, timezone

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values, Json

from rule_layer import apply_rules  
from main_pipeline import process_record, compute_source_hash


DB_DSN = dict(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    dbname=os.environ.get("POSTGRES_DB", "moku_repos"),
    user=os.environ.get("POSTGRES_USER", "vetgy"),
    password=os.environ.get("POSTGRES_PASSWORD", "255233255233"),
    port=os.environ.get("POSTGRES_PORT", "5432"),
)


def get_existing_hashes(conn, pairs):
    if not pairs:
        return {}
    with conn.cursor() as cur:
        cur.execute("SELECT num, current_datetime, source_hash FROM application_status_enriched")
        rows = cur.fetchall()
    all_hashes = {(num, str(dt)): h for num, dt, h in rows}
    wanted = set(pairs)
    return {k: v for k, v in all_hashes.items() if k in wanted}


def _finish_run(conn, run_id, status, rows_read=None, rows_processed=None,
                 rows_new_candidates=None, error_message=None):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE pipeline_run_log SET
                finished_at = now(), status = %s, rows_read = %s, rows_processed = %s,
                rows_new_candidates = %s, error_message = %s
            WHERE run_id = %s
        """, (status, rows_read, rows_processed, rows_new_candidates, error_message, run_id))
    conn.commit()


def run_load() -> dict:
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    conn = psycopg2.connect(**DB_DSN)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO pipeline_run_log (run_id, run_type, started_at, status)
            VALUES (%s, 'full_load', %s, 'running')
        """, (run_id, started_at))
    conn.commit()

    try:
        src = pd.read_sql(
            "SELECT num, start_datetime, current_datetime, status_name, status_comment, region "
            "FROM source_application_status ORDER BY current_datetime",
            conn,
        )
        rows_read = len(src)

        if rows_read == 0:
            _finish_run(conn, run_id, 'success', rows_read=0, rows_processed=0, rows_new_candidates=0)
            return {'rows_read': 0, 'rows_processed': 0}

        pairs = list(zip(src['num'], src['current_datetime'].astype(str)))
        existing_hashes = get_existing_hashes(conn, pairs)

        enriched_rows, candidate_rows = [], []
        rows_processed = 0

        for _, row in src.iterrows():
            key = (row['num'], str(row['current_datetime']))
            new_hash = compute_source_hash(row['status_comment'])
            if existing_hashes.get(key) == new_hash:
                continue  

            rec = process_record(
                num=row['num'], current_datetime=str(row['current_datetime']),
                status_name=row['status_name'], status_comment=row['status_comment'],
            )
            rows_processed += 1

            enriched_rows.append((
                rec.num, rec.current_datetime, row['start_datetime'], rec.status_name,
                rec.status_comment_raw, row['region'], rec.is_meaningful,
                rec.reason_category_code, rec.reason_category_label, rec.category_source,
                rec.category_confidence, rec.epgu_current_num, rec.related_app_num,
                rec.related_app_date, Json(rec.other_dates), Json(rec.urls), rec.internal_ref,
                Json(rec.extra_entities) if rec.extra_entities else None,
                rec.is_new_category_candidate, rec.source_hash, run_id,
            ))

            if rec.is_new_category_candidate:
                candidate_rows.append((rec.num, rec.current_datetime, rec.status_comment_raw))

        if enriched_rows:
            with conn.cursor() as cur:
                execute_values(cur, """
                    INSERT INTO application_status_enriched (
                        num, current_datetime, start_datetime, status_name, status_comment_raw,
                        region, is_meaningful, reason_category_code, reason_category_label,
                        category_source, category_confidence, epgu_current_num, related_app_num,
                        related_app_date, other_dates, urls, internal_ref, extra_entities,
                        is_new_category_candidate, source_hash, pipeline_run_id
                    ) VALUES %s
                    ON CONFLICT (num, current_datetime) DO UPDATE SET
                        is_meaningful = EXCLUDED.is_meaningful,
                        reason_category_code = EXCLUDED.reason_category_code,
                        reason_category_label = EXCLUDED.reason_category_label,
                        category_source = EXCLUDED.category_source,
                        category_confidence = EXCLUDED.category_confidence,
                        epgu_current_num = EXCLUDED.epgu_current_num,
                        related_app_num = EXCLUDED.related_app_num,
                        related_app_date = EXCLUDED.related_app_date,
                        other_dates = EXCLUDED.other_dates,
                        urls = EXCLUDED.urls,
                        internal_ref = EXCLUDED.internal_ref,
                        extra_entities = EXCLUDED.extra_entities,
                        is_new_category_candidate = EXCLUDED.is_new_category_candidate,
                        source_hash = EXCLUDED.source_hash,
                        processed_at = now(),
                        pipeline_run_id = EXCLUDED.pipeline_run_id
                """, enriched_rows)
            conn.commit()

        if candidate_rows:
            with conn.cursor() as cur:
                execute_values(cur, """
                    INSERT INTO uncategorized_candidates (num, current_datetime, status_comment_raw)
                    VALUES %s
                    ON CONFLICT (num, current_datetime) DO NOTHING
                """, candidate_rows)
            conn.commit()

        _finish_run(conn, run_id, 'success', rows_read=rows_read, rows_processed=rows_processed,
                    rows_new_candidates=len(candidate_rows))

        return {'rows_read': rows_read, 'rows_processed': rows_processed,
                'skipped_idempotent': rows_read - rows_processed, 'new_candidates': len(candidate_rows)}

    except Exception as e:
        _finish_run(conn, run_id, 'failed', error_message=str(e))
        raise
    finally:
        conn.close()
