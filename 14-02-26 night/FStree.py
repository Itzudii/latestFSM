import uuid
import pickle
import os

class TreeNode:
    __slots__ = ("name","is_dir","id","childs","parent")
    def __init__(self,name:str,is_dir:bool):
        self.name = name
        self.is_dir = is_dir
        self.id = None
        self.childs = {} if is_dir else None
        self.parent = None

class Tree:
    def __init__(self, db_path="save/root.pkl", autosave=True):
        self.root = None
        self.db_path = db_path
        self.autosave = autosave
        self.load()

     # ---------------- Persistence ---------------- #

    def save(self):
        """
        Save HashMaster state to pickle
        """
        data = {
            "root": self.root
        }
        with open(self.db_path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        print("root save")

    def load(self):
        """
        Load HashMaster state from pickle
        """
        if not os.path.exists(self.db_path):
            os.makedirs('save',exist_ok=True)
            self.root = TreeNode("placeholder",True)
            return

        try:
            with open(self.db_path, "rb") as f:
                data = pickle.load(f)

            self.root = data['root']
            print("root load")

        except Exception:
            # Corrupted pickle → safe reset
            self.root = TreeNode("placeholder",True)
            print("root not load")
            

