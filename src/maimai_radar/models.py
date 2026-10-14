from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryResult:
    tool: str
    status: str
    payload: Any = None
    queried_at: str = ''
    coverage: str = 'unknown'
    message: str = ''


@dataclass
class Sku:
    item_id: str | int | float | None
    points: str | int | float | None = None
    cash: str | int | float | None = None
    trade_price: str | int | float | None = None


@dataclass
class Card:
    title: str
    kind: str
    points: str | int | float | None = None
    cash: str | int | float | None = None
    dates: str | None = None
    description: str = ''
    source_url: str | None = None
    source_tool: str = ''
    phase: str = '时间未确认'
    item_id: int | str | None = None
    skus: list[Sku] = field(default_factory=list)
    notes: str = ''
    detail_text: str = ''
    image_urls: list[str] = field(default_factory=list)
