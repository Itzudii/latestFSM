import json
from config import ACTIVE_LOG

def log_event(event_type, path):
    ACTIVE_LOG.parent.mkdir(exist_ok=True)

    data = {
        "type": event_type,
        "path": path
    }

    with open(ACTIVE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")
        f.flush()
