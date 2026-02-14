import json
import time
from config import ACTIVE_LOG, PROCESSING_LOG


def load_events(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                yield json.loads(line.strip())
            except:
                continue


def prepare_processing_log():
    # handle previous crash
    if PROCESSING_LOG.exists():
        return PROCESSING_LOG

    if ACTIVE_LOG.exists():
        time.sleep(0.1)  # avoid write collision
        ACTIVE_LOG.rename(PROCESSING_LOG)
        return PROCESSING_LOG

    return None


def run_startup_sync(tree):
    log_file = prepare_processing_log()

    if not log_file:
        return

    dirty_dirs = set()

    for event in load_events(log_file):
        dirty_dirs.add(event["path"])

    for d in dirty_dirs:
        tree.refresh_path(d)

    log_file.unlink(missing_ok=True)
