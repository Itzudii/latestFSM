import os
from collections import defaultdict
import pickle

class pickle_dict:
    def __init__(self, db_path, autosave=True):
        self.db_path = db_path
        self.autosave = autosave
        self.data = defaultdict(list)
        self.load()

    
    # ---------------- Core Operations ---------------- #

    def add(self, name, path):
        """
        Insert or update path with hash
        """
        if path not in self.data[name]:
            self.data[name].append(path)
        if self.autosave:
            self.save()
        

    def remove(self, name, path):
        """
        Delete path entry
        """
        lst = self.data.get(name,None)
        if lst:
            if len(lst) == 1:
                del self.data[name]
            else:
                self.data[name].remove(path)
            if self.autosave:
                self.save()


    def save(self):
        """
        Save HashMaster state to pickle
        """
        if os.path.dirname(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with open(self.db_path, "wb") as f:
            pickle.dump(self.data, f, protocol=pickle.HIGHEST_PROTOCOL)


    def load(self):
        """
        Load HashMaster state from pickle
        """
        if not os.path.exists(self.db_path):
            return

        try:
            with open(self.db_path, "rb") as f:
                self.data = pickle.load(f)

            # logger.info(f"{self.db_path} successfully loaded")
        except Exception:
            # Corrupted pickle → safe reset
            # logger.warning(f"{self.db_path} Corrupted pickle → safe reset")
            pass
    
