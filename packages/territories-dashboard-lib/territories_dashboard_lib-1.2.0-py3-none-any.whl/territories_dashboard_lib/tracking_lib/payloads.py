from typing import Optional

from pydantic import BaseModel

from territories_dashboard_lib.tracking_lib.enums import EventType


class EventPayload(BaseModel):
    indicator: str
    event: EventType
    objet: Optional[str] = None
    type: Optional[str] = None
