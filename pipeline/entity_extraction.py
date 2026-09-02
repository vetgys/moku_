import re
from dataclasses import dataclass, field, asdict
from typing import Optional

RU_MONTHS = r'(?:январ[яь]|феврал[яь]|март[а]?|апрел[яь]|ма[йя]|июн[яь]|июл[яь]|август[а]?|сентябр[яь]|октябр[яь]|ноябр[яь]|декабр[яь])'

RE_EPGU_CURRENT = re.compile(
    r'Индивидуальный\s+номер\s+заявления\s+([\d\s]{15,25})', re.IGNORECASE
)
RE_DUPLICATE = re.compile(
    r'заявлени[ея]\s+с\s+номером\s+(\d{10,20})\s+от\s+(\d{1,2}\s+' + RU_MONTHS + r'\s+\d{4})',
    re.IGNORECASE
)
RE_DATE_ISO = re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')
RE_DATE_DMY_DOT = re.compile(r'\b(\d{1,2}\.\d{1,2}\.\d{2,4})\b')
RE_DATE_TEXT = re.compile(r'\b(\d{1,2}\s+' + RU_MONTHS + r'\s+\d{4})\b', re.IGNORECASE)
RE_URL = re.compile(r'https?://[^\s,()]+')
RE_INTERNAL_REF = re.compile(r'номером?\s+Г\s*-?\s*(\d+)', re.IGNORECASE)

# мусорные значения без содержательной информации
GARBAGE_VALUES = {'.', '..', '-', '--', '=', '+', 'да', 'нет', '1'}


@dataclass
class ExtractedEntities:
    is_meaningful: bool
    epgu_current_num: Optional[str] = None
    related_app_num: Optional[str] = None
    related_app_date: Optional[str] = None
    other_dates: list = field(default_factory=list)
    urls: list = field(default_factory=list)
    internal_ref: Optional[str] = None
    extra: Optional[dict] = None

    def to_dict(self):
        return asdict(self)


def _clean_num(s: str) -> str:
    return re.sub(r'\s+', '', s)


def extract_entities(text: Optional[str]) -> ExtractedEntities:
    if text is None or (isinstance(text, float)):
        return ExtractedEntities(is_meaningful=False)

    stripped = text.strip()
    if stripped == '' or stripped.lower() in GARBAGE_VALUES:
        return ExtractedEntities(is_meaningful=False)

    # На случай нескольких совпадений в одном тексте
    epgu_all = [_clean_num(g) for g in RE_EPGU_CURRENT.findall(text)]
    epgu_current = epgu_all[0] if epgu_all else None

    dup_all = RE_DUPLICATE.findall(text)  # список кортежей (num, date)
    related_num, related_date = (dup_all[0][0], dup_all[0][1]) if dup_all else (None, None)

    dates = set()
    for rex in (RE_DATE_ISO, RE_DATE_DMY_DOT, RE_DATE_TEXT):
        for mm in rex.finditer(text):
            dates.add(mm.group(1))
    # исключаем дату дубликата, чтобы не задваивать
    if related_date and related_date in dates:
        dates.discard(related_date)

    urls = RE_URL.findall(text)

    internal_ref = None
    m = RE_INTERNAL_REF.search(text)
    if m:
        internal_ref = f"Г-{m.group(1)}"

    extra = {}
    if len(epgu_all) > 1:
        extra['extra_epgu_nums'] = epgu_all[1:]
    if len(dup_all) > 1:
        extra['extra_related_apps'] = [{'num': n, 'date': d} for n, d in dup_all[1:]]

    return ExtractedEntities(
        is_meaningful=True,
        epgu_current_num=epgu_current,
        related_app_num=related_num,
        related_app_date=related_date,
        other_dates=sorted(dates),
        urls=urls,
        internal_ref=internal_ref,
        extra=extra or None,
    )
