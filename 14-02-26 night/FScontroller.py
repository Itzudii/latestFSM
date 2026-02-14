import threading
import time
import queue

# from FSTags import TagGenerator
from FSmain import FSManager
from FSstorage import Storage
# from FSCLI import CLI
# from FSvector import MrVectorExpert
from FStask import TaskPerformer
from multiprocessing import Process, Queue, Event
import time

def tag_worker(tag_queue: Queue, result_queue: Queue, pause_event: Event, stop_event: Event):

        print("Tag process started")
        # tagG = TagGenerator()

        while not stop_event.is_set():

            # pause support
            pause_event.wait()

            try:
                path = tag_queue.get(timeout=0.5)
            except:
                continue

            print("Generating tag for:", path)

            # simulate heavy work
            time.sleep(3)

            # tag = tagG.generate_tags_path(path)

            result_queue.put({
                "type":"tagGenration",
                "path":path,
                "tags":["fix","in","tag","worker"]
            })

            print("Tag process stopped")

class Controller:

    def __init__(self):

        self.task_queue = queue.Queue()
        self.task_result_queue = queue.Queue()

        self.tag_queue = Queue()
        self.tag_result_queue = Queue()

        self.tag_pause_event = Event()
        self.tag_stop_event = Event()

        self.task_pause_event = threading.Event()
        self.task_stop_event = threading.Event()
        



        self.isRunning = True

        #  vector load 
        # self.vec = MrVectorExpert()
        # self.vec.load()
        self.vec = []

        self.storage = Storage("save/fs_index.db")

        

        self.fs = FSManager(self.storage, self.vec,self.tag_queue,self.tag_result_queue)
        # self.fs.load()

        # self.cli = CLI(self.fs)

        #  multi processing 
        self.tag_pause_event.set()   # allow running
        self.tag_process = Process(
            target=tag_worker,
            args=(self.tag_queue, self.tag_result_queue, self.tag_pause_event, self.tag_stop_event)
        )
        self.tag_process.start()

        # Task performer
        self.performer = TaskPerformer(self.fs)

        self.task_pause_event.set()
        self.task_process = threading.Thread(
            target=self.fs_background,
            daemon=True
        )
        self.task_process.start()

    def on_close(self):
        print("close window")
        self.stop_fs_background()
        self.stop_tag_worker()

    def stop_fs_background(self):
        self.task_stop_event.set()
        self.task_process.join()

    def stop_tag_worker(self):
        self.tag_stop_event.set()
        self.tag_process.join()
        
    def fs_background(self):

        print("background worker started")
        self.fs.startup()

        while not self.task_stop_event.is_set():

            self.task_pause_event.wait()

            try:
                task = self.task_queue.get_nowait()
                result = self.task_handler(task)
                self.task_result_queue.put(result)
                continue

            except queue.Empty:
                pass
            
            self.fs.active()

            self.fs.background_index_step1()
          

            self.fs.background_index_step2()


            self.fs.mrvec.background_task_step()

            time.sleep(0.001)
 
        print("safely exit thread")

    def task_handler(self, task):

        target = task.get("for")
        name = task.get("name")
        args = task.get("args", [])

        if target == "TaskPerformer":
            fn = getattr(self.performer, name)
            return fn(*args)

        return {"error": "unknown task"}

    def start_task(self, task):

        self.task_queue.put(task)

        while True:
            try:
                return self.task_result_queue.get_nowait()
            except queue.Empty:
                pass

            time.sleep(0.001)
