from FS.constant import DEFAULT_NAME,DEFAULT_PATH,ALLOWED_TAGS_EXT
from FS.stack import Stack
from FS.prifixSearch import Trie
from FS.hash import HashMaster
from FS.extSearch import CustomHashMap
from FS.fileReader import universal_reader
from FS.useful import needs_rehash,file_hash,name_ext
from FS.cusq import Que

import os
import sys
import shutil
import hashlib
from pathlib import Path
import pickle
from queue import Queue
import time
import logging

logger = logging.getLogger("FS")


class Node:
    def __init__(self,name,path):
        self.path = path
        self.name = name
        self.childs = {}
        self.type = 'dir'

        self.state = "indexed"

        self.prifixSearch = Trie()
        self.extensionSearch =  CustomHashMap()

        self.hash = None
        self.vector = None
        self.tags = None

        # st.st_size
        self.size = None
        # st.st_mtime
        self.modified_time = None
        # st.st_ctime
        self.created_time = None
        # st.st_mode
        self.mode = None

    def _config_stat(self,st):

        self.size = st.st_size
        self.modified_time = st.st_mtime
        self.created_time = st.st_ctime
        self.mode = st.st_mode
    
    def config(self,item):
        logger.info(f"config > {self.name}")
        st = item.stat()
        self._config_stat(st)
        if item.is_dir():
            self.type = 'dir'
        else:
            self.type = 'file'
    def config_by_path(self,path):
        st = os.stat(path)
        self._config_stat(st)

    def _add_file_to_search_structure(self,node):
        self.prifixSearch.insert(node.name,node.path)
        self.extensionSearch.insert(node.name,node.path)
    
    def _del_file_to_search_structure(self,node):
        self.prifixSearch.delete(node.name,node.path)
        self.extensionSearch.delete(node.name,node.path)

    def _add_dir_to_search_structure(self,node):
        self.prifixSearch.insert(node.name,node.path)

    def _del_dir_to_search_structure(self,node):
        self.prifixSearch.delete(node.name,node.path)

    def search_prifix(self,prifix):
        return self.prifixSearch.search_by_prefix(prifix)
    
    def search_ext(self,ext):
        return self.extensionSearch.get_by_extension(ext)

    def to_dict(self):
        return {
            'name': self.name,
            'path': self.path,
            'type': self.type,
            'size': self.size,
            'modified_time': self.modified_time,
            'created_time': self.created_time,
            'mode': self.mode
        }
    
    
    
    def __repr__(self):
        return f"Node(name={self.name}, path={self.path}, type={self.type})"



