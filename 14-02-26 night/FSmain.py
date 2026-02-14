# from operator import itemgetter
from FS.constant import DEFAULT_NAME,DEFAULT_PATH,ALLOWED_TAGS_EXT
from FS.stack import Stack
# from FS.prifixSearch import Trie
from FS.hash import HashMaster
# from FS.extSearch import CustomHashMap
# from FS.fileReader import universal_reader
from FS.useful import needs_rehash,file_hash,name_ext,filename_dup_normalizer
from FS.cusq import Que
from FS.cus_dict import pickle_dict
from FStree import Tree,TreeNode
import os
import sys
import shutil
# import hashlib
from pathlib import Path
import pickle
# from queue import Queue
import time
import logging
from FSlogmanger import LogManager
import uuid
from FSstorage import Storage

active = "watcher/logs/active.jsonl"
processing = "watcher/logs/processing.jsonl"
logger = logging.getLogger("FS")

class FSManager:
    '''file management'''
    def __init__(self,storage:Storage,mrvec,tagq,tagrq):
        self.default = DEFAULT_PATH
        self.default_name = DEFAULT_NAME

        self.db = storage

        self.tree = Tree("save/root.pkl")
        self.root = self.tree.root
        self.cwd = self.root

        self.id_to_node = dict()
        
        self.selected_nodes = set()
        self.state = 'ideal'
        self.pointer = None
        self.undoStack = Stack()
        self.redoStack = Stack()
        self.hash_queue = []
        self.hash_Master = HashMaster()
        # self.mrvec = mrvec
        self.tag_queue = tagq
        self.tag_result_queue = tagrq
        self.rehash_queue = Que(db_path="save/rehash.pkl",autosave=False)
        self.quick_access = pickle_dict(db_path="save/quickA.pkl")
        self.uuid = pickle_dict(db_path="save/uuid.pkl")
        #  all time are in nano second
        self.average_prifixS_time = None
        self.average_extS_time = None
        self.count_ = 0

        self.log = LogManager(active,processing)

    def insert_root_in_db(self): # verified
        st = os.stat(DEFAULT_PATH)
        id = self.db.add_node(
            name=DEFAULT_NAME,
            path=DEFAULT_PATH,
            type_= 'd',
            ext = 'unknown',
            size=st.st_size,
            modified_time=st.st_mtime,
            created_time=st.st_ctime,
            mode=st.st_mode
        )
        self.root.id = id
        self.root.name = DEFAULT_NAME

    def process_event(self,event):
        path = self.normalize_path(event['path'])
        print("path",path)
        data = self.get_node_by_path(path)
        node = data['result']
        if node is None:
            print("node is None")
            return
        if node.type == 'd':
            print("node is directory")
            for _ in self._refresh_quick(node):
                pass

    def active(self):
        new_events = self.log.active()
        if new_events:
            print("newevents",new_events)
        for e in new_events:
            self.process_event(e)     

    def startup(self):
        events = self.log.startup()
        for event in events:
            self.process_event(event)


    def normalize_path(self,path): # verified
        driver,path = path.split(':',1)
        path = driver.lower()+':'+path
        return Path(path).as_posix()
    
    def _set_cwd(self,node):
        self.undoStack.push(self.cwd)
        self.cwd = node

    def get_path(self,id): # verified
        node = self.id_to_node.get(id)
        stack = []
        while node.parent:
            stack.append(node.name)
            node = node.parent
        stack.append(DEFAULT_PATH)
        return '/'.join(reversed(stack))
        


    '''                                                                                
        CORE FEATURE OF FILE MANGEMENT SYSTEM 
        > REFRESH Very Experimental do not touch currently in 99.9% safe stage   
    '''
    def _refresh_quick(self, root_node): # verified
            root_path = self.get_path(root_node.id)

            stack = [root_node]
            paths = [root_path]
    
            meta_data = dict()
    
            get_meta = self.get_meta
            add_node = self.db.add_node
            normalize = self.normalize_path
            rehash_put = self.rehash_queue.put
            get_node_by_parent = self.db.get_node_by_parent
    
            
    
            while stack:
                node = stack.pop()
                path = paths.pop()
    
                all_nodes = get_node_by_parent(node.id)
                if all_nodes:
                    for _node in all_nodes:
                        meta_data[_node[0]] = get_meta(_node)
    
                try:
                    internal = node.childs
                    seen = set()
    
                    for item in os.scandir(path):
                        
                        name = item.name
                        seen.add(name)
                        isNew =  False
                        st = item.stat(follow_symlinks=False)
    
                        node_ = internal.get(name)
                        is_dir = item.is_dir(follow_symlinks=False)
                        print(item.name,node_)
    
                        # CREATE
                        if node_ is None:
                            isNew = True
                            data = name_ext(name)
                            path_ = normalize(item.path)
                            # type_ = 'd' if item.is_dir(follow_symlinks=False) else 'f'
    
                            node_id = add_node(
                                name=name,
                                path=path_,
                                type_='d' if is_dir else 'f',
                                parent_id=node.id,
                                ext=data.get('ext'),
                                size=st.st_size,
                                modified_time=st.st_mtime,
                                created_time=st.st_ctime,
                                mode=st.st_mode
                            )
                            meta_data[node_id] = get_meta((node_id, name,path_, 'd' if is_dir else 'f', 'indexed', 'sync', 0, None, data.get('ext'), None, None, None, st.st_size, st.st_mtime, st.st_ctime, st.st_mode, node.id))
    
                            newNode = TreeNode(name,is_dir)
                            newNode.parent = node
                            newNode.id = node_id
                            node.childs[name] = newNode
    
                            node_ = newNode
    
                        else:
                            self.db.set_size(node_.id,st.st_size)
                            self.db.set_modified_time(node_.id,st.st_mtime)
    
                        # PROCESS
                        if is_dir and not item.is_symlink():
                            pass
                                # stack.append(node_)
                                # paths.append( meta_data[node_.id].get('path'))
                        else:
                            if not meta_data[node_.id].get('islocked'):
                                self.db.set_indicator(node_.id,'sync')
    
                            mt = meta_data[node_.id].get('modified_time')
                            size = meta_data[node_.id].get('size')
                            if isNew or needs_rehash({"m":mt,"s":size}, st):
                                path_= self.normalize_path(item.path)
                                rehash_put(path_)
    
                        yield
    
                    # DELETE
                    for name in tuple(internal):
                        if name not in seen:
                            d_node = internal[name]
                            self._delete_internal(d_node)
                            node.pop(name)
                        yield
    
                except Exception as e:
                    print(f'{e}')
                    yield
    
    def _refresh_first(self): # verified
        self.insert_root_in_db()
        stack = [self.root]
        paths = [DEFAULT_PATH]

        add_node = self.db.add_node
        normalize = self.normalize_path
        rehash_put = self.rehash_queue.put

        while stack:
            node = stack.pop()
            path = paths.pop()

            try:
                for item in os.scandir(path):
                    try:
                        name = item.name
                        is_dir = item.is_dir(follow_symlinks=False)
                        st = item.stat(follow_symlinks=False)
                        data = name_ext(name)
                        path_ = normalize(item.path)

                        node_id = add_node(
                            name=name,
                            path=path_,
                            type_='d' if is_dir else 'f',
                            parent_id=node.id,
                            ext=data.get('ext'),
                            size=st.st_size,
                            modified_time=st.st_mtime,
                            created_time=st.st_ctime,
                            mode=st.st_mode
                        )

                        newNode = TreeNode(name,is_dir)
                        newNode.parent = node
                        newNode.id = node_id
                        node.childs[name] = newNode

                        self.count_ += 1
                        if self.count_ % 1000 == 0:
                            print(self.count_)

                        if is_dir and not item.is_symlink():
                            stack.append(newNode)
                            paths.append(path_)
                        else:
                            rehash_put(path_)

                    except Exception as e:
                        logger.error(e)

            except Exception as e:
                logger.error(e)

        self.tree.save()    
        self.db.commit() 
        self.rehash_queue.save()
        # print(self.tree.root.childs)       # yield

    def get_meta(self,node): # verified
        return {
            "id":node[0],
           "name":node[1],
           "path":node[2],
           "type":node[3],
           "state":node[4],
           "indicator":node[5],
           "islocked":node[6],
           "locked_hash":node[7],
           "ext":node[8],
           "hash":node[9],
           "vector":node[10],
           "tags":node[11],
           "size":node[12],
           "modified_time":node[13],
           "created_time":node[14],
           "mode":node[15],
           "parent_id":node[16]
        }

    def _refresh(self, root_node): # verified
        root_path = self.get_path(root_node.id)

        stack = [root_node]
        paths = [root_path]

        meta_data = dict()

        get_meta = self.get_meta
        add_node = self.db.add_node
        normalize = self.normalize_path
        rehash_put = self.rehash_queue.put
        get_node_by_parent = self.db.get_node_by_parent

        

        while stack:
            node = stack.pop()
            path = paths.pop()

            all_nodes = get_node_by_parent(node.id)
            if all_nodes:
                for _node in all_nodes:
                    meta_data[_node[0]] = get_meta(_node)
            try:
                internal = node.childs
                seen = set()

                for item in os.scandir(path):
                    
                    name = item.name
                    seen.add(name)
                    isNew =  False
                    st = item.stat(follow_symlinks=False)

                    node_ = internal.get(name)
                    is_dir = item.is_dir(follow_symlinks=False)
                    print(item.name,node_)

                    # CREATE
                    if node_ is None:
                        isNew = True
                        data = name_ext(name)
                        path_ = normalize(item.path)
                        # type_ = 'd' if item.is_dir(follow_symlinks=False) else 'f'

                        node_id = add_node(
                            name=name,
                            path=path_,
                            type_='d' if is_dir else 'f',
                            parent_id=node.id,
                            ext=data.get('ext'),
                            size=st.st_size,
                            modified_time=st.st_mtime,
                            created_time=st.st_ctime,
                            mode=st.st_mode
                        )
                        meta_data[node_id] = get_meta((node_id, name,path_, 'd' if is_dir else 'f', 'indexed', 'sync', 0, None, data.get('ext'), None, None, None, st.st_size, st.st_mtime, st.st_ctime, st.st_mode, node.id))

                        newNode = TreeNode(name,is_dir)
                        newNode.parent = node
                        newNode.id = node_id
                        node.childs[name] = newNode

                        node_ = newNode

                    else:
                        self.db.set_size(node_.id,st.st_size)
                        self.db.set_modified_time(node_.id,st.st_mtime)

                    # PROCESS
                    if is_dir and not item.is_symlink():
                            stack.append(node_)
                            paths.append( meta_data[node_.id].get('path'))
                    else:
                        if not meta_data[node_.id].get('islocked'):
                            self.db.set_indicator(node_.id,'sync')

                        mt = meta_data[node_.id].get('modified_time')
                        size = meta_data[node_.id].get('size')
                        if isNew or needs_rehash({"m":mt,"s":size}, st):
                            path_= self.normalize_path(item.path)
                            rehash_put(path_)

                    yield

                # DELETE
                for name in tuple(internal):
                    if name not in seen:
                        d_node = internal[name]
                        self._delete_internal(d_node)
                        node.pop(name)
                    yield

            except Exception as e:
                print(f'{e}')
                yield

    def refresh_cwd(self): # verified
        ''' start analysis and updating tree structure from cwd '''
        for _ in self._refresh(self.cwd):
            pass
        self.db.commit()
        self.tree.save()
        self.rehash_queue.save()
    
    def refresh_root(self): # verified
        ''' start analysis and updating tree structure from root '''
        logger.info("full root loading started")
        for _ in self._refresh(self.root):
            pass
        print("full root loading completed")
        self.db.commit()
        self.tree.save()
        self.rehash_queue.save()

    def refresh_node(self,node): # verified
        ''' start analysis and updating tree structure from given node '''
        logger.info(f"refresh start > {node.path}")
        for _ in self._refresh(node):
            pass
        logger.info(f"refresh complete > {node.path}")
        self.db.commit()
        self.tree.save()
        self.rehash_queue.save()
    
    def create_id_to_node(self): # verified
        id_to_node = dict() 
        stack = [self.root]

        id_to_node[self.root.id] = self.root

        while stack:
            node = stack.pop()
            for node_ in node.childs.values():
                id_to_node[node_.id] = node_
                if node_.is_dir:
                    stack.append(node_)
        
        self.id_to_node = id_to_node

    """
       > SELECT > UNSELECT > SELECTALL > UNSELECTALL
    """ 
    def select(self,*args): # verified
        self.selected_nodes = self.selected_nodes.union(args)

    def unselect(self,*args): # verified
        self.selected_nodes.difference_update(args)
      
    def select_all(self):  # verified
        self.select(*[node.id for node in self.cwd.childs.values()])
    
    def unselect_all(self): # verified
        self.selected_nodes.clear()

    """
        > OPEN 
    """
    def _open_file_with_default_app(self,file_path):   # verified
        file_path = os.path.abspath(file_path)  # make path absolute
        if not os.path.exists(file_path):
            logger.error(f"open > {file_path} : not found")
            return False
        try:
            if sys.platform == "win32":                    # Windows
                os.startfile(file_path)                    # simplest for Windows

            logger.info(f"open > {file_path} : successfully")
            return True
        except Exception as e:
            logger.info(f" {e}")
            logger.error(f"open > {file_path} :Could not open file > {e}")
            return False

    def open(self,node): # verified
        ''' open file with default application '''
        if not node.is_dir:
           
            path = self.get_path(node.id)
            self._open_file_with_default_app(path)
        else:
            if self.state == 'ideal':
                self.unselect_all()
            self._set_cwd(node)

    def open_id(self,id): # verified
        node= self.id_to_node.get(id)
        if node:
            self.open(node)
        else:
            print("node not found:open_id")


    """
    > DELETE
    """

    def _delete_internal(self,del_node): # verified
        pop_node = self.id_to_node.pop

        stack = [del_node]
        ids = []
        while stack:
            node =  stack.pop()
            ids.append(node.id)
            stack.extend(node.childs.values())

        self.db.delete_ids(ids) # remove in db
        
        for id in ids: # remove in id_to_node
            pop_node(id,None)
        
        p_node = del_node.parent
        p_node.childs.pop(del_node.name) # pop in parents
           
    def _delete_memory(self,node): # verified 
        ''' delete file/folder from memeory only '''
        path = self.get_path(node.id)
        if node.id[0] == 'f':
            os.remove(path)
        elif node.id[0] == 'd':
            shutil.rmtree(path)
    
    def delete_node(self,node,): # verified 
        ''' delete file/folder from disk and tree structure '''
        self._delete_memory(node)
        self._delete_internal(node)

    def delete(self,*args): # verified
        childs_metadata = self.collect_metadata_parent_id(self.cwd.id)
        for id in args:
            node = self.id_to_node.get(id)
            meta = childs_metadata.get(id)
            if node:
                self.delete_node(node,meta)

            

    # def trash(self,filepath):

    """
    > CUT > COPY > PASTE
    """
    def _set_pointer(self,node): # work good
        self.pointer = node

    def _get_pointer(self): # work good
        return self.pointer
    
    def cut(self): # work good
        if self.state == 'ideal':
            if self.selected_nodes:
                self.state = 'move'
                self._set_pointer(self.cwd)
                logger.info("move mode activated")

    def copy(self): # work good
        if self.state == 'ideal':
            if self.selected_nodes:
                self.state = 'copy'
                self._set_pointer(self.cwd)
                logger.info("copy mode activated")

    def collect_metadata_parent_id(self,parent_id):
        meta_data = dict()
        get_meta =  self.get_meta
        all_nodes = self.db.get_node_by_parent(parent_id)

        if all_nodes:
            for node in all_nodes:
                meta_data[node[0]] = get_meta(node)
        return meta_data
    
    

    def _paste_for_move(self): # work good
        def _paste_for_move_helper(node):
            try:
                shutil.move(self.get_path(node.id),self.get_path(self.cwd.id))
                self.cwd.childs[node.name] = node
    
                p_node = node.parent
                p_node.childs.pop(node.name)
                return True
            except Exception:
                return False
        results = []
        for id in self.selected_nodes:
            node = self.id_to_node.get(id)
            if node:
                result = (node.name,_paste_for_move_helper(node))
                results.append(result)
        return results


    def _paste_for_copy_helper(self,node):
        try:
            cwd_path = self.get_path(self.cwd.id)
            node_path = self.get_path(node.id)
            if not node.is_dir:
                shutil.copy2(node_path,cwd_path)
            elif node.is_dir:
                dest_path = os.path.join(cwd_path,node.name)
                shutil.copytree(node_path,dest_path)
            
            return True
        except Exception:
            return False

    def _paste_for_copy(self): # work good
        results = []
        for id in self.selected_nodes:
            node = self.id_to_node.get(id)
            if node:
                result = (node.name,self._paste_for_copy_helper(node))
                results.append(result)
        return results

    def paste(self): # work good
        '''there is a issue of already exist thing'''#<<<<<<<<<<ERROR
        if self.state == 'move':
            result = self._paste_for_move()
            self.unselect_all()
            # self.refresh_cwd()
            self.state = 'ideal'
            return result
        elif self.state == 'copy':
            result = self._paste_for_copy()
            self.unselect_all()
            self.refresh_cwd()
            self.state = 'ideal'
            return result
        return []
    
    """
    > CREATE
    """
    def _write_content_to_file(self,filepath,content):
        with open(filepath,"w") as f:
            f.write(f'{content}\n')

    def _append_content_to_file(self,filepath,content):
        with open(filepath,"a") as f:
            f.write(f'{content}\n')

        
    def _create_dir_memory(self,dir_name,p_node= None): # work good
        if p_node is None:
            p_node = self.cwd
            new_dir_path = os.path.join(p_node.path,dir_name)
        if not os.path.exists(new_dir_path):
            os.makedirs(new_dir_path)
            logger.info("directory created at:",new_dir_path) 
            return True
        else:
            return False
    
    def _create_dir_internal(self,dir_name,p_node= None): # work good
        if p_node is None:
            p_node = self.cwd
        newNode = Node(dir_name,self.normalize_path(os.path.join(p_node.path,dir_name)),'d')
        p_node.add(newNode)
        logger.info("directory node created at:",newNode.path)
        return newNode
    
    def _create_file_memory(self,file_name,content="",p_node= None): # work good
        if p_node is None:
            p_node = self.cwd
        new_file_path = os.path.join(p_node.path,file_name)
        if not os.path.exists(new_file_path):
            self._write_content_to_file(new_file_path,content)
            logger.info("file created at:",new_file_path)
            return True
        return False
    
    def _create_file_internal(self,file_name,p_node= None): # work good
        if p_node is None:
            p_node = self.cwd
        newNode = Node(file_name,self.normalize_path(os.path.join(p_node.path,file_name)),'f')
        p_node.add(newNode)
        logger.info("file node created at:",newNode.path)
        return newNode

    def create_dir(self,dir_name,p_node= None):
        isDone = self._create_dir_memory(dir_name,p_node)
        if isDone:
            node = self._create_dir_internal(dir_name,p_node)
            node._config_stat()
            self.save_if_autosave()
            logger.info(f"create in dir > {dir_name}")
            return node.to_dict()
        else:
            return self.create_dir(filename_dup_normalizer(dir_name),p_node)

    def create_file(self,file_name,content="",p_node= None):
        isDone = self._create_file_memory(file_name,content,p_node)
        if isDone:
            node = self._create_file_internal(file_name,p_node)
            self.hash_queue.append(node)
            node._config_stat()
            self.save_if_autosave()
            logger.info(f"create in file > {file_name}")
            return node.to_dict()
        else:
            return self.create_file(filename_dup_normalizer(file_name),content,p_node)
    
    def write_to_file(self,node,content):
        if node.type == 'f':
            self._write_content_to_file(node.path,content)
            node._config_stat()
            self.save_if_autosave()
            logger.info(f"written to file > {node.path}")
        else:
            logger.error(f"cannot write to a directory > {node.path}")
    
    def append_to_file(self,node,content):
        if node.type == 'f':
            self._append_content_to_file(node.path,content)
            node._config_stat()
            self.save_if_autosave()
            logger.info(f"append to file > {node.path}")
        else:
            logger.error(f"cannot append to a directory > {node.path}")

    """
    > SHOW LIST

    """

    def show_list(self,filter = None) -> list: # work good
        ''' show list of files and folders in current working directory '''
        logger.info(f"call show list>: {self.cwd.path}")
        result = []
        for name,child in self.cwd.childs.items():
            result.append(child)
        return result
    """
    > HOME >GOTO > UNDO 

    """

    def go_to_root(self): # work good
        self._set_cwd(self.root)   
    
    def go_to(self,name): # work good
        node = self.get_node(name)
        if node:
            self.open(node)
            return True
        else:
            print(f"{name} not found in cwd")
            return False
    
    def go_back(self): # work good
        if self.state == 'ideal':
            self.unselect_all()
        if self.undoStack.empty():
            logger.info("no undo -> Empty")
            print("no undo -> Empty")
            return False
        # it not need history push
        self.redoStack.push(self.cwd)
        prev_node = self.undoStack.pop()
        self.cwd = prev_node
        return True

    def go_forward(self): # work good
        if self.state == 'ideal':
            self.unselect_all()
        if self.redoStack.empty():
            logger.info("no redo->empty")
            print("no redo->empty")
            return
        # it not need history push
        prev_node = self.redoStack.pop()
        self.open(prev_node)

    def go_to_address(self,path):
        driver,sub_path = path.split(':',1)
        
        path = driver.lower()+":"+sub_path
        data = self.get_node_by_path(path)
        r = data['result']
        m = data['message']
        if r:
            self.open(r)
            return (True,m)
        return (False,m)

    """
   > RENAME

    """
    def _rename_internal(self,filename,node,p_node=None):
        if p_node is None:
            p_node = self.cwd
        if node.type == 'd':
            p_node._del_dir_to_search_structure(node)    
        else:
            self.hash_Master.delete(node.path)
            # self.mrvec.delete(node.path)
            p_node._del_file_to_search_structure(node)    

        node.path  = node.path[:-len(node.name)]+filename #path change
        

        del p_node.childs[node.name]
        p_node.childs[filename] = node
        node.parent = p_node
        
        node.name = filename
        node._config_stat()
        if node.type == 'd':
            p_node._add_dir_to_search_structure(node)    
        else:
            p_node._add_file_to_search_structure(node)
            self.hash_queue.append(node)    
          
    def _rename_memory(self,name,node):
        old_add = node.path
        new_add = node.path[:-len(node.name)]+name
        try:
            os.rename(old_add,new_add)
            return True
        except Exception as e:
            return False

    def rename_node(self,name,node,p_node=None):
        isDone = self._rename_memory(name,node)
        if isDone:
            self._rename_internal(name,node,p_node)
            logger.info(f"rename > '{node.name}' to '{name}'")
            return {
            "status":True,
            "msg": "name rename done"
            }
        return {
            "status":False,
            "msg": "invalid charcters used"
        }
        
    def rename(self,old,new):
        if any([new.__contains__(char)for char in '/*?"<>:|']):
            return {
            "status":False,
            "msg": 'not use this any this character / * ? " < > : |'
        }
        if new not in self.cwd.childs:
            node = self.get_node(old)
            if node:
                return self.rename_node(new,node)

        return {
            "status":False,
            "msg": "name alredy exist"
        }
        

    """
     > SEARCH
    """ 
    "PRIFIX AND EXTENSION"
    def search_helper_prifix(self,node,prifix,results,type_,subdir = True):
        if not prifix:
            if type_ == 'd':
                result = node.prifixSearch_folder.get_all()
            else:
                result = node.prifixSearch_file.get_all()
        elif type_ == 'd':
            result = node.search_prifix_folder(prifix)
        else:
            result = node.search_prifix_file(prifix)

        results += result
        if subdir:
            for item in node.childs.values():
                if item.type == 'd':
                    self.search_helper_prifix(item,prifix,results,type_)
        return results

    def search_helper_ext(self,node,ext,results,subdir = True):
        result = node.search_ext(ext)
        results += result
        if subdir:
            for item in node.childs.values():
                if item.type == 'd':
                    self.search_helper_ext(item,ext,results)
        return results

    def search_prifix(self,prifix,type_,subdir = True):
        results = []
        ns1 =time.perf_counter_ns()
        self.search_helper_prifix(self.cwd,prifix,results,type_,subdir)
        ns2 =time.perf_counter_ns()
        self.average_prifixS_time = ns2-ns1
        return results

    def search_prifix_all(self,prifix,type_):
        results = []
        self.search_helper_prifix(self.root,prifix,results,type_,True)
        return results
    
    def search_ext(self,ext,subdir = True):
        results = []
        ns1 =time.perf_counter_ns()
        self.search_helper_ext(self.cwd,ext,results,subdir)
        ns2 =time.perf_counter_ns()
        self.average_extS_time = ns2-ns1
        return results

    def search_ext_all(self,ext):
        results = []
        self.search_helper_ext(self.root,ext,results,True )
        return results
    
    def filter_prifix(self,prifix,files):
        results = []
        for file in files:
            if file['name'].startswith(prifix):
                results.append(file)
        return results

    def filter_substring(self,substring,files):
        results = []
        for file in files:
            if substring in  file['name']:
                results.append(file)
        return results


    def ultra_search(self,search_for,search_where,prifix,extension,substring):
        results =[]
        Both = True if search_for == 'fd' else False
       
        if extension:
            print("enter extension")
            if search_where == 'pd':
                results = self.search_ext(extension,False)
            elif search_where == 'sd':
                results = self.search_ext(extension,True)
            elif search_where == 'rd':
                results = self.search_ext_all(extension)

            if prifix:
                results = self.filter_prifix(prifix,results)

            if substring:
                results = self.filter_substring(substring,results)
            return results
        
      
        if search_for == 'f' or Both:
            if search_where == 'pd':
                results += self.search_prifix(prifix,'f',False)
            elif search_where == 'sd':
                results += self.search_prifix(prifix,'f',True)
            elif search_where == 'rd':
                results += self.search_prifix_all(prifix,'f')
        if search_for == 'd' or Both:
            if search_where == 'pd':
                results += self.search_prifix(prifix,'d',False)
            elif search_where == 'sd':
                results += self.search_prifix(prifix,'d',True)
            elif search_where == 'rd':
                results += self.search_prifix_all(prifix,'d')
        if substring:
            results = self.filter_substring(substring,results)

        return results



    "HASH"
    def search_hash_by_path(self, path: str):
        return self.hash_Master.search_hash_by_path(path)
        
    def search_paths_by_hash(self, file_hash: str):
        return self.hash_Master.search_paths_by_hash(file_hash)

    def search_duplicate_files(self):
        return self.hash_Master.search_duplicate_files()
       
    def lock_file(self,node):
        if node.type == 'f':
            node.lock_hash = node.hash
            node.islocked = True
            return True
        return False

    def unlock_file(self,node):
        node.lock_hash = None
        node.islocked = False
    
    def is_corupted(self,node):
        if not os.path.exists(node.path):
            return {"status": "NOT_FOUND"}

        stat = os.stat(node.path)

        # Silent corruption case
        if (
            stat.st_size == node.size
            and stat.st_mtime == node.modified_time
            and node.hash != file_hash(node.path)
        ):
            return {
                "status": "SILENT_CORRUPTION",
            }

        return {"status": "OK"}


    """
        EXTRA HELPING FEATURES 
        >GET NODE > GET NODE BY PATH
    """

    def get_node(self,filename): # work good
        return self.cwd.childs.get(filename)

    def path_verifier(self,path):
        print(path)
        return True if DEFAULT_PATH in path else False

    def path_breaker(self,path):
        rootv=DEFAULT_PATH.split('/')
        pathv=path.split('/')
        length = len(rootv)
        return pathv[length:]
    
    def _path_break_to_dict(self,path):
        if self.path_verifier(path):
            rootv=self.root.path.split('/')
            pathv=path.split('/')
            length = len(rootv)
            data = {"HOME":self.root.path}
            for name in pathv[length:]:
                if name:
                    data[name] = f'{self.root.path}/{name}'
            return data
        return {}

    def path_break_cwd(self):
        return self._path_break_to_dict(self.cwd.path)
        
    def get_node_by_path(self,path):
        if self.path_verifier(path):
            results = self.path_breaker(path)
            root = self.root
            for pathname in results:
                if pathname in root.childs:
                    root = root.childs[pathname]
                elif pathname:
                    return {
                        'result':None,
                        'message':'path not exist'
                    }
              
            return {
                    'result':root,
                    'message':'path exist'
            }
        return {
                    'result':None,
                    'message':'path is incorrect or formate is incorrect'
            }


    """
        performance table
    """
    def _status(self):
        return f'''
        FS State: Active
        Indexed File: {len(self.mrvec.path_to_vector)}
        pending tag jobs: {self.tag_queue.__len__()}
        pending vector jobs: {self.tag_queue.__len__()}
        '''
   
    def _stats(self):
        return f'''
        Indexed File: {len(self.mrvec.path_to_vector)}
       Average Search Time:
                prifix -> {self.average_prifixS_time}
                extension -> {self.average_extS_time}
                context -> {self.mrvec.average_contextS_time}
        '''

        
    """
    > CONTEXT CHANGE DETECT 
    
    """
    def changes_detector(self,node):

        hash_ = file_hash(node.path)
        if node.hash != hash_ and hash_:
            if node.hash:
                if node.islocked:
                    node.indicator = 'lock_m'
                else:
                    node.indicator = 'modified'
                print("context change detected",node.name)
            logger.info(f'file content changes detected > {node.path}')
            ("hash updt")
            node.hash = hash_ # update hash
            self.hash_Master.insert(node.path,hash_) # update and add hash in path_to_hash dictss
            result = name_ext(node.name)
            if result['ext'] in ALLOWED_TAGS_EXT:
                node.state = "pending"
                path_ = node.path
                self.tag_queue.put(path_)
                logger.info(f"{node.name} > tag queue")
            # genrate tags and assign  to them
            
        node._config_stat()

    
    """
    > BACKGROUND TASK AND TAG GENRATION
    
    """
    

    def background_index_step1(self):
        logger.info("background task start")
        if self.tag_result_queue.empty():
            return False
        
    
        tag_data = self.tag_result_queue.get()
        data = self.get_node_by_path(tag_data['path'])
        node_ = data['result']
        mgs = data['message']
        logger.info(mgs)
        if node_:
            tags = tag_data['tags']
            if tags:
                print(tags)
                # vector = self.mrvec.convert_tags_to_vector(tags)
                vector = [1,2,3,4,5,6,7,8,9,10,11,12,13]

                node_.vector = vector
                node_.tags = tags
                # print(node_.tags)

                # self.mrvec.insert(node_.path, vector)
                # print(self.mrvec.path_to_vector)
            node_.state = "indexed"

            logger.info(f"{node_.path} > indexed")
        return True

    def background_index_step2(self):
        logger.info("background task start")
        if self.rehash_queue.empty():
            return False
    
        path_ = self.rehash_queue.get()
        data = self.get_node_by_path(path_)
        node_ = data['result']
        mgs = data['message']
        logger.info(mgs)
        if node_:
            self.changes_detector(node_)
        return True


if __name__ == '__main__':
    storage = Storage("save/fs_index.db")
    fs = FSManager(storage, [],[],[])
    fs.create_id_to_node()
    fs.delete('fab890f0e5fa54234b469e89ae09e2db9')
    
