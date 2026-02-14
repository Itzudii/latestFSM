import pickle
import os


class HashMaster:
    def __init__(self, db_path="save/hashmaster.pkl", autosave=True):
        self.db_path = db_path
        self.autosave = autosave

        self.path_to_hash = {}
        self.hash_to_paths = {}

        self.load()

    # ---------------- Core Operations ---------------- #

    def insert(self, path: str, file_hash: str):
        """
        Insert or update path with hash
        """
        if path in self.path_to_hash:
            old_hash = self.path_to_hash[path]
            if old_hash == file_hash:
                return  # no change

            self.hash_to_paths[old_hash].discard(path)
            if not self.hash_to_paths[old_hash]:
                del self.hash_to_paths[old_hash]

        self.path_to_hash[path] = file_hash
        self.hash_to_paths.setdefault(file_hash, set()).add(path)

        if self.autosave:
            self.save()

    def delete(self, path: str):
        """
        Delete path entry
        """
        if path not in self.path_to_hash:
            return

        file_hash = self.path_to_hash.pop(path)
        self.hash_to_paths[file_hash].discard(path)

        if not self.hash_to_paths[file_hash]:
            del self.hash_to_paths[file_hash]

        if self.autosave:
            self.save()

    # ---------------- Search ---------------- #

    def search_hash_by_path(self, path: str):
        return self.path_to_hash.get(path)

    def search_paths_by_hash(self, file_hash: str):
        return self.hash_to_paths.get(file_hash, set())

    def search_duplicate_files(self):
        return {
            h: paths
            for h, paths in self.hash_to_paths.items()
            if len(paths) > 1
        }

    # ---------------- Persistence ---------------- #

    def save(self):
        """
        Save HashMaster state to pickle
        """
        data = {
            "path_to_hash": self.path_to_hash,
            "hash_to_paths": self.hash_to_paths
        }
        with open(self.db_path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load(self):
        """
        Load HashMaster state from pickle
        """
        if not os.path.exists(self.db_path):
            os.makedirs('save',exist_ok=True)
            return

        try:
            with open(self.db_path, "rb") as f:
                data = pickle.load(f)

            self.path_to_hash = data.get("path_to_hash", {})
            self.hash_to_paths = data.get("hash_to_paths", {})

        except Exception:
            # Corrupted pickle → safe reset
            self.path_to_hash = {}
            self.hash_to_paths = {}
