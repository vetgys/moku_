CREATE TABLE IF NOT EXISTS source_application_status (
    num                 varchar     NOT NULL,
    start_datetime      timestamp   NOT NULL,
    current_datetime    timestamp   NOT NULL,
    status_name         varchar     NOT NULL,
    status_comment      text,
    region              varchar,
    loaded_at           timestamp   NOT NULL DEFAULT now(),
    PRIMARY KEY (num, current_datetime)
);

CREATE INDEX IF NOT EXISTS idx_source_current_dt
    ON source_application_status (current_datetime);

CREATE TABLE IF NOT EXISTS application_status_enriched (
    num                     varchar     NOT NULL,
    current_datetime        timestamp   NOT NULL,
    start_datetime          timestamp,
    status_name              varchar,
    status_comment_raw       text,
    region                    varchar,

    is_meaningful             boolean     NOT NULL,
    reason_category_code      varchar,
    reason_category_label     varchar,
    category_source           varchar,       
    category_confidence       numeric(5,4),  

    epgu_current_num          varchar,
    related_app_num           varchar,
    related_app_date          varchar,
    other_dates                jsonb,
    urls                        jsonb,
    internal_ref                varchar,
    extra_entities               jsonb,

    is_new_category_candidate    boolean     NOT NULL DEFAULT false,  
    source_hash                   varchar     NOT NULL,   
    processed_at                   timestamp   NOT NULL DEFAULT now(),
    pipeline_run_id                 varchar,               

    PRIMARY KEY (num, current_datetime)
);

CREATE INDEX IF NOT EXISTS idx_enriched_category
    ON application_status_enriched (reason_category_code);
CREATE INDEX IF NOT EXISTS idx_enriched_related_num
    ON application_status_enriched (related_app_num);
CREATE INDEX IF NOT EXISTS idx_enriched_candidate
    ON application_status_enriched (is_new_category_candidate)
    WHERE is_new_category_candidate = true;

CREATE TABLE IF NOT EXISTS category_rules (
    rule_id             varchar     PRIMARY KEY,
    category_code       varchar     NOT NULL,
    category_label       varchar     NOT NULL,
    pattern_regex          text        NOT NULL,
    priority                integer     NOT NULL DEFAULT 100,  
    is_active                boolean     NOT NULL DEFAULT true,
    created_at                timestamp   NOT NULL DEFAULT now(),
    updated_at                 timestamp   NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS uncategorized_candidates (
    id                    bigserial   PRIMARY KEY,
    num                     varchar     NOT NULL,
    current_datetime           timestamp   NOT NULL,
    status_comment_raw           text        NOT NULL,
    is_resolved                    boolean     NOT NULL DEFAULT false,
    resolved_category_code            varchar,
    created_at                          timestamp   NOT NULL DEFAULT now(),
    UNIQUE (num, current_datetime)
);


CREATE TABLE IF NOT EXISTS pipeline_run_log (
    run_id                varchar     PRIMARY KEY,
    run_type                varchar     NOT NULL DEFAULT 'full_load',
    started_at                  timestamp   NOT NULL,
    finished_at                   timestamp,
    status                          varchar     NOT NULL,   
    rows_read                        integer,
    rows_processed                     integer,
    rows_new_candidates                   integer,
    error_message                          text
);
