import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models.outcome import AuditLog


def log_event(
    db: Session,
    event_type: str,
    lead_id: Optional[str] = None,
    input_data=None,
    output_data=None,
    model_version: Optional[str] = None,
    prompt_version: Optional[str] = None,
    weights_version: Optional[str] = None,
    actor: Optional[str] = None,
):
    def _serialize(value):
        if value is None:
            return None
        try:
            return json.dumps(value, default=str)[:4000]
        except TypeError:
            return str(value)[:4000]

    entry = AuditLog(
        lead_id=lead_id,
        event_type=event_type,
        input=_serialize(input_data),
        output=_serialize(output_data),
        model_version=model_version,
        prompt_version=prompt_version,
        weights_version=weights_version,
        actor=actor,
    )
    db.add(entry)
    db.commit()
    return entry
