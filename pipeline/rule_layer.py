import re
from dataclasses import dataclass
from typing import Optional

from entity_extraction import RE_DUPLICATE


@dataclass
class RuleMatch:
    category_code: str
    category_label: str
    rule_id: str


_RULES = [
    (
        "dup_by_number_pattern",
        "duplicate_application",
        "Дублирующее (повторное) заявление",
        None,  
    ),
    (
        "dup_keyword",
        "duplicate_application",
        "Дублирующее (повторное) заявление",
        re.compile(r"дублиру|повторн(ого|ое)\s+заявлен", re.IGNORECASE),
    ),
    (
        "org_not_found",
        "organization_not_found",
        "Не найдена организация для регистрации заявления",
        re.compile(r"не найдена организация для регистрации заявления", re.IGNORECASE),
    ),
    (
        "application_not_found",
        "application_not_found",
        "Заявление не найдено",
        re.compile(r"^\s*заявление не найдено\.?\s*$", re.IGNORECASE),
    ),
    (
        "wrong_date_order",
        "invalid_date_error",
        "Ошибка в датах заявления (дата поступления раньше подачи)",
        re.compile(r"желаемая дата поступления не может быть раньше", re.IGNORECASE),
    ),
    (
        "missing_certificate_titlepage",
        "missing_document_certificate",
        "Не хватает документа об образовании (аттестат/титульный лист)",
        re.compile(
            r"(титульн\w* лист|неполн\w* отображени\w* документа об основном общем)",
            re.IGNORECASE,
        ),
    ),
    (
        "attach_certificate_scan",
        "missing_document_certificate",
        "Не хватает документа об образовании (аттестат/титульный лист)",
        re.compile(
            r"прикрепите.{0,15}(скан|документ).{0,40}аттестат|"
            r"предоставьте скан-копию аттестата|"
            r"предоставить все страницы аттестата",
            re.IGNORECASE,
        ),
    ),
    (
        "no_documents_provided",
        "missing_document_generic",
        "Документы не предоставлены / неполный пакет",
        re.compile(
            r"документы не были предоставлены|"
            r"не предъявлены все документы, требуемые порядком приема",
            re.IGNORECASE,
        ),
    ),
    (
        "medical_certificate_required",
        "missing_medical_certificate",
        "Требуется медицинская справка",
        re.compile(r"медицинск\w* справк|медицинск\w* осмотр|врача[- ]?психиатр", re.IGNORECASE),
    ),
    (
        "cancelled_by_request",
        "cancelled_by_request",
        "Заявление отменено по запросу заявителя",
        re.compile(
            r"^\s*заявление отменено\.?\s*$|"
            r"заявление о постановке на учет отменено по запросу",
            re.IGNORECASE,
        ),
    ),
    (
        "testing_required",
        "testing_required",
        "Требуется пройти вступительное тестирование",
        re.compile(r"тестирование.{0,80}проходной балл|минимальный проходной балл", re.IGNORECASE),
    ),
    (
        "epgu_registration_notice",
        "procedural_registration_notice",
        "Служебное уведомление о регистрации/номере заявления (не причина отказа)",
        re.compile(
            r"индивидуальный номер заявления|"
            r"внутренний номер заявления|"
            r"зарегистрировано под номером г\s*-?\s*\d",
            re.IGNORECASE,
        ),
    ),
    (
        "wrong_priority",
        "invalid_priority",
        "Неверный приоритет заявления",
        re.compile(r"неверный приоритет", re.IGNORECASE),
    ),
    (
        "single_specialty_only",
        "multiple_specialty_violation",
        "Подача возможна только на одну специальность",
        re.compile(r"подача заявления возможна на одну специальность", re.IGNORECASE),
    ),
]


def apply_rules(text: Optional[str]) -> Optional[RuleMatch]:
    if not text or not text.strip():
        return None

    if RE_DUPLICATE.search(text):
        return RuleMatch("duplicate_application", "Дублирующее (повторное) заявление", "dup_by_number_pattern")

    for rule_id, code, label, rex in _RULES:
        if rex is None:
            continue
        if rex.search(text):
            return RuleMatch(code, label, rule_id)

    return None
