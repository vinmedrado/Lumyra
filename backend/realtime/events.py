from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Literal

RealtimeEventType = Literal[
    'guest_updated','rsvp_updated','message_sent','message_failed','financial_updated',
    'insight_created','job_completed','notification_created','activity_created','presence_updated'
]

@dataclass(slots=True)
class RealtimeEvent:
    type: RealtimeEventType | str
    tenant_id: int | None = None
    event_id: int | None = None
    payload: dict[str, Any] | None = None
    created_at: str = ''

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data['created_at'] = data['created_at'] or datetime.now(timezone.utc).isoformat()
        data['payload'] = data['payload'] or {}
        return data


def make_event(event_type: str, tenant_id: int | None = None, event_id: int | None = None, **payload: Any) -> RealtimeEvent:
    return RealtimeEvent(type=event_type, tenant_id=tenant_id, event_id=event_id, payload=payload)
