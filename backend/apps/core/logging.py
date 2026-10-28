"""Allowlisted structured events; credentials and request content excluded."""

import json
import logging
from datetime import datetime, timezone


class SecurityJSONFormatter(logging.Formatter):
    def format(self, record):
        event = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event_code", "application_event"),
        }
        if hasattr(record, "status_code"):
            event["status"] = record.status_code
        if record.exc_info and record.exc_info[0]:
            event["exception_type"] = record.exc_info[0].__name__
        return json.dumps(event, ensure_ascii=False)
