import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from event_logger import log_event
from config import WATCH_PATHS, ACTIVE_LOG
import os
class Handler(FileSystemEventHandler):

    def on_created(self, event):
        log_event("create", event.src_path)
      

    def on_deleted(self, event):
        log_event("delete", event.src_path)
      

    def on_modified(self, event):
        if os.path.isdir(event.src_path):
            log_event("modify", event.src_path)

    def on_moved(self, event):
        log_event("move", event.dest_path)
     


def ensure_active_log():
    if not ACTIVE_LOG.exists():
        ACTIVE_LOG.touch()


def run():
    observer = Observer()
    handler = Handler()

    for p in WATCH_PATHS:
        observer.schedule(handler, p, recursive=True)

    observer.start()

    try:
        while True:
            ensure_active_log()
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    run()

