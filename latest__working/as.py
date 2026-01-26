import threading
import time
from queue import Queue

class FSArchitecture:

    def __init__(self):
        self.task_queue = Queue()
        self.stop_event = threading.Event()

    def input_listener(self):
        """
        Waits for user input and stores it in variable + queue
        """
        while not self.stop_event.is_set():
            user_input = input("FS> ")
            print(f"[INPUT CAPTURED] -> {user_input}")

            if user_input.lower() == "exit":
                self.stop_event.set()
                self.task_queue.put(None)
                break

            # store user input in variable
            self.last_input = user_input

            # push into task queue
            self.task_queue.put(user_input)

    def background_worker(self):
        """
        Runs background tasks when no user input exists
        """
        while not self.stop_event.is_set():
            if self.task_queue.empty():
                self.run_background_task()
            else:
                task = self.task_queue.get()
                if task is None:
                    break
                self.process_user_task(task)

    def run_background_task(self):
        """
        Background job
        """
        print("[BG] Running background maintenance...")
        time.sleep(2)

    def process_user_task(self, task):
        """
        Process user input
        """
        print(f"[USER TASK] Executing: {task}")
        time.sleep(1)


if __name__ == "__main__":
    fs = FSArchitecture()

    t1 = threading.Thread(target=fs.input_listener, daemon=True)
    t2 = threading.Thread(target=fs.background_worker, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
