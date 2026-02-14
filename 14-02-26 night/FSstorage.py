import sqlite3
import uuid
import time

class Storage:
    def __init__(self, db_path="fs_index.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            path TEXT,
            type TEXT,
            state TEXT,
            indicator TEXT,
            islocked INTEGER,
            locked_hash TEXT,
            ext TEXT,
            hash TEXT,
            vector BLOB,
            tags TEXT,
            size INTEGER,
            modified_time TEXT,
            created_time TEXT,
            mode TEXT,
            parent_id TEXT
        )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON nodes(name)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent ON nodes(parent_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash ON nodes(hash)")
        self.conn.commit()

    def commit(self):
        self.conn.commit()

    def add_node(self, name, path, type_, parent_id=None, ext=None, tags=None,
                 hash_=None, vector=None, size=0, modified_time=None, created_time=None, mode=None):
        # node_id = type_+uuid.uuid4().hex
        state = "indexed"
        indicator = "sync"
        islocked = 0
        locked_hash = None
        created_time = created_time or time.strftime("%Y-%m-%d %H:%M:%S")
        modified_time = modified_time or created_time
        self.cursor.execute("""
        INSERT INTO nodes (name, path, type, state, indicator, islocked, locked_hash, ext, hash, vector, tags, size, modified_time, created_time, mode, parent_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ( name, path, type_, state, indicator, islocked, locked_hash, ext, hash_, vector, tags, size, modified_time, created_time, mode, parent_id))
        # self.conn.commit()
        return self.cursor.lastrowid

    # Fetch full node attributes by UUID
    def get_node(self, node_id):
        self.cursor.execute("SELECT * FROM nodes WHERE id=?", (node_id,))
        return self.cursor.fetchone()
    
    # Fetch full node attributes by parentid
    def get_node_by_parent(self, parent_id):
        self.cursor.execute("SELECT * FROM nodes WHERE parent_id=?", (parent_id,))
        return self.cursor.fetchall()

    # Prefix search
    def search_prefix(self, prefix, type_=None, parent_id=None, limit=50):
        query = "SELECT id, name FROM nodes WHERE name LIKE ?"
        params = [prefix + "%"]
        if type_:
            query += " AND type=?"
            params.append(type_)
        if parent_id:
            query += " AND parent_id=?"
            params.append(parent_id)
        query += " LIMIT ?"
        params.append(limit)
        self.cursor.execute(query, tuple(params))
        return self.cursor.fetchall()

    # Hash search
    def search_hash(self, hash_):
        self.cursor.execute("SELECT id, name FROM nodes WHERE hash=?", (hash_,))
        return self.cursor.fetchall()

    # Close DB
    def close(self):
        self.conn.close()


     # -----------------------
    # Node setters
    # -----------------------
    def set_vector(self, node_id, vector):
        """Store or update vector for a node."""
        self.cursor.execute("UPDATE nodes SET vector=? WHERE id=?", (vector, node_id))
        self.conn.commit()

    def set_indicator(self, node_id, indicator):
        """Store or update vector for a node."""
        self.cursor.execute("UPDATE nodes SET indicator=? WHERE id=?", (indicator, node_id))
        

    def set_tags(self, node_id, tags):
        """Store or update tags for a node."""
        self.cursor.execute("UPDATE nodes SET tags=? WHERE id=?", (tags, node_id))
        self.conn.commit()

    def set_hash(self, node_id, hash_):
        """Store or update hash for a node."""
        self.cursor.execute("UPDATE nodes SET hash=? WHERE id=?", (hash_, node_id))
        self.conn.commit()

    def set_size(self, node_id, size):
        self.cursor.execute("UPDATE nodes SET size=? WHERE id=?", (size, node_id))
      

    def set_modified_time(self, node_id, modified_time):
        self.cursor.execute("UPDATE nodes SET modified_time=? WHERE id=?", (modified_time, node_id))
 

    def set_locked(self, node_id, locked=True, locked_hash=None):
        """Lock or unlock a node."""
        self.cursor.execute("UPDATE nodes SET islocked=?, locked_hash=? WHERE id=?",
                            (int(locked), locked_hash, node_id))
        self.conn.commit()

    # -----------------------
    # Node getters
    # -----------------------
    def get_vector(self, node_id):
        self.cursor.execute("SELECT vector FROM nodes WHERE id=?", (node_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_tags(self, node_id):
        self.cursor.execute("SELECT tags FROM nodes WHERE id=?", (node_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_hash(self, node_id):
        self.cursor.execute("SELECT hash FROM nodes WHERE id=?", (node_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def get_modified_time(self, node_id):
        self.cursor.execute("SELECT modified_time FROM nodes WHERE id=?", (node_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def get_size(self, node_id):
        self.cursor.execute("SELECT size FROM nodes WHERE id=?", (node_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def get_path(self, node_id):
        self.cursor.execute("SELECT path FROM nodes WHERE id=?", (node_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def get_islocked(self, node_id):
        self.cursor.execute("SELECT islocked FROM nodes WHERE id=?", (node_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None
    # -----------------------
    # multiple set
    # -----------------------
    def set_vectors_batch(self, updates):
        """
        updates = [(uuid1, vector1), (uuid2, vector2), ...]
        """
        self.cursor.executemany("UPDATE nodes SET vector=? WHERE id=?", updates)
        self.conn.commit()

    def delete_ids(self,ids):
        #  ids = ['id','id']
        placeholders = ",".join("?" * len(ids))
        query = f"DELETE FROM nodes WHERE id IN ({placeholders})"
        print(query,ids)
        self.cursor.execute(query,ids)
        self.conn.commit()
