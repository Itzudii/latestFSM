import os
import hashlib

def bytes_to_mb(byte_size):
    return byte_size / (1024 * 1024)

def file_hash(path):
    """Compute hash of a file based on its size.
       - <=2 MB: full hash
       - >2 MB: first 1 MB + last 1 MB
    """
    CHUNK_SIZE = 1024 * 1024  # 1 MB
    SIZE_LIMIT = 2 * 1024 * 1024  # 2 MB

    size = os.path.getsize(path)
    h = hashlib.sha256()

    with open(path, "rb") as f:
        if size <= SIZE_LIMIT:
            # Small file: hash entire content
            while chunk := f.read(CHUNK_SIZE):
                h.update(chunk)
        else:
            # Large file: hash first and last 1 MB
            h.update(f.read(CHUNK_SIZE))  # first 1 MB
            f.seek(size - CHUNK_SIZE)    # move to last 1 MB
            h.update(f.read(CHUNK_SIZE))

    return h.hexdigest()

def needs_rehash(node, st):
    """
    Decide whether file content hash must be recalculated
    """

    # Case 1: hash not calculated yet
    if not hasattr(node, "hash") or node.hash is None:
        return True

    # Case 2: file size changed
    if node.size != st.st_size:
        return True

    # Case 3: modification time changed
    if node.modified_time != st.st_mtime:
        return True

    # Otherwise: safe to skip hashing
    return False

def name_ext(filename):
    if '.' in filename:
        parts = filename.split('.')
        _name,_ext = '.'.join(parts[:-1]),parts[-1]
    else:
        _name,_ext = (filename,"unknown")

    return {'name':_name,
        'ext':_ext,
        'isHidden':True if filename.startswith('.') else False}