from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import datetime, date
from enum import Enum
from ..Shared.Enums.Code import Code
from ..Shared.Enums.Message import Message
from decimal import Decimal

from typing import Any


def _is_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except Exception:
        return False


def deep_serialize(obj: Any):

    # 1️⃣ None explícito
    if obj is None:
        return None

    # 2️⃣ datetime reales → SOLO FECHA
    if isinstance(obj, datetime):
        return obj.date().isoformat()

    if isinstance(obj, date):
        return obj.isoformat()

    # 3️⃣ Decimal
    if isinstance(obj, Decimal):
        return format(obj, ".2f")

    # 4️⃣ Enum
    if isinstance(obj, Enum):
        return obj.value if hasattr(obj, "value") else str(obj)

    # 5️⃣ String ISO datetime → SOLO FECHA
    if isinstance(obj, str):
        if "T" in obj and _is_iso_datetime(obj):
            return obj.split("T")[0]
        return obj

    # 6️⃣ Dataclass
    if is_dataclass(obj):
        return {k: deep_serialize(v) for k, v in asdict(obj).items()}

    # 7️⃣ Dict
    if isinstance(obj, dict):
        return {k: deep_serialize(v) for k, v in obj.items()}

    # 8️⃣ List / tuple / set
    if isinstance(obj, (list, tuple, set)):
        return [deep_serialize(item) for item in obj]

    # 9️⃣ Fallback
    return obj


@dataclass
class Response:
    status: str = field(default=Code.PROCESS_SUCCESS_CODE)
    message: str = field(default=Message.PROCESS_SUCCESS_MSG)
    data: str = field(default=None)

    def __post_init__(self):
        if isinstance(self.status, Enum):
            self.status = str(self.status)
        if isinstance(self.message, Enum):
            self.message = str(self.message)

    def send(self):
        return {
            "status": self.status,
            "message": self.message,
            "data": deep_serialize(self.data),
        }
