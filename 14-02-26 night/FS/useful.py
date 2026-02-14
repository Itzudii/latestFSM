import os
import hashlib
import re
import stat
import time


def bytes_to_mb(byte_size):
    return byte_size / (1024 * 1024)

def file_hash(path):
    """Compute hash of a file based on its size.
       - <=2 MB: full hash
       - >2 MB: first 1 MB + last 1 MB
    """
    CHUNK_SIZE = 1024 * 1024  # 1 MB
    SIZE_LIMIT = 2 * 1024 * 1024  # 2 MB
    if os.path.exists(path):
        size = os.path.getsize(path)
    else:
        return None
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

def needs_rehash(dic, st):
    """
    Decide whether file content hash must be recalculated
    """

    # Case 1: hash not calculated yet
    # if not hasattr(node, "hash") or node.hash is None:
    #     return True

    # Case 2: file size changed
    if dic['s'] != st.st_size:
        return True

    # Case 3: modification time changed
    if dic['m'] != st.st_mtime:
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
        'ishidden':True if filename.startswith('.') else False}


def filename_dup_normalizer(filename):
    data = name_ext(filename)
    name = data['name']
    ext = data['ext']

    match = re.search(r"\(\d+\)", name)
    if match:
        pointer = match.group()
        number = re.search(r"\d+",pointer).group()
        new_pointer = f'({int(number) + 1})'
        name = name.replace(pointer,new_pointer)
    else:
        name +='(1)'
    

    return f'{name}' if ext == 'unknown' else f'{name}.{ext}'

def get_stat(path):
    return os.stat(path)

def formate_sttime(st_time):
    return time.strftime('%Y-%m-%d %H:%M',time.localtime(st_time))

def get_filemode(st_mode):
    return stat.filemode(st_mode)

def filemode_readable(filemode):
    chars={
    "d"	:"directory",
    "-"	:"",
    "l"	:"symlink",
    "r"	:"read",
    "w"	:"write",
    "x"	:"execute"}
    return {"owner" : [chars[char] for char in filemode[1:4]],
    "groups" : [chars[char] for char in filemode[4:7]],
    "everyone" : [chars[char] for char in filemode[7:10]]}
  
def file_type(type_):
    return 'Folder' if type_ == 'd' else 'File'

def get_indicator(state):
    match state:
        case 'sync':
            return "🟢"  
        case 'lock_m':
            return "🔴"  
        case 'modified':
            return "🟠"  
        
        