class FSManager:
    '''file management'''
    def __init__(self,tagG,mrvec,db_path="save/root.pkl", autosave=True):
        self.default = DEFAULT_PATH
        self.default_name = DEFAULT_NAME
        self.tagG = tagG
        self.root = None
        self.root_store_path = db_path
        self.autosave = autosave
        self.cwd = self.root
        self.selected_nodes = []
        self.state = 'ideal'
        self.pointer = None
        self.undoStack = Stack()
        self.redoStack = Stack()
        self.hash_queue = []
        self.hash_Master = HashMaster()
        self.mrvec = mrvec
        self.tag_queue = Que()

    def normalize_path(self,path):
        return Path(path).as_posix()

    def save(self):
        """
        Save HashMaster state to pickle
        """
        data = {
            "root": self.root
        }
        with open(self.root_store_path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def save_if_autosave(self):
        if self.autosave:
            self.save()

    def load(self):
        """
        Load HashMaster state from pickle
        """
        if not os.path.exists(self.root_store_path):
            logger.error("root.pkl file not exist!")
            
            self.root = Node(self.default_name,self.default)
            self.cwd = self.root
            self.refresh_cwd()
            
            return

        try:
            with open(self.root_store_path, "rb") as f:
                data = pickle.load(f)

            self.root = data.get("root", Node(self.default_name,self.default))
            if self.root.name != self.default_name:
                raise Exception("root change")
            self.cwd = self.root
            logger.info(f"{self.root_store_path} is loaded succesfully")

        except Exception:
            # Corrupted pickle → safe reset
            logger.warning(f"{self.root_store_path} Corrupted pickle → safe reset")
            self.root = Node(self.default_name,self.default)
            self.cwd = self.root
        self.refresh_cwd()

    '''                                                                                
        CORE FEATURE OF FILE MANGEMENT SYSTEM 
        > REFRESH    
    '''
    def _refresh(self, root_node):
        stack = [root_node]

        while stack:
            node = stack.pop()

            try:
                internal = list(node.childs.keys())
                original = list(os.scandir(node.path))
                original_names = [f.name for f in original]

                # create + update
                for item in original:
                    if item.name not in internal:
                        logger.info(f"new file/dir detected > {item.name}")
                        newNode = Node(item.name, self.normalize_path(item.path))
                        newNode.config(item)

                        if item.is_dir():
                            node._add_dir_to_search_structure(newNode)
                        else:
                            node._add_file_to_search_structure(newNode)

                        node.childs[newNode.name] = newNode

                    if item.is_dir():
                        stack.append(node.childs[item.name])
                    else:
                        st = item.stat()
                        node_ = node.childs[item.name]
                        if needs_rehash(node_, st):
                            self.changes_detector(node_)

                    yield   # MICRO STEP

                # delete
                for name in internal:
                    if name not in original_names:
                        self._delete_internal(node.childs[name], node)

                    yield   # MICRO STEP

            except Exception as e:
                logger.error(f'{e}')
                yield
    
    def refresh_cwd(self): # work good
        ''' start analysis and updating tree structure from cwd '''
        logger.info(f"refresh start cwd > {self.cwd.path}")
        for _ in self._refresh(self.cwd):
            pass
        logger.info(f"refresh complete cwd > {self.cwd.path}")
        self.save_if_autosave()
    
    def refresh_root(self): # work good
        ''' start analysis and updating tree structure from root '''
        logger.info("full root loading started")
        for _ in self._refresh(self.root):
            pass
        logger.info("full root loading completed")
        self.save_if_autosave()

    def refresh_node(self,node): # work good
        ''' start analysis and updating tree structure from given node '''
        logger.info(f"refresh start > {node.path}")
        for _ in self._refresh(node):
            pass
        logger.info(f"refresh complete > {node.path}")
        self.save_if_autosave()
    
    """
       > SELECT > UNSELECT > SELECTALL > UNSELECTALL
    """ 
    def select(self,node):  # work good
        if node not in self.selected_nodes:
            self.selected_nodes.append(node)
            logger.info(f'select > {node.name}')
    
    def unselect(self,node): # work good
        if node in self.selected_nodes:
            self.selected_nodes.remove(node)
            logger.info(f'unselect > {node.name}')
    
    def _select_all(self,node): # work good
        self.select(node)
        if node.type == 'dir':
            for name,child in node.childs.items():
                self._select_all(child)
    
    def select_all(self): # work good
        self._select_all(self.cwd)
    
    def unselect_all(self): # work good
        self.selected_nodes = []
        logger.info('unselect all')

    """
        > OPEN 
    """
    def _open_file_with_default_app(self,file_path):
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
    
    def _set_cwd(self,node):
        self.undoStack.push(self.cwd)
        self.cwd = node
        self.refresh_cwd()
        logger.info(f"changed cwd > {node.path}")

    def open(self,node): # work good
        ''' open file with default application '''
        if node.type == 'file':
            self._open_file_with_default_app(node.path)
        else:
            if self.state == 'ideal':
                self.unselect_all()
            self._set_cwd(node)
            logger.info(f"changed cwd >{node.path}")

    """
     > INFO
    """
    def info(self): # work good
        return self.cwd.to_dict()
    
    """
    > DELETE
    """

    def _delete_internal(self,del_node,parent_node=None): # work good
        ''' delete file/folder from disk and tree structure '''
        if parent_node is None:
            parent_node = self.cwd
        if del_node.type == 'file':
            self.hash_Master.delete(del_node.path)
            self.mrvec.delete(del_node.path)
            parent_node._del_file_to_search_structure(del_node)

        elif del_node.type == 'dir':
            parent_node._del_dir_to_search_structure(del_node)
            for name,child in list(del_node.childs.items()):
                    self._delete_internal(child,del_node)
        del parent_node.childs[del_node.name]
        logger.info(f"delete-internal>{del_node.type} > {del_node.path}")

    def _delete_memory(self,node): # work good
        ''' delete file/folder from memeory only '''
        if node.type == 'file':
            os.remove(node.path)
            logger.info(f"delete-memory > file > {node.path}")
        elif node.type == 'dir':
            shutil.rmtree(node.path)
            logger.info(f"delete-memory > dir > {node.path}")
    
    def delete_node(self,node): # work good
        ''' delete file/folder from disk and tree structure '''
        self._delete_memory(node)
        self._delete_internal(node)
        self.save_if_autosave()
    
    def delete(self,filename):
        node = self.get_node(filename)
        if node:
            self.delete_node(node)
            return True
        return False

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
    
    def _paste_for_move(self): # work good
            if self.selected_nodes:
                for node in self.selected_nodes:
                    shutil.move(node.path,self.cwd.path)
                    logger.info(f"moved {node.path} to {self.cwd.path}")
                    self._delete_internal(node,self._get_pointer())
                logger.info("paste completed, back to ideal mode")

    def _paste_for_copy(self): # work good
            if self.selected_nodes:
                for node in self.selected_nodes:
                    if node.type == 'file':
                        shutil.copy2(node.path,self.cwd.path)
                        logger.info(f"copied {node.path} to {self.cwd.path}")
                    elif node.type == 'dir':
                        dest_path = os.path.join(self.cwd.path,node.name)
                        shutil.copytree(node.path,dest_path)
                        logger.info(f"copied directory {node.path} to {dest_path}")
                logger.info("paste completed, back to ideal mode")

    def paste(self): # work good
        '''there is a issue of already exist thing'''#<<<<<<<<<<ERROR
        if self.state == 'move':
            self._paste_for_move()
        elif self.state == 'copy':
            self._paste_for_copy()
        self.unselect_all()
        self.refresh_cwd()
        self.state = 'ideal'
    
    """
    > CREATE
    """
    def _write_content_to_file(self,filepath,content):
        with open(filepath,"w") as f:
            f.write(f'{content}\n')

    def _append_content_to_file(self,filepath,content):
        with open(filepath,"a") as f:
            f.write(f'{content}\n')

    def _config_node(self,node):
        stat = os.stat(node.path)
        node._config_stat(stat)
        
    def _create_dir_memory(self,dir_name,p_node= None): # work good
        if p_node is None:
            p_node = self.cwd
        new_dir_path = os.path.join(p_node.path,dir_name)
        os.makedirs(new_dir_path,exist_ok=True)
        logger.info("directory created at:",new_dir_path) 
    
    def _create_dir_internal(self,dir_name,p_node= None): # work good
        if p_node is None:
            p_node = self.cwd
        newNode = Node(dir_name,self.normalize_path(os.path.join(p_node.path,dir_name)))
        newNode.type = 'dir'
        p_node.childs[dir_name] = newNode
        p_node._add_dir_to_search_structure(newNode)
        logger.info("directory node created at:",newNode.path)
        return newNode
    
    def _create_file_memory(self,file_name,content="",p_node= None): # work good
        if p_node is None:
            p_node = self.cwd
        new_file_path = os.path.join(p_node.path,file_name)
        self._write_content_to_file(new_file_path,content)
        logger.info("file created at:",new_file_path)
    
    def _create_file_internal(self,file_name,p_node= None): # work good
        if p_node is None:
            p_node = self.cwd
        newNode = Node(file_name,self.normalize_path(os.path.join(p_node.path,file_name)))
        newNode.type = 'file'
        p_node.childs[file_name] = newNode
        p_node._add_file_to_search_structure(newNode)
        logger.info("file node created at:",newNode.path)
        return newNode

    def create_dir(self,dir_name,p_node= None):
        self._create_dir_memory(dir_name,p_node)
        node = self._create_dir_internal(dir_name,p_node)
        self._config_node(node)
        self.save_if_autosave()
        logger.info(f"create in dir > {dir_name}")
        return node.to_dict()

    def create_file(self,file_name,content="",p_node= None):
        self._create_file_memory(file_name,content,p_node)
        node = self._create_file_internal(file_name,p_node)
        self.hash_queue.append(node)
        self._config_node(node)
        self.save_if_autosave()
        logger.info(f"create in file > {file_name}")
        return node.to_dict()
    
    def write_to_file(self,node,content):
        if node.type == 'file':
            self._write_content_to_file(node.path,content)
            self._config_node(node)
            self.save_if_autosave()
            logger.info(f"written to file > {node.path}")
        else:
            logger.error(f"cannot write to a directory > {node.path}")
    
    def append_to_file(self,node,content):
        if node.type == 'file':
            self._append_content_to_file(node.path,content)
            self._config_node(node)
            self.save_if_autosave()
            logger.info(f"append to file > {node.path}")
        else:
            logger.error(f"cannot append to a directory > {node.path}")

    """
    > SHOW LIST

    """

    def show_list(self,filter = None): # work good
        ''' show list of files and folders in current working directory '''
        logger.info(f"call show list>: {self.cwd.path}")
        result = []
        for name,child in self.cwd.childs.items():
            result.append(child.to_dict())
        return result
    """
    > HOME >GOTO > UNDO 

    """

    def go_to_root(self): # work good
        self._set_cwd(self.root)   
    
    def go_to(self,name): # work good
        if self.state == 'ideal':
            self.unselect_all()
        if name in self.cwd.childs:
            node = self.cwd.childs[name]
            self.open(node)
        else:
            logger.info(f"{name} not found in cwd")
    
    def go_back(self): # work good
        if self.state == 'ideal':
            self.unselect_all()
        if self.undoStack.empty():
            logger.info("no undo -> Empty")
            print("no undo -> Empty")
            return
        # it not need history push
        self.redoStack.push(self.cwd)
        prev_node = self.undoStack.pop()
        self.cwd = prev_node

    def go_forward(self): # work good
        if self.state == 'ideal':
            self.unselect_all()
        if self.redoStack.empty():
            logger.info("no redo->empty")
            print("no redo->empty")
            return
        # it not need history push
        prev_node = self.redoStack.pop()
        self._set_cwd(prev_node)

    def go_to_address(self,path):
        data = self.get_node_by_path(path)
        r = data['result']
        m = data['message']
        if r:
            self._set_cwd(r)
            return (True,m)
        return (False,m)



    """
   > RENAME

    """
    def _rename_internal(self,filename,node,p_node=None):
        if p_node is None:
            p_node = self.cwd
        if node.type == 'dir':
            p_node._del_dir_to_search_structure(node)    
        else:
            self.hash_Master.delete(node.path)
            self.mrvec.delete(node.path)
            p_node._del_file_to_search_structure(node)    

        node.path  = node.path[:-len(node.name)]+filename #path change
        

        del p_node.childs[node.name]
        p_node.childs[filename] = node
        
        node.name = filename
        self._config_node(node)
        if node.type == 'dir':
            p_node._add_dir_to_search_structure(node)    
        else:
            p_node._add_file_to_search_structure(node)
            self.hash_queue.append(node)    
          
    def _rename_memory(self,name,node):
        old_add = node.path
        new_add = node.path[:-len(node.name)]+name
        os.rename(old_add,new_add)

    def rename_node(self,name,node,p_node=None):
        self._rename_memory(name,node)
        self._rename_internal(name,node,p_node)
        logger.info(f"rename > '{node.name}' to '{name}'")
        
    def rename(self,old,new):
        if new not in self.cwd.childs:
            node = self.get_node(old)
            if node:
                self.rename_node(new,node)
                return True

        return False
        

    """
     > SEARCH
    """ 
    "PRIFIX AND EXTENSION"
    def search_helper_prifix(self,node,prifix,results):
        result = node.search_prifix(prifix)
        results += result
        for item in node.childs.values():
            if item.type == 'dir':
                self.search_helper_prifix(item,prifix,results)
        return results

    def search_helper_ext(self,node,ext,results):
        result = node.search_ext(ext)
        results += result
        for item in node.childs.values():
            if item.type == 'dir':
                self.search_helper_ext(item,ext,results)
        return results

    def search_prifix(self,prifix):
        results = []
        self.search_helper_prifix(self.cwd,prifix,results)
        return results

    def search_prifix_all(self,prifix):
        results = []
        self.search_helper_prifix(self.root,prifix,results)
        return results
    
    def search_ext(self,ext):
        results = []
        self.search_helper_ext(self.cwd,ext,results)
        return results

    def search_ext_all(self,ext):
        results = []
        self.search_helper_ext(self.root,ext,results)
        return results

    "HASH"
    def search_hash_by_path(self, path: str):
        return self.hash_Master.search_hash_by_path(path)
        
    def search_paths_by_hash(self, file_hash: str):
        return self.hash_Master.search_paths_by_hash(file_hash)

    def search_duplicate_files(self):
        return self.hash_Master.search_duplicate_files()

    """
        EXTRA HELPING FEATURES 
        >GET NODE > GET NODE BY PATH

    """

    def get_node(self,filename): # work good
        if filename in self.cwd.childs.keys():
            return self.cwd.childs[filename]
        else:
            return None

    def path_verifier(self,path):
        return True if self.root.path in path else False

    def path_breaker(self,path):
        rootv=self.root.path.split('/')
        pathv=path.split('/')
        length = len(rootv)
        return pathv[length:]
    
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
    > CONTEXT CHANGE DETECT 
    
    """
    def changes_detector(self,node):

        hash_ = file_hash(node.path)
        if node.hash != hash_:
            logger.info(f'file content changes detected > {node.path}')
            
            node.hash = hash_ # update hash
            self.hash_Master.insert(node.path,hash_) # update and add hash in path_to_hash dictss
            result = name_ext(node.name)
            if result['ext'] in ALLOWED_TAGS_EXT:
                node.state = "pending"
                self.tag_queue.put(node.path)
                logger.info(f"{node.name} > tag queue")
            # genrate tags and assign  to them
            
        node.config_by_path(node.path)
    
    """
    > BACKGROUND TASK AND TAG GENRATION
    
    """


    def background_index_step(self):
        logger.info("background task start")
        if self.tag_queue.empty():
            return False
    
        path_ = self.tag_queue.get()
        data = self.get_node_by_path(path_)
        node_ = data['result']
        mgs = data['message']
        logger.info(mgs)
        if node_:
            tags = self.tagG.generate_tags_path(node_.path)
            vector = self.mrvec.convert_tags_to_vector(tags)

            node_.vector = vector
            node_.tags = tags

            self.mrvec.insert(node_.path, vector)
            node_.state = "indexed"

            logger.info(f"{node_.path} > indexed")
        return True
            