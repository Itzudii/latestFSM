import json
import os
import time
from pathlib import Path


class LogManager:

    def __init__(self, active_log, processing_log):
        self.active_log = Path(active_log)
        self.processing_log = Path(processing_log)
        self.offset = 0   # last read position in active.log

    # ---------------------------
    # STARTUP MODE
    # ---------------------------
    def startup(self):
        """
        Freeze past logs and return events for full processing.
        """
        events = []

        # 1️⃣ process leftover processing.log
        if self.processing_log.exists():
            events.extend(self._read_all(self.processing_log))
            self.processing_log.unlink(missing_ok=True)

        # 2️⃣ freeze active.log into processing.log
        if self.active_log.exists():
            time.sleep(0.1)  # avoid write collision
            self.active_log.rename(self.processing_log)

            events.extend(self._read_all(self.processing_log))
            self.processing_log.unlink(missing_ok=True)

        # reset runtime reader
        self.offset = 0

        return events

    # ---------------------------
    # ACTIVE MODE (runtime)
    # ---------------------------
    def active(self):
        """
        Read only new events written into active.log.
        """
        events = []

        if not self.active_log.exists():
            return events

        size = os.path.getsize(self.active_log)

        # file recreated or truncated
        if size < self.offset:
            self.offset = 0

        with open(self.active_log, "r", encoding="utf-8") as f:
            f.seek(self.offset)

            for line in f:
                try:
                    events.append(json.loads(line.strip()))
                except:
                    continue

            self.offset = f.tell()

        return events

    # ---------------------------
    # INTERNAL HELPER
    # ---------------------------
    def _read_all(self, path):
        data = []

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data.append(json.loads(line.strip()))
                except:
                    continue

        return data

        