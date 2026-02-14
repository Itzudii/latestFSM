import pickle
import os
from queue import Queue
import logging

logger = logging.getLogger("FS")
class Que:
    def __init__(self, db_path="save/tagq.pkl", autosave=True):
        self.db_path = db_path
        self.autosave = autosave
        self.len_ = 0

        self.tagQ = Queue()

        self.load()

    # ---------------- Core Operations ---------------- #

    def put(self, item):
        """
        Insert or update path with hash
        """
        self.tagQ.put(item)
        self.len_ += 1
        if self.autosave:
            self.save()
        

    def get(self):
        """
        Delete path entry
        """
        item = self.tagQ.get()
        self.len_ -= 1
        if self.autosave:
            self.save()
        return item

    def empty(self):
        return self.tagQ.empty()

    def save(self):
        """
        Save HashMaster state to pickle
        """
        items = []
        while True:
            try:
                items.append(self.tagQ.get_nowait())
            except Exception:
                break

        # restore queue
        for item in items:
            self.tagQ.put(item)

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with open(self.db_path, "wb") as f:
            pickle.dump(items, f, protocol=pickle.HIGHEST_PROTOCOL)


    def load(self):
        """
        Load HashMaster state from pickle
        """
        if not os.path.exists(self.db_path):
            logger.error(f'{self.db_path} not exist')
            return

        try:
            with open(self.db_path, "rb") as f:
                items = pickle.load(f)

            for item in items:
                self.tagQ.put(item)
            logger.info(f"{self.db_path} successfully loaded")
        except Exception:
            # Corrupted pickle → safe reset
            logger.warning(f"{self.db_path} Corrupted pickle → safe reset")
    
    def __len__(self):
        return self.len_
