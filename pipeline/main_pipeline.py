import hashlib
from dataclasses import dataclass, asdict
from typing import Optional, List
import pandas as pd
from entity_extraction import extract_entities, ExtractedEntities
from rule_layer import apply_rules


@dataclass
class EnrichedRecord:
    num: str
    current_datetime: str
    status_name: str
    status_comment_raw: Optional[str]
    is_meaningful: bool
    reason_category_code: Optional[str]
    reason_category_label: Optional[str]
    category_source: Optional[str]   
    category_confidence: Optional[float]  
    epgu_current_num: Optional[str]
    related_app_num: Optional[str]
    related_app_date: Optional[str]
    other_dates: List[str]
    urls: List[str]
    internal_ref: Optional[str]
    extra_entities: Optional[dict]
    source_hash: str
    is_new_category_candidate: bool  

    def to_dict(self):
        return asdict(self)


def compute_source_hash(status_comment: Optional[str]) -> str:
    raw = status_comment if (status_comment is not None and not pd.isna(status_comment)) else "__NULL__"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def process_record(
    num: str,
    current_datetime: str,
    status_name: str,
    status_comment: Optional[str],
) -> EnrichedRecord:
    entities: ExtractedEntities = extract_entities(status_comment)
    src_hash = compute_source_hash(status_comment)

    if not entities.is_meaningful:
        return EnrichedRecord(
            num=num, current_datetime=current_datetime, status_name=status_name,
            status_comment_raw=status_comment, is_meaningful=False,
            reason_category_code=None, reason_category_label=None,
            category_source=None, category_confidence=None,
            epgu_current_num=None, related_app_num=None, related_app_date=None,
            other_dates=[], urls=[], internal_ref=None, extra_entities=None,
            source_hash=src_hash, is_new_category_candidate=False,
        )

    rule_match = apply_rules(status_comment)
    if rule_match is not None:
        cat_code, cat_label, cat_source, cat_conf = (
            rule_match.category_code, rule_match.category_label, "rule", 1.0
        )
        is_candidate = False
    else:
        cat_code, cat_label, cat_source, cat_conf = None, None, None, None
        is_candidate = True

    return EnrichedRecord(
        num=num, current_datetime=current_datetime, status_name=status_name,
        status_comment_raw=status_comment, is_meaningful=True,
        reason_category_code=cat_code, reason_category_label=cat_label,
        category_source=cat_source, category_confidence=cat_conf,
        epgu_current_num=entities.epgu_current_num,
        related_app_num=entities.related_app_num,
        related_app_date=entities.related_app_date,
        other_dates=entities.other_dates, urls=entities.urls,
        internal_ref=entities.internal_ref, extra_entities=entities.extra,
        source_hash=src_hash, is_new_category_candidate=is_candidate,
    )
