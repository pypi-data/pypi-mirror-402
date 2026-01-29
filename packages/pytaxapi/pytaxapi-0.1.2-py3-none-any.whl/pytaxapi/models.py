from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta


def now_iso_with_tz(offset_hours: int = 3) -> str:
    tz = timezone(timedelta(hours=offset_hours))
    return datetime.now(tz).isoformat(timespec="seconds")

@dataclass
class TaxClient:
    contact_phone: Optional[str] = None
    display_name: Optional[str] = None
    inn: Optional[str] = None
    income_type: str = "FROM_INDIVIDUAL"

@dataclass
class TaxServices:
    name: str
    amount: int
    quantity: int

@dataclass
class Receipt:
    operation_time: str
    services: List[TaxServices]
    total_amount: str
    client: TaxClient
    request_time: str = field(
        default_factory=lambda: now_iso_with_tz(3)
    )
    payment_type: str = "CASH"
    ignore_max_total_income_restriction: bool = False